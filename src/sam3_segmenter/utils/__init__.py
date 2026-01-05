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
from .mask_processing import (
    postprocess_mask,
    constrain_mask_to_box,
    # Drawing-specific post-processing (solid regions)
    keep_largest_component,
    fill_all_holes,
    postprocess_mask_for_drawings,
    # HuggingFace SAM3-style post-processing
    compute_stability_score,
    filter_masks_by_stability,
    apply_nms_to_masks,
    is_mask_near_edge,
    filter_edge_masks,
    apply_non_overlapping_constraints,
    filter_masks_by_iou,
)
from .debug_logging import (
    DebugLogger,
    create_debug_logger,
)

__all__ = [
    # Image utilities
    "decode_base64_image",
    "encode_image_to_base64",
    "encode_mask_to_base64",
    "crop_image_to_bbox",
    # Geometry utilities
    "normalize_bbox",
    "denormalize_bbox",
    "calculate_area_ratio",
    "calculate_iou",
    "merge_overlapping_boxes",
    "is_bbox_in_region",
    # Mask post-processing (existing)
    "postprocess_mask",
    "constrain_mask_to_box",
    # Drawing-specific post-processing (solid regions)
    "keep_largest_component",
    "fill_all_holes",
    "postprocess_mask_for_drawings",
    # HuggingFace SAM3-style post-processing
    "compute_stability_score",
    "filter_masks_by_stability",
    "apply_nms_to_masks",
    "is_mask_near_edge",
    "filter_edge_masks",
    "apply_non_overlapping_constraints",
    "filter_masks_by_iou",
    # Debug logging
    "DebugLogger",
    "create_debug_logger",
]
