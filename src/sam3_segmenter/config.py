"""Configuration settings for the SAM3 Drawing Segmenter service."""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Model settings
    model_path: str = "sam3.pt"
    default_confidence_threshold: float = 0.3

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8001

    # CORS settings
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3005",
        "http://localhost:3006",
        "http://localhost:3007",
        "http://localhost:3008",
        "http://localhost:8000",
    ]

    # GPU settings (None = auto-detect)
    device: Optional[str] = None

    # Exemplars directory
    exemplars_dir: str = "./exemplars"

    # Batch processing settings
    max_batch_size: int = 10

    # Mask post-processing settings
    # NOTE: SAM3's internal postprocess_masks() has max_sprinkle_area=0 by default,
    # which leaves noise artifacts. Our post-processing removes these and improves
    # mask quality to match Roboflow's output.
    enable_mask_postprocessing: bool = True
    mask_min_component_area: int = 100  # Remove sprinkles smaller than this (pixels)
    mask_fill_holes: bool = True
    mask_max_hole_area: int = 500  # Fill holes smaller than this (pixels)
    mask_apply_morphology: bool = True
    mask_morphology_kernel_size: int = 5  # Kernel size for smoothing (odd number)

    # Drawing-specific post-processing (for engineering/structural drawings)
    # SAM3 segments LINE WORK instead of ENCLOSED AREAS in drawings.
    # This post-processing creates solid regions like Roboflow by:
    # 1. Keeping only the largest connected component (removes scattered lines)
    # 2. Filling ALL interior holes (creates solid fill, not just line outlines)
    enable_drawing_mode: bool = True            # Enable drawing-specific post-processing
    drawing_keep_largest_only: bool = True      # Keep only largest connected component
    drawing_fill_all_holes: bool = True         # Fill ALL interior holes (solid region)
    drawing_min_area_ratio: float = 0.001       # Minimum mask area as ratio of image

    # Fill method for box prompts: "box_fill", "morphological", or "convex_hull"
    # - box_fill: Fill the user's box region directly (Roboflow-style, best for box prompts)
    # - morphological: Use large morphological closing to bridge gaps (preserves shape)
    # - convex_hull: Fill convex hull of mask points (may distort non-convex regions)
    drawing_fill_method: str = "box_fill"       # Default to box_fill for Roboflow-like results
    drawing_morphology_kernel: int = 25         # Kernel for morphological fill (larger = more fill)

    # Advanced mask filtering (HuggingFace SAM3-style)
    # These provide additional quality filtering beyond basic post-processing

    # Stability filtering: Rejects uncertain masks based on threshold consistency
    # High stability = mask is consistent across threshold variations
    enable_stability_filtering: bool = False  # Disabled by default (strict filter)
    stability_score_thresh: float = 0.95      # HuggingFace default (very strict)
    stability_score_offset: float = 1.0       # Offset for stability computation

    # NMS (Non-Maximum Suppression): Removes overlapping duplicate detections
    enable_nms: bool = True                   # Enabled - recommended for text prompts
    nms_iou_threshold: float = 0.7            # HuggingFace default

    # Edge rejection: Filters masks touching image boundaries (likely incomplete)
    enable_edge_rejection: bool = False       # Disabled by default
    edge_tolerance_pixels: int = 20           # HuggingFace default

    # Non-overlapping: Ensures each pixel belongs to only one mask
    enable_non_overlapping: bool = False      # Disabled by default

    # IoU filtering: Minimum predicted IoU score for interactive segmentation
    enable_iou_filtering: bool = False        # Disabled by default
    min_iou_score: float = 0.5                # Minimum IoU to keep

    # Box prompt behavior settings
    # Meta recommends single mask for box prompts (non-ambiguous), but multi-mask
    # can be useful for comparing candidates in interactive workflows
    # Set to False for Roboflow-style "choose a mask" workflow
    force_single_mask_for_box: bool = False   # False = return 3 mask candidates for selection

    # Box constraint: Constrains masks to box region + margin
    # Useful for structural drawings where you want tight bounds
    # Disable for refinement workflows where mask may extend beyond box
    # Set to False for Roboflow-style refinement (click inside/outside to refine)
    enable_box_constraint: bool = False       # False = allow mask to extend beyond box
    box_constraint_margin: float = 0.15       # Margin ratio (15% of box size)

    # ==========================================================================
    # Precision Mode for Smart Select (Roboflow-style pixel-precise masks)
    # ==========================================================================
    # When enabled, bypasses all drawing-specific post-processing to preserve
    # SAM's raw mask output. This is essential for CAD/engineering drawings
    # where thin lines and fine details must be preserved.
    #
    # Precision mode changes:
    # - Disables box_fill (returns SAM's actual mask, not a filled rectangle)
    # - Disables keep_largest_only (preserves all connected components)
    # - Disables hole filling (preserves interior details)
    # - Disables morphological smoothing (preserves sharp edges)
    # - Uses complexity-aware candidate scoring instead of IoU-only
    #
    # Set via SAM3_ENABLE_PRECISION_MODE=true for Smart Select workflows

    enable_precision_mode: bool = True        # Enable by default for Smart Select
    precision_mode_multimask: bool = True     # Return 3 candidates in precision mode

    # SAM transform settings (applied inside SAM before we see the mask)
    # Set to 0 for raw SAM output (Roboflow-style precision)
    interactive_max_hole_area: float = 0.0    # 0 = no hole filling by SAM
    interactive_max_sprinkle_area: float = 0.0  # 0 = no sprinkle removal by SAM

    # Complexity-based candidate scoring (alternative to IoU-only)
    # For line drawings, more complex masks (higher perimeter/area) are often better
    enable_complexity_scoring: bool = True    # Use complexity in candidate ranking
    complexity_weight: float = 0.5            # Weight for complexity vs IoU (0-1)
    # NOTE: Changed from 0.3 to 0.5 to better preserve boundary details in engineering drawings.
    # At 0.3, "filled" masks with higher IoU were winning over detailed boundary masks.
    # At 0.5, complexity (perimeter/sqrt(area)) is weighted equally with IoU.

    # ==========================================================================
    # Mask Candidate Selection Strategy
    # ==========================================================================
    # SAM3 returns multiple mask candidates. This controls which one is preferred:
    # - "iou": Select by IoU score only (SAM3's confidence)
    # - "combined": Use IoU + complexity scoring (current behavior)
    # - "largest": Prefer candidate with most pixels (captures grid bubbles, annotations)
    # - "smallest": Prefer candidate with fewest pixels (tightest fit)
    # For engineering drawings with grid bubbles, "largest" often works best
    mask_selection_mode: str = "largest"

    # Component bonus for complexity scoring (rewards disjoint regions like grid bubbles)
    # Added to complexity score: complexity + component_bonus * num_components
    # Set to 0 to disable component bonus
    component_complexity_bonus: float = 0.5

    # ==========================================================================
    # Mask Output Settings (affects boundary precision)
    # ==========================================================================
    # Mask binarization threshold for float masks (0.0-1.0)
    # Lower values include more uncertain edge pixels, higher values are stricter
    # Default changed to 0.35 to capture more edge pixels (grid bubbles, annotations)
    # SAM3 standard is 0.5; lower values help with thin lines and boundary details
    mask_binarization_threshold: float = 0.35

    # Precision mode mask dilation (expands mask boundaries to capture edge pixels)
    # When enabled, applies small morphological dilation AFTER SAM inference
    # This helps capture boundary details that SAM's internal threshold might miss
    enable_precision_dilation: bool = False   # Disabled by default
    precision_dilation_pixels: int = 2        # Pixels to expand mask boundary

    # Precision mode smoothing (morphological closing after dilation)
    # Applies closing to smooth jagged edges and fill small gaps between components
    # This mimics Roboflow's smoother boundary output
    enable_precision_smoothing: bool = False  # Disabled by default
    precision_smoothing_kernel: int = 5       # Kernel size for closing (odd number)

    # Union mode: merge top-k mask candidates instead of selecting one
    # This captures edge details that may only appear in secondary candidates
    # e.g., grid bubbles might be in candidate #2 while main area is in #1
    enable_candidate_union: bool = False      # Disabled by default
    candidate_union_topk: int = 2             # Number of top candidates to merge (2-3)

    # ==========================================================================
    # Find Similar Settings
    # ==========================================================================
    # Enables "Find Similar" feature that searches for objects similar to a
    # selected region using SAM3's backbone feature embeddings.

    enable_find_similar: bool = True

    # Search parameters
    find_similar_default_threshold: float = 0.7    # Cosine similarity threshold
    find_similar_max_results: int = 10             # Maximum results to return
    find_similar_grid_stride: int = 32             # Grid stride for scanning
    find_similar_nms_threshold: float = 0.5        # NMS IoU threshold

    # Feature extraction settings
    find_similar_feature_level: int = 1            # FPN level (0=288x288, 1=144x144, 2=72x72)
    find_similar_pool_size: int = 7                # RoI pooling output size

    # Scale search: check multiple scales relative to exemplar
    find_similar_scale_factors: list[float] = [0.5, 0.75, 1.0, 1.25, 1.5]

    # Document storage directory (for uploaded images)
    documents_dir: str = "./storage"
    max_document_size_mb: int = 50

    # Logging
    log_level: str = "INFO"

    # Debug logging - saves verbose logs to storage directory for each run
    # Includes: all settings, inputs (points, boxes, prompts), outputs (masks, scores)
    enable_debug_logging: bool = True  # Enable by default for debugging
    debug_log_masks: bool = True  # Save mask images to debug directory
    debug_log_inputs: bool = True  # Log raw input data (base64 images, coordinates)

    model_config = {
        "env_file": ".env",
        "env_prefix": "SAM3_",
        "extra": "ignore",
    }


settings = Settings()
