"""Video handling: frame sampling and the source interface behind it."""

from .sampling import FrameSource, OpenCVFrameSource, sample_frames

__all__ = ["FrameSource", "OpenCVFrameSource", "sample_frames"]
