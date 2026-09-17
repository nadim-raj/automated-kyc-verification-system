"""Face embeddings behind a narrow interface.

The pipeline only ever asks for a vector. That keeps the model swappable and
means this repository can demonstrate the architecture without shipping weights
or touching a real face.
"""

from __future__ import annotations

import hashlib
import math
from typing import Protocol, Sequence, runtime_checkable

from ..domain import ImageRef

Embedding = tuple[float, ...]

DEFAULT_DIM = 32


@runtime_checkable
class FaceEmbedder(Protocol):
    def embed(self, image: ImageRef) -> Embedding | None: ...


def cosine(left: Sequence[float], right: Sequence[float]) -> float:
    """Cosine similarity, clamped to ``[0, 1]``."""
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if norm_left == 0.0 or norm_right == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_left * norm_right)))


def _unit_vector(seed: str, dim: int) -> Embedding:
    """A deterministic unit vector derived from a seed string."""
    values: list[float] = []
    counter = 0
    while len(values) < dim:
        digest = hashlib.sha256(f"{seed}:{counter}".encode()).digest()
        values.extend((b - 127.5) / 127.5 for b in digest)
        counter += 1
    vector = values[:dim]
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return tuple(v / norm for v in vector)


class SyntheticEmbedder:
    """Deterministic embeddings for synthetic fixtures.

    Two captures of the same synthetic identity land close together; different
    identities land far apart. This exists so the pipeline can be demonstrated
    and tested end to end. It must never be pointed at real images.
    """

    def __init__(self, dim: int = DEFAULT_DIM, jitter: float = 0.12) -> None:
        self.dim = dim
        self.jitter = jitter

    def embed(self, image: ImageRef) -> Embedding | None:
        payload = image.payload or {}
        seed = payload.get("identity_seed")
        if not seed:
            return None
        base = _unit_vector(str(seed), self.dim)
        capture = str(payload.get("capture", ""))
        if not capture:
            return base
        noise = _unit_vector(f"{seed}:{capture}:noise", self.dim)
        mixed = tuple(b + self.jitter * n for b, n in zip(base, noise))
        norm = math.sqrt(sum(v * v for v in mixed)) or 1.0
        return tuple(v / norm for v in mixed)


class TorchFaceEmbedder:
    """Adapter for a PyTorch face-recognition backbone.

    Weights are deliberately **not** shipped with this repository. Point it at
    your own model and implement the preprocessing your backbone expects.
    """

    def __init__(self, weights_path: str, device: str = "cpu") -> None:
        import torch  # imported lazily; part of the ``ml`` extra

        self._torch = torch
        self.device = device
        self.weights_path = weights_path

    def embed(self, image: ImageRef) -> Embedding | None:  # pragma: no cover - needs weights
        raise NotImplementedError(
            "Wire your preprocessing and backbone here. This repository ships no weights."
        )
