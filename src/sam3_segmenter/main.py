"""FastAPI application for SAM3 Drawing Zone Segmenter."""

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import torch
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from sqlalchemy.orm import Session

from .config import settings
from .database import (
    init_db,
    get_db,
    Exemplar,
    Drawing,
    PromptConfig,
    InferenceConfig,
    get_or_seed_configs,
    seed_prompt_config,
    seed_inference_config,
)
from .models import (
    SegmentRequest,
    SegmentResponse,
    StructuralSegmentRequest,
    StructuralSegmentResponse,
    BatchSegmentRequest,
    BatchSegmentResponse,
    BatchSegmentResponseItem,
    HealthResponse,
    ExemplarUploadRequest,
    ExemplarUploadResponse,
    ExemplarMetadata,
    ExemplarListResponse,
    ExemplarDetailResponse,
    ExemplarUpdateRequest,
    ExemplarTestRequest,
    ExemplarTestResponse,
    ZoneTypeInfo,
    ZoneTypesResponse,
    DrawingUploadRequest,
    DrawingUploadResponse,
    DrawingMetadata,
    DrawingDetailResponse,
    ZonePromptConfig,
    InferenceSettings,
    PromptConfigResponse,
    PromptConfigUpdateRequest,
    InteractiveSegmentRequest,
    InteractiveSegmentResponse,
    MaskCandidate,
    # Document storage models
    DocumentUploadResponse,
    DocumentMetadata,
    DocumentListResponse,
    DocumentDetailResponse,
)
from .segmenter import DrawingSegmenter
from .utils.image import decode_base64_image, encode_image_to_base64
from .utils.mask_processing import (
    postprocess_mask,
    postprocess_mask_for_drawings,
    constrain_mask_to_box,
    apply_nms_to_masks,
    filter_edge_masks,
    apply_non_overlapping_constraints,
    filter_masks_by_iou,
    sort_masks_by_combined_score,
)
from .utils.debug_logging import create_debug_logger
from .zone_classifier import post_process_zones
from .document_storage import DocumentStorage, get_document_storage

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global segmenter instance
segmenter: Optional[DrawingSegmenter] = None

# Global document storage instance
doc_storage: Optional[DocumentStorage] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize model and database on startup and cleanup on shutdown."""
    global segmenter, doc_storage

    logger.info(f"Starting SAM3 Drawing Zone Segmenter...")

    # Initialize document storage
    doc_storage = DocumentStorage(settings.documents_dir)
    logger.info(f"Document storage initialized at {settings.documents_dir}")

    # Initialize database
    logger.info("Initializing database...")
    try:
        init_db()
        # Seed default configs if not present
        db = next(get_db())
        try:
            get_or_seed_configs(db)
            logger.info("Database initialized and configs seeded successfully")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise

    # Load SAM3 model
    logger.info(f"Loading SAM3 model from {settings.model_path}...")
    try:
        segmenter = DrawingSegmenter(
            model_path=settings.model_path,
            device=settings.device,
            confidence_threshold=settings.default_confidence_threshold,
        )

        # Pre-load model
        _ = segmenter.model

        # Load exemplars if directory exists
        exemplars_path = Path(settings.exemplars_dir)
        if exemplars_path.exists():
            segmenter.load_exemplars_from_directory(exemplars_path)
            logger.info(f"Loaded exemplars from {settings.exemplars_dir}")

        logger.info("SAM3 model loaded successfully")

    except Exception as e:
        logger.error(f"Failed to initialize segmenter: {e}", exc_info=True)
        raise

    yield

    # Cleanup
    logger.info("Shutting down SAM3 Drawing Zone Segmenter...")
    segmenter = None
    doc_storage = None


app = FastAPI(
    title="SAM3 Drawing Zone Segmenter",
    description=(
        "Segment engineering and structural drawings into semantic zones "
        "using Meta's SAM3 (Segment Anything Model 3)"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID tracking middleware
@app.middleware("http")
async def add_request_id(request, call_next):
    """Add unique request ID to each request for tracing."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


@app.post("/segment", response_model=SegmentResponse)
async def segment_drawing(request: SegmentRequest):
    """
    Segment a drawing with custom text prompts.

    This endpoint accepts any text prompts for zero-shot segmentation
    using SAM3's Promptable Concept Segmentation (PCS) capability.
    """
    if segmenter is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start_time = time.time()

    try:
        image = decode_base64_image(request.image_base64)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

    try:
        zones = segmenter.segment(
            image=image,
            prompts=request.prompts,
            confidence_threshold=request.confidence_threshold,
            return_masks=request.return_masks,
            return_crops=request.return_crops,
        )
    except Exception as e:
        logger.error(f"Segmentation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Segmentation failed: {str(e)}")

    # Post-process zones
    img_width, img_height = image.size
    zones = post_process_zones(zones, img_width, img_height)

    processing_time = (time.time() - start_time) * 1000

    return SegmentResponse(
        zones=zones,
        image_size=[img_width, img_height],
        processing_time_ms=processing_time,
    )


@app.post("/segment/structural", response_model=StructuralSegmentResponse)
async def segment_structural_drawing(request: StructuralSegmentRequest, db: Session = Depends(get_db)):
    """
    Segment a structural/construction drawing with configured prompts.

    This endpoint uses the current prompt configuration (from database or defaults):
    - Title blocks and revision blocks
    - Plan views, elevations, sections
    - Detail drawings
    - Schedule tables
    - Notes and legends
    - Grid systems

    Only enabled prompts in the configuration will be used for detection.
    """
    if segmenter is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start_time = time.time()

    try:
        image = decode_base64_image(request.image_base64)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

    # Load prompt config from database
    prompt_config = _get_prompt_config_list(db)

    try:
        zones = segmenter.segment_structural(
            image=image,
            return_masks=request.return_masks,
            return_crops=request.return_crops,
            prompt_config=prompt_config,
        )
    except Exception as e:
        logger.error(f"Structural segmentation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Segmentation failed: {str(e)}")

    # Post-process zones
    img_width, img_height = image.size
    zones = post_process_zones(zones, img_width, img_height)

    processing_time = (time.time() - start_time) * 1000

    return StructuralSegmentResponse(
        zones=zones,
        image_size=[img_width, img_height],
        processing_time_ms=processing_time,
    )


