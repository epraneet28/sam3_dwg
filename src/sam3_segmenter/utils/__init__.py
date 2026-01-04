"""Utility functions for image processing and geometry operations."""

from .image import (
    decode_base64_image,
    encode_image_to_base64,
    encode_mask_to_base64,
    crop_image_to_bbox,
)
from .geometry import (
    normalize_bbox,
    denormalize_bbox,
    calculate_area_ratio,
    calculate_iou,
    merge_overlapping_boxes,
    is_bbox_in_region,
)

__all__ = [
    "decode_base64_image",
    "encode_image_to_base64",
    "encode_mask_to_base64",
    "crop_image_to_bbox",
    "normalize_bbox",
    "denormalize_bbox",
    "calculate_area_ratio",
    "calculate_iou",
    "merge_overlapping_boxes",
    "is_bbox_in_region",
]
