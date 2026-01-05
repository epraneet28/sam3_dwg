/**
 * Canvas Coordinate Utilities
 *
 * Handles coordinate transformation between screen/canvas and image coordinate systems.
 * Used by both Viewer and Playground for consistent coordinate handling.
 *
 * Accounts for:
 * - Pan offset (CSS translate)
 * - Zoom level (CSS scale)
 * - CSS downscaling from maxWidth/maxHeight constraints on large images
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
 * Calculate the CSS scale factor when maxWidth/maxHeight constraints
 * cause the canvas to be rendered smaller than its intrinsic dimensions.
 *
 * @param containerRect - Container element's bounding rect
 * @param imageDimensions - Original image dimensions
 * @returns CSS scale factor (1.0 if no downscaling, <1.0 if image is larger than container)
 */
export function calculateCssScale(
  containerRect: ContainerRect,
  imageDimensions: ImageDimensions
): number {
  // With maxWidth: 100% and maxHeight: 100%, the browser scales to fit
  // while maintaining aspect ratio
  const scaleX = containerRect.width / imageDimensions.width;
  const scaleY = containerRect.height / imageDimensions.height;
  // CSS never upscales beyond 1.0 with max-width/max-height
  return Math.min(scaleX, scaleY, 1.0);
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
 * @param cssScale - Optional CSS scale factor for large images (default: auto-calculated)
 * @returns Image coordinates in pixels
 */
export function screenToImageCoords(
  clientX: number,
  clientY: number,
  containerRect: ContainerRect,
  pan: Pan,
  zoom: number,
  imageDimensions: ImageDimensions,
  cssScale?: number
): Point {
  // Calculate CSS scale if not provided
  const effectiveCssScale = cssScale ?? calculateCssScale(containerRect, imageDimensions);

  // Total scale combines CSS downscaling and user zoom
  const totalScale = effectiveCssScale * zoom;

  // Position relative to container center
  const mouseRelativeToContainer = {
    x: clientX - containerRect.left - containerRect.width / 2,
    y: clientY - containerRect.top - containerRect.height / 2,
  };

  // Transform to image coordinates accounting for pan and total scale
  return {
    x: (mouseRelativeToContainer.x - pan.x) / totalScale + imageDimensions.width / 2,
    y: (mouseRelativeToContainer.y - pan.y) / totalScale + imageDimensions.height / 2,
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
 * @param cssScale - Optional CSS scale factor for large images (default: auto-calculated)
 * @returns Screen coordinates (relative to viewport)
 */
export function imageToScreenCoords(
  imageX: number,
  imageY: number,
  containerRect: ContainerRect,
  pan: Pan,
  zoom: number,
  imageDimensions: ImageDimensions,
  cssScale?: number
): Point {
  // Calculate CSS scale if not provided
  const effectiveCssScale = cssScale ?? calculateCssScale(containerRect, imageDimensions);

  // Total scale combines CSS downscaling and user zoom
  const totalScale = effectiveCssScale * zoom;

  // Image coords relative to image center
  const relativeToImageCenter = {
    x: imageX - imageDimensions.width / 2,
    y: imageY - imageDimensions.height / 2,
  };

  // Apply total scale and pan
  const screenRelativeToContainer = {
    x: relativeToImageCenter.x * totalScale + pan.x,
    y: relativeToImageCenter.y * totalScale + pan.y,
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
