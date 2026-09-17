"""Routing policy.

Every number here is an **illustrative placeholder** chosen so the synthetic
demo produces a readable spread of outcomes. They are not the values used in
any production system, and publishing calibrated thresholds for a fraud control
would be a poor idea in any case: a public threshold is a public instruction for
staying just underneath it.

Real calibration belongs in private configuration, derived from a reviewer-
labelled sample and revisited as the mix of customers changes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionPolicy:
    """Score bands used to route a case."""

    name_auto_clear: float = 0.93
    dob_auto_clear: float = 1.0
    document_number_auto_clear: float = 1.0
    nationality_auto_clear: float = 1.0
    face_auto_clear: float = 0.78
    sole_presence_auto_clear: float = 0.95
    video_consistency_auto_clear: float = 0.70

    #: Providers that return no video can still clear on documents alone.
    allow_text_only_auto_clear: bool = True

    #: Off by design. The pipeline clears clean cases and escalates the rest;
    #: declining somebody's identity is a decision a human makes and owns.
    auto_decline_enabled: bool = False

    def threshold_for(self, signal_name: str) -> float | None:
        return {
            "name_match": self.name_auto_clear,
            "dob_match": self.dob_auto_clear,
            "document_number_match": self.document_number_auto_clear,
            "nationality_match": self.nationality_auto_clear,
            "face_match": self.face_auto_clear,
            "sole_presence": self.sole_presence_auto_clear,
            "video_consistency": self.video_consistency_auto_clear,
        }.get(signal_name)
