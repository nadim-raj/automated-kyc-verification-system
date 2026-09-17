"""Frame sampling.

Scoring every frame of a verification video buys very little and costs a lot.
Sampling evenly across the clip keeps the cost flat regardless of length, and
covers the whole recording rather than only its opening seconds.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from ..domain import ImageRef, VideoRef


@runtime_checkable
class FrameSource(Protocol):
    def frames(self, video: VideoRef) -> Sequence[ImageRef]: ...


class PrefetchedFrameSource:
    """Frames the provider or a fixture already supplied."""

    def frames(self, video: VideoRef) -> Sequence[ImageRef]:
        return list(video.frames)


class OpenCVFrameSource:  # pragma: no cover - requires the optional dependency
    """Decode frames from a real video file with OpenCV."""

    def __init__(self) -> None:
        import cv2  # noqa: F401 - imported lazily, part of the ``ml`` extra

        raise NotImplementedError(
            "Decoding is deployment-specific; this repository runs on prefetched frames."
        )


def sample_frames(video: VideoRef, *, max_frames: int = 12, source: FrameSource | None = None) -> list[ImageRef]:
    """Take up to ``max_frames`` frames spread evenly across the video."""
    available = list((source or PrefetchedFrameSource()).frames(video))
    if not available or max_frames <= 0:
        return []
    if len(available) <= max_frames:
        return available
    step = len(available) / max_frames
    return [available[min(int(i * step), len(available) - 1)] for i in range(max_frames)]
