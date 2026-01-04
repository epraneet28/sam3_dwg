"""SAM3 Drawing Zone Segmenter - Semantic segmentation for engineering drawings."""

__version__ = "1.0.0"

from .segmenter import DrawingSegmenter
from .models import (
    ZoneType,
    PageType,
    ZoneResult,
    SegmentRequest,
    SegmentResponse,
    StructuralSegmentRequest,
    StructuralSegmentResponse,
)

__all__ = [
    "DrawingSegmenter",
    "ZoneType",
    "PageType",
    "ZoneResult",
    "SegmentRequest",
    "SegmentResponse",
    "StructuralSegmentRequest",
    "StructuralSegmentResponse",
]
