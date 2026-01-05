# HuggingFace SAM3 Feature Implementation Plan

> **Status**: ✅ COMPLETED
> **Created**: 2026-01-04
> **Last Updated**: 2026-01-04

---

## Overview

This document tracks the implementation of HuggingFace SAM3 post-processing features into our codebase. Each feature is audited for correctness if already implemented, or implemented from scratch if missing.

---

## Feature Checklist

| # | Feature | Status | Priority | Action Required |
|---|---------|--------|----------|-----------------|
| 1 | Sprinkle Removal (SAM2Transforms) | VERIFY | HIGH | Audit current impl |
| 2 | Hole Filling | VERIFY | HIGH | Audit current impl |
| 3 | Morphological Smoothing | VERIFY | MEDIUM | Audit current impl |
| 4 | Box Constraint | VERIFY | HIGH | Audit current impl |
| 5 | Stability Score Filtering | IMPLEMENT | HIGH | New implementation |
| 6 | Non-Maximum Suppression (NMS) | IMPLEMENT | HIGH | New implementation |
| 7 | Edge Mask Rejection | IMPLEMENT | MEDIUM | New implementation |
| 8 | Non-Overlapping Constraints | IMPLEMENT | MEDIUM | New implementation |
| 9 | Batched Mask-to-Box | VERIFY | LOW | Audit current impl |
| 10 | Confidence Threshold Filtering | VERIFY | HIGH | Audit current impl |
| 11 | Mask Interpolation (NEAREST) | VERIFY | HIGH | Audit current impl |
| 12 | RLE Encoding | SKIP | LOW | Not needed for our use case |

---

## Phase 1: Audit Existing Implementations

### 1.1 Sprinkle Removal
- **Location**: `segmenter.py` (SAM2Transforms) + `mask_processing.py` (_remove_small_components)
- **HuggingFace Reference**: `max_sprinkle_area` parameter in SAM2Transforms
- **Audit Checklist**:
  - [ ] SAM2Transforms configured with max_sprinkle_area > 0
  - [ ] _remove_small_components uses connected components correctly
  - [ ] Parameters match HuggingFace defaults (100 pixels)

### 1.2 Hole Filling
- **Location**: `mask_processing.py` (_fill_small_holes)
- **HuggingFace Reference**: `max_hole_area` parameter in SAM2Transforms
- **Audit Checklist**:
  - [ ] Inverted mask approach for finding holes
  - [ ] Connected components analysis on inverted mask
  - [ ] Fills holes <= max_hole_area

