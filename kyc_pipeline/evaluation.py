"""Measuring how well the pipeline routes.

`docs/evaluation.md` argues that an automation clearing identity checks has to
be measured before it is trusted. This module is that measurement.

Two errors matter, and they are not symmetric:

* A **missed escalation** is a case the pipeline cleared that a reviewer would
  have stopped. This is the error that lets something through, and it is the
  one that governs whether automation is safe to switch on at all.
* An **unnecessary escalation** is a case the pipeline sent to a human that the
  reviewer cleared without hesitation. This costs reviewer time, which is the
  thing automation was meant to save.

Reporting a single accuracy number would blur the two together, so this module
never does.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .domain import Decision, Outcome, VerificationCase
from .orchestrator import Orchestrator
from .providers import load_case
from .synthetic import generate

DEFAULT_CASES = Path("data/synthetic/cases.json")
DEFAULT_LABELS = Path("data/synthetic/labels.json")

CLEAR = "clear"
ESCALATE = "escalate"


@dataclass(frozen=True)
class CaseResult:
    """One case, what the pipeline did, and what a reviewer would have done."""

    case_id: str
    provider: str
    pipeline_outcome: str
    reviewer_outcome: str
    reasons: tuple[str, ...]

    @property
    def pipeline_cleared(self) -> bool:
        return self.pipeline_outcome == Outcome.AUTO_CLEAR.value

    @property
    def reviewer_cleared(self) -> bool:
        return self.reviewer_outcome == CLEAR

    @property
    def missed_escalation(self) -> bool:
        """Cleared automatically when a reviewer would have stopped it."""
        return self.pipeline_cleared and not self.reviewer_cleared

    @property
    def unnecessary_escalation(self) -> bool:
        """Sent to a human who would have cleared it anyway."""
        return not self.pipeline_cleared and self.reviewer_cleared

    @property
    def agrees(self) -> bool:
        return self.pipeline_cleared == self.reviewer_cleared


@dataclass
class Evaluation:
    """Aggregate view over every labelled case."""

    results: list[CaseResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def cleared(self) -> list[CaseResult]:
        return [r for r in self.results if r.pipeline_cleared]

    @property
    def escalated(self) -> list[CaseResult]:
        return [r for r in self.results if not r.pipeline_cleared]

    @property
    def missed_escalations(self) -> list[CaseResult]:
        return [r for r in self.results if r.missed_escalation]

    @property
    def unnecessary_escalations(self) -> list[CaseResult]:
        return [r for r in self.results if r.unnecessary_escalation]

    @property
    def escalation_rate(self) -> float:
        return len(self.escalated) / self.total if self.total else 0.0

    @property
    def agreement_on_cleared(self) -> float:
        """Share of auto-cleared cases a reviewer would also have cleared.

        The safety number. One below 1.0 means the pipeline is letting through
        cases a human would have stopped.
        """
        cleared = self.cleared
        if not cleared:
            return 1.0
        return sum(1 for r in cleared if r.reviewer_cleared) / len(cleared)

    @property
    def overall_agreement(self) -> float:
        return sum(1 for r in self.results if r.agrees) / self.total if self.total else 0.0

    def reason_frequency(self) -> list[tuple[str, int]]:
        """Which checks send cases to humans, most often first."""
        counter: Counter[str] = Counter()
        for result in self.escalated:
            for reason in result.reasons:
                counter[reason.split(" scored ")[0].split(" (")[0]] += 1
        return counter.most_common()

    def by_provider(self) -> dict[str, dict[str, Any]]:
        """Per-provider slice. An aggregate can hide one provider doing badly."""
        out: dict[str, dict[str, Any]] = {}
        for provider in sorted({r.provider for r in self.results}):
            subset = [r for r in self.results if r.provider == provider]
            cleared = [r for r in subset if r.pipeline_cleared]
            out[provider] = {
                "cases": len(subset),
                "cleared": len(cleared),
                "escalated": len(subset) - len(cleared),
                "missed_escalations": sum(1 for r in subset if r.missed_escalation),
            }
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_cases": self.total,
            "auto_cleared": len(self.cleared),
            "escalated": len(self.escalated),
            "escalation_rate": round(self.escalation_rate, 4),
            "agreement_on_cleared": round(self.agreement_on_cleared, 4),
            "overall_agreement": round(self.overall_agreement, 4),
            "missed_escalations": [r.case_id for r in self.missed_escalations],
            "unnecessary_escalations": [r.case_id for r in self.unnecessary_escalations],
            "escalation_reasons": dict(self.reason_frequency()),
            "by_provider": self.by_provider(),
        }


def load_labels(path: Path | None = None) -> dict[str, str]:
    """Read reviewer labels, keyed by case id."""
    path = path or DEFAULT_LABELS
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {case_id: entry["reviewer_outcome"] for case_id, entry in payload["labels"].items()}


def load_cases(path: Path | None = None) -> list[VerificationCase]:
    path = path or DEFAULT_CASES
    payloads = json.loads(path.read_text(encoding="utf-8")) if path.exists() else generate()
    return [load_case(p) for p in payloads]


def evaluate(
    cases: Iterable[VerificationCase],
    labels: Mapping[str, str],
    orchestrator: Orchestrator | None = None,
) -> Evaluation:
    """Route every labelled case and compare against the reviewer's decision."""
    orchestrator = orchestrator or Orchestrator()
    evaluation = Evaluation()
    for case in cases:
        label = labels.get(case.case_id)
        if label is None:
            continue  # unlabelled cases cannot be scored, and guessing would be worse
        decision: Decision = orchestrator.evaluate(case)
        evaluation.results.append(
            CaseResult(
                case_id=case.case_id,
                provider=case.provider.value,
                pipeline_outcome=decision.outcome.value,
                reviewer_outcome=label,
                reasons=decision.reasons,
            )
        )
    return evaluation


