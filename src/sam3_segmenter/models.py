"""Pydantic models for request/response schemas."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ZoneType(str, Enum):
    """Types of zones that can be detected in engineering drawings."""

    TITLE_BLOCK = "title_block"
    REVISION_BLOCK = "revision_block"
    PLAN_VIEW = "plan_view"
    ELEVATION_VIEW = "elevation_view"
    SECTION_VIEW = "section_view"
    DETAIL_VIEW = "detail_view"
    SCHEDULE_TABLE = "schedule_table"
    NOTES_AREA = "notes_area"
    LEGEND = "legend"
    GRID_SYSTEM = "grid_system"
    UNKNOWN = "unknown"


class PageType(str, Enum):
    """Classification of drawing page types."""

    SPEC_SHEET = "spec_sheet"
    PLAN = "plan"
    ELEVATION = "elevation"
    SECTION = "section"
    DETAILS = "details"
    UNKNOWN = "unknown"


class ZoneResult(BaseModel):
    """Result for a single detected zone."""

    zone_id: str = Field(..., description="Unique identifier for this zone")
    zone_type: str = Field(..., description="Type of zone detected")
    prompt_matched: str = Field(..., description="The prompt that matched this zone")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    bbox: list[float] = Field(..., description="Bounding box [x1, y1, x2, y2] in pixels")
    bbox_normalized: Optional[list[float]] = Field(
        None, description="Bounding box [x1, y1, x2, y2] normalized to 0-1"
    )
    area_ratio: Optional[float] = Field(None, description="Zone area / total image area")
    mask_base64: Optional[str] = Field(None, description="Base64 encoded PNG mask")
    crop_base64: Optional[str] = Field(None, description="Base64 encoded cropped zone image")


class SegmentRequest(BaseModel):
    """Request model for general segmentation."""

    image_base64: str = Field(..., description="Base64 encoded image (PNG or JPEG)")
    prompts: list[str] = Field(..., min_length=1, description="Text prompts for segmentation")
    exemplar_ids: Optional[list[str]] = Field(
        None, description="IDs of stored visual exemplars to use"
    )
    return_masks: bool = Field(True, description="Include mask data in response")
    return_crops: bool = Field(False, description="Include cropped zone images in response")
    confidence_threshold: float = Field(
        0.3, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )


class StructuralSegmentRequest(BaseModel):
    """Request model for structural drawing segmentation."""

    image_base64: str = Field(..., description="Base64 encoded image (PNG or JPEG)")
    return_masks: bool = Field(True, description="Include mask data in response")
    return_crops: bool = Field(False, description="Include cropped zone images in response")


class BatchImageItem(BaseModel):
    """Single image item for batch processing."""

    image_base64: str = Field(..., description="Base64 encoded image")
    page_id: str = Field(..., description="Identifier for this page")


class BatchSegmentRequest(BaseModel):
    """Request model for batch segmentation."""

    images: list[BatchImageItem] = Field(..., min_length=1, description="List of images to process")
    prompts: list[str] = Field(..., min_length=1, description="Text prompts for segmentation")
    return_masks: bool = Field(False, description="Include mask data in response")
    confidence_threshold: float = Field(0.3, ge=0.0, le=1.0)


class SegmentResponse(BaseModel):
    """Response model for segmentation results."""

    zones: list[ZoneResult] = Field(default_factory=list, description="List of detected zones")
    image_size: list[int] = Field(..., description="Image dimensions [width, height]")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    model_version: str = Field("sam3", description="Model version used")


class StructuralSegmentResponse(SegmentResponse):
    """Response model for structural drawing segmentation."""
    # Page classification removed - now handled via prompt configuration
    pass


class BatchSegmentResponseItem(BaseModel):
    """Response for a single item in batch processing."""

    page_id: str
    zones: list[ZoneResult]
    image_size: list[int]
    processing_time_ms: float
    error: Optional[str] = None


class BatchSegmentResponse(BaseModel):
    """Response model for batch segmentation."""

    results: list[BatchSegmentResponseItem]
    total_processing_time_ms: float
    model_version: str = "sam3"


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Service status")
    model: str = Field(..., description="Model name")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    gpu_available: bool = Field(..., description="Whether GPU is available")
    gpu_name: Optional[str] = Field(None, description="GPU device name")
    gpu_memory_used_mb: Optional[int] = Field(None, description="GPU memory usage in MB")


class ExemplarUploadRequest(BaseModel):
    """Request model for uploading an exemplar."""

    zone_type: str = Field(..., description="Zone type this exemplar represents")
    image_base64: str = Field(..., description="Base64 encoded exemplar image")
    name: Optional[str] = Field(None, description="Optional name for this exemplar")


class ExemplarUploadResponse(BaseModel):
    """Response model for exemplar upload."""

    exemplar_id: str = Field(..., description="Unique ID for this exemplar")
    zone_type: str = Field(..., description="Zone type")
    message: str = Field(..., description="Status message")


class ExemplarMetadata(BaseModel):
    """Exemplar metadata model."""

    id: int = Field(..., description="Database ID")
    zone_type: str = Field(..., description="Zone type this exemplar represents")
    filename: str = Field(..., description="Filename in exemplars directory")
    name: Optional[str] = Field(None, description="Human-readable name")
    description: Optional[str] = Field(None, description="Description of this exemplar")
    upload_date: str = Field(..., description="Upload timestamp (ISO format)")
    source_drawing_id: Optional[int] = Field(None, description="Source drawing ID if applicable")
    effectiveness_score: Optional[float] = Field(None, description="Computed effectiveness score")
    times_used: int = Field(0, description="Number of times this exemplar was used")
    avg_confidence_improvement: Optional[float] = Field(
        None, description="Average confidence improvement when using this exemplar"
    )
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    image_width: Optional[int] = Field(None, description="Image width in pixels")
    image_height: Optional[int] = Field(None, description="Image height in pixels")
    is_active: bool = Field(True, description="Whether this exemplar is active")


class ExemplarListResponse(BaseModel):
    """Response model for listing exemplars."""

    exemplars: list[ExemplarMetadata] = Field(default_factory=list)
    total_count: int = Field(..., description="Total number of exemplars")


class ExemplarDetailResponse(BaseModel):
    """Response model for exemplar detail with image."""

    metadata: ExemplarMetadata
    image_base64: str = Field(..., description="Base64 encoded exemplar image")


class ExemplarUpdateRequest(BaseModel):
    """Request model for updating exemplar metadata."""

    name: Optional[str] = Field(None, description="New name for the exemplar")
    description: Optional[str] = Field(None, description="New description")
    is_active: Optional[bool] = Field(None, description="Whether exemplar should be active")


class ExemplarTestRequest(BaseModel):
    """Request model for testing an exemplar."""

    test_image_base64: str = Field(..., description="Base64 encoded test image")
    confidence_threshold: float = Field(0.3, ge=0.0, le=1.0, description="Confidence threshold")


class ExemplarTestResponse(BaseModel):
    """Response model for exemplar testing."""

    zones_with_exemplar: list[ZoneResult] = Field(default_factory=list)
    zones_without_exemplar: list[ZoneResult] = Field(default_factory=list)
    confidence_improvement: Optional[float] = Field(
        None, description="Average confidence improvement"
    )
    processing_time_ms: float = Field(..., description="Processing time")


class ZoneTypeInfo(BaseModel):
    """Information about a zone type."""

    zone_type: str = Field(..., description="Zone type enum value")
    primary_prompt: str = Field(..., description="Primary text prompt")
    typical_location: str = Field(..., description="Typical location on page")
    expected_per_page: str = Field(..., description="Expected count per page")
    exemplar_count: int = Field(0, description="Number of exemplars for this zone type")


class ZoneTypesResponse(BaseModel):
    """Response model for zone types listing."""

    zone_types: list[ZoneTypeInfo] = Field(default_factory=list)


class DrawingUploadRequest(BaseModel):
    """Request model for uploading and storing a drawing."""

    image_base64: str = Field(..., description="Base64 encoded drawing image")
    filename: Optional[str] = Field(None, description="Original filename")
    notes: Optional[str] = Field(None, description="Optional notes about this drawing")
    confidence_threshold: float = Field(0.3, ge=0.0, le=1.0, description="Confidence threshold")


class DrawingUploadResponse(BaseModel):
    """Response model for drawing upload."""

    drawing_id: int = Field(..., description="Database ID of the uploaded drawing")
    filename: str = Field(..., description="Stored filename")
    zones: list[ZoneResult] = Field(default_factory=list, description="Segmentation results")
    page_type: Optional[str] = Field(None, description="Classified page type")
    page_type_confidence: Optional[float] = Field(None, description="Page type confidence")
    processing_time_ms: float = Field(..., description="Processing time")


class DrawingMetadata(BaseModel):
    """Drawing metadata model."""

    id: int = Field(..., description="Database ID")
    filename: str = Field(..., description="Stored filename")
    original_filename: Optional[str] = Field(None, description="Original filename")
    upload_date: str = Field(..., description="Upload timestamp (ISO format)")
    file_size_bytes: Optional[int] = Field(None, description="File size")
    image_width: Optional[int] = Field(None, description="Image width")
    image_height: Optional[int] = Field(None, description="Image height")
    file_format: Optional[str] = Field(None, description="File format (PNG, JPEG, etc)")
    processing_date: Optional[str] = Field(None, description="Processing timestamp")
    processing_time_ms: Optional[int] = Field(None, description="Processing time")
    page_type: Optional[str] = Field(None, description="Page type")
    page_type_confidence: Optional[float] = Field(None, description="Page type confidence")
    confidence_threshold: Optional[float] = Field(None, description="Confidence threshold used")
    used_exemplars: bool = Field(False, description="Whether exemplars were used")
    notes: Optional[str] = Field(None, description="User notes")


class DrawingDetailResponse(BaseModel):
    """Response model for drawing detail."""

    metadata: DrawingMetadata
    zones: Optional[list[ZoneResult]] = Field(None, description="Segmentation zones")
    image_base64: Optional[str] = Field(None, description="Base64 encoded drawing image")


# =============================================================================
# Prompt Configuration Models
# =============================================================================


class ZonePromptConfig(BaseModel):
    """Configuration for a single zone type prompt."""

    zone_type: str = Field(..., description="Zone type identifier (e.g., 'title_block')")
    primary_prompt: str = Field(..., description="Primary text prompt sent to SAM3")
    alternate_prompts: list[str] = Field(
        default_factory=list, description="Alternative prompt variations"
    )
    typical_location: str = Field("any", description="Expected location on page")
    priority: int = Field(5, ge=1, le=10, description="Detection priority (1=highest)")
    enabled: bool = Field(True, description="Whether this zone type is active")


class InferenceSettings(BaseModel):
    """Settings for SAM3 inference."""

    confidence_threshold: float = Field(
        0.3, ge=0.0, le=1.0, description="Minimum confidence threshold for detections"
    )
    return_masks: bool = Field(True, description="Return segmentation masks")


class PromptConfigResponse(BaseModel):
    """Response containing all prompt configurations."""

    prompts: list[ZonePromptConfig] = Field(
        default_factory=list, description="List of zone prompt configurations"
    )
    inference: InferenceSettings = Field(
        default_factory=InferenceSettings, description="Inference settings"
    )
    version: int = Field(1, description="Configuration version number")


class PromptConfigUpdateRequest(BaseModel):
    """Request to update prompt configurations."""

    prompts: list[ZonePromptConfig] = Field(..., description="Updated prompt configurations")
    inference: Optional[InferenceSettings] = Field(
        None, description="Updated inference settings"
    )


# =============================================================================
# Interactive Segmentation (PVS - Promptable Visual Segmentation)
# =============================================================================


class PointPrompt(BaseModel):
    """A single point prompt for interactive segmentation."""

    x: float = Field(..., description="X coordinate in image space")
    y: float = Field(..., description="Y coordinate in image space")
    label: int = Field(
        ...,
        ge=0,
        le=1,
        description="Point label: 1 = positive (include), 0 = negative (exclude)",
    )


class InteractiveSegmentRequest(BaseModel):
    """Request for interactive segmentation using points and/or bounding box.

    This uses SAM3's Promptable Visual Segmentation (PVS) capability for
    instance-specific segmentation at specified locations.

    Supports both single box and multi-box modes:
    - Single box: Use `box` field for one bounding box
    - Multi-box: Use `boxes` field for multiple bounding boxes (masks are merged)
    """

    image_base64: str = Field(..., description="Base64 encoded image")
    points: Optional[list[PointPrompt]] = Field(
        None, description="Point prompts (click locations)"
    )
    box: Optional[tuple[float, float, float, float]] = Field(
        None, description="Single bounding box [x1, y1, x2, y2] in image coordinates"
    )
    boxes: Optional[list[tuple[float, float, float, float]]] = Field(
        None, description="Multiple bounding boxes [[x1, y1, x2, y2], ...] for multi-box segmentation"
    )
    mask_input_base64: Optional[str] = Field(
        None,
        description="Base64 encoded binary mask to refine (from previous segmentation). "
                    "For best refinement quality, use mask_logits_base64 instead.",
    )
    mask_logits_base64: Optional[str] = Field(
        None,
        description="Base64 encoded low-resolution logits (numpy .npy format) for refinement. "
                    "Use low_res_logits_base64 from previous response for optimal quality.",
    )
    multimask_output: bool = Field(
        True, description="Return multiple mask candidates with IOU scores"
    )
    doc_id: Optional[str] = Field(
        None,
        description="Document ID for saving debug logs to document storage directory",
    )


class MaskCandidate(BaseModel):
    """A single mask candidate from interactive segmentation."""

    mask_base64: str = Field(..., description="Base64 encoded binary mask (PNG)")
    iou_score: float = Field(..., description="Predicted IOU score for this mask")
    bbox: tuple[float, float, float, float] = Field(
        ..., description="Bounding box [x1, y1, x2, y2] of the mask"
    )
    low_res_logits_base64: Optional[str] = Field(
        None,
        description="Base64 encoded low-resolution logits (256x256 float32) for refinement. "
                    "Use this instead of mask_base64 for mask_input in subsequent calls."
    )


class InteractiveSegmentResponse(BaseModel):
    """Response from interactive segmentation.

    Returns multiple mask candidates sorted by IOU score (best first).
    In multimask mode, typically returns 3 candidates.
    """

    masks: list[MaskCandidate] = Field(..., description="Mask candidates sorted by IOU score")
    image_size: tuple[int, int] = Field(..., description="[width, height] of input image")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


# =============================================================================
# Find Similar Models
# =============================================================================


class FindSimilarRequest(BaseModel):
    """Request for finding similar regions to an exemplar mask."""

    image_base64: str = Field(..., description="Base64 encoded image")
    exemplar_mask_base64: str = Field(
        ...,
        description="Base64 encoded binary mask (PNG) of the exemplar region",
    )
    exemplar_bbox: Optional[tuple[float, float, float, float]] = Field(
        None,
        description="Bounding box [x1, y1, x2, y2] of exemplar (computed from mask if not provided)",
    )
    max_results: int = Field(
        10,
        ge=1,
        le=50,
        description="Maximum number of similar regions to return",
    )
    # FIX: Lowered default from 0.7 to 0.5 to match function default
    similarity_threshold: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity threshold",
    )
    nms_threshold: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="DEPRECATED: No longer used. Dense similarity replaced grid scanning.",
    )
    grid_stride: int = Field(
        32,
        ge=8,
        le=128,
        description="DEPRECATED: No longer used. Dense similarity replaced grid scanning.",
    )
    doc_id: Optional[str] = Field(
        None,
        description="Document ID for debug logging",
    )


class SimilarRegion(BaseModel):
    """A single similar region found by find-similar."""

    region_id: str = Field(..., description="Unique identifier for this region")
    mask_base64: str = Field(..., description="Base64 encoded binary mask (PNG)")
    bbox: tuple[float, float, float, float] = Field(
        ..., description="Bounding box [x1, y1, x2, y2]"
    )
    similarity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Cosine similarity to exemplar"
    )
    iou_score: Optional[float] = Field(
        None, description="SAM's predicted IoU score for this mask"
    )
    low_res_logits_base64: Optional[str] = Field(
        None,
        description="Base64 encoded low-res logits for refinement",
    )


class FindSimilarResponse(BaseModel):
    """Response from find-similar endpoint."""

    regions: list[SimilarRegion] = Field(
        default_factory=list,
        description="List of similar regions, sorted by similarity (best first)",
    )
    exemplar_bbox: tuple[float, float, float, float] = Field(
        ..., description="Bounding box of the exemplar region"
    )
    image_size: tuple[int, int] = Field(..., description="[width, height] of input image")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    regions_scanned: int = Field(..., description="Number of candidate regions scanned")
    regions_above_threshold: int = Field(
        ..., description="Regions above similarity threshold before NMS"
    )


# =============================================================================
# Document Storage Models (for Playground)
# =============================================================================


class DocumentUploadResponse(BaseModel):
    """Response for document upload."""

    doc_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Stored filename")
    original_filename: Optional[str] = Field(None, description="Original filename")
    total_pages: int = Field(1, description="Number of pages (for PDF)")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    image_width: Optional[int] = Field(None, description="Image width in pixels")
    image_height: Optional[int] = Field(None, description="Image height in pixels")


class DocumentMetadata(BaseModel):
    """Document metadata for listing."""

    doc_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Stored filename")
    original_filename: Optional[str] = Field(None, description="Original filename")
    upload_date: str = Field(..., description="Upload timestamp (ISO format)")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    image_width: Optional[int] = Field(None, description="Image width in pixels")
    image_height: Optional[int] = Field(None, description="Image height in pixels")
    file_format: Optional[str] = Field(None, description="File format (PNG, JPEG)")
    total_pages: int = Field(1, description="Number of pages")


class DocumentListResponse(BaseModel):
    """Response for listing documents."""

    documents: list[DocumentMetadata] = Field(default_factory=list)
    total_count: int = Field(..., description="Total number of documents")


class DocumentDetailResponse(BaseModel):
    """Response for document detail with optional image."""

    metadata: DocumentMetadata
    image_base64: Optional[str] = Field(None, description="Base64 encoded image")
