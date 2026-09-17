"""Domain objects shared by every stage of the pipeline.

Everything here is provider-agnostic on purpose: adapters translate a vendor
payload into these types, and the rest of the pipeline never learns which
vendor a case came from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Mapping, Sequence


class ProviderKind(str, Enum):
    """What a verification provider is able to supply."""

    VIDEO_CAPABLE = "video_capable"
    DATA_ONLY = "data_only"


class Outcome(str, Enum):
    """Where a case is routed once the pipeline has scored it."""

    AUTO_CLEAR = "auto_clear"
    REVIEW = "review"
    DECLINE = "decline"


@dataclass(frozen=True)
class IdentityClaim:
    """What the customer told us when they registered."""

    full_name: str
    date_of_birth: date | None = None
    nationality: str | None = None
    document_number: str | None = None


@dataclass(frozen=True)
class DocumentExtract:
    """What was read off the identity document the customer submitted."""

    full_name: str
    date_of_birth: date | None = None
    nationality: str | None = None
    document_number: str | None = None
    document_type: str | None = None


@dataclass(frozen=True)
class ImageRef:
    """A pointer to an image.

    `payload` carries synthetic fixture data and is always empty for real
    captures, where `uri` points at the object store instead.
    """

    uri: str
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VideoRef:
    """A pointer to a recorded video, plus any frames already sampled from it."""

    uri: str
    duration_s: float = 0.0
    frames: Sequence[ImageRef] = ()


@dataclass(frozen=True)
class MediaBundle:
    """The media a provider returned. Any field may be absent."""

    selfie: ImageRef | None = None
    document_portrait: ImageRef | None = None
    video: VideoRef | None = None

    @property
    def has_video(self) -> bool:
        return self.video is not None and bool(self.video.frames)

    @property
    def has_face_pair(self) -> bool:
        return self.selfie is not None and self.document_portrait is not None


@dataclass(frozen=True)
class VerificationCase:
    """One customer's verification attempt, normalised across providers."""

    case_id: str
    provider: ProviderKind
    claim: IdentityClaim
    document: DocumentExtract
    media: MediaBundle = field(default_factory=MediaBundle)


@dataclass(frozen=True)
class Signal:
    """One scored comparison.

    `available` is False when the inputs a signal needs were not supplied — a
    missing signal is deliberately distinct from a failing one, because the two
    call for different handling.
    """

    name: str
    score: float | None
    available: bool
    detail: str = ""

    @classmethod
    def missing(cls, name: str, detail: str) -> "Signal":
        return cls(name=name, score=None, available=False, detail=detail)

    def passes(self, threshold: float) -> bool:
        return self.available and self.score is not None and self.score >= threshold


@dataclass(frozen=True)
class Decision:
    """The pipeline's output for one case."""

    case_id: str
    outcome: Outcome
    reasons: tuple[str, ...]
    signals: tuple[Signal, ...]

    def signal(self, name: str) -> Signal | None:
        for s in self.signals:
            if s.name == name:
                return s
        return None
