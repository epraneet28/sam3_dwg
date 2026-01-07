"""Bounding box and geometry utilities."""

from typing import Literal, Optional

import numpy as np


def normalize_bbox(
    bbox: list[float],
    image_width: int,
    image_height: int,
) -> list[float]:
    """
    Normalize bounding box coordinates to 0-1 range.

    Args:
        bbox: Bounding box [x1, y1, x2, y2] in pixels
        image_width: Image width in pixels
        image_height: Image height in pixels

    Returns:
        Normalized bounding box [x1, y1, x2, y2] in 0-1 range
    """
    x1, y1, x2, y2 = bbox
    return [
        x1 / image_width,
        y1 / image_height,
        x2 / image_width,
        y2 / image_height,
    ]


def denormalize_bbox(
    bbox: list[float],
    image_width: int,
    image_height: int,
) -> list[float]:
    """
    Convert normalized bounding box to pixel coordinates.

    Args:
        bbox: Normalized bounding box [x1, y1, x2, y2] in 0-1 range
        image_width: Image width in pixels
        image_height: Image height in pixels

    Returns:
        Bounding box [x1, y1, x2, y2] in pixels
    """
    x1, y1, x2, y2 = bbox
    return [
        x1 * image_width,
        y1 * image_height,
        x2 * image_width,
        y2 * image_height,
    ]


def calculate_area_ratio(
    bbox: list[float],
    image_width: int,
    image_height: int,
) -> float:
    """
    Calculate the ratio of bounding box area to total image area.

    Args:
        bbox: Bounding box [x1, y1, x2, y2] in pixels
        image_width: Image width in pixels
        image_height: Image height in pixels

    Returns:
        Area ratio (0-1)
    """
    x1, y1, x2, y2 = bbox
    box_area = (x2 - x1) * (y2 - y1)
    image_area = image_width * image_height
    return box_area / image_area if image_area > 0 else 0.0


def calculate_iou(bbox1: list[float], bbox2: list[float]) -> float:
    """
    Calculate Intersection over Union (IoU) between two bounding boxes.

    Args:
        bbox1: First bounding box [x1, y1, x2, y2]
        bbox2: Second bounding box [x1, y1, x2, y2]

    Returns:
        IoU score (0-1)
    """
    x1_1, y1_1, x2_1, y2_1 = bbox1
    x1_2, y1_2, x2_2, y2_2 = bbox2

    # Calculate intersection
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)

    if x2_i <= x1_i or y2_i <= y1_i:
        return 0.0

    intersection = (x2_i - x1_i) * (y2_i - y1_i)

    # Calculate union
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


def merge_overlapping_boxes(
    boxes: list[list[float]],
    iou_threshold: float = 0.5,
) -> list[list[float]]:
    """
    Merge overlapping bounding boxes.

    Args:
        boxes: List of bounding boxes [x1, y1, x2, y2]
        iou_threshold: IoU threshold for merging

    Returns:
        List of merged bounding boxes
    """
    if not boxes:
        return []

    boxes = [list(box) for box in boxes]
    merged = []

    while boxes:
        current = boxes.pop(0)
        merged_with_current = [current]

        i = 0
        while i < len(boxes):
            if calculate_iou(current, boxes[i]) >= iou_threshold:
                merged_with_current.append(boxes.pop(i))
            else:
                i += 1

        # Merge all boxes in the group
        if len(merged_with_current) > 1:
            x1 = min(b[0] for b in merged_with_current)
            y1 = min(b[1] for b in merged_with_current)
            x2 = max(b[2] for b in merged_with_current)
            y2 = max(b[3] for b in merged_with_current)
            merged.append([x1, y1, x2, y2])
        else:
            merged.append(current)

    return merged


def is_bbox_in_region(
    bbox: list[float],
    image_width: int,
    image_height: int,
    region: Literal[
        "top_left",
        "top_right",
        "bottom_left",
        "bottom_right",
        "center",
        "left_side",
        "right_side",
        "top",
        "bottom",
    ],
    tolerance: float = 0.1,
) -> bool:
    """
    Check if a bounding box center is in a specific region of the image.

    Args:
        bbox: Bounding box [x1, y1, x2, y2] in pixels
        image_width: Image width
        image_height: Image height
        region: Target region name
        tolerance: Region boundary tolerance (0-1)

    Returns:
        True if bbox center is in the specified region
    """
    x1, y1, x2, y2 = bbox
    center_x = (x1 + x2) / 2 / image_width
    center_y = (y1 + y2) / 2 / image_height

    # Define region boundaries
    left = 0.33
    right = 0.67
    top = 0.33
    bottom = 0.67

    region_checks = {
        "top_left": center_x < left and center_y < top,
        "top_right": center_x > right and center_y < top,
        "bottom_left": center_x < left and center_y > bottom,
        "bottom_right": center_x > right and center_y > bottom,
        "center": left <= center_x <= right and top <= center_y <= bottom,
        "left_side": center_x < left,
        "right_side": center_x > right,
        "top": center_y < top,
        "bottom": center_y > bottom,
    }

    return region_checks.get(region, False)


def bbox_from_mask(mask: np.ndarray) -> Optional[list[float]]:
    """
    Extract bounding box from a binary mask.

    Args:
        mask: Binary mask array (2D)

    Returns:
        Bounding box [x1, y1, x2, y2] or None if mask is empty
    """
    if hasattr(mask, "cpu"):
        # Check if it's a floating-point tensor (not boolean) - bfloat16→float32
        if hasattr(mask, "is_floating_point") and mask.is_floating_point():
            mask = mask.float().cpu().numpy()
        else:
            mask = mask.cpu().numpy()

    if mask.ndim > 2:
        mask = mask.squeeze()

    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)

    if not rows.any() or not cols.any():
        return None

    y1, y2 = np.where(rows)[0][[0, -1]]
    x1, x2 = np.where(cols)[0][[0, -1]]

    return [float(x1), float(y1), float(x2 + 1), float(y2 + 1)]


def expand_bbox(
    bbox: list[float],
    image_width: int,
    image_height: int,
    expansion_ratio: float = 0.1,
) -> list[float]:
    """
    Expand a bounding box by a given ratio.

    Args:
        bbox: Bounding box [x1, y1, x2, y2]
        image_width: Image width for bounds checking
        image_height: Image height for bounds checking
        expansion_ratio: How much to expand (0.1 = 10%)

    Returns:
        Expanded bounding box
    """
    x1, y1, x2, y2 = bbox
    width = x2 - x1
    height = y2 - y1

    expand_x = width * expansion_ratio
    expand_y = height * expansion_ratio

    return [
        max(0, x1 - expand_x),
        max(0, y1 - expand_y),
        min(image_width, x2 + expand_x),
        min(image_height, y2 + expand_y),
    ]
