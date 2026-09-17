"""Comparisons built on face embeddings."""

from __future__ import annotations

from typing import Iterable

from ..domain import ImageRef, MediaBundle, Signal
from .embedding import FaceEmbedder, cosine


def face_match_signal(media: MediaBundle, embedder: FaceEmbedder) -> Signal:
    """Does the selfie look like the portrait on the identity document?"""
    if not media.has_face_pair:
        return Signal.missing("face_match", "a selfie or document portrait was not supplied")
    selfie = embedder.embed(media.selfie)  # type: ignore[arg-type]
    portrait = embedder.embed(media.document_portrait)  # type: ignore[arg-type]
    if selfie is None or portrait is None:
        return Signal.missing("face_match", "an embedding could not be produced")
    return Signal(
        name="face_match",
        score=round(cosine(selfie, portrait), 4),
        available=True,
        detail="selfie compared with the document portrait",
    )


def video_consistency_signal(
    frames: Iterable[ImageRef],
    reference: ImageRef | None,
    embedder: FaceEmbedder,
) -> Signal:
    """Is the person in the video the same one as on the document, throughout?

    Reports the weakest frame rather than the average: an average hides the few
    frames where somebody else is in shot, which are exactly the frames worth
    a reviewer's attention.
    """
    frames = list(frames)
    if reference is None or not frames:
        return Signal.missing("video_consistency", "no video frames or no reference portrait")
    reference_vector = embedder.embed(reference)
    if reference_vector is None:
        return Signal.missing("video_consistency", "the reference portrait could not be embedded")

    scores: list[float] = []
    for frame in frames:
        vector = embedder.embed(frame)
        if vector is not None:
            scores.append(cosine(vector, reference_vector))
    if not scores:
        return Signal.missing("video_consistency", "no frame could be embedded")

    weakest = min(scores)
    mean = sum(scores) / len(scores)
    return Signal(
        name="video_consistency",
        score=round(weakest, 4),
        available=True,
        detail=f"weakest of {len(scores)} frames {weakest:.2f}, mean {mean:.2f}",
    )
