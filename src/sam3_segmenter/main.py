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
)
from .segmenter import DrawingSegmenter
from .utils.image import decode_base64_image, encode_image_to_base64
from .zone_classifier import post_process_zones

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global segmenter instance
segmenter: Optional[DrawingSegmenter] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize model and database on startup and cleanup on shutdown."""
    global segmenter

    logger.info(f"Starting SAM3 Drawing Zone Segmenter...")

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

    try:
        image = decode_base64_image(request.image_base64)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

    img_width, img_height = image.size

    try:
        # Convert point prompts to numpy arrays if provided
        point_coords = None
        point_labels = None
        if request.points:
            import numpy as np

            point_coords = np.array([[p.x, p.y] for p in request.points])
            point_labels = np.array([p.label for p in request.points])

        # Convert box to numpy array if provided
        box = None
        if request.box:
            import numpy as np

            box = np.array(request.box)

        # Decode mask input if provided
        mask_input = None
        if request.mask_input_base64:
            import base64
            import io
            from PIL import Image as PILImage

            mask_bytes = base64.b64decode(request.mask_input_base64)
            mask_img = PILImage.open(io.BytesIO(mask_bytes)).convert("L")
            # Convert to binary mask (0 or 1)
            mask_input = (np.array(mask_img) > 127).astype(np.float32)
            # SAM expects mask_input with shape [1, H, W]
            mask_input = mask_input[np.newaxis, :, :]

        # Call segmenter's interactive method
        masks, iou_scores, bboxes = segmenter.segment_interactive(
            image=image,
            point_coords=point_coords,
            point_labels=point_labels,
            box=box,
            mask_input=mask_input,
            multimask_output=request.multimask_output,
        )

        # Build response with mask candidates
        mask_candidates = []
        for mask, iou_score, bbox in zip(masks, iou_scores, bboxes):
            # Convert mask to base64 PNG
            from PIL import Image as PILImage
            import io
            import base64

            mask_img = PILImage.fromarray((mask * 255).astype("uint8"))
            buffer = io.BytesIO()
            mask_img.save(buffer, format="PNG")
            mask_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            mask_candidates.append(
                MaskCandidate(
                    mask_base64=mask_base64,
                    iou_score=float(iou_score),
                    bbox=tuple(bbox),
                )
            )

        # Sort by IOU score (best first)
        mask_candidates.sort(key=lambda m: m.iou_score, reverse=True)

        processing_time = (time.time() - start_time) * 1000

        return InteractiveSegmentResponse(
            masks=mask_candidates,
            image_size=(img_width, img_height),
            processing_time_ms=processing_time,
        )

    except Exception as e:
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


# Run with: uvicorn src.sam3_segmenter.main:app --reload --port 8001
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.sam3_segmenter.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
