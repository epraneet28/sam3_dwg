"""Mask post-processing utilities for cleaning up segmentation masks."""

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Try to import OpenCV for morphological operations
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.debug("OpenCV not available, advanced mask post-processing disabled")


def postprocess_mask(
    mask: np.ndarray,
    min_component_area: int = 64,
    fill_holes: bool = True,
    max_hole_area: int = 256,
    apply_morphology: bool = True,
    kernel_size: int = 3,
) -> np.ndarray:
    """
    Clean up segmentation mask by removing sprinkles and optionally filling holes.

    This addresses the issue where SAM3's default max_sprinkle_area=0.0 leaves
    small disconnected noise regions in the mask.

    Args:
        mask: Binary mask array (2D, dtype bool or uint8)
        min_component_area: Minimum area (pixels) for connected components to keep.
            Components smaller than this are removed as "sprinkles".
        fill_holes: Whether to fill small holes in the mask.
        max_hole_area: Maximum hole area (pixels) to fill. Larger holes are preserved.
        apply_morphology: Whether to apply morphological open/close to smooth edges.
        kernel_size: Size of morphological kernel (must be odd, e.g., 3, 5, 7).

    Returns:
        Cleaned binary mask (same shape as input, dtype bool)

    Note:
        Falls back to input mask if OpenCV is not available or processing fails.
    """
    if mask is None or mask.size == 0:
        return mask

    # Ensure 2D
    if mask.ndim > 2:
        mask = mask.squeeze()
    if mask.ndim != 2:
        logger.warning(f"Expected 2D mask, got shape {mask.shape}, returning as-is")
        return mask

    # Convert to binary uint8 for OpenCV
    if mask.dtype == bool:
        mask_uint8 = mask.astype(np.uint8) * 255
    elif mask.dtype == np.float32 or mask.dtype == np.float64:
        mask_uint8 = ((mask > 0.5) * 255).astype(np.uint8)
    else:
        mask_uint8 = mask.astype(np.uint8)
        if mask_uint8.max() <= 1:
            mask_uint8 = mask_uint8 * 255

    # Check if mask is too small for processing
    if mask_uint8.shape[0] < kernel_size or mask_uint8.shape[1] < kernel_size:
        logger.debug(f"Mask too small for post-processing ({mask_uint8.shape}), returning as-is")
        return mask > 0 if mask.dtype != bool else mask

    if not CV2_AVAILABLE:
        logger.debug("OpenCV not available, skipping mask post-processing")
        return mask > 0 if mask.dtype != bool else mask

    try:
        processed = mask_uint8.copy()

        # Step 1: Remove small components (sprinkles)
        if min_component_area > 0:
            processed = _remove_small_components(processed, min_component_area)

        # Step 2: Fill small holes
        if fill_holes and max_hole_area > 0:
            processed = _fill_small_holes(processed, max_hole_area)

        # Step 3: Apply morphological operations to smooth edges
        if apply_morphology and kernel_size > 0:
            processed = _apply_morphology(processed, kernel_size)

        return processed > 127

    except Exception as e:
        logger.warning(f"Mask post-processing failed: {e}", exc_info=True)
        return mask > 0 if mask.dtype != bool else mask


def _remove_small_components(mask: np.ndarray, min_area: int) -> np.ndarray:
    """Remove connected components smaller than min_area pixels."""
    # Find all connected components
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)

    # Create output mask
    result = np.zeros_like(mask)

    # Keep only components larger than min_area (skip background label 0)
    for label_id in range(1, num_labels):
        area = stats[label_id, cv2.CC_STAT_AREA]
        if area >= min_area:
            result[labels == label_id] = 255

    return result


def keep_largest_component(mask: np.ndarray) -> np.ndarray:
    """
    Keep only the largest connected component in the mask.

    This is crucial for engineering drawings where SAM3 often segments
    individual line elements, creating many small disconnected regions.
    Keeping only the largest component gives clean, Roboflow-like results.

    Args:
        mask: Binary mask (2D, dtype bool or uint8)

    Returns:
        Mask with only the largest connected component
    """
    if mask is None or mask.size == 0:
        return mask

    if not CV2_AVAILABLE:
        return mask

    # Ensure uint8
    if mask.dtype == bool:
        mask_uint8 = mask.astype(np.uint8) * 255
    else:
        mask_uint8 = mask.astype(np.uint8)
        if mask_uint8.max() <= 1:
            mask_uint8 = mask_uint8 * 255

    # Find all connected components
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask_uint8, connectivity=8)

    if num_labels <= 1:  # Only background
        return mask_uint8

    # Find largest component (skip background label 0)
    largest_label = 1
    largest_area = 0
    for label_id in range(1, num_labels):
        area = stats[label_id, cv2.CC_STAT_AREA]
        if area > largest_area:
            largest_area = area
            largest_label = label_id

    # Create mask with only largest component
    result = np.zeros_like(mask_uint8)
    result[labels == largest_label] = 255

    logger.debug(f"keep_largest_component: kept {largest_area}px, removed {num_labels - 2} smaller components")

    return result


