/**
 * SAM3 Drawing Zone Segmenter - Type Definitions
 */

export type ZoneType =
  | 'title_block'
  | 'revision_block'
  | 'plan_view'
  | 'elevation_view'
  | 'section_view'
  | 'detail_view'
  | 'schedule_table'
  | 'notes_area'
  | 'legend'
  | 'grid_system'
  | 'unknown';

export interface ZoneResult {
  zone_id: string;
  zone_type: ZoneType;
  prompt_matched: string;
  confidence: number;
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
  bbox_normalized: [number, number, number, number];
  area_ratio: number;
  mask_base64?: string | null;
  crop_base64?: string | null;
}

export interface SegmentResponse {
  zones: ZoneResult[];
  image_size: [number, number];
  processing_time_ms: number;
  model_version: string;
}

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  gpu_available: boolean;
  gpu_name: string | null;
  gpu_memory_used_mb: number | null;
}

export interface SegmentRequest {
  image_base64: string;
  return_masks?: boolean;
  return_crops?: boolean;
}

// ============================================================================
// Multi-Page Document Support
// ============================================================================

export type DocumentStatus = 'pending' | 'segmented' | 'error';

export interface PageData {
  pageNumber: number;
  imageUrl: string;
  zones: ZoneResult[];
  pageType: string | null;
  processingTimeMs: number;
}

export interface SAM3Document {
  id: string;
  name: string;
  uploadedAt: string;
  totalPages: number;
  size?: number;
  status: DocumentStatus;
  pages: PageData[];
  error?: string;
  configVersionUsed?: number; // Track which config version was used for segmentation
}

// Document API Types
export interface UploadDocumentResponse {
  docId: string;
  totalPages: number;
  // Extended fields from backend
  doc_id?: string; // Backend uses snake_case
  filename?: string;
  original_filename?: string | null;
  file_size_bytes?: number | null;
  image_width?: number | null;
  image_height?: number | null;
}

export interface DocumentMetadata {
  doc_id: string;
  filename: string;
  original_filename: string | null;
  upload_date: string;
  file_size_bytes: number | null;
  image_width: number | null;
  image_height: number | null;
  file_format: string | null;
  total_pages: number;
}

export interface DocumentListResponse {
  documents: DocumentMetadata[];
  total_count: number;
}

export interface DocumentDetailResponse {
  metadata: DocumentMetadata;
  image_base64: string | null;
}

export interface SegmentDocumentRequest {
  confidenceThreshold?: number;
}

export interface SegmentDocumentResponse {
  documentId: string;
  totalPages: number;
  pages: {
    pageNumber: number;
    zones: ZoneResult[];
    pageType: string | null;
    processingTimeMs: number;
  }[];
}

// ============================================================================
// Prompt Configuration Types
// ============================================================================

export interface ZonePromptConfig {
  zone_type: string;
  primary_prompt: string;
  alternate_prompts: string[];
  typical_location: string;
  priority: number;
  enabled: boolean;
}

export interface InferenceSettings {
  confidence_threshold: number;
  return_masks: boolean;
}

export interface PromptConfigResponse {
  prompts: ZonePromptConfig[];
  inference: InferenceSettings;
  version: number;
}

export interface PromptConfigUpdateRequest {
  prompts: ZonePromptConfig[];
  inference?: InferenceSettings;
}

// ============================================================================
// Interactive Prompt Types (Playground)
// ============================================================================

/**
 * Point prompt label: 1 = positive (include), 0 = negative (exclude)
 * This matches SAM3's convention.
 */
export type PointPromptLabel = 0 | 1;

/**
 * A single point prompt with coordinates and label.
 */
export interface PointPrompt {
  id: string;
  x: number; // Image coordinate X (pixels)
  y: number; // Image coordinate Y (pixels)
  label: PointPromptLabel;
}

export type PointPromptMode = 'positive' | 'negative';

/**
 * A bounding box prompt.
 */
export interface BoxPrompt {
  id: string;
  x1: number; // Top-left X
  y1: number; // Top-left Y
  x2: number; // Bottom-right X
  y2: number; // Bottom-right Y
}

export type BoxPromptMode = 'single' | 'multi';

/**
 * State for box drawing in progress.
 */
export interface BoxDragState {
  startX: number;
  startY: number;
  currentX: number;
  currentY: number;
}

/**
 * Single mask candidate returned by SAM3 interactive segmentation.
 */
export interface MaskCandidate {
  mask_base64: string;
  iou_score: number;
  bbox: [number, number, number, number];
  /** Low-resolution logits (256x256) for refinement - use this instead of mask_base64 for better quality */
  low_res_logits_base64?: string | null;
}

/**
 * Request for interactive segmentation (points/boxes).
 */
export interface InteractiveSegmentRequest {
  image_base64: string;
  points?: Array<{ x: number; y: number; label: PointPromptLabel }>;
  box?: [number, number, number, number]; // [x1, y1, x2, y2]
  multimask_output?: boolean;
}

/**
 * Response from interactive segmentation.
 */
export interface InteractiveSegmentResponse {
  masks: MaskCandidate[];
  image_size: [number, number];
  processing_time_ms: number;
}

// ============================================================================
// Smart Select Types (Roboflow-style features)
// ============================================================================

/**
 * Output mode for Smart Select - pixels (mask) or polygon
 */
export type SmartSelectOutputMode = 'pixels' | 'polygon';

/**
 * State of the Smart Select refinement workflow
 */
export type SmartSelectState =
  | 'idle'        // No selection yet
  | 'initial'     // First mask generated
  | 'refining'    // Iteratively refining with clicks
  | 'confirmed';  // User confirmed selection (Enter)

/**
 * A polygon extracted from a mask
 */
export interface PolygonData {
  /** Simplified polygon vertices */
  points: Array<{ x: number; y: number }>;
  /** Area in pixels */
  area: number;
  /** Perimeter in pixels */
  perimeter: number;
}

/**
 * History entry for undo/redo
 */
export interface SmartSelectHistoryEntry {
  mask: MaskCandidate;
  points: PointPrompt[];
  box: BoxPrompt | null;
  polygon: PolygonData | null;
  timestamp: number;
}

/**
 * Full Smart Select state for a session
 */
export interface SmartSelectSession {
  state: SmartSelectState;
  outputMode: SmartSelectOutputMode;
  currentMask: MaskCandidate | null;
  currentPolygon: PolygonData | null;
  polygonComplexity: number; // 0-1, affects simplification
  history: SmartSelectHistoryEntry[];
  historyIndex: number; // -1 = no history, 0+ = current position
  points: PointPrompt[];
  box: BoxPrompt | null;
}
