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
    complexity_weight: float = 0.3            # Weight for complexity vs IoU (0-1)

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
