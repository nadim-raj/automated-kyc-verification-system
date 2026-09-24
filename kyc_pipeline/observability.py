"""Telemetry for a pipeline that handles identity documents.

Two things make observability here different from an ordinary service.

The first is that the interesting signal is not latency or error rate, but
*routing drift*: the share of cases reaching a human, and which check sent them
there. A pipeline that quietly starts escalating everything is still returning
200s, and a pipeline that quietly stops escalating is worse.

The second is that everything flowing through it is personal data. Logs get
copied to more places than anyone tracks - aggregators, error trackers, local
terminals, screenshots in tickets. So the rule here is absolute: scores and
outcomes travel, identities do not. `personal_data_leaks` exists to make that
rule testable rather than aspirational.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .domain import Decision, Outcome, VerificationCase
from .pii import mask_name, mask_number, pseudonymize


def reason_code(reason: str) -> str:
    """Reduce a reason sentence to the check that produced it.

    Counting raw reason strings would produce a cardinality explosion, because
    every one carries a score. The check name is the part worth grouping on.
    """
    return reason.split(" scored ")[0].split(" (")[0].strip()


@dataclass
class PipelineMetrics:
    """Counters over a batch or a window of cases."""

    cases: int = 0
    outcomes: Counter = field(default_factory=Counter)
    reasons: Counter = field(default_factory=Counter)
    unavailable: Counter = field(default_factory=Counter)
    providers: Counter = field(default_factory=Counter)

    def record(self, case: VerificationCase, decision: Decision) -> None:
        self.cases += 1
        self.outcomes[decision.outcome.value] += 1
        self.providers[case.provider.value] += 1
        for reason in decision.reasons:
            self.reasons[reason_code(reason)] += 1
        for signal in decision.signals:
            if not signal.available:
                self.unavailable[signal.name] += 1

    @property
    def escalation_rate(self) -> float:
        if not self.cases:
            return 0.0
        return (self.cases - self.outcomes.get(Outcome.AUTO_CLEAR.value, 0)) / self.cases

    def to_dict(self) -> dict[str, Any]:
        return {
            "cases": self.cases,
            "escalation_rate": round(self.escalation_rate, 4),
            "outcomes": dict(self.outcomes),
            "escalation_reasons": dict(self.reasons),
            "unavailable_signals": dict(self.unavailable),
            "providers": dict(self.providers),
        }


def log_record(case: VerificationCase, decision: Decision, *, salt: str) -> dict[str, Any]:
    """One structured record per case, safe to ship anywhere logs go.

    Carries what an on-call engineer needs to explain a routing decision, and
    nothing that identifies the person it was about.
    """
    return {
        "event": "verification.decision",
        "case_ref": pseudonymize(case.case_id, salt),
        "provider": case.provider.value,
        "outcome": decision.outcome.value,
        "reason_codes": [reason_code(r) for r in decision.reasons],
        "reason_count": len(decision.reasons),
        "scores": {s.name: s.score for s in decision.signals if s.available},
        "unavailable": [s.name for s in decision.signals if not s.available],
        "media": {"video": case.media.has_video, "face_pair": case.media.has_face_pair},
        "name_preview": mask_name(case.claim.full_name),
        "document_preview": mask_number(case.document.document_number),
    }


def emit(record: Mapping[str, Any]) -> str:
    """Serialise a record deterministically, one line per event."""
    return json.dumps(record, sort_keys=True, separators=(",", ":"))


def personal_data_leaks(record: Mapping[str, Any], case: VerificationCase) -> list[str]:
    """Return any raw identifying values from `case` that appear in `record`.

    An empty list is the only acceptable result. This is deliberately a function
    rather than a line in a style guide: a rule that cannot be asserted is a
    rule that erodes the first time somebody adds a field "just for debugging".
    """
    serialised = emit(record)
    candidates = {
        "claim_name": case.claim.full_name,
        "document_name": case.document.full_name,
        "claim_document_number": case.claim.document_number,
        "document_number": case.document.document_number,
        "date_of_birth": str(case.claim.date_of_birth) if case.claim.date_of_birth else None,
        "case_id": case.case_id,
    }
    return [
        label
        for label, value in candidates.items()
        if value and len(str(value)) > 3 and str(value) in serialised
    ]


def observe(pairs: Iterable[tuple[VerificationCase, Decision]], *, salt: str) -> tuple[PipelineMetrics, list[str]]:
    """Fold a batch into metrics and their log lines."""
    metrics = PipelineMetrics()
    lines: list[str] = []
    for case, decision in pairs:
        metrics.record(case, decision)
        lines.append(emit(log_record(case, decision, salt=salt)))
    return metrics, lines
