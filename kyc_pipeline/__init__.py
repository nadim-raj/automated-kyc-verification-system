"""Clean-room reference implementation of an automated KYC verification pipeline.

This package demonstrates the architecture of a document/identity verification
pipeline that triages straightforward cases automatically and escalates the rest
to human reviewers. It runs entirely on synthetic fixtures; it contains no
production code, no trained weights, and no calibrated thresholds.
"""

from .domain import (
    Decision,
    DocumentExtract,
    IdentityClaim,
    ImageRef,
    MediaBundle,
    Outcome,
    ProviderKind,
    Signal,
    VerificationCase,
    VideoRef,
)

__version__ = "0.1.0"
__all__ = [
    "Decision",
    "DocumentExtract",
    "IdentityClaim",
    "ImageRef",
    "MediaBundle",
    "Outcome",
    "ProviderKind",
    "Signal",
    "VerificationCase",
    "VideoRef",
]