def fill_all_holes(mask: np.ndarray, use_convex_hull: bool = True) -> np.ndarray:
    """
    Fill ALL interior holes in the mask, creating a solid region.

    This is crucial for engineering drawings where we want the enclosed
    area, not just the line work. SAM3 often segments lines, leaving
    white space between them. This fills all that interior space.

    For fragmented line work (common in engineering drawings), we use
    convex hull which handles gaps in the boundary. For closed boundaries,
    flood fill is used.

    Args:
        mask: Binary mask (2D, dtype bool or uint8)
        use_convex_hull: If True, use convex hull for solid fill (handles gaps).
                        If False, use flood fill (requires closed boundary).

    Returns:
        Mask with all interior holes filled
    """
    if mask is None or mask.size == 0:
        return mask

    if not CV2_AVAILABLE:
        return mask

    # Ensure uint8
    if mask.dtype == bool:
        mask_uint8 = mask.astype(np.uint8) * 255
    else:
        mask_uint8 = mask.astype(np.uint8)
        if mask_uint8.max() <= 1:
            mask_uint8 = mask_uint8 * 255

    if use_convex_hull:
        # Use convex hull - creates solid region from fragmented line work
        # This is robust to gaps in the boundary (common in SAM3 line work)
        return _fill_with_convex_hull(mask_uint8)
    else:
        # Use flood fill - only works for closed boundaries
        return _fill_with_flood_fill(mask_uint8)


def _fill_with_convex_hull(mask_uint8: np.ndarray) -> np.ndarray:
    """Fill mask using convex hull of all foreground pixels."""
    h, w = mask_uint8.shape

    # Find all contours
    contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return mask_uint8

    # Combine all contour points
    all_points = np.vstack(contours)

    # Compute convex hull
    hull = cv2.convexHull(all_points)

    # Create filled mask from convex hull
    result = np.zeros((h, w), dtype=np.uint8)
    cv2.fillConvexPoly(result, hull, 255)

    original_pixels = np.sum(mask_uint8 > 0)
    filled_pixels = np.sum(result > 0)
    logger.debug(
        f"fill_with_convex_hull: {original_pixels} -> {filled_pixels} pixels "
        f"(+{filled_pixels - original_pixels} filled)"
    )

    return result


def _fill_with_flood_fill(mask_uint8: np.ndarray) -> np.ndarray:
    """Fill holes using flood fill from corners (requires closed boundary)."""
    filled = mask_uint8.copy()
    h, w = filled.shape

    # Create a mask for flood fill (must be 2 pixels larger)
    flood_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)

    # Flood fill from all four corners (in case object touches some edges)
    # This marks all exterior background as 128 in flood_mask
    cv2.floodFill(filled, flood_mask, (0, 0), 128)
    cv2.floodFill(filled, flood_mask, (w - 1, 0), 128)
    cv2.floodFill(filled, flood_mask, (0, h - 1), 128)
    cv2.floodFill(filled, flood_mask, (w - 1, h - 1), 128)

    # Now: 255 = original foreground, 128 = exterior background, 0 = interior holes
    # Fill interior holes (anything that's still 0)
    result = np.where(filled == 0, 255, filled)

    # Convert back to binary (255 for foreground)
    result = np.where(result == 128, 0, 255).astype(np.uint8)

    holes_filled = np.sum((mask_uint8 == 0) & (result == 255))
    logger.debug(f"fill_with_flood_fill: filled {holes_filled} interior pixels")

    return result


def _fill_with_box(
    mask_uint8: np.ndarray,
    box: tuple,
    margin_ratio: float = 0.02,
) -> np.ndarray:
    """Fill the box region directly - Roboflow-style for box prompts.

    This is the simplest and most effective approach for box prompts.
    The user drew a box around what they want - just fill it.

    Args:
        mask_uint8: Original mask (used to determine any refinement)
        box: (x1, y1, x2, y2) box coordinates
        margin_ratio: Small margin to add around box (default 2%)

    Returns:
        Mask filled within the box region
    """
    h, w = mask_uint8.shape
    x1, y1, x2, y2 = [int(v) for v in box]

    # Add small margin
    margin_x = int((x2 - x1) * margin_ratio)
    margin_y = int((y2 - y1) * margin_ratio)

    # Clamp to image bounds
    x1 = max(0, x1 - margin_x)
    y1 = max(0, y1 - margin_y)
    x2 = min(w, x2 + margin_x)
    y2 = min(h, y2 + margin_y)

    # Create filled box mask
    result = np.zeros((h, w), dtype=np.uint8)
    result[y1:y2, x1:x2] = 255

    filled_pixels = np.sum(result > 0)
    logger.info(f"fill_with_box: created {filled_pixels} pixel box region [{x1},{y1},{x2},{y2}]")

    return result


