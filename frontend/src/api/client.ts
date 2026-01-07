/**
 * SAM3 API Client
 */

import axios from 'axios';
import type {
  SegmentRequest,
  SegmentResponse,
  HealthResponse,
  UploadDocumentResponse,
  SegmentDocumentResponse,
  SegmentDocumentRequest,
  PromptConfigResponse,
  PromptConfigUpdateRequest,
  InteractiveSegmentResponse,
  PointPromptLabel,
  DocumentMetadata,
  DocumentListResponse,
  DocumentDetailResponse,
  FindSimilarResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 second timeout for segmentation
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  async getHealth(): Promise<HealthResponse> {
    const { data } = await apiClient.get<HealthResponse>('/health');
    return data;
  },

  async segmentStructural(request: SegmentRequest): Promise<SegmentResponse> {
    const { data } = await apiClient.post<SegmentResponse>('/segment/structural', request);
    return data;
  },

  /**
   * Segment with custom prompts (for Playground)
   */
  async segmentWithPrompts(
    imageBase64: string,
    prompts: string[],
    confidenceThreshold: number = 0.3
  ): Promise<SegmentResponse> {
    // Strip data URL prefix if present
    const base64Data = imageBase64.replace(/^data:image\/\w+;base64,/, '');

    const { data } = await apiClient.post<SegmentResponse>('/segment', {
      image_base64: base64Data,
      prompts,
      confidence_threshold: confidenceThreshold,
      return_masks: true,
      return_crops: false,
    });
    return data;
  },

  // ============================================================================
  // Prompt Configuration
  // ============================================================================

  /**
   * Get current prompt configuration
   */
  async getPromptConfig(): Promise<PromptConfigResponse> {
    const { data } = await apiClient.get<PromptConfigResponse>('/config/prompts');
    return data;
  },

  /**
   * Update prompt configuration
   */
  async updatePromptConfig(request: PromptConfigUpdateRequest): Promise<PromptConfigResponse> {
    const { data } = await apiClient.put<PromptConfigResponse>('/config/prompts', request);
    return data;
  },

  /**
   * Reset prompt configuration to defaults
   */
  async resetPromptConfig(): Promise<PromptConfigResponse> {
    const { data } = await apiClient.post<PromptConfigResponse>('/config/prompts/reset');
    return data;
  },

  // ============================================================================
  // Interactive Segmentation (Playground)
  // ============================================================================

  /**
   * Segment with point prompts (for Playground)
   */
  async segmentWithPoints(
    imageBase64: string,
    points: Array<{ x: number; y: number; label: PointPromptLabel }>
  ): Promise<InteractiveSegmentResponse> {
    const base64Data = imageBase64.replace(/^data:image\/\w+;base64,/, '');

    const { data } = await apiClient.post<InteractiveSegmentResponse>('/segment/interactive', {
      image_base64: base64Data,
      points: points.map((p) => ({ x: p.x, y: p.y, label: p.label })),
      multimask_output: true,
    });
    return data;
  },

  /**
   * Segment with bounding box prompt (for Playground)
   */
  async segmentWithBox(
    imageBase64: string,
    box: [number, number, number, number] // [x1, y1, x2, y2]
  ): Promise<InteractiveSegmentResponse> {
    const base64Data = imageBase64.replace(/^data:image\/\w+;base64,/, '');

    const { data } = await apiClient.post<InteractiveSegmentResponse>('/segment/interactive', {
      image_base64: base64Data,
      box,
      multimask_output: true,
    });
    return data;
  },

  /**
   * Combined interactive segmentation with points, box, and/or mask input (for Playground)
   * Supports both single box and multi-box modes.
   */
  async segmentInteractive(
    imageBase64: string,
    options: {
      points?: Array<{ x: number; y: number; label: PointPromptLabel }>;
      box?: [number, number, number, number]; // Single box (backwards compatible)
      boxes?: Array<[number, number, number, number]>; // Multi-box (merged into single mask)
      maskInput?: string; // Base64 encoded binarized mask (legacy mode)
      maskLogits?: string; // Base64 encoded low-res logits (preferred for refinement)
      docId?: string; // Document ID for debug logging
    }
  ): Promise<InteractiveSegmentResponse> {
    const base64Data = imageBase64.replace(/^data:image\/\w+;base64,/, '');

    const { data } = await apiClient.post<InteractiveSegmentResponse>('/segment/interactive', {
      image_base64: base64Data,
      points: options.points?.map((p) => ({ x: p.x, y: p.y, label: p.label })),
      box: options.box,
      boxes: options.boxes,
      // Prefer logits over binarized mask for higher quality refinement
      mask_logits_base64: options.maskLogits,
      mask_input_base64: options.maskLogits ? undefined : options.maskInput,
      multimask_output: true,
      // Send doc_id for debug logging (optional)
      doc_id: options.docId,
    });
    return data;
  },

  /**
   * Find and segment regions similar to an exemplar mask.
   * Returns separate masks for each similar region.
   */
  async segmentFindSimilar(
    imageBase64: string,
    exemplarMaskBase64: string,
    options?: {
      exemplarBbox?: [number, number, number, number];
      maxResults?: number;
      similarityThreshold?: number;
      docId?: string;
    }
  ): Promise<FindSimilarResponse> {
    const base64Data = imageBase64.replace(/^data:image\/\w+;base64,/, '');
    const maskData = exemplarMaskBase64.replace(/^data:image\/\w+;base64,/, '');

    const { data } = await apiClient.post<FindSimilarResponse>(
      '/segment/find-similar',
      {
        image_base64: base64Data,
        exemplar_mask_base64: maskData,
        exemplar_bbox: options?.exemplarBbox,
        max_results: options?.maxResults ?? 10,
        // FIX: Lowered from 0.7 to 0.5 to match find_similar_dense() default.
        // Raw cosine similarity for similar regions is often 0.60-0.75 before
        // region-averaging, which drops it further. 0.7 was too aggressive.
        similarity_threshold: options?.similarityThreshold ?? 0.5,
        doc_id: options?.docId,
      }
    );
    return data;
  },

  // ============================================================================
  // Document Management (File-based backend storage)
  // ============================================================================

  /**
   * Upload a document (image file) to backend storage.
   * The file is stored in the server's storage directory.
   */
  async uploadDocument(file: File): Promise<UploadDocumentResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await apiClient.post<{
      doc_id: string;
      filename: string;
      original_filename: string | null;
      total_pages: number;
      file_size_bytes: number | null;
      image_width: number | null;
      image_height: number | null;
    }>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000, // 2 minute timeout for large files
    });

    // Map backend response to frontend interface
    return {
      docId: data.doc_id,
      totalPages: data.total_pages,
      doc_id: data.doc_id,
      filename: data.filename,
      original_filename: data.original_filename,
      file_size_bytes: data.file_size_bytes,
      image_width: data.image_width,
      image_height: data.image_height,
    };
  },

  /**
   * List all documents from backend storage.
   */
  async listDocuments(): Promise<DocumentMetadata[]> {
    const { data } = await apiClient.get<DocumentListResponse>('/documents');
    return data.documents;
  },

  /**
   * Get a specific document's metadata and optionally its image.
   */
  async getDocument(docId: string, includeImage = false): Promise<DocumentDetailResponse> {
    const { data } = await apiClient.get<DocumentDetailResponse>(
      `/documents/${docId}`,
      { params: { include_image: includeImage } }
    );
    return data;
  },

  /**
   * Delete a document from backend storage.
   */
  async deleteDocument(docId: string): Promise<void> {
    await apiClient.delete(`/documents/${docId}`);
  },

  /**
   * Get document image as base64.
   */
  async getDocumentImage(docId: string): Promise<string> {
    const { data } = await apiClient.get<{ image_base64: string }>(
      `/documents/${docId}/image`
    );
    return data.image_base64;
  },

  /**
   * Segment all pages of a document.
   * Fetches image from backend, then segments using structural endpoint.
   */
  async segmentDocument(
    docId: string,
    _options?: SegmentDocumentRequest
  ): Promise<SegmentDocumentResponse> {
    // Fetch image from backend storage
    const imageBase64 = await api.getDocumentImage(docId);

    // Segment using existing endpoint - masks enabled for visualization
    const result = await api.segmentStructural({
      image_base64: imageBase64,
      return_masks: true,
      return_crops: false,
    });

    return {
      documentId: docId,
      totalPages: 1,
      pages: [
        {
          pageNumber: 0,
          zones: result.zones,
          pageType: null,
          processingTimeMs: result.processing_time_ms,
        },
      ],
    };
  },

  /**
   * Get image URL/data for a page.
   * Now fetches from backend storage.
   */
  async getPageImageUrl(docId: string, _pageNumber: number): Promise<string> {
    const imageBase64 = await api.getDocumentImage(docId);
    // Return as data URL for compatibility with existing code
    return `data:image/png;base64,${imageBase64}`;
  },

  // ============================================================================
  // Viewer Zone Storage
  // ============================================================================

  /**
   * Save viewer zones (auto-run segmentation results) for a document.
   */
  async saveViewerZones(
    docId: string,
    zonesData: { zones: unknown[]; processing_time_ms?: number }
  ): Promise<{ message: string; doc_id: string }> {
    const { data } = await apiClient.post(`/documents/${docId}/viewer/zones`, zonesData);
    return data;
  },

  /**
   * Get viewer zones for a document.
   */
  async getViewerZones(docId: string): Promise<{
    zones: unknown[] | null;
    saved_at: string | null;
    processing_time_ms?: number;
  }> {
    const { data } = await apiClient.get(`/documents/${docId}/viewer/zones`);
    return data;
  },

  // ============================================================================
  // Playground Session Storage
  // ============================================================================

  /**
   * Save a playground session snapshot.
   */
  async savePlaygroundSession(
    docId: string,
    sessionId: string,
    sessionData: Record<string, unknown>
  ): Promise<{ message: string; doc_id: string; session_id: string }> {
    const { data } = await apiClient.post(
      `/documents/${docId}/playground/sessions/${sessionId}`,
      sessionData
    );
    return data;
  },

  /**
   * List all playground sessions for a document.
   */
  async listPlaygroundSessions(docId: string): Promise<{
    sessions: Array<{ session_id: string; saved_at: string | null }>;
    count: number;
  }> {
    const { data } = await apiClient.get(`/documents/${docId}/playground/sessions`);
    return data;
  },

  /**
   * Get a specific playground session.
   */
  async getPlaygroundSession(
    docId: string,
    sessionId: string
  ): Promise<Record<string, unknown>> {
    const { data } = await apiClient.get(
      `/documents/${docId}/playground/sessions/${sessionId}`
    );
    return data;
  },

  // ============================================================================
  // Storage Migration (Admin)
  // ============================================================================

  /**
   * Migrate from flat storage to folder-based structure.
   */
  async migrateStorage(): Promise<{ message: string; migrated_documents: number }> {
    const { data } = await apiClient.post('/admin/migrate-storage');
    return data;
  },
};

export default apiClient;