@app.post("/segment/batch", response_model=BatchSegmentResponse)
async def segment_batch(request: BatchSegmentRequest):
    """
    Process multiple images in a single request.

    Each image is segmented independently with the provided prompts.
    Results are returned in the same order as the input images.
    """
    if segmenter is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if len(request.images) > settings.max_batch_size:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size {len(request.images)} exceeds maximum {settings.max_batch_size}",
        )

    start_time = time.time()
    results = []

    for item in request.images:
        item_start = time.time()
        try:
            image = decode_base64_image(item.image_base64)
            zones = segmenter.segment(
                image=image,
                prompts=request.prompts,
                confidence_threshold=request.confidence_threshold,
                return_masks=request.return_masks,
            )

            img_width, img_height = image.size
            zones = post_process_zones(zones, img_width, img_height)

            results.append(
                BatchSegmentResponseItem(
                    page_id=item.page_id,
                    zones=zones,
                    image_size=[img_width, img_height],
                    processing_time_ms=(time.time() - item_start) * 1000,
                )
            )
        except Exception as e:
            logger.error(f"Batch segmentation failed for {item.page_id}: {e}", exc_info=True)
            results.append(
                BatchSegmentResponseItem(
                    page_id=item.page_id,
                    zones=[],
                    image_size=[0, 0],
                    processing_time_ms=(time.time() - item_start) * 1000,
                    error=str(e),
                )
            )

    total_time = (time.time() - start_time) * 1000

    return BatchSegmentResponse(
        results=results,
        total_processing_time_ms=total_time,
    )


