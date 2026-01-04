/**
 * Canvas Coordinate Utilities
 *
 * Handles coordinate transformation between screen/canvas and image coordinate systems.
 * Used by both Viewer and Playground for consistent coordinate handling.
 */

interface Point {
  x: number;
  y: number;
}

interface ContainerRect {
  left: number;
  top: number;
  width: number;
  height: number;
}

interface Pan {
  x: number;
  y: number;
}

interface ImageDimensions {
  width: number;
  height: number;
}

/**
 * Convert screen coordinates (from mouse event) to image coordinates.
 *
 * @param clientX - Mouse clientX from event
 * @param clientY - Mouse clientY from event
 * @param containerRect - Container element's bounding rect
 * @param pan - Current pan offset
 * @param zoom - Current zoom level
 * @param imageDimensions - Original image dimensions
 * @returns Image coordinates in pixels
 */
export function screenToImageCoords(
  clientX: number,
  clientY: number,
  containerRect: ContainerRect,
  pan: Pan,
  zoom: number,
  imageDimensions: ImageDimensions
): Point {
  // Position relative to container center
  const mouseRelativeToContainer = {
    x: clientX - containerRect.left - containerRect.width / 2,
    y: clientY - containerRect.top - containerRect.height / 2,
  };

  // Transform to image coordinates accounting for pan and zoom
  return {
    x: (mouseRelativeToContainer.x - pan.x) / zoom + imageDimensions.width / 2,
    y: (mouseRelativeToContainer.y - pan.y) / zoom + imageDimensions.height / 2,
  };
}

/**
 * Convert image coordinates to screen coordinates.
 *
 * @param imageX - X coordinate in image pixels
 * @param imageY - Y coordinate in image pixels
 * @param containerRect - Container element's bounding rect
 * @param pan - Current pan offset
 * @param zoom - Current zoom level
 * @param imageDimensions - Original image dimensions
 * @returns Screen coordinates (relative to viewport)
 */
export function imageToScreenCoords(
  imageX: number,
  imageY: number,
  containerRect: ContainerRect,
  pan: Pan,
  zoom: number,
  imageDimensions: ImageDimensions
): Point {
  // Image coords relative to image center
  const relativeToImageCenter = {
    x: imageX - imageDimensions.width / 2,
    y: imageY - imageDimensions.height / 2,
  };

  // Apply zoom and pan
  const screenRelativeToContainer = {
    x: relativeToImageCenter.x * zoom + pan.x,
    y: relativeToImageCenter.y * zoom + pan.y,
  };

  // Add container center offset
  return {
    x: screenRelativeToContainer.x + containerRect.width / 2 + containerRect.left,
    y: screenRelativeToContainer.y + containerRect.height / 2 + containerRect.top,
  };
}

/**
 * Generate a unique ID for prompts.
 */
export function generatePromptId(prefix: string = 'prompt'): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}