def _fill_with_morphological_closing(
    mask_uint8: np.ndarray,
    kernel_size: int = 25,
    iterations: int = 3,
) -> np.ndarray:
    """Fill gaps using morphological closing - preserves non-convex shapes.

    Better than convex hull for L-shaped or complex regions.
    Large kernel bridges gaps without destroying shape.

    Args:
        mask_uint8: Binary mask (0/255)
        kernel_size: Size of closing kernel (default 25)
        iterations: Number of closing operations (default 3)

    Returns:
        Mask with gaps filled via morphological closing
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))

    result = mask_uint8.copy()
    for i in range(iterations):
        result = cv2.morphologyEx(result, cv2.MORPH_CLOSE, kernel)

    # After closing, fill any remaining interior holes with flood fill
    result = _fill_with_flood_fill(result)

    original_pixels = np.sum(mask_uint8 > 0)
    filled_pixels = np.sum(result > 0)
    logger.info(
        f"fill_with_morphological_closing: {original_pixels} -> {filled_pixels} pixels "
        f"(kernel={kernel_size}, iterations={iterations})"
    )

    return result


def postprocess_mask_for_drawings(
    mask: np.ndarray,
    keep_largest: bool = True,
    fill_holes: bool = True,
    apply_morphology: bool = True,
    morphology_kernel: int = 5,
    min_area_ratio: float = 0.001,
    fill_method: str = "box_fill",
    box: Optional[tuple] = None,
    morphology_fill_kernel: int = 25,
) -> np.ndarray:
    """
    Post-process mask specifically for engineering drawings.

    This addresses the fundamental issue where SAM3 segments LINE WORK
    instead of ENCLOSED AREAS in engineering drawings.

    Fill methods:
    - "box_fill": Fill the user's box region (Roboflow-style, best for box prompts)
    - "morphological": Use large morphological closing (preserves non-convex shapes)
    - "convex_hull": Fill convex hull of mask (may distort L-shaped regions)

    Args:
        mask: Binary mask from SAM3
        keep_largest: Keep only largest connected component (default: True)
        fill_holes: Fill interior holes (default: True)
        apply_morphology: Apply morphological smoothing (default: True)
        morphology_kernel: Kernel size for final smoothing (default: 5)
        min_area_ratio: Minimum mask area as ratio of image (default: 0.001)
        fill_method: "box_fill", "morphological", or "convex_hull"
        box: (x1, y1, x2, y2) box coords for box_fill method
        morphology_fill_kernel: Kernel size for morphological fill (default: 25)

    Returns:
        Cleaned mask suitable for engineering drawings
    """
    if mask is None or mask.size == 0:
        return mask

    if not CV2_AVAILABLE:
        logger.warning("OpenCV not available, skipping drawing-specific post-processing")
        return mask

    # Log entry with settings for debugging
    logger.info(
        f"postprocess_mask_for_drawings: fill_method={fill_method}, "
        f"box={'provided' if box is not None else 'None'}, "
        f"mask dtype={mask.dtype}, shape={mask.shape}"
    )

    # Convert to uint8 - handle bool, float, and uint8 inputs
    if mask.dtype == bool:
        processed = mask.astype(np.uint8) * 255
    elif mask.dtype in (np.float32, np.float64):
        # Handle float masks (0.0-1.0 range) - threshold at 0.5
        processed = ((mask > 0.5) * 255).astype(np.uint8)
    else:
        processed = mask.astype(np.uint8)
        if processed.max() <= 1:
            processed = processed * 255

    original_pixels = np.sum(processed > 0)
    total_pixels = processed.shape[0] * processed.shape[1]

    logger.info(f"Input mask: {original_pixels} pixels, dtype converted to uint8 0/255")

    # Check if original mask has any content
    if original_pixels == 0:
        logger.warning("Empty mask after conversion, returning as-is")
        return mask

    # Step 1: Fill holes using selected method
    if fill_holes:
        if fill_method == "box_fill" and box is not None:
            # Roboflow-style: just fill the box
            processed = _fill_with_box(processed, box)
        elif fill_method == "morphological":
            # Shape-preserving fill
            processed = _fill_with_morphological_closing(
                processed, kernel_size=morphology_fill_kernel
            )
        else:
            # Default to convex hull (legacy behavior)
            processed = fill_all_holes(processed, use_convex_hull=True)

        logger.info(f"After {fill_method} fill: {np.sum(processed > 0)} pixels")

    # Step 2: Keep only largest connected component (cleanup)
    # Skip for box_fill since it's already a single region
    if keep_largest and fill_method != "box_fill":
        processed = keep_largest_component(processed)
        logger.info(f"After keep_largest: {np.sum(processed > 0)} pixels")

    # Step 3: Apply morphological closing to smooth edges
    if apply_morphology and morphology_kernel > 0:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (morphology_kernel, morphology_kernel)
        )
        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)

    # Check if mask is too small (likely noise)
    final_pixels = np.sum(processed > 0)
    if final_pixels < total_pixels * min_area_ratio:
        logger.warning(
            f"Mask too small after processing ({final_pixels}/{total_pixels} = "
            f"{final_pixels/total_pixels:.6f} < {min_area_ratio}), returning empty"
        )
        return np.zeros_like(processed, dtype=bool)

    logger.info(
        f"postprocess_mask_for_drawings DONE: {original_pixels} -> {final_pixels} pixels "
        f"({final_pixels/original_pixels:.1%} of original)"
    )

    return processed > 127


def _fill_small_holes(mask: np.ndarray, max_hole_area: int) -> np.ndarray:
    """Fill holes (background regions) smaller than max_hole_area pixels."""
    # Invert mask to find holes (background becomes foreground)
    inverted = cv2.bitwise_not(mask)

    # Find connected components in inverted mask (these are the holes)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(inverted, connectivity=8)

    # Fill small holes
    result = mask.copy()
    for label_id in range(1, num_labels):
        area = stats[label_id, cv2.CC_STAT_AREA]
        if area <= max_hole_area:
            # Fill this hole
            result[labels == label_id] = 255

    return result


def _apply_morphology(mask: np.ndarray, kernel_size: int) -> np.ndarray:
    """Apply morphological opening then closing to smooth mask edges."""
    # Create kernel
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (kernel_size, kernel_size)
    )

    # Opening: erode then dilate - removes small protrusions
    opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # Closing: dilate then erode - fills small gaps
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)

    return closed


def constrain_mask_to_box(
    mask: np.ndarray,
    box: tuple,
    margin_ratio: float = 0.1,
) -> np.ndarray:
    """
    Constrain mask to be within/near the box prompt region.

    This removes spurious detections far from the intended area, similar to
    how Roboflow constrains SAM masks to the region of interest.

    Args:
        mask: Binary mask (2D, dtype bool or uint8)
        box: Bounding box (x1, y1, x2, y2) in pixels
        margin_ratio: Margin as ratio of box dimensions (0.1 = 10% margin)

    Returns:
        Constrained binary mask (same shape as input, dtype bool)

    Example:
        >>> mask = segmenter.segment_interactive(image, box=[100, 100, 300, 400])
        >>> constrained = constrain_mask_to_box(mask, box=(100, 100, 300, 400))
    """
    if mask is None or mask.size == 0:
        return mask

    # Ensure 2D
    if mask.ndim > 2:
        mask = mask.squeeze()
    if mask.ndim != 2:
        logger.warning(f"Expected 2D mask for box constraint, got shape {mask.shape}")
        return mask

    x1, y1, x2, y2 = [int(v) for v in box]
    h, w = mask.shape

    # Calculate margin based on box dimensions
    box_width = x2 - x1
    box_height = y2 - y1
    margin_x = int(box_width * margin_ratio)
    margin_y = int(box_height * margin_ratio)

    # Create region mask with margin
    region_mask = np.zeros((h, w), dtype=bool)
    y_start = max(0, y1 - margin_y)
    y_end = min(h, y2 + margin_y)
    x_start = max(0, x1 - margin_x)
    x_end = min(w, x2 + margin_x)
    region_mask[y_start:y_end, x_start:x_end] = True

    # Constrain mask to region
    if mask.dtype == bool:
        return mask & region_mask
    else:
        return (mask > 0) & region_mask


# =============================================================================
# HuggingFace SAM3-style Post-Processing Functions
# =============================================================================


def compute_stability_score(
    mask_logits: np.ndarray,
    mask_threshold: float = 0.0,
    stability_score_offset: float = 1.0,
) -> float:
    """
    Compute stability score for a mask (HuggingFace-style).

    Stability measures how consistent the mask is across threshold variations.
    High stability = more confident segmentation.

    Reference: HuggingFace transformers/models/sam2/image_processing_sam2_fast.py

    Args:
        mask_logits: Mask logits (pre-sigmoid values), shape (H, W)
        mask_threshold: Base threshold for binarization (default 0.0 for logits)
        stability_score_offset: Offset for computing stability (default 1.0)

    Returns:
        Stability score in [0, 1]. Higher = more stable/confident.

    Example:
        >>> score = compute_stability_score(mask_logits)
        >>> if score >= 0.95:  # HuggingFace default threshold
        ...     # Mask is stable, keep it
    """
    if mask_logits is None or mask_logits.size == 0:
        return 0.0

    # Ensure 2D
    if mask_logits.ndim > 2:
        mask_logits = mask_logits.squeeze()

    # Compute intersection: pixels above (threshold + offset)
    high_thresh = mask_threshold + stability_score_offset
    intersection = np.sum(mask_logits > high_thresh)

    # Compute union: pixels above (threshold - offset)
    low_thresh = mask_threshold - stability_score_offset
    union = np.sum(mask_logits > low_thresh)

    # Avoid division by zero
    if union == 0:
        return 0.0

    return float(intersection / union)


def filter_masks_by_stability(
    masks: list[np.ndarray],
    mask_logits: Optional[list[np.ndarray]],
    scores: list[float],
    boxes: list[tuple],
    stability_thresh: float = 0.95,
    stability_offset: float = 1.0,
) -> tuple[list[np.ndarray], list[float], list[tuple]]:
    """
    Filter masks by stability score (requires mask logits).

    Reference: HuggingFace transformers/models/sam2/image_processing_sam2_fast.py

    Args:
        masks: List of binary masks
        mask_logits: List of mask logits (pre-threshold). If None, returns all.
        scores: List of IoU/confidence scores
        boxes: List of bounding boxes (x1, y1, x2, y2)
        stability_thresh: Minimum stability score (HuggingFace default: 0.95)
        stability_offset: Offset for stability computation (default: 1.0)

    Returns:
        Filtered (masks, scores, boxes) tuples
    """
    if mask_logits is None or len(mask_logits) == 0:
        logger.debug("No mask logits provided, skipping stability filtering")
        return masks, scores, boxes

    if len(masks) != len(mask_logits):
        logger.warning(
            f"Mask count ({len(masks)}) != logits count ({len(mask_logits)}), "
            "skipping stability filtering"
        )
        return masks, scores, boxes

    filtered_masks = []
    filtered_scores = []
    filtered_boxes = []

    for mask, logits, score, box in zip(masks, mask_logits, scores, boxes):
        stability = compute_stability_score(
            logits,
            mask_threshold=0.0,
            stability_score_offset=stability_offset
        )

        if stability >= stability_thresh:
            filtered_masks.append(mask)
            filtered_scores.append(score)
            filtered_boxes.append(box)
        else:
            logger.debug(f"Filtered mask with stability {stability:.3f} < {stability_thresh}")

    logger.debug(
        f"Stability filtering: kept {len(filtered_masks)}/{len(masks)} masks "
        f"(thresh={stability_thresh})"
    )

    return filtered_masks, filtered_scores, filtered_boxes


def apply_nms_to_masks(
    masks: list[np.ndarray],
    scores: list[float],
    boxes: list[tuple],
    iou_threshold: float = 0.7,
) -> tuple[list[np.ndarray], list[float], list[tuple]]:
    """
    Apply Non-Maximum Suppression to remove overlapping masks.

    Reference: HuggingFace transformers/models/sam2/image_processing_sam2_fast.py
               Uses torchvision.ops.batched_nms

    Args:
        masks: List of binary masks
        scores: List of confidence/IoU scores
        boxes: List of bounding boxes (x1, y1, x2, y2)
        iou_threshold: IoU threshold for suppression (HuggingFace default: 0.7)

    Returns:
        Filtered (masks, scores, boxes) tuples with overlapping removed
    """
    if len(masks) == 0:
        return masks, scores, boxes

    if len(masks) == 1:
        return masks, scores, boxes

    try:
        import torch
        from torchvision.ops import batched_nms

        # Convert to tensors
        boxes_tensor = torch.tensor(
            [list(b) for b in boxes],
            dtype=torch.float32
        )
        scores_tensor = torch.tensor(scores, dtype=torch.float32)

        # All masks belong to same class (class_id=0)
        class_ids = torch.zeros(len(boxes), dtype=torch.int64)

        # Apply NMS
        keep_indices = batched_nms(
            boxes=boxes_tensor,
            scores=scores_tensor,
            idxs=class_ids,
            iou_threshold=iou_threshold,
        )

        keep_indices = keep_indices.tolist()

        logger.debug(
            f"NMS: kept {len(keep_indices)}/{len(masks)} masks (iou_thresh={iou_threshold})"
        )

        return (
            [masks[i] for i in keep_indices],
            [scores[i] for i in keep_indices],
            [boxes[i] for i in keep_indices],
        )

    except ImportError:
        logger.warning("torchvision not available, skipping NMS")
        return masks, scores, boxes
    except Exception as e:
        logger.warning(f"NMS failed: {e}", exc_info=True)
        return masks, scores, boxes


def is_mask_near_edge(
    mask: np.ndarray,
    image_shape: tuple,
    edge_tolerance: int = 20,
) -> bool:
    """
    Check if mask touches image edges (likely incomplete/truncated).

    Reference: HuggingFace _is_box_near_crop_edge

    Args:
        mask: Binary mask (H, W)
        image_shape: (height, width) of original image
        edge_tolerance: Pixels from edge to consider "near" (default: 20)

    Returns:
        True if mask bounding box is within tolerance of image edge
    """
    if mask is None or mask.size == 0:
        return False

    # Ensure 2D
    if mask.ndim > 2:
        mask = mask.squeeze()

    h, w = image_shape
    ys, xs = np.where(mask)

    if len(xs) == 0 or len(ys) == 0:
        return False

    # Get mask bounding box
    x_min, x_max = xs.min(), xs.max()
    y_min, y_max = ys.min(), ys.max()

    # Check if mask touches any edge within tolerance
    touches_left = x_min <= edge_tolerance
    touches_right = x_max >= w - edge_tolerance - 1
    touches_top = y_min <= edge_tolerance
    touches_bottom = y_max >= h - edge_tolerance - 1

    return touches_left or touches_right or touches_top or touches_bottom


def filter_edge_masks(
    masks: list[np.ndarray],
    scores: list[float],
    boxes: list[tuple],
    image_shape: tuple,
    edge_tolerance: int = 20,
) -> tuple[list[np.ndarray], list[float], list[tuple]]:
    """
    Filter out masks that touch image edges (likely incomplete).

    Reference: HuggingFace _is_box_near_crop_edge

    Args:
        masks: List of binary masks
        scores: List of scores
        boxes: List of bounding boxes
        image_shape: (height, width) of image
        edge_tolerance: Pixels from edge to consider "near" (default: 20)

    Returns:
        Filtered (masks, scores, boxes) tuples
    """
    if len(masks) == 0:
        return masks, scores, boxes

    filtered_masks = []
    filtered_scores = []
    filtered_boxes = []

    for mask, score, box in zip(masks, scores, boxes):
        if not is_mask_near_edge(mask, image_shape, edge_tolerance):
            filtered_masks.append(mask)
            filtered_scores.append(score)
            filtered_boxes.append(box)
        else:
            logger.debug(f"Filtered edge-touching mask with score {score:.3f}")

    logger.debug(
        f"Edge filtering: kept {len(filtered_masks)}/{len(masks)} masks "
        f"(tolerance={edge_tolerance}px)"
    )

    return filtered_masks, filtered_scores, filtered_boxes


def apply_non_overlapping_constraints(
    masks: list[np.ndarray],
    scores: list[float],
) -> list[np.ndarray]:
    """
    Ensure each pixel belongs to at most one mask (highest scoring wins).

    Reference: HuggingFace _apply_non_overlapping_constraints

    Args:
        masks: List of binary masks (same shape)
        scores: List of scores (higher = priority)

    Returns:
        List of non-overlapping masks (same order as input)
    """
    if len(masks) == 0:
        return masks

    if len(masks) == 1:
        return masks

    # Sort by score descending, keeping track of original indices
    indexed_pairs = list(enumerate(zip(scores, masks)))
    indexed_pairs.sort(key=lambda x: -x[1][0])  # Sort by score descending

    # Track which pixels are claimed
    claimed = np.zeros(masks[0].shape, dtype=bool)

    # Process in score order, but store results in original order
    result_masks = [None] * len(masks)

    for original_idx, (score, mask) in indexed_pairs:
        # Ensure mask is boolean
        if mask.dtype != bool:
            mask = mask > 0

        # Remove pixels already claimed by higher-scoring masks
        adjusted_mask = mask & ~claimed

        # Claim these pixels
        claimed = claimed | mask

        result_masks[original_idx] = adjusted_mask

    overlap_removed = sum(
        np.sum(orig != adj)
        for orig, adj in zip(masks, result_masks)
        if orig is not None and adj is not None
    )
    logger.debug(f"Non-overlapping: removed {overlap_removed} overlapping pixels")

    return result_masks


def filter_masks_by_iou(
    masks: list[np.ndarray],
    scores: list[float],
    boxes: list[tuple],
    min_iou: float = 0.5,
) -> tuple[list[np.ndarray], list[float], list[tuple]]:
    """
    Filter masks by predicted IoU score.

    Args:
        masks: List of binary masks
        scores: List of predicted IoU scores
        boxes: List of bounding boxes
        min_iou: Minimum IoU score to keep (default: 0.5)

    Returns:
        Filtered (masks, scores, boxes) tuples
    """
    if len(masks) == 0:
        return masks, scores, boxes

    filtered_masks = []
    filtered_scores = []
    filtered_boxes = []

    for mask, score, box in zip(masks, scores, boxes):
        if score >= min_iou:
            filtered_masks.append(mask)
            filtered_scores.append(score)
            filtered_boxes.append(box)
        else:
            logger.debug(f"Filtered mask with IoU {score:.3f} < {min_iou}")

    logger.debug(
        f"IoU filtering: kept {len(filtered_masks)}/{len(masks)} masks (min_iou={min_iou})"
    )

    return filtered_masks, filtered_scores, filtered_boxes


# =============================================================================
# Complexity-based Mask Scoring (for line drawings)
# =============================================================================


def compute_mask_complexity(mask: np.ndarray, threshold: float = 0.35) -> float:
    """
    Compute complexity score for a mask based on perimeter-to-area ratio.

    For line drawings, more complex masks (higher perimeter/area) often
    correspond to more detailed/precise segmentation vs. simple blobs.

    Args:
        mask: Binary mask (2D, bool or uint8)
        threshold: Binarization threshold for float masks (default 0.35 to match config)

    Returns:
        Complexity score (higher = more complex/detailed)
    """
    if mask is None or mask.size == 0:
        return 0.0

    if not CV2_AVAILABLE:
        return 0.0

    # Convert to uint8 if needed, using configurable threshold
    if mask.dtype == bool:
        mask_uint8 = mask.astype(np.uint8) * 255
    elif mask.dtype in (np.float32, np.float64):
        mask_uint8 = ((mask > threshold) * 255).astype(np.uint8)  # Use configurable threshold
    else:
        mask_uint8 = mask.astype(np.uint8)
        if mask_uint8.max() <= 1:
            mask_uint8 = mask_uint8 * 255

    # Find contours
    contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return 0.0

    # Compute total perimeter and area
    total_perimeter = sum(cv2.arcLength(c, closed=True) for c in contours)
    total_area = np.sum(mask_uint8 > 0)

    if total_area == 0:
        return 0.0

    # Perimeter/area ratio (normalized by sqrt(area) for scale-invariance)
    # Higher = more complex boundary
    complexity = total_perimeter / np.sqrt(total_area)

    return float(complexity)


def compute_combined_score(
    iou_score: float,
    mask: np.ndarray,
    complexity_weight: float = 0.3,
    component_bonus: float = 0.0,
    threshold: float = 0.35,
) -> float:
    """
    Compute combined score using IoU and complexity.

    For line drawings, pure IoU-sorting often picks the coarsest mask
    (higher overlap = more fill). This adds complexity to favor detailed masks.

    Args:
        iou_score: SAM's predicted IoU score (0-1)
        mask: Binary mask for complexity computation
        complexity_weight: Weight for complexity vs IoU (0-1, default 0.3)
        component_bonus: Bonus per connected component (rewards disjoint regions)
        threshold: Binarization threshold for float masks (default 0.35 to match config)

    Returns:
        Combined score for ranking (higher = better)
    """
    complexity = compute_mask_complexity(mask, threshold)

    # Normalize complexity to roughly 0-1 range
    # Typical values: circle ~3.5, square ~4.0, complex shape ~6-10+
    normalized_complexity = min(complexity / 10.0, 1.0)

    # Add bonus for multiple connected components (grid bubbles, annotations)
    if component_bonus > 0 and CV2_AVAILABLE:
        # Convert to uint8 for connected components analysis, using configurable threshold
        if mask.dtype == bool:
            mask_uint8 = mask.astype(np.uint8) * 255
        elif mask.dtype in (np.float32, np.float64):
            mask_uint8 = ((mask > threshold) * 255).astype(np.uint8)  # Use configurable threshold
        else:
            mask_uint8 = mask.astype(np.uint8)
            if mask_uint8.max() <= 1:
                mask_uint8 = mask_uint8 * 255

        num_components, _ = cv2.connectedComponents(mask_uint8)
        # num_components includes background (0), so actual components = num_components - 1
        actual_components = max(0, num_components - 1)
        # Bonus is normalized: 1 component = 0, 2 = bonus, 3 = 2*bonus, etc.
        component_score = component_bonus * max(0, actual_components - 1) / 5.0  # Normalize to ~0-1
        normalized_complexity = min(normalized_complexity + component_score, 1.0)
        logger.debug(f"Component bonus: {actual_components} components, bonus={component_score:.3f}")

    # Combine: (1-w)*IoU + w*complexity
    # With w=0.3: 70% IoU, 30% complexity
    combined = (1 - complexity_weight) * iou_score + complexity_weight * normalized_complexity

    logger.debug(
        f"Combined score: IoU={iou_score:.3f}, complexity={complexity:.2f} "
        f"(norm={normalized_complexity:.3f}), combined={combined:.3f}"
    )

    return combined


def sort_masks_by_combined_score(
    masks: list[np.ndarray],
    iou_scores: list[float],
    boxes: list[tuple],
    complexity_weight: float = 0.3,
    low_res_logits: Optional[list] = None,
    component_bonus: float = 0.0,
    threshold: float = 0.35,
) -> tuple[list[np.ndarray], list[float], list[tuple], list[float], Optional[list]]:
    """
    Sort mask candidates by combined IoU + complexity score.

    Args:
        masks: List of binary masks
        iou_scores: List of IoU scores
        boxes: List of bounding boxes
        complexity_weight: Weight for complexity (default 0.3)
        low_res_logits: Optional list of low-res logits for refinement
        component_bonus: Bonus for masks with multiple connected components
        threshold: Binarization threshold for float masks (default 0.35 to match config)

    Returns:
        Tuple of (sorted_masks, sorted_ious, sorted_boxes, combined_scores, sorted_logits)
        sorted_logits is None if low_res_logits was None
    """
    if len(masks) == 0:
        return masks, iou_scores, boxes, [], low_res_logits

    # Compute combined scores using configurable threshold
    combined_scores = [
        compute_combined_score(iou, mask, complexity_weight, component_bonus, threshold)
        for iou, mask in zip(iou_scores, masks)
    ]

    # Sort by combined score descending
    sorted_indices = sorted(
        range(len(masks)),
        key=lambda i: combined_scores[i],
        reverse=True
    )

    sorted_masks = [masks[i] for i in sorted_indices]
    sorted_ious = [iou_scores[i] for i in sorted_indices]
    sorted_boxes = [boxes[i] for i in sorted_indices]
    sorted_combined = [combined_scores[i] for i in sorted_indices]

    # Also reorder low_res_logits if provided
    sorted_logits = None
    if low_res_logits is not None and len(low_res_logits) == len(masks):
        sorted_logits = [low_res_logits[i] for i in sorted_indices]

    logger.info(
        f"Complexity-aware sorting: reordered {len(masks)} candidates "
        f"(weight={complexity_weight})"
    )

    return sorted_masks, sorted_ious, sorted_boxes, sorted_combined, sorted_logits


def sort_masks_by_area(
    masks: list[np.ndarray],
    iou_scores: list[float],
    boxes: list[tuple],
    low_res_logits: Optional[list] = None,
    largest_first: bool = True,
    threshold: float = 0.35,
) -> tuple[list[np.ndarray], list[float], list[tuple], list[int], Optional[list]]:
    """
    Sort mask candidates by pixel area.

    This mode is useful for engineering drawings where the largest candidate
    typically includes grid bubbles, annotations, and other peripheral elements.

    Args:
        masks: List of binary masks
        iou_scores: List of IoU scores
        boxes: List of bounding boxes
        low_res_logits: Optional list of low-res logits for refinement
        largest_first: If True, sort largest first (default); if False, smallest first
        threshold: Binarization threshold for float masks (default 0.35 to match config)

    Returns:
        Tuple of (sorted_masks, sorted_ious, sorted_boxes, areas, sorted_logits)
    """
    if len(masks) == 0:
        return masks, iou_scores, boxes, [], low_res_logits

    # Compute areas using configurable threshold (matches mask_binarization_threshold)
    areas = []
    for mask in masks:
        if mask.dtype == bool:
            area = np.sum(mask)
        elif mask.dtype in (np.float32, np.float64):
            area = np.sum(mask > threshold)  # Use configurable threshold, not hardcoded 0.5
        else:
            area = np.sum(mask > 0)
        areas.append(int(area))

    # Sort by area
    sorted_indices = sorted(
        range(len(masks)),
        key=lambda i: areas[i],
        reverse=largest_first
    )

    sorted_masks = [masks[i] for i in sorted_indices]
    sorted_ious = [iou_scores[i] for i in sorted_indices]
    sorted_boxes = [boxes[i] for i in sorted_indices]
    sorted_areas = [areas[i] for i in sorted_indices]

    sorted_logits = None
    if low_res_logits is not None and len(low_res_logits) == len(masks):
        sorted_logits = [low_res_logits[i] for i in sorted_indices]

    mode = "largest" if largest_first else "smallest"
    logger.info(
        f"Area-based sorting ({mode} first): reordered {len(masks)} candidates, "
        f"areas={sorted_areas}"
    )

    return sorted_masks, sorted_ious, sorted_boxes, sorted_areas, sorted_logits