@app.post("/segment/interactive", response_model=InteractiveSegmentResponse)
async def segment_interactive(request: InteractiveSegmentRequest):
    """
    Interactive segmentation using points and/or bounding box.

    This endpoint uses SAM3's Promptable Visual Segmentation (PVS) capability
    for instance-specific segmentation at specified locations.

    Input modes:
    - Points only: Click points to include (label=1) or exclude (label=0) regions
    - Box only: Draw a bounding box around the region of interest
    - Combined: Use both points and box for precise control

    Returns multiple mask candidates with IOU scores, sorted best-first.
    """
    if segmenter is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Validate that at least one prompt type is provided
    if not request.points and not request.box:
        raise HTTPException(
            status_code=400,
            detail="At least one prompt type (points or box) must be provided",
        )

    start_time = time.time()

    # =========================================================================
    # Debug Logging Setup
    # =========================================================================
    # Get storage path from request if doc_id provided, otherwise use default
    storage_path = None
    if request.doc_id:
        storage = _get_storage()
        if storage.document_exists(request.doc_id):
            storage_path = storage.get_document_dir(request.doc_id)

    debug_logger = create_debug_logger(storage_path=storage_path)
    debug_logger.log_settings()

    try:
        image = decode_base64_image(request.image_base64)
    except ValueError as e:
        debug_logger.log_error(e, "image_decode")
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

    img_width, img_height = image.size

    # Log input image
    debug_logger.log_input_image(image, request.image_base64)
    debug_logger.log_timing("image_decode", (time.time() - start_time) * 1000)

    try:
        import numpy as np

        # Convert point prompts to numpy arrays if provided
        point_coords = None
        point_labels = None
        if request.points:
            point_coords = np.array([[p.x, p.y] for p in request.points])
            point_labels = np.array([p.label for p in request.points])

        # Decode mask input if provided
        # Prefer low-res logits (mask_logits_base64) for better refinement quality
        # Fall back to binarized mask (mask_input_base64) for backwards compatibility
        mask_input = None
        if request.mask_logits_base64:
            # Decode low-res logits (numpy .npy format, shape [1, H, W])
            import base64
            import io

            logits_bytes = base64.b64decode(request.mask_logits_base64)
            mask_input = np.load(io.BytesIO(logits_bytes))
            # Ensure correct shape [1, H, W]
            if mask_input.ndim == 2:
                mask_input = mask_input[np.newaxis, :, :]
            logger.debug(f"Using low-res logits for refinement, shape: {mask_input.shape}")
        elif request.mask_input_base64:
            # Fall back to binarized mask (legacy mode)
            import base64
            import io
            from PIL import Image as PILImage

            mask_bytes = base64.b64decode(request.mask_input_base64)
            mask_img = PILImage.open(io.BytesIO(mask_bytes)).convert("L")
            # Convert to binary mask (0 or 1)
            mask_input = (np.array(mask_img) > 127).astype(np.float32)
            # SAM expects mask_input with shape [1, H, W]
            mask_input = mask_input[np.newaxis, :, :]
            logger.debug(f"Using binarized mask for refinement (legacy mode), shape: {mask_input.shape}")

        # Determine boxes to process (multi-box or single box)
        boxes_to_process = []
        if request.boxes:
            boxes_to_process = [np.array(b) for b in request.boxes]
        elif request.box:
            boxes_to_process = [np.array(request.box)]

        # Log all prompts
        debug_logger.log_prompts(
            point_coords=point_coords,
            point_labels=point_labels,
            box=boxes_to_process[0] if boxes_to_process else None,
            mask_input=mask_input,
            multimask_output=request.multimask_output,
        )

        sam_start = time.time()

        # Multi-box mode: run SAM3 for each box
        low_res_logits = []  # Store low-res logits for refinement
        if len(boxes_to_process) > 1:
            logger.info(f"Multi-box mode: processing {len(boxes_to_process)} boxes")
            all_masks = []
            all_iou_scores = []
            all_logits = []

            # In precision mode, preserve individual masks for candidate diversity
            # In zone mode, merge masks for solid region output
            preserve_candidates = settings.enable_precision_mode

            for i, box in enumerate(boxes_to_process):
                box_masks, box_iou_scores, _, box_logits = segmenter.segment_interactive(
                    image=image,
                    point_coords=point_coords,
                    point_labels=point_labels,
                    box=box,
                    mask_input=mask_input,
                    multimask_output=preserve_candidates,  # Multiple masks in precision mode
                )
                if len(box_masks) > 0:
                    if preserve_candidates:
                        # Keep all candidates from each box
                        all_masks.extend(box_masks)
                        all_iou_scores.extend(box_iou_scores)
                        if box_logits:
                            all_logits.extend(box_logits)
                    else:
                        # Zone mode: just take best mask per box
                        all_masks.append(box_masks[0])
                        all_iou_scores.append(box_iou_scores[0])
                        if box_logits and len(box_logits) > 0:
                            all_logits.append(box_logits[0])

            if all_masks:
                if preserve_candidates:
                    # Precision mode: return all individual masks as candidates
                    masks = all_masks
                    iou_scores = all_iou_scores
                    low_res_logits = all_logits if all_logits else []
                    # Recalculate bboxes for each mask
                    bboxes = []
                    for mask in masks:
                        ys, xs = np.where(mask > 0.5 if mask.dtype in (np.float32, np.float64) else mask)
                        if len(xs) > 0:
                            bboxes.append((float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())))
                        else:
                            bboxes.append((0.0, 0.0, 0.0, 0.0))
                    logger.info(f"Precision mode: preserved {len(masks)} individual mask candidates from {len(boxes_to_process)} boxes")
                else:
                    # Zone mode: Merge all masks using logical OR (union)
                    merged_mask = np.zeros_like(all_masks[0], dtype=bool)
                    for mask in all_masks:
                        merged_mask = np.logical_or(merged_mask, mask > 0.5)
                    avg_iou = sum(all_iou_scores) / len(all_iou_scores)
                    masks = [merged_mask.astype(np.float32)]
                    iou_scores = [avg_iou]
                    # Calculate merged bbox
                    ys, xs = np.where(merged_mask)
                    if len(xs) > 0:
                        bboxes = [(float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max()))]
                    else:
                        bboxes = [(0.0, 0.0, 0.0, 0.0)]
                    # For multi-box, combine logits by taking max (not ideal, but reasonable)
                    if all_logits:
                        merged_logits = np.maximum.reduce(all_logits)
                        low_res_logits = [merged_logits]
            else:
                masks, iou_scores, bboxes = [], [], []
        else:
            # Single box or points-only mode
            box = boxes_to_process[0] if boxes_to_process else None

            # Determine multimask_output behavior:
            # - In precision mode, use precision_mode_multimask setting (default True)
            # - Otherwise, use request's multimask_output setting
            if settings.enable_precision_mode:
                use_multimask = settings.precision_mode_multimask
            else:
                use_multimask = request.multimask_output

            masks, iou_scores, bboxes, low_res_logits = segmenter.segment_interactive(
                image=image,
                point_coords=point_coords,
                point_labels=point_labels,
                box=box,
                mask_input=mask_input,
                multimask_output=use_multimask,
            )

        debug_logger.log_timing("sam3_inference", (time.time() - sam_start) * 1000)

        # Log raw SAM3 output BEFORE any post-processing
        debug_logger.log_raw_sam_output(list(masks), list(iou_scores), stage="raw")

        # Import utilities at function scope
        from PIL import Image as PILImage
        import io
        import base64
        import numpy as np

        # Convert to lists for processing
        masks = list(masks)
        iou_scores = list(iou_scores)
        bboxes = list(bboxes)

        # =====================================================================
        # HuggingFace SAM3-style Post-Processing Pipeline
        # =====================================================================

        # Step 1: IoU filtering (filter by predicted IoU score)
        if settings.enable_iou_filtering and len(masks) > 0:
            masks, iou_scores, bboxes = filter_masks_by_iou(
                masks, iou_scores, bboxes,
                min_iou=settings.min_iou_score,
            )

        # Step 2: NMS (remove overlapping duplicates)
        # Skip NMS when multimask_output=true to preserve mask candidates for user selection
        if settings.enable_nms and len(masks) > 1 and not request.multimask_output:
            masks, iou_scores, bboxes = apply_nms_to_masks(
                masks, iou_scores, bboxes,
                iou_threshold=settings.nms_iou_threshold,
            )

        # Step 3: Edge rejection (filter masks touching image boundaries)
        if settings.enable_edge_rejection and len(masks) > 0:
            masks, iou_scores, bboxes = filter_edge_masks(
                masks, iou_scores, bboxes,
                image_shape=(img_height, img_width),
                edge_tolerance=settings.edge_tolerance_pixels,
            )

        # Step 4: Per-mask processing (cleanup, box constraint, resize)
        postprocess_start = time.time()
        processed_masks = []

        # PRECISION MODE: Skip all drawing-specific post-processing for Smart Select
        # This preserves SAM's raw pixel-precise masks for CAD/engineering drawings
        # where thin lines and fine details must be preserved.
        use_precision_mode = settings.enable_precision_mode
        if use_precision_mode:
            logger.info(
                "Precision mode ENABLED: bypassing drawing post-processing "
                "(box_fill, keep_largest, hole_fill, morphology)"
            )

        for i, mask in enumerate(masks):
            mask_before = mask.copy()

            # Use drawing-specific post-processing for engineering drawings
            # SKIP in precision mode to preserve raw SAM output
            if settings.enable_drawing_mode and not use_precision_mode:
                # Get box from request for box_fill method
                box_for_fill = None
                if request.box is not None:
                    box_for_fill = tuple(request.box)
                elif request.boxes and len(request.boxes) > 0:
                    # For multi-box, use the merged bounding box
                    all_coords = np.array(request.boxes)
                    box_for_fill = (
                        float(all_coords[:, 0].min()),
                        float(all_coords[:, 1].min()),
                        float(all_coords[:, 2].max()),
                        float(all_coords[:, 3].max()),
                    )

                mask = postprocess_mask_for_drawings(
                    mask,
                    keep_largest=settings.drawing_keep_largest_only,
                    fill_holes=settings.drawing_fill_all_holes,
                    apply_morphology=settings.mask_apply_morphology,
                    morphology_kernel=settings.mask_morphology_kernel_size,
                    min_area_ratio=settings.drawing_min_area_ratio,
                    fill_method=settings.drawing_fill_method,
                    box=box_for_fill,
                    morphology_fill_kernel=settings.drawing_morphology_kernel,
                )
                debug_logger.log_postprocessing_step(
                    "postprocess_for_drawings", mask_before, mask, mask_index=i
                )
            # Fallback to generic post-processing for natural images (skip in precision mode)
            elif settings.enable_mask_postprocessing and not use_precision_mode:
                mask = postprocess_mask(
                    mask,
                    min_component_area=settings.mask_min_component_area,
                    fill_holes=settings.mask_fill_holes,
                    max_hole_area=settings.mask_max_hole_area,
                    apply_morphology=settings.mask_apply_morphology,
                    kernel_size=settings.mask_morphology_kernel_size,
                )
                debug_logger.log_postprocessing_step(
                    "postprocess_mask", mask_before, mask, mask_index=i
                )

            # Constrain mask to box region (if box prompt was provided and enabled)
            # Disable via SAM3_ENABLE_BOX_CONSTRAINT=false for refinement workflows
            # Adjust margin via SAM3_BOX_CONSTRAINT_MARGIN (default 0.15 = 15%)
            if request.box is not None and settings.enable_box_constraint:
                mask_before_box = mask.copy()
                mask = constrain_mask_to_box(
                    mask, request.box, margin_ratio=settings.box_constraint_margin
                )
                debug_logger.log_postprocessing_step(
                    "constrain_to_box", mask_before_box, mask, mask_index=i
                )

            # Ensure mask matches image dimensions (use NEAREST for sharp edges)
            if mask.shape != (img_height, img_width):
                mask_before_resize = mask.copy()
                mask_pil = PILImage.fromarray(
                    (mask * 255).astype("uint8") if mask.dtype == bool else mask
                )
                mask_pil = mask_pil.resize(
                    (img_width, img_height),
                    PILImage.Resampling.NEAREST
                )
                mask = np.array(mask_pil) > 127
                debug_logger.log_postprocessing_step(
                    "resize", mask_before_resize, mask, mask_index=i
                )

            processed_masks.append(mask)

        masks = processed_masks
        debug_logger.log_timing("postprocessing", (time.time() - postprocess_start) * 1000)

        # Step 5: Non-overlapping constraints (each pixel -> one mask)
        # Skip non-overlapping when multimask_output=true to preserve mask candidates
        if settings.enable_non_overlapping and len(masks) > 1 and not request.multimask_output:
            masks = apply_non_overlapping_constraints(masks, iou_scores)

        # Log final masks after all post-processing
        debug_logger.log_raw_sam_output(masks, iou_scores, stage="after_postprocess")

        # Recalculate bboxes after post-processing (they may have changed)
        final_bboxes = []
        for mask in masks:
            ys, xs = np.where(mask)
            if len(xs) > 0 and len(ys) > 0:
                bbox = (float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max()))
            else:
                bbox = (0.0, 0.0, 0.0, 0.0)
            final_bboxes.append(bbox)

        # Log final output
        debug_logger.log_final_output(masks, iou_scores, final_bboxes)

        # =====================================================================
        # Complexity-aware sorting (before building response)
        # =====================================================================
        # In precision mode, use combined IoU + complexity score to favor
        # more detailed masks over simple blobs for line drawings
        if settings.enable_precision_mode and settings.enable_complexity_scoring and len(masks) > 1:
            masks, iou_scores, final_bboxes, combined_scores, sorted_logits = sort_masks_by_combined_score(
                masks, iou_scores, final_bboxes,
                complexity_weight=settings.complexity_weight,
                low_res_logits=low_res_logits,
            )
            # Update low_res_logits with sorted version (for correct refinement pairing)
            if sorted_logits is not None:
                low_res_logits = sorted_logits

        # =====================================================================
        # Build response with mask candidates
        # =====================================================================
        mask_candidates = []
        for i, (mask, iou_score, bbox) in enumerate(zip(masks, iou_scores, final_bboxes)):
            # Convert mask to base64 PNG - handle bool, float, and uint8 dtypes
            if mask.dtype == bool:
                mask_uint8 = (mask * 255).astype("uint8")
            elif mask.dtype in (np.float32, np.float64):
                # Float masks: threshold at 0.5 and convert to uint8
                mask_uint8 = ((mask > 0.5) * 255).astype("uint8")
            else:
                # Assume uint8, but ensure 0-255 range
                mask_uint8 = mask.astype("uint8")
                if mask_uint8.max() <= 1:
                    mask_uint8 = mask_uint8 * 255
            mask_img = PILImage.fromarray(mask_uint8)
            buffer = io.BytesIO()
            mask_img.save(buffer, format="PNG")
            mask_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            # Encode low-res logits for refinement (as numpy float32 bytes)
            logits_base64 = None
            if i < len(low_res_logits) and low_res_logits[i] is not None:
                logits = low_res_logits[i]
                # Ensure float32 and add batch dimension [1, H, W] for SAM3 input
                if logits.ndim == 2:
                    logits = logits[np.newaxis, :, :]
                logits = logits.astype(np.float32)
                # Encode as base64 numpy bytes
                logits_buffer = io.BytesIO()
                np.save(logits_buffer, logits)
                logits_base64 = base64.b64encode(logits_buffer.getvalue()).decode("utf-8")

            mask_candidates.append(
                MaskCandidate(
                    mask_base64=mask_base64,
                    iou_score=float(iou_score),
                    bbox=tuple(bbox),
                    low_res_logits_base64=logits_base64,
                )
            )

        # Sort mask candidates (if not already sorted by complexity scoring above)
        # Complexity-aware sorting is done earlier when precision_mode + complexity_scoring
        if not (settings.enable_precision_mode and settings.enable_complexity_scoring):
            # Default: Sort by IoU score only (best first)
            mask_candidates.sort(key=lambda m: m.iou_score, reverse=True)

        processing_time = (time.time() - start_time) * 1000
        debug_logger.log_timing("total", processing_time)

        # Save debug log
        debug_log_path = debug_logger.save()
        if debug_log_path:
            logger.info(f"Debug log saved: {debug_log_path}")

        return InteractiveSegmentResponse(
            masks=mask_candidates,
            image_size=(img_width, img_height),
            processing_time_ms=processing_time,
        )

    except Exception as e:
        debug_logger.log_error(e, "segment_interactive")
        debug_logger.save()  # Save debug log even on error
        logger.error(f"Interactive segmentation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Segmentation failed: {str(e)}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check service health and GPU status.

    Returns information about:
    - Service status
    - Model loading status
    - GPU availability and memory usage
    """
    gpu_available = torch.cuda.is_available()
    gpu_name = None
    gpu_memory = None

    if gpu_available:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.memory_allocated(0) // (1024 * 1024)

    return HealthResponse(
        status="healthy" if segmenter is not None else "loading",
        model="sam3",
        model_loaded=segmenter is not None,
        gpu_available=gpu_available,
        gpu_name=gpu_name,
        gpu_memory_used_mb=gpu_memory,
    )


# =============================================================================
# Prompt Configuration Endpoints
# =============================================================================


def _get_prompt_config_list(db: Session) -> list[dict]:
    """Get prompt config as list of dicts for segmenter."""
    configs = db.query(PromptConfig).order_by(PromptConfig.priority).all()
    return [c.to_dict() for c in configs]


def _get_inference_config(db: Session) -> InferenceConfig:
    """Get inference config, creating default if not exists."""
    config = db.query(InferenceConfig).first()
    if not config:
        seed_inference_config(db)
        config = db.query(InferenceConfig).first()
    return config


@app.get("/config/prompts", response_model=PromptConfigResponse)
async def get_prompt_config(db: Session = Depends(get_db)):
    """
    Get all prompt configurations.

    Returns the current prompt configuration from the database,
    including which zones are enabled and their prompt text.
    This is what will be sent to SAM3 during segmentation.
    """
    # Ensure configs exist
    get_or_seed_configs(db)

    # Get all prompt configs
    prompt_configs = db.query(PromptConfig).order_by(PromptConfig.priority).all()
    prompts = [ZonePromptConfig(**c.to_dict()) for c in prompt_configs]

    # Get inference config
    inference_config = _get_inference_config(db)
    inference = InferenceSettings(**inference_config.to_dict())

    return PromptConfigResponse(
        prompts=prompts,
        inference=inference,
        version=inference_config.version,
    )


@app.put("/config/prompts", response_model=PromptConfigResponse)
async def update_prompt_config(request: PromptConfigUpdateRequest, db: Session = Depends(get_db)):
    """
    Update prompt configurations.

    Updates the prompt configuration in the database.
    Changes take effect on the next segmentation request.
    """
    try:
        # Update each prompt config
        for prompt in request.prompts:
            existing = db.query(PromptConfig).filter(
                PromptConfig.zone_type == prompt.zone_type
            ).first()

            if existing:
                existing.primary_prompt = prompt.primary_prompt
                existing.alternate_prompts = json.dumps(prompt.alternate_prompts)
                existing.typical_location = prompt.typical_location
                existing.priority = prompt.priority
                existing.enabled = prompt.enabled
            else:
                # Create new prompt config
                new_config = PromptConfig(
                    zone_type=prompt.zone_type,
                    primary_prompt=prompt.primary_prompt,
                    alternate_prompts=json.dumps(prompt.alternate_prompts),
                    typical_location=prompt.typical_location,
                    priority=prompt.priority,
                    enabled=prompt.enabled,
                )
                db.add(new_config)

        # Update inference settings if provided
        if request.inference:
            inference_config = _get_inference_config(db)
            inference_config.confidence_threshold = request.inference.confidence_threshold
            inference_config.return_masks = request.inference.return_masks
            inference_config.version += 1

        db.commit()

        # Return updated config
        prompt_configs = db.query(PromptConfig).order_by(PromptConfig.priority).all()
        prompts = [ZonePromptConfig(**c.to_dict()) for c in prompt_configs]
        inference_config = _get_inference_config(db)

        logger.info(f"Updated prompt configuration (version {inference_config.version})")

        return PromptConfigResponse(
            prompts=prompts,
            inference=InferenceSettings(**inference_config.to_dict()),
            version=inference_config.version,
        )

    except Exception as e:
        logger.error(f"Failed to update prompt config: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@app.post("/config/prompts/reset", response_model=PromptConfigResponse)
async def reset_prompt_config(db: Session = Depends(get_db)):
    """
    Reset all prompts to defaults.

    Deletes all custom configurations and re-seeds from STRUCTURAL_ZONE_PROMPTS.
    """
    try:
        # Delete all existing configs
        db.query(PromptConfig).delete()
        db.query(InferenceConfig).delete()
        db.commit()

        # Re-seed defaults
        seed_prompt_config(db)
        seed_inference_config(db)

        # Return fresh config
        prompt_configs = db.query(PromptConfig).order_by(PromptConfig.priority).all()
        prompts = [ZonePromptConfig(**c.to_dict()) for c in prompt_configs]
        inference_config = _get_inference_config(db)

        logger.info("Reset prompt configuration to defaults")

        return PromptConfigResponse(
            prompts=prompts,
            inference=InferenceSettings(**inference_config.to_dict()),
            version=inference_config.version,
        )

    except Exception as e:
        logger.error(f"Failed to reset prompt config: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reset configuration: {str(e)}")


@app.get("/prompts/structural")
async def get_structural_prompts(db: Session = Depends(get_db)):
    """
    Return available structural drawing prompts (legacy endpoint).

    For the new configurable prompts, use GET /config/prompts instead.
    """
    # Ensure configs exist
    get_or_seed_configs(db)

    prompt_configs = db.query(PromptConfig).order_by(PromptConfig.priority).all()
    return {c.zone_type: c.to_dict() for c in prompt_configs}


@app.post("/exemplars/upload", response_model=ExemplarUploadResponse)
async def upload_exemplar(request: ExemplarUploadRequest, db: Session = Depends(get_db)):
    """
    Upload a visual exemplar for a zone type.

    Exemplars help improve segmentation accuracy for specific zone types
    by providing visual examples of what to look for.
    """
    if segmenter is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        image = decode_base64_image(request.image_base64)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

    # Save exemplar to disk
    exemplar_id = f"{request.zone_type}_{uuid.uuid4().hex[:8]}"
    exemplars_dir = Path(settings.exemplars_dir) / request.zone_type
    exemplars_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{exemplar_id}.png"
    save_path = exemplars_dir / filename
    image.save(save_path, format="PNG")

    # Load into segmenter
    segmenter.load_exemplar(request.zone_type, save_path)

    # Save metadata to database
    try:
        file_size = save_path.stat().st_size
        img_width, img_height = image.size

        exemplar = Exemplar(
            zone_type=request.zone_type,
            filename=filename,
            name=request.name,
            description=None,
            file_size_bytes=file_size,
            image_width=img_width,
            image_height=img_height,
        )
        db.add(exemplar)
        db.commit()
        db.refresh(exemplar)

        logger.info(f"Saved exemplar {exemplar.id} to database")

    except Exception as e:
        logger.error(f"Failed to save exemplar metadata to database: {e}", exc_info=True)
        db.rollback()
        # Continue even if database save fails

    return ExemplarUploadResponse(
        exemplar_id=exemplar_id,
        zone_type=request.zone_type,
        message=f"Exemplar saved and loaded successfully",
    )


@app.get("/exemplars")
async def list_exemplars():
    """
    List all loaded exemplars by zone type (legacy endpoint).

    For detailed exemplar metadata, use GET /exemplars/{zone_type}
    """
    if segmenter is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    exemplar_counts = {}
    for zone_type in segmenter._exemplars:
        exemplar_counts[zone_type] = len(segmenter._exemplars[zone_type])

    return {"exemplars": exemplar_counts}


@app.get("/exemplars/{zone_type}", response_model=ExemplarListResponse)
async def list_exemplars_by_type(zone_type: str, db: Session = Depends(get_db)):
    """
    List all exemplars for a specific zone type with metadata.

    Returns detailed information including effectiveness scores, usage stats, etc.
    """
    exemplars = db.query(Exemplar).filter(
        Exemplar.zone_type == zone_type,
        Exemplar.is_active == True
    ).all()

    exemplar_metadata = [ExemplarMetadata(**ex.to_dict()) for ex in exemplars]

    return ExemplarListResponse(
        exemplars=exemplar_metadata,
        total_count=len(exemplar_metadata)
    )


@app.get("/exemplars/{zone_type}/{exemplar_id}", response_model=ExemplarDetailResponse)
async def get_exemplar_detail(zone_type: str, exemplar_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific exemplar including the image.
    """
    exemplar = db.query(Exemplar).filter(
        Exemplar.id == exemplar_id,
        Exemplar.zone_type == zone_type
    ).first()

    if not exemplar:
        raise HTTPException(status_code=404, detail="Exemplar not found")

    # Load image from disk
    exemplar_path = Path(settings.exemplars_dir) / zone_type / exemplar.filename

    if not exemplar_path.exists():
        logger.warning(f"Exemplar file not found: {exemplar_path}")
        raise HTTPException(status_code=404, detail="Exemplar image file not found")

    try:
        with Image.open(exemplar_path) as img:
            image_base64 = encode_image_to_base64(img)
    except Exception as e:
        logger.error(f"Failed to read exemplar image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to read exemplar image: {str(e)}")

    return ExemplarDetailResponse(
        metadata=ExemplarMetadata(**exemplar.to_dict()),
        image_base64=image_base64
    )


@app.get("/exemplars/{zone_type}/{exemplar_id}/image")
async def get_exemplar_image(zone_type: str, exemplar_id: int, db: Session = Depends(get_db)):
    """
    Get just the exemplar image (returns base64 encoded PNG).
    """
    exemplar = db.query(Exemplar).filter(
        Exemplar.id == exemplar_id,
        Exemplar.zone_type == zone_type
    ).first()

    if not exemplar:
        raise HTTPException(status_code=404, detail="Exemplar not found")

    exemplar_path = Path(settings.exemplars_dir) / zone_type / exemplar.filename

    if not exemplar_path.exists():
        raise HTTPException(status_code=404, detail="Exemplar image file not found")

    try:
        with Image.open(exemplar_path) as img:
            image_base64 = encode_image_to_base64(img)
    except Exception as e:
        logger.error(f"Failed to read exemplar image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to read image: {str(e)}")

    return {"image_base64": image_base64}


@app.delete("/exemplars/{zone_type}/{exemplar_id}")
async def delete_exemplar(zone_type: str, exemplar_id: int, db: Session = Depends(get_db)):
    """
    Delete an exemplar (marks as inactive in database and removes from memory).

    The physical file is not deleted for safety, but the exemplar won't be used.
    """
    exemplar = db.query(Exemplar).filter(
        Exemplar.id == exemplar_id,
        Exemplar.zone_type == zone_type
    ).first()

    if not exemplar:
        raise HTTPException(status_code=404, detail="Exemplar not found")

    try:
        # Mark as inactive in database
        exemplar.is_active = False
        db.commit()

        # Remove from segmenter memory if loaded
        if segmenter and zone_type in segmenter._exemplars:
            exemplar_path = Path(settings.exemplars_dir) / zone_type / exemplar.filename
            if exemplar_path in segmenter._exemplars[zone_type]:
                segmenter._exemplars[zone_type].remove(exemplar_path)
                logger.info(f"Removed exemplar {exemplar_id} from segmenter memory")

        return {"message": f"Exemplar {exemplar_id} deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete exemplar: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete exemplar: {str(e)}")


@app.put("/exemplars/{zone_type}/{exemplar_id}", response_model=ExemplarMetadata)
async def update_exemplar_metadata(
    zone_type: str,
    exemplar_id: int,
    request: ExemplarUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update exemplar metadata (name, description, active status).
    """
    exemplar = db.query(Exemplar).filter(
        Exemplar.id == exemplar_id,
        Exemplar.zone_type == zone_type
    ).first()

    if not exemplar:
        raise HTTPException(status_code=404, detail="Exemplar not found")

    try:
        if request.name is not None:
            exemplar.name = request.name

        if request.description is not None:
            exemplar.description = request.description

        if request.is_active is not None:
            exemplar.is_active = request.is_active

        db.commit()
        db.refresh(exemplar)

        logger.info(f"Updated exemplar {exemplar_id} metadata")

        return ExemplarMetadata(**exemplar.to_dict())

    except Exception as e:
        logger.error(f"Failed to update exemplar: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update exemplar: {str(e)}")


@app.post("/exemplars/{zone_type}/{exemplar_id}/test", response_model=ExemplarTestResponse)
async def test_exemplar(
    zone_type: str,
    exemplar_id: int,
    request: ExemplarTestRequest,
    db: Session = Depends(get_db)
):
    """
    Test an exemplar against a test image to measure its effectiveness.

    Returns results both with and without the exemplar for comparison.
    """
    if segmenter is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Verify exemplar exists
    exemplar = db.query(Exemplar).filter(
        Exemplar.id == exemplar_id,
        Exemplar.zone_type == zone_type
    ).first()

    if not exemplar:
        raise HTTPException(status_code=404, detail="Exemplar not found")

    try:
        test_image = decode_base64_image(request.test_image_base64)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid test image: {str(e)}")

    start_time = time.time()

    try:
        # Test WITHOUT exemplar
        zones_without = segmenter.segment(
            image=test_image,
            prompts=[zone_type.replace("_", " ")],
            confidence_threshold=request.confidence_threshold,
            return_masks=False,
            return_crops=False
        )

        # Test WITH exemplar
        zones_with = segmenter.segment(
            image=test_image,
            prompts=[zone_type.replace("_", " ")],
            confidence_threshold=request.confidence_threshold,
            return_masks=False,
            return_crops=False
        )

        # Calculate confidence improvement
        conf_improvement = None
        if zones_with and zones_without:
            avg_with = sum(z.confidence for z in zones_with) / len(zones_with)
            avg_without = sum(z.confidence for z in zones_without) / len(zones_without)
            conf_improvement = avg_with - avg_without

        processing_time = (time.time() - start_time) * 1000

        # Update exemplar usage stats
        exemplar.times_used += 1
        if conf_improvement is not None:
            if exemplar.avg_confidence_improvement is None:
                exemplar.avg_confidence_improvement = conf_improvement
            else:
                # Running average
                n = exemplar.times_used
                exemplar.avg_confidence_improvement = (
                    (exemplar.avg_confidence_improvement * (n - 1) + conf_improvement) / n
                )
        db.commit()

        return ExemplarTestResponse(
            zones_with_exemplar=zones_with,
            zones_without_exemplar=zones_without,
            confidence_improvement=conf_improvement,
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"Exemplar testing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Testing failed: {str(e)}")


@app.get("/zones/types", response_model=ZoneTypesResponse)
async def list_zone_types(db: Session = Depends(get_db)):
    """
    List all available zone types with their prompt information and exemplar counts.

    Provides metadata about each zone type including primary prompts,
    typical locations, and how many exemplars exist for each type.
    """
    from .models import ZoneType
    from .prompts.structural import STRUCTURAL_ZONE_PROMPTS

    zone_types_list = []

    for zone_type in ZoneType:
        if zone_type == ZoneType.UNKNOWN:
            continue

        # Get prompt info if available
        prompt_info = STRUCTURAL_ZONE_PROMPTS.get(zone_type.value, {})

        # Count exemplars for this zone type
        exemplar_count = db.query(Exemplar).filter(
            Exemplar.zone_type == zone_type.value,
            Exemplar.is_active == True
        ).count()

        zone_info = ZoneTypeInfo(
            zone_type=zone_type.value,
            primary_prompt=prompt_info.get("primary_prompt", zone_type.value.replace("_", " ")),
            typical_location=prompt_info.get("typical_location", "unknown"),
            expected_per_page=str(prompt_info.get("expected_per_page", "variable")),
            exemplar_count=exemplar_count
        )
        zone_types_list.append(zone_info)

    return ZoneTypesResponse(zone_types=zone_types_list)


@app.post("/drawings/upload", response_model=DrawingUploadResponse)
async def upload_drawing(request: DrawingUploadRequest, db: Session = Depends(get_db)):
    """
    Upload and process a drawing, storing it with metadata and segmentation results.

    This endpoint saves the drawing to disk, runs segmentation, and stores
    all results in the database for future reference.
    """
    if segmenter is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        image = decode_base64_image(request.image_base64)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

    start_time = time.time()

    # Generate filename
    drawing_id_str = uuid.uuid4().hex[:12]
    filename = f"drawing_{drawing_id_str}.png"

    # Save drawing to disk
    drawings_dir = Path("drawings")
    drawings_dir.mkdir(parents=True, exist_ok=True)
    save_path = drawings_dir / filename
    image.save(save_path, format="PNG")

    # Load prompt config from database
    prompt_config = _get_prompt_config_list(db)

    # Run segmentation
    try:
        zones = segmenter.segment_structural(
            image=image,
            return_masks=False,
            return_crops=False,
            prompt_config=prompt_config,
        )

        img_width, img_height = image.size
        zones = post_process_zones(zones, img_width, img_height)

        processing_time = (time.time() - start_time) * 1000

    except Exception as e:
        logger.error(f"Drawing segmentation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Segmentation failed: {str(e)}")

    # Save to database
    try:
        file_size = save_path.stat().st_size
        zones_json = json.dumps([z.model_dump() for z in zones])

        drawing = Drawing(
            filename=filename,
            original_filename=request.filename,
            file_size_bytes=file_size,
            image_width=img_width,
            image_height=img_height,
            file_format="PNG",
            processing_date=datetime.now(timezone.utc),
            processing_time_ms=int(processing_time),
            page_type=None,
            page_type_confidence=None,
            zones_json=zones_json,
            confidence_threshold=request.confidence_threshold,
            used_exemplars=True,
            notes=request.notes,
        )

        db.add(drawing)
        db.commit()
        db.refresh(drawing)

        logger.info(f"Saved drawing {drawing.id} to database")

        return DrawingUploadResponse(
            drawing_id=drawing.id,
            filename=filename,
            zones=zones,
            page_type=None,
            page_type_confidence=None,
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"Failed to save drawing to database: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save drawing: {str(e)}")


@app.get("/drawings/{drawing_id}", response_model=DrawingDetailResponse)
async def get_drawing_detail(drawing_id: int, include_image: bool = False, db: Session = Depends(get_db)):
    """
    Get detailed information about a stored drawing.

    Optionally includes the drawing image (base64 encoded).
    Set include_image=true to retrieve the image data.
    """
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()

    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")

    # Parse zones from JSON
    zones = None
    if drawing.zones_json:
        try:
            zones_data = json.loads(drawing.zones_json)
            from .models import ZoneResult
            zones = [ZoneResult(**z) for z in zones_data]
        except Exception as e:
            logger.warning(f"Failed to parse zones JSON: {e}", exc_info=True)

    # Optionally load image
    image_base64 = None
    if include_image:
        drawing_path = Path("drawings") / drawing.filename
        if drawing_path.exists():
            try:
                with Image.open(drawing_path) as img:
                    image_base64 = encode_image_to_base64(img)
            except Exception as e:
                logger.error(f"Failed to read drawing image: {e}", exc_info=True)
        else:
            logger.warning(f"Drawing file not found: {drawing_path}")

    return DrawingDetailResponse(
        metadata=DrawingMetadata(**drawing.to_dict()),
        zones=zones,
        image_base64=image_base64
    )


@app.get("/drawings/{drawing_id}/results")
async def get_drawing_results(drawing_id: int, db: Session = Depends(get_db)):
    """
    Get just the segmentation results for a drawing (without image).

    Lightweight endpoint for retrieving zone data and metadata.
    """
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()

    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")

    zones = None
    if drawing.zones_json:
        try:
            zones_data = json.loads(drawing.zones_json)
            from .models import ZoneResult
            zones = [ZoneResult(**z) for z in zones_data]
        except Exception as e:
            logger.warning(f"Failed to parse zones JSON: {e}", exc_info=True)

    return {
        "drawing_id": drawing.id,
        "filename": drawing.filename,
        "page_type": drawing.page_type,
        "page_type_confidence": drawing.page_type_confidence,
        "processing_time_ms": drawing.processing_time_ms,
        "zones": zones
    }


# =============================================================================
# Document Storage Endpoints (for Playground - folder-based storage)
# =============================================================================
# Each document has its own folder: storage/{timestamp}_{filename}/
#   ├── metadata.json       # Document metadata
#   ├── original/           # Original uploaded image
#   │   └── image.{ext}
#   ├── viewer/             # Auto-run segmentation results
#   │   ├── zones.json      # Zone detection results
#   │   └── masks/          # Individual mask images
#   └── playground/         # Interactive session data
#       ├── sessions/       # Session snapshots
#       └── exports/        # User exports


def _get_storage() -> DocumentStorage:
    """Get document storage instance."""
    global doc_storage
    if doc_storage is None:
        doc_storage = DocumentStorage(settings.documents_dir)
    return doc_storage


@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a document (image file) for interactive segmentation.

    Creates a folder structure for the document:
        storage/{timestamp}_{filename}/
        ├── metadata.json
        ├── original/image.{ext}
        ├── viewer/
        └── playground/

    Supports PNG and JPEG formats.
    """
    try:
        storage = _get_storage()

        # Validate file type
        content_type = file.content_type or ""
        if not content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {content_type}. Only images are supported."
            )

        # Read file content
        content = await file.read()

        # Check file size
        max_size = settings.max_document_size_mb * 1024 * 1024
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {settings.max_document_size_mb}MB"
            )

        # Determine file extension
        ext = ".png"
        if "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"

        # Open and validate image
        import io
        try:
            image = Image.open(io.BytesIO(content))
            width, height = image.size
            file_format = image.format or "PNG"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")

        # Generate document ID with timestamp and filename
        doc_id = storage.generate_doc_id(file.filename or "document")

        # Create folder structure
        original_dir = storage.get_original_dir(doc_id, create=True)
        storage.get_viewer_dir(doc_id, create=True)  # Pre-create viewer folder
        storage.get_playground_dir(doc_id, create=True)  # Pre-create playground folder

        # Save the image to original/ folder
        save_path = original_dir / f"image{ext}"

        # Convert to RGB if necessary (e.g., RGBA -> RGB for JPEG)
        if ext == ".jpg" and image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        image.save(save_path, format="PNG" if ext == ".png" else "JPEG")

        # Save metadata
        metadata = {
            "doc_id": doc_id,
            "filename": f"image{ext}",
            "original_filename": file.filename,
            "upload_date": datetime.now(timezone.utc).isoformat(),
            "file_size_bytes": len(content),
            "image_width": width,
            "image_height": height,
            "file_format": file_format,
            "total_pages": 1,
        }

        storage.save_metadata(doc_id, metadata)

        logger.info(f"Document uploaded: {doc_id} ({width}x{height}, {len(content)} bytes)")

        return DocumentUploadResponse(**metadata)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """List all uploaded documents."""
    try:
        storage = _get_storage()
        documents_data = storage.list_documents()
        documents = [DocumentMetadata(**d) for d in documents_data]

        return DocumentListResponse(documents=documents, total_count=len(documents))

    except Exception as e:
        logger.error(f"Failed to list documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@app.get("/documents/{doc_id}", response_model=DocumentDetailResponse)
async def get_document(doc_id: str, include_image: bool = False):
    """Get document details, optionally including the image as base64."""
    try:
        storage = _get_storage()

        # Load metadata
        metadata = storage.load_metadata(doc_id)
        if not metadata:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        # Optionally load image
        image_base64 = None
        if include_image:
            image_path = storage.get_original_image_path(doc_id)
            if image_path and image_path.exists():
                image = Image.open(image_path)
                image_base64 = encode_image_to_base64(image)

        return DocumentDetailResponse(
            metadata=DocumentMetadata(**metadata),
            image_base64=image_base64
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get document {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@app.get("/documents/{doc_id}/image")
async def get_document_image(doc_id: str):
    """Get document image as base64."""
    try:
        storage = _get_storage()
        image_path = storage.get_original_image_path(doc_id)

        if not image_path or not image_path.exists():
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        image = Image.open(image_path)
        image_base64 = encode_image_to_base64(image)

        return {"image_base64": image_base64}

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get document image {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get image: {str(e)}")


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document and all its files/folders."""
    try:
        storage = _get_storage()

        # Check if document exists
        if not storage.document_exists(doc_id):
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        # Delete entire document folder
        deleted = storage.delete_document(doc_id)

        if deleted:
            logger.info(f"Document deleted: {doc_id}")
            return {"message": f"Document {doc_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete document {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


# =============================================================================
# Viewer Zone Storage Endpoints
# =============================================================================


@app.post("/documents/{doc_id}/viewer/zones")
async def save_viewer_zones(doc_id: str, zones_data: dict):
    """Save viewer zones (auto-run segmentation results) for a document."""
    try:
        storage = _get_storage()

        if not storage.document_exists(doc_id):
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        # Add timestamp
        zones_data["saved_at"] = datetime.now(timezone.utc).isoformat()

        storage.save_viewer_zones(doc_id, zones_data)
        logger.info(f"Saved viewer zones for document: {doc_id}")

        return {"message": "Zones saved successfully", "doc_id": doc_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save viewer zones for {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save zones: {str(e)}")


@app.get("/documents/{doc_id}/viewer/zones")
async def get_viewer_zones(doc_id: str):
    """Get viewer zones (auto-run segmentation results) for a document."""
    try:
        storage = _get_storage()

        if not storage.document_exists(doc_id):
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        zones_data = storage.load_viewer_zones(doc_id)

        if zones_data is None:
            return {"zones": None, "saved_at": None}

        return zones_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get viewer zones for {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get zones: {str(e)}")


# =============================================================================
# Playground Session Storage Endpoints
# =============================================================================


@app.post("/documents/{doc_id}/playground/sessions/{session_id}")
async def save_playground_session(doc_id: str, session_id: str, session_data: dict):
    """Save a playground session snapshot."""
    try:
        storage = _get_storage()

        if not storage.document_exists(doc_id):
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        # Add timestamp
        session_data["saved_at"] = datetime.now(timezone.utc).isoformat()
        session_data["session_id"] = session_id

        storage.save_playground_session(doc_id, session_id, session_data)
        logger.info(f"Saved playground session {session_id} for document: {doc_id}")

        return {"message": "Session saved successfully", "doc_id": doc_id, "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save playground session for {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save session: {str(e)}")


@app.get("/documents/{doc_id}/playground/sessions")
async def list_playground_sessions(doc_id: str):
    """List all playground sessions for a document."""
    try:
        storage = _get_storage()

        if not storage.document_exists(doc_id):
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        sessions_dir = storage.get_playground_sessions_dir(doc_id)
        sessions = []

        if sessions_dir.exists():
            for session_file in sessions_dir.glob("*.json"):
                try:
                    with open(session_file, "r") as f:
                        session_data = json.load(f)
                    sessions.append({
                        "session_id": session_file.stem,
                        "saved_at": session_data.get("saved_at"),
                    })
                except Exception as e:
                    logger.warning(f"Failed to load session {session_file}: {e}")

        # Sort by saved_at (newest first)
        sessions.sort(key=lambda s: s.get("saved_at", ""), reverse=True)

        return {"sessions": sessions, "count": len(sessions)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list playground sessions for {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@app.get("/documents/{doc_id}/playground/sessions/{session_id}")
async def get_playground_session(doc_id: str, session_id: str):
    """Get a specific playground session."""
    try:
        storage = _get_storage()

        if not storage.document_exists(doc_id):
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        sessions_dir = storage.get_playground_sessions_dir(doc_id)
        session_path = sessions_dir / f"{session_id}.json"

        if not session_path.exists():
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        with open(session_path, "r") as f:
            session_data = json.load(f)

        return session_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get playground session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


# =============================================================================
# Storage Migration Endpoint
# =============================================================================


@app.post("/admin/migrate-storage")
async def migrate_storage():
    """Migrate from flat storage structure to folder-based structure.

    This is a one-time operation to migrate existing documents from the old
    flat structure (doc_id.json + doc_id.ext) to the new folder structure
    (doc_id/metadata.json + doc_id/original/image.ext).
    """
    try:
        storage = _get_storage()
        migrated_count = storage.migrate_flat_storage()

        return {
            "message": f"Migration complete",
            "migrated_documents": migrated_count
        }

    except Exception as e:
        logger.error(f"Storage migration failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")


# Run with: uvicorn src.sam3_segmenter.main:app --reload --port 8001
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.sam3_segmenter.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
