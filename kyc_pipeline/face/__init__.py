"""Face comparison interfaces and the synthetic implementations used for demos."""

from .embedding import Embedding, FaceEmbedder, SyntheticEmbedder, TorchFaceEmbedder, cosine
from .presence import FaceCounter, SyntheticFaceCounter, sole_presence_signal
from .verification import face_match_signal, video_consistency_signal

__all__ = [
    "Embedding",
    "FaceCounter",
    "FaceEmbedder",
    "SyntheticEmbedder",
    "SyntheticFaceCounter",
    "TorchFaceEmbedder",
    "cosine",
    "face_match_signal",
    "sole_presence_signal",
    "video_consistency_signal",
]
