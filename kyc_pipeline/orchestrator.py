"""Turning signals into a routing decision.

The pipeline answers one question: can this case be cleared without a person
looking at it? Anything else goes to a reviewer with the reasons attached, so
the queue arrives pre-explained rather than as a pile of raw cases.
"""

from __future__ import annotations

from .domain import Decision, Outcome, ProviderKind, Signal, VerificationCase
from .face.embedding import FaceEmbedder, SyntheticEmbedder
from .face.presence import FaceCounter, SyntheticFaceCounter, sole_presence_signal
from .face.verification import face_match_signal, video_consistency_signal
from .matching import text_signals
from .policy import DecisionPolicy
from .video.sampling import sample_frames


class Orchestrator:
    """Scores a case and routes it."""

    def __init__(
        self,
        *,
        policy: DecisionPolicy | None = None,
        embedder: FaceEmbedder | None = None,
        counter: FaceCounter | None = None,
        max_frames: int = 12,
    ) -> None:
        self.policy = policy or DecisionPolicy()
        self.embedder = embedder or SyntheticEmbedder()
        self.counter = counter or SyntheticFaceCounter()
        self.max_frames = max_frames

    def collect_signals(self, case: VerificationCase) -> tuple[Signal, ...]:
        signals: list[Signal] = list(text_signals(case.claim, case.document))
        media = case.media

        if media.has_face_pair:
            signals.append(face_match_signal(media, self.embedder))

        if media.has_video:
            frames = sample_frames(media.video, max_frames=self.max_frames)  # type: ignore[arg-type]
            signals.append(sole_presence_signal(frames, self.counter))
            signals.append(video_consistency_signal(frames, media.document_portrait, self.embedder))

        return tuple(signals)

    def evaluate(self, case: VerificationCase) -> Decision:
        signals = self.collect_signals(case)
        reasons: list[str] = []

        for signal in signals:
            threshold = self.policy.threshold_for(signal.name)
            if threshold is None or not signal.available:
                continue
            if not signal.passes(threshold):
                reasons.append(
                    f"{signal.name} scored {signal.score:.2f} against {threshold:.2f} ({signal.detail})"
                )

        reasons.extend(self._coverage_gaps(case))

        outcome = Outcome.AUTO_CLEAR if not reasons else Outcome.REVIEW
        if reasons and self.policy.auto_decline_enabled and self._contradicted(signals):
            outcome = Outcome.DECLINE

        return Decision(
            case_id=case.case_id,
            outcome=outcome,
            reasons=tuple(reasons),
            signals=signals,
        )

    def _coverage_gaps(self, case: VerificationCase) -> list[str]:
        """Reasons that come from missing evidence rather than a failing check."""
        gaps: list[str] = []
        media = case.media

        if not media.has_face_pair:
            gaps.append("no selfie and document portrait pair to compare")

        if case.provider is ProviderKind.VIDEO_CAPABLE and not media.has_video:
            gaps.append("this provider supplies video, but none was attached to the case")

        if case.provider is ProviderKind.DATA_ONLY and not self.policy.allow_text_only_auto_clear:
            gaps.append("policy requires media evidence, which this provider does not supply")

        return gaps

    @staticmethod
    def _contradicted(signals: tuple[Signal, ...]) -> bool:
        """Flatly contradicted identity fields, rather than a weak similarity score."""
        by_name = {s.name: s for s in signals}
        dob = by_name.get("dob_match")
        number = by_name.get("document_number_match")
        return bool(
            dob and dob.available and dob.score == 0.0
            and number and number.available and (number.score or 0.0) < 0.5
        )
