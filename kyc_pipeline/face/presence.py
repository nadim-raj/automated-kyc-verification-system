"""How many faces appear in the frame.

The check is deliberately coarse: it reports how consistently a single face is
present across sampled frames, and leaves the judgement to the policy layer and,
for anything short of clean, to a human reviewer.
"""

from __future__ import annotations

from typing import Iterable, Protocol, runtime_checkable

from ..domain import ImageRef, Signal


@runtime_checkable
class FaceCounter(Protocol):
    def count(self, image: ImageRef) -> int: ...


class SyntheticFaceCounter:
    """Reads the face list out of a synthetic fixture."""

    def count(self, image: ImageRef) -> int:
        payload = image.payload or {}
        faces = payload.get("faces")
        if isinstance(faces, (list, tuple)):
            return len(faces)
        return 1 if payload.get("identity_seed") else 0


def sole_presence_signal(frames: Iterable[ImageRef], counter: FaceCounter) -> Signal:
    """Share of sampled frames showing exactly one face."""
    frames = list(frames)
    if not frames:
        return Signal.missing("sole_presence", "no frames were sampled")
    counts = [counter.count(frame) for frame in frames]
    single = sum(1 for c in counts if c == 1)
    share = single / len(counts)
    extra = sum(1 for c in counts if c > 1)
    empty = sum(1 for c in counts if c == 0)
    detail = f"{single}/{len(counts)} frames show one face"
    if extra:
        detail += f"; {extra} show more than one"
    if empty:
        detail += f"; {empty} show none"
    return Signal(name="sole_presence", score=round(share, 4), available=True, detail=detail)
