"""What a human reviewer receives.

A reviewer should open a case already knowing why it is in front of them. The
packet carries the failing checks first, in plain language, so the reviewer
starts from the disagreement instead of hunting for it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .domain import Decision, VerificationCase
from .pii import mask_name, mask_number, pseudonymize


@dataclass(frozen=True)
class ReviewPacket:
    case_id: str
    outcome: str
    headline: str
    reasons: tuple[str, ...]
    checks: tuple[dict[str, Any], ...]


def build_packet(case: VerificationCase, decision: Decision) -> ReviewPacket:
    checks = tuple(
        {
            "check": signal.name,
            "score": signal.score,
            "available": signal.available,
            "detail": signal.detail,
        }
        for signal in decision.signals
    )
    headline = (
        "Cleared automatically; no reviewer action required."
        if not decision.reasons
        else f"{len(decision.reasons)} check(s) need a look: {decision.reasons[0]}"
    )
    return ReviewPacket(
        case_id=case.case_id,
        outcome=decision.outcome.value,
        headline=headline,
        reasons=decision.reasons,
        checks=checks,
    )


def to_log_record(case: VerificationCase, decision: Decision, *, salt: str) -> dict[str, Any]:
    """A record safe to send to logs, metrics, and error tracking.

    Scores and outcomes travel; names and document numbers do not.
    """
    return {
        "case_ref": pseudonymize(case.case_id, salt),
        "provider": case.provider.value,
        "outcome": decision.outcome.value,
        "reason_count": len(decision.reasons),
        "scores": {s.name: s.score for s in decision.signals if s.available},
        "unavailable": [s.name for s in decision.signals if not s.available],
        "name_preview": mask_name(case.claim.full_name),
        "document_preview": mask_number(case.document.document_number),
    }