### 1.3 Morphological Smoothing
- **Location**: `mask_processing.py` (_apply_morphology)
- **HuggingFace Reference**: NOT IN HUGGINGFACE (we're ahead)
- **Audit Checklist**:
  - [ ] Uses elliptical structuring element
  - [ ] Applies OPEN then CLOSE operations
  - [ ] Kernel size is configurable

### 1.4 Box Constraint
- **Location**: `mask_processing.py` (constrain_mask_to_box)
- **HuggingFace Reference**: NOT IN HUGGINGFACE (we're ahead)
- **Audit Checklist**:
  - [ ] Margin is ratio-based (not fixed pixels)
  - [ ] Handles edge cases (mask at image boundary)
  - [ ] Returns boolean mask

### 1.5 Confidence Threshold Filtering
- **Location**: `main.py` (/segment/interactive endpoint)
- **HuggingFace Reference**: `threshold` parameter (default 0.3)
- **Audit Checklist**:
  - [ ] Filters by confidence before returning
  - [ ] Default threshold matches (0.3)

### 1.6 Mask Interpolation
- **Location**: `main.py` (/segment/interactive endpoint)
- **HuggingFace Reference**: Uses bilinear, we should use NEAREST
- **Audit Checklist**:
  - [ ] Uses PIL.Resampling.NEAREST
  - [ ] Resizes to original image dimensions
  - [ ] Thresholds after resize (> 127)

### 1.7 Mask-to-Box Conversion
- **Location**: `segmenter.py` (segment_interactive method)
- **HuggingFace Reference**: _batched_mask_to_box
- **Audit Checklist**:
  - [ ] Handles empty masks correctly
  - [ ] Returns (x1, y1, x2, y2) format
  - [ ] Uses numpy efficiently

---

## Phase 2: Implement Missing Features

### 2.1 Stability Score Filtering [HIGH PRIORITY]

**Purpose**: Filter out uncertain masks where the model isn't confident

**HuggingFace Implementation**:
```python
def _compute_stability_score(masks, mask_threshold, stability_score_offset):
    intersections = (masks > (mask_threshold + stability_score_offset)).sum()
    unions = (masks > (mask_threshold - stability_score_offset)).sum()
    return intersections / unions
```

**Our Implementation Plan**:
- Add to: `mask_processing.py`
- Function: `compute_stability_score()`
- Function: `filter_masks_by_stability()`
- Config: `enable_stability_filtering`, `stability_score_thresh`

**Default Parameters**:
- `stability_score_thresh`: 0.95 (HuggingFace default)
- `stability_score_offset`: 1.0

### 2.2 Non-Maximum Suppression [HIGH PRIORITY]

**Purpose**: Remove overlapping duplicate detections

**HuggingFace Implementation**:
```python
from torchvision.ops import batched_nms
keep = batched_nms(boxes, scores, idxs, iou_threshold=0.7)
```

**Our Implementation Plan**:
- Add to: `mask_processing.py`
- Function: `apply_nms_to_masks()`
- Config: `enable_nms`, `nms_iou_threshold`

**Default Parameters**:
- `nms_iou_threshold`: 0.7 (HuggingFace default)

### 2.3 Edge Mask Rejection [MEDIUM PRIORITY]

**Purpose**: Reject masks touching image boundaries (likely incomplete)

**HuggingFace Implementation**:
```python
def _is_box_near_crop_edge(boxes, crop_box, orig_box, atol=20.0):
    near_crop_edge = torch.isclose(boxes, crop_box, atol=atol)
    near_image_edge = torch.isclose(boxes, orig_box, atol=atol)
    return near_crop_edge & ~near_image_edge
```

**Our Implementation Plan**:
- Add to: `mask_processing.py`
- Function: `is_mask_near_edge()`
- Function: `filter_edge_masks()`
- Config: `enable_edge_rejection`, `edge_tolerance_pixels`

**Default Parameters**:
- `edge_tolerance_pixels`: 20 (HuggingFace default)
- `enable_edge_rejection`: False (disabled by default)

### 2.4 Non-Overlapping Constraints [MEDIUM PRIORITY]

**Purpose**: Ensure each pixel belongs to at most one mask

**Our Implementation Plan**:
- Add to: `mask_processing.py`
- Function: `apply_non_overlapping_constraints()`
- Config: `enable_non_overlapping`

**Default Parameters**:
- `enable_non_overlapping`: False (disabled by default)

---

## Phase 3: Integration

### 3.1 Update Config

Add new settings to `config.py`:
```python
# Advanced mask filtering (HuggingFace-style)
enable_stability_filtering: bool = False
stability_score_thresh: float = 0.95
stability_score_offset: float = 1.0

enable_nms: bool = True
nms_iou_threshold: float = 0.7

enable_edge_rejection: bool = False
edge_tolerance_pixels: int = 20

enable_non_overlapping: bool = False
```

### 3.2 Update main.py

Integrate new post-processing in `/segment/interactive`:
1. After getting masks from segmenter
2. Apply stability filtering (if enabled)
3. Apply existing postprocess_mask
4. Apply box constraint
5. Apply NMS (if enabled)
6. Apply edge rejection (if enabled)
7. Apply non-overlapping (if enabled)
8. Resize with NEAREST interpolation

### 3.3 Update Exports

Update `utils/__init__.py` with new functions.

---

## Execution Order

1. [ ] **AUDIT**: Verify sprinkle removal implementation
2. [ ] **AUDIT**: Verify hole filling implementation
3. [ ] **AUDIT**: Verify morphological smoothing
4. [ ] **AUDIT**: Verify box constraint
5. [ ] **AUDIT**: Verify confidence filtering
6. [ ] **AUDIT**: Verify NEAREST interpolation
7. [ ] **AUDIT**: Verify mask-to-box conversion
8. [ ] **IMPLEMENT**: Stability score filtering
9. [ ] **IMPLEMENT**: NMS
10. [ ] **IMPLEMENT**: Edge mask rejection
11. [ ] **IMPLEMENT**: Non-overlapping constraints
12. [ ] **INTEGRATE**: Update config.py
13. [ ] **INTEGRATE**: Update main.py
14. [ ] **INTEGRATE**: Update __init__.py exports
15. [ ] **TEST**: Verify all features work together

---

## Progress Tracking

| Step | Status | Date | Notes |
|------|--------|------|-------|
| 1. Audit sprinkle removal | ✅ DONE | 2026-01-04 | SAM2Transforms + connected components |
| 2. Audit hole filling | ✅ DONE | 2026-01-04 | Inverted mask + connected components |
| 3. Audit morphology | ✅ DONE | 2026-01-04 | OPEN then CLOSE with ellipse kernel |
| 4. Audit box constraint | ✅ DONE | 2026-01-04 | Ratio-based margin (0.15) |
| 5. Audit confidence filter | ✅ DONE | 2026-01-04 | PCS uses threshold, PVS returns all |
| 6. Audit NEAREST interp | ✅ DONE | 2026-01-04 | PIL NEAREST + threshold > 127 |
| 7. Audit mask-to-box | ✅ DONE | 2026-01-04 | Handles empty, correct XYXY format |
| 8. Implement stability | ✅ DONE | 2026-01-04 | compute_stability_score, filter_masks_by_stability |
| 9. Implement NMS | ✅ DONE | 2026-01-04 | apply_nms_to_masks using torchvision |
| 10. Implement edge reject | ✅ DONE | 2026-01-04 | is_mask_near_edge, filter_edge_masks |
| 11. Implement non-overlap | ✅ DONE | 2026-01-04 | apply_non_overlapping_constraints |
| 12. Update config.py | ✅ DONE | 2026-01-04 | Added 10 new settings |
| 13. Update main.py | ✅ DONE | 2026-01-04 | New pipeline with 5-step processing |
| 14. Update exports | ✅ DONE | 2026-01-04 | 7 new functions exported |
| 15. Final testing | ✅ DONE | 2026-01-04 | All functions verified |

---

## Success Criteria

1. All existing implementations pass audit (match HuggingFace behavior)
2. New features are implemented and configurable
3. All features can be enabled/disabled via config
4. No regression in existing functionality
5. Unit tests pass (if applicable)
