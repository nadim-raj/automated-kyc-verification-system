"""Threshold sensitivity: what happens to routing when a band moves.

The bands in `policy.py` are placeholders. This module exists because the
interesting question is not what they are, but how you would arrive at real
ones — and what each is worth.

For every band it sweeps a range of values, re-runs the evaluation at each
step, and reports the trade-off: tighten a band and more cases reach a human;
loosen it and more clear automatically, until cases a reviewer would have
stopped start slipping through.

Two honest limits, stated here because a sensitivity curve looks authoritative
whether or not it means anything:

* **Synthetic fixtures cannot calibrate anything.** Eleven invented cases show
  the shape of the trade-off, not where the line belongs. Real values come from
  a reviewer-labelled sample of real traffic.
* **A band that changes nothing is a gap in the data, not a safe band.** The
  report names those explicitly rather than showing a flat line and moving on.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .domain import VerificationCase
from .evaluation import Evaluation, evaluate, load_cases, load_labels
from .orchestrator import Orchestrator
from .policy import DecisionPolicy

#: Bands worth sweeping, with the range each is swept over.
SCORE_BANDS: tuple[str, ...] = (
    "name_auto_clear",
    "face_auto_clear",
    "sole_presence_auto_clear",
    "video_consistency_auto_clear",
)

#: Exact-match bands. Sweeping them is still informative: it shows how much of
#: the escalation volume rests on fields that currently demand a perfect match.
EXACT_BANDS: tuple[str, ...] = (
    "dob_auto_clear",
    "document_number_auto_clear",
    "nationality_auto_clear",
)


def default_grid(start: float = 0.50, stop: float = 1.00, step: float = 0.05) -> tuple[float, ...]:
    values: list[float] = []
    current = start
    while current <= stop + 1e-9:
        values.append(round(current, 2))
        current += step
    return tuple(values)


@dataclass(frozen=True)
class SweepPoint:
    """One band held at one value, scored against the reviewer labels."""

    band: str
    value: float
    escalated: int
    escalation_rate: float
    missed_escalations: int
    unnecessary_escalations: int
    agreement_on_cleared: float

    @classmethod
    def from_evaluation(cls, band: str, value: float, evaluation: Evaluation) -> "SweepPoint":
        return cls(
            band=band,
            value=value,
            escalated=len(evaluation.escalated),
            escalation_rate=round(evaluation.escalation_rate, 4),
            missed_escalations=len(evaluation.missed_escalations),
            unnecessary_escalations=len(evaluation.unnecessary_escalations),
            agreement_on_cleared=round(evaluation.agreement_on_cleared, 4),
        )


@dataclass(frozen=True)
class BandSweep:
    """Every point for one band, plus what the shape of it means."""

    band: str
    points: tuple[SweepPoint, ...]

    @property
    def is_inert(self) -> bool:
        """True when no value in the range changes any routing decision."""
        return len({p.escalated for p in self.points}) <= 1

    @property
    def safe_ceiling(self) -> float | None:
        """Loosest value that still misses no escalation, if one exists."""
        safe = [p.value for p in self.points if p.missed_escalations == 0]
        return min(safe) if safe else None

    @property
    def escalation_span(self) -> tuple[int, int]:
        counts = [p.escalated for p in self.points]
        return (min(counts), max(counts))


def sweep_band(
    band: str,
    cases: Sequence[VerificationCase],
    labels: Mapping[str, str],
    values: Iterable[float] | None = None,
    base_policy: DecisionPolicy | None = None,
) -> BandSweep:
    """Hold every other band fixed and move one."""
    base = base_policy or DecisionPolicy()
    if not hasattr(base, band):
        raise ValueError(f"unknown band: {band!r}")
    points = []
    for value in values or default_grid():
        policy = replace(base, **{band: value})
        evaluation = evaluate(cases, labels, Orchestrator(policy=policy))
        points.append(SweepPoint.from_evaluation(band, value, evaluation))
    return BandSweep(band=band, points=tuple(points))


def sweep_all(
    cases: Sequence[VerificationCase],
    labels: Mapping[str, str],
    bands: Iterable[str] = SCORE_BANDS + EXACT_BANDS,
    base_policy: DecisionPolicy | None = None,
) -> list[BandSweep]:
    return [sweep_band(b, cases, labels, base_policy=base_policy) for b in bands]


def format_report(sweeps: Sequence[BandSweep], total_cases: int) -> str:
    lines: list[str] = []
    lines.append(f"Threshold sensitivity across {total_cases} labelled cases")
    lines.append("Each band is moved on its own; every other band stays at its default.")
    lines.append("")

    active = [s for s in sweeps if not s.is_inert]
    inert = [s for s in sweeps if s.is_inert]

    for sweep in active:
        low, high = sweep.escalation_span
        lines.append(f"{sweep.band}  (escalations range {low}-{high})")
        lines.append("   value   escalated   missed   wasted   agreement")
        for p in sweep.points:
            flag = "  <-- misses an escalation" if p.missed_escalations else ""
            lines.append(
                f"   {p.value:<7.2f} {p.escalated:^9} {p.missed_escalations:^8} "
                f"{p.unnecessary_escalations:^8} {p.agreement_on_cleared:^10.0%}{flag}"
            )
        ceiling = sweep.safe_ceiling
        lines.append(
            f"   loosest value that still misses nothing: {ceiling:.2f}"
            if ceiling is not None
            else "   no value in this range avoids missing an escalation"
        )
        lines.append("")

    if inert:
        lines.append("Bands no fixture exercises (every value routes identically):")
        for sweep in inert:
            lines.append(f"   {sweep.band}")
        lines.append("")
        lines.append("   A flat band is a gap in the test data, not a safe setting. Each one")
        lines.append("   needs a case that depends on it before its value means anything.")
        lines.append("")

    lines.append("These curves show the shape of the trade-off, not where the line belongs.")
    lines.append("Real values come from a reviewer-labelled sample of real traffic.")
    return "\n".join(lines)


def to_dict(sweeps: Sequence[BandSweep]) -> dict[str, object]:
    return {
        sweep.band: {
            "inert": sweep.is_inert,
            "safe_ceiling": sweep.safe_ceiling,
            "points": [
                {
                    "value": p.value,
                    "escalated": p.escalated,
                    "escalation_rate": p.escalation_rate,
                    "missed_escalations": p.missed_escalations,
                    "unnecessary_escalations": p.unnecessary_escalations,
                    "agreement_on_cleared": p.agreement_on_cleared,
                }
                for p in sweep.points
            ],
        }
        for sweep in sweeps
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=None)
    parser.add_argument("--labels", type=Path, default=None)
    parser.add_argument("--band", action="append", help="sweep only this band (repeatable)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    cases = load_cases(args.cases)
    labels = load_labels(args.labels)
    bands = tuple(args.band) if args.band else SCORE_BANDS + EXACT_BANDS
    sweeps = sweep_all(cases, labels, bands)

    print(json.dumps(to_dict(sweeps), indent=2) if args.json else format_report(sweeps, len(cases)))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
