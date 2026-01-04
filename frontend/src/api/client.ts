/**
 * SAM3 API Client
 */

import axios from 'axios';
import type {
  SegmentRequest,
  SegmentResponse,
  HealthResponse,
  SAM3Document,
  UploadDocumentResponse,
  SegmentDocumentResponse,
  SegmentDocumentRequest,
  PromptConfigResponse,
  PromptConfigUpdateRequest,
  InteractiveSegmentResponse,
  PointPromptLabel,
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
   */
  async segmentInteractive(
    imageBase64: string,
    options: {
      points?: Array<{ x: number; y: number; label: PointPromptLabel }>;
      box?: [number, number, number, number];
      maskInput?: string; // Base64 encoded mask for refinement
    }
  ): Promise<InteractiveSegmentResponse> {
    const base64Data = imageBase64.replace(/^data:image\/\w+;base64,/, '');

    const { data } = await apiClient.post<InteractiveSegmentResponse>('/segment/interactive', {
      image_base64: base64Data,
      points: options.points?.map((p) => ({ x: p.x, y: p.y, label: p.label })),
      box: options.box,
      mask_input_base64: options.maskInput,
      multimask_output: true,
    });
    return data;
  },

  // ============================================================================
  // Document Management (MOCK - Backend endpoints not implemented yet)
  // ============================================================================

  /**
   * Upload a document (PDF or image)
   * TODO: Backend needs to implement POST /documents/upload
   * Mock: Stores file as base64 in localStorage, generates mock docId
   */
  async uploadDocument(file: File): Promise<UploadDocumentResponse> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onloadend = () => {
        const docId = `doc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const base64 = reader.result as string;

        // Store in localStorage temporarily
        localStorage.setItem(`sam3_doc_${docId}`, base64);
        localStorage.setItem(`sam3_doc_${docId}_name`, file.name);

        // For now, treat single image as 1-page document
        // TODO: Backend should extract pages from PDF
        resolve({
          docId,
          totalPages: 1,
        });
      };

      reader.onerror = () => {
        reject(new Error('Failed to read file'));
      };

      reader.readAsDataURL(file);
    });
  },

  /**
   * List all documents
   * TODO: Backend needs to implement GET /documents
   * Mock: Returns empty array (documents managed in Zustand store)
   */
  async listDocuments(): Promise<SAM3Document[]> {
    // Documents are managed client-side in Zustand store for now
    return [];
  },

  /**
   * Get a specific document
   * TODO: Backend needs to implement GET /documents/{docId}
   * Mock: Returns from Zustand store
   */
  async getDocument(docId: string): Promise<SAM3Document> {
    throw new Error(`Document ${docId} not found - backend not implemented`);
  },

  /**
   * Delete a document
   * TODO: Backend needs to implement DELETE /documents/{docId}
   * Mock: Removes from localStorage
   */
  async deleteDocument(docId: string): Promise<void> {
    localStorage.removeItem(`sam3_doc_${docId}`);
    localStorage.removeItem(`sam3_doc_${docId}_name`);
  },

  /**
   * Segment all pages of a document
   * TODO: Backend needs to implement POST /documents/{docId}/segment
   * Mock: Uses existing /segment/structural endpoint for single image
   */
  async segmentDocument(
    docId: string,
    _options?: SegmentDocumentRequest
  ): Promise<SegmentDocumentResponse> {
    const base64 = localStorage.getItem(`sam3_doc_${docId}`);
    if (!base64) {
      throw new Error(`Document ${docId} not found`);
    }

    // Extract base64 data (remove data:image/...;base64, prefix)
    const imageBase64 = base64.split(',')[1];

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
          pageType: null, // Page classification removed
          processingTimeMs: result.processing_time_ms,
        },
      ],
    };
  },

  /**
   * Get URL for a page image
   * TODO: Backend needs to implement GET /documents/{docId}/pages/{pageNumber}/image
   * Mock: Returns data URL from localStorage
   */
  getPageImageUrl(docId: string, _pageNumber: number): string {
    const base64 = localStorage.getItem(`sam3_doc_${docId}`);
    return base64 || '';
  },
};

export default apiClient;
