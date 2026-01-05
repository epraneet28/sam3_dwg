# SAM3 Implementation Analysis & Replication Plan

## Executive Summary
The significant discrepancy between the current "playground" implementation and Roboflow's results (as seen in the provided images) is driven by three primary factors: **mask generation strategy**, **post-processing aggression**, and **prompt engineering**.

Roboflow's "Smart Select" leverages SAM3 with specific optimizations for fine-grained detail (essential for CAD drawings), whereas the current implementation is optimized for "blob-like" objects with aggressive smoothing.

## 1. Issue Analysis

### A. The "Blob" Problem (Post-Processing)
**Observation:** The user's result (Image 0) shows a "blobby" purple mask that spills over lines and lacks definition.
**Cause:** The current codebase aggressively smooths masks using morphological operations.
**Evidence:**
- `src/sam3_segmenter/utils/mask_processing.py`:
  - Applies `cv2.morphologyEx` (OPEN and CLOSE) with a fixed kernel size of 3.
  - Fills holes up to 256 pixels (`max_hole_area`).
  - Removes components smaller than 64 pixels (`min_component_area`).
**Impact:** For CAD drawings composed of thin lines and precise geometries, this post-processing actively destroys the data, merging distinct lines into blobs and filling in legitimate empty spaces (like the interior of a room outline).

### B. The "Single Mask" Constraint (Model Configuration)
**Observation:** The user's result has a low IoU (59.8%) and fails to capture the complex shape of the floor plan.
**Cause:** The backend explicitly forces SAM3 to return only a simple, single mask when a box is used.
**Evidence:**
- `src/sam3_segmenter/segmenter.py` (Line 354):
  ```python
  if box is not None and multimask_output:
      # ...
      multimask_output = False
  ```
**Impact:** SAM3 is capable of returning 3 levels of granularity (whole object, part, sub-part). By forcing `False`, the system takes the "ambiguous" single best guess, which is often just a coarse blob fitting the box, rather than the intricate detailed mask that Roboflow selects.

### C. Prompting Strategy
**Observation:** Roboflow's selection is extremely precise to the pixels.
**Cause:** Roboflow likely employs a "Smart Polygon" strategy that doesn't rely solely on a bounding box.
**Hypothesis:** Roboflow uses a grid of positive points *inside* the user's box to force SAM to pay attention to the internal details, or they use the `multimask_output=True` and select the mask with the highest complexity (perimeter-to-area ratio) suitable for line drawings.

## 2. Technical Recommendations (For Implementation)

The following changes should be executed by the engineering agent to replicate Roboflow's performance.

### Step 1: Disable "Blob" Post-Processing for CAD
**Goal:** preserve sharp lines and details.
**Action:**
- Modify `postprocess_mask` to accept a `mode` or `aggressiveness` parameter.
- For CAD/Line drawings, set `kernel_size=0` (disable morphology) and reduce `max_hole_area` to near zero (e.g., 10px).
- **Roboflow likely does almost zero smoothing** on these types of images.

### Step 2: Enable Multi-Mask Selection
**Goal:** Allow SAM3 to return the *detailed* mask, not just the *dominant* mask.
**Action:**
- In `segmenter.py`, remove or make conditional the logic that forces `multimask_output = False` when a box is present.
- **New Logic:** Request 3 masks (`multimask_output=True`). Calculate the "complexity" (e.g., edge density) of each mask. For CAD drawings, prefer the mask with higher complexity/detail rather than the highest bare confidence score, or return all 3 to the UI for the user to "tab" through (a common feature in advanced annotation tools).

### Step 3: Implement "Smart Grid" Prompting
**Goal:** Force SAM to capture the full object inside the box.
**Action:**
- If the user provides *only* a box, generate a 3x3 or 5x5 grid of points evenly spaced within the central 50% of the box.
- Submit these as `point_labels=1` (positive points) along with the box.
- This effectively tells SAM: "I want the object that occupies this *entire* space," preventing it from collapsing onto just one small wall or line.

### Step 4: Resolution Handling
**Goal:** Prevent thin lines from disappearing during resize.
**Action:**
- Check `utils/image.py`. Ensure `max_size` is at least 1024, but preferably higher (2048 or native) for large CAD sheets.
- If performance allows, process crops at native resolution: Crop the image to the user's box (plus padding) *before* sending to SAM, rather than resizing the whole giant blueprint.

## 3. Comparison Summary

| Feature | Current Implementation | Roboflow (Target) | Fix |
| :--- | :--- | :--- | :--- |
| **Prompt** | Box Only | Box + Smart Logic (Points?) | Add "Smart Grid" points inside box |
| **Output** | Single Mask (Forced) | Best of 3 (likely) | Enable `multimask_output=True` |
| **Smoothing** | Aggressive (Kernel 3) | Minimal / None | Disable morphology for CAD |
| **Resolution**| Max 2048 (Full Sheet) | Likely Tiled/Cropped | Crop-then-Segment strategy |

## 4. Proposed Execution Order
1.  **Immediate Fix:** Modify `segmenter.py` to allow `multimask_output=True` with boxes.
2.  **Immediate Fix:** Disable default post-processing (morphology and hole filling) in `main.py` when calling `postprocess_mask`.
3.  **Enhancement:** Implement the "Crop-then-Segment" logic to handle high-res blueprints without downscaling artifacts.