def format_report(evaluation: Evaluation) -> str:
    lines: list[str] = []
    lines.append(f"Cases evaluated: {evaluation.total}")
    lines.append(
        f"Auto-cleared:    {len(evaluation.cleared)}  "
        f"Escalated: {len(evaluation.escalated)}  "
        f"(escalation rate {evaluation.escalation_rate:.0%})"
    )
    lines.append(f"Agreement on auto-cleared cases: {evaluation.agreement_on_cleared:.0%}")
    lines.append(f"Overall agreement with reviewers: {evaluation.overall_agreement:.0%}")
    lines.append("")

    missed = evaluation.missed_escalations
    lines.append(f"Missed escalations ({len(missed)}) - cleared, but a reviewer would not have:")
    lines.extend(f"  - {r.case_id}" for r in missed) if missed else lines.append("  none")

    unnecessary = evaluation.unnecessary_escalations
    lines.append("")
    lines.append(f"Unnecessary escalations ({len(unnecessary)}) - reviewer time spent on clean cases:")
    lines.extend(f"  - {r.case_id}" for r in unnecessary) if unnecessary else lines.append("  none")

    lines.append("")
    lines.append("What sends cases to humans:")
    for reason, count in evaluation.reason_frequency():
        lines.append(f"  {count:>3}  {reason}")

    lines.append("")
    lines.append("By provider:")
    for provider, stats in evaluation.by_provider().items():
        lines.append(
            f"  {provider:<16} {stats['cases']} cases, "
            f"{stats['cleared']} cleared, {stats['escalated']} escalated, "
            f"{stats['missed_escalations']} missed"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a report")
    parser.add_argument(
        "--allow-missed-escalations",
        action="store_true",
        help="exit 0 even when a case a reviewer would stop was cleared automatically",
    )
    args = parser.parse_args(argv)

    evaluation = evaluate(load_cases(args.cases), load_labels(args.labels))
    print(json.dumps(evaluation.to_dict(), indent=2) if args.json else format_report(evaluation))

    if evaluation.missed_escalations and not args.allow_missed_escalations:
        print(
            f"\nFAIL: {len(evaluation.missed_escalations)} case(s) cleared that a reviewer would have stopped.",
        )
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
