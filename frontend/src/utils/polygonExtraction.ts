/**
 * Polygon Extraction Utilities
 *
 * Extracts polygon contours from binary masks using:
 * 1. Marching Squares algorithm for contour extraction
 * 2. Douglas-Peucker algorithm for polygon simplification
 */

export interface Point {
  x: number;
  y: number;
}

export interface PolygonResult {
  /** Simplified polygon vertices */
  points: Point[];
  /** Original contour before simplification */
  rawPoints: Point[];
  /** Area of the polygon in pixels */
  area: number;
  /** Perimeter of the polygon in pixels */
  perimeter: number;
}

/**
 * Extract polygon contours from a base64-encoded mask image.
 *
 * @param maskBase64 - Base64 encoded PNG mask (white = mask area)
 * @param complexity - Simplification level 0-1 (0 = most simplified, 1 = raw contour)
 * @returns Promise resolving to array of polygons (outer contour + holes)
 */
export async function extractPolygonsFromMask(
  maskBase64: string,
  complexity: number = 0.5
): Promise<PolygonResult[]> {
  // Decode mask to ImageData
  const imageData = await decodeBase64ToImageData(maskBase64);

  // Extract binary mask (threshold at 128)
  const binaryMask = extractBinaryMask(imageData);

  // Find contours using marching squares
  const contours = findContours(binaryMask, imageData.width, imageData.height);

  // Simplify each contour based on complexity
  const tolerance = calculateTolerance(imageData.width, imageData.height, complexity);

  return contours.map(contour => {
    const simplified = douglasPeucker(contour, tolerance);
    return {
      points: simplified,
      rawPoints: contour,
      area: calculatePolygonArea(simplified),
      perimeter: calculatePolygonPerimeter(simplified),
    };
  });
}

/**
 * Decode base64 image to ImageData
 */
async function decodeBase64ToImageData(base64: string): Promise<ImageData> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        reject(new Error('Failed to get canvas context'));
        return;
      }
      ctx.drawImage(img, 0, 0);
      resolve(ctx.getImageData(0, 0, img.width, img.height));
    };
    img.onerror = () => reject(new Error('Failed to decode mask image'));

    // Handle both with and without data URL prefix
    img.src = base64.startsWith('data:')
      ? base64
      : `data:image/png;base64,${base64}`;
  });
}

/**
 * Extract binary mask from ImageData (white pixels = 1, else = 0)
 */
function extractBinaryMask(imageData: ImageData): Uint8Array {
  const { data, width, height } = imageData;
  const mask = new Uint8Array(width * height);

  for (let i = 0; i < width * height; i++) {
    // Use red channel, threshold at 128
    mask[i] = data[i * 4] > 128 ? 1 : 0;
  }

  return mask;
}

/**
 * Find contours using a simplified marching squares approach.
 * Returns the outer boundary of connected white regions.
 */
function findContours(
  mask: Uint8Array,
  width: number,
  height: number
): Point[][] {
  const visited = new Set<string>();
  const contours: Point[][] = [];

  // Find starting points (transitions from 0 to 1)
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = y * width + x;
      const key = `${x},${y}`;

      // Look for edge pixels (mask pixel with non-mask neighbor)
      if (mask[idx] === 1 && !visited.has(key)) {
        const isEdge = isEdgePixel(mask, x, y, width, height);
        if (isEdge) {
          const contour = traceContour(mask, x, y, width, height, visited);
          if (contour.length >= 3) {
            contours.push(contour);
          }
        }
      }
    }
  }

  return contours;
}

/**
 * Check if a pixel is on the edge of the mask
 */
function isEdgePixel(
  mask: Uint8Array,
  x: number,
  y: number,
  width: number,
  height: number
): boolean {
  // Check 4-connected neighbors
  const neighbors = [
    [x - 1, y], [x + 1, y], [x, y - 1], [x, y + 1]
  ];

  for (const [nx, ny] of neighbors) {
    if (nx < 0 || nx >= width || ny < 0 || ny >= height) {
      return true; // Border pixel
    }
    if (mask[ny * width + nx] === 0) {
      return true; // Adjacent to background
    }
  }

  return false;
}

/**
 * Trace contour starting from an edge pixel using Moore neighborhood tracing
 */
function traceContour(
  mask: Uint8Array,
  startX: number,
  startY: number,
  width: number,
  height: number,
  globalVisited: Set<string>
): Point[] {
  const contour: Point[] = [];
  const localVisited = new Set<string>();

  // Moore neighborhood: 8 directions clockwise from left
  const directions = [
    [-1, 0], [-1, -1], [0, -1], [1, -1],
    [1, 0], [1, 1], [0, 1], [-1, 1]
  ];

  let x = startX;
  let y = startY;
  let dir = 0; // Start looking left

  const maxIterations = width * height * 2;
  let iterations = 0;

  do {
    const key = `${x},${y}`;
    if (!localVisited.has(key)) {
      contour.push({ x, y });
      localVisited.add(key);
      globalVisited.add(key);
    }

    // Find next edge pixel
    let found = false;
    for (let i = 0; i < 8; i++) {
      const checkDir = (dir + i) % 8;
      const [dx, dy] = directions[checkDir];
      const nx = x + dx;
      const ny = y + dy;

      if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
        if (mask[ny * width + nx] === 1 && isEdgePixel(mask, nx, ny, width, height)) {
          x = nx;
          y = ny;
          // Backtrack direction for next search
          dir = (checkDir + 5) % 8;
          found = true;
          break;
        }
      }
    }

    if (!found) break;
    iterations++;

  } while ((x !== startX || y !== startY) && iterations < maxIterations);

  return contour;
}

/**
 * Douglas-Peucker algorithm for polygon simplification.
 *
 * @param points - Original polygon points
 * @param tolerance - Maximum distance tolerance for simplification
 * @returns Simplified polygon points
 */
export function douglasPeucker(points: Point[], tolerance: number): Point[] {
  if (points.length <= 2) return points;

  // Find the point with the maximum distance from the line
  let maxDist = 0;
  let maxIndex = 0;

  const start = points[0];
  const end = points[points.length - 1];

  for (let i = 1; i < points.length - 1; i++) {
    const dist = perpendicularDistance(points[i], start, end);
    if (dist > maxDist) {
      maxDist = dist;
      maxIndex = i;
    }
  }

  // If max distance is greater than tolerance, recursively simplify
  if (maxDist > tolerance) {
    const left = douglasPeucker(points.slice(0, maxIndex + 1), tolerance);
    const right = douglasPeucker(points.slice(maxIndex), tolerance);

    // Combine results (avoiding duplicate point at maxIndex)
    return [...left.slice(0, -1), ...right];
  }

  // All points are within tolerance, keep only endpoints
  return [start, end];
}

/**
 * Calculate perpendicular distance from a point to a line segment
 */
function perpendicularDistance(point: Point, lineStart: Point, lineEnd: Point): number {
  const dx = lineEnd.x - lineStart.x;
  const dy = lineEnd.y - lineStart.y;

  if (dx === 0 && dy === 0) {
    // Line segment is a point
    return Math.sqrt(
      Math.pow(point.x - lineStart.x, 2) +
      Math.pow(point.y - lineStart.y, 2)
    );
  }

  const t = Math.max(0, Math.min(1, (
    (point.x - lineStart.x) * dx +
    (point.y - lineStart.y) * dy
  ) / (dx * dx + dy * dy)));

  const projX = lineStart.x + t * dx;
  const projY = lineStart.y + t * dy;

  return Math.sqrt(
    Math.pow(point.x - projX, 2) +
    Math.pow(point.y - projY, 2)
  );
}

/**
 * Calculate tolerance based on image size and complexity setting
 */
function calculateTolerance(
  width: number,
  height: number,
  complexity: number
): number {
  // Base tolerance as percentage of image diagonal
  const diagonal = Math.sqrt(width * width + height * height);

  // complexity 1 = NO simplification (tolerance = 0)
  // complexity 0 = maximum simplification (high tolerance)
  const minTolerance = 0; // pixels - changed from 1 to preserve 1-2px details at complexity 1.0
  const maxTolerance = diagonal * 0.005; // 0.5% of diagonal (changed from 2%)
  // NOTE: minTolerance changed to 0 so complexity 1.0 preserves ALL vertices.
  // For a 2000x1500 image: maxTolerance=12.5px, at complexity 1.0 tolerance=0px

  return minTolerance + (1 - complexity) * (maxTolerance - minTolerance);
}

/**
 * Calculate polygon area using Shoelace formula
 */
export function calculatePolygonArea(points: Point[]): number {
  if (points.length < 3) return 0;

  let area = 0;
  const n = points.length;

  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    area += points[i].x * points[j].y;
    area -= points[j].x * points[i].y;
  }

  return Math.abs(area / 2);
}

/**
 * Calculate polygon perimeter
 */
export function calculatePolygonPerimeter(points: Point[]): number {
  if (points.length < 2) return 0;

  let perimeter = 0;
  const n = points.length;

  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    perimeter += Math.sqrt(
      Math.pow(points[j].x - points[i].x, 2) +
      Math.pow(points[j].y - points[i].y, 2)
    );
  }

  return perimeter;
}

/**
 * Convert polygon points to SVG path data string
 */
export function polygonToSvgPath(points: Point[]): string {
  if (points.length === 0) return '';

  const pathParts = points.map((p, i) =>
    `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`
  );

  return pathParts.join(' ') + ' Z';
}

/**
 * Check if a point is inside a polygon using ray casting
 */
export function isPointInPolygon(point: Point, polygon: Point[]): boolean {
  if (polygon.length < 3) return false;

  let inside = false;
  const n = polygon.length;

  for (let i = 0, j = n - 1; i < n; j = i++) {
    const xi = polygon[i].x, yi = polygon[i].y;
    const xj = polygon[j].x, yj = polygon[j].y;

    if (((yi > point.y) !== (yj > point.y)) &&
        (point.x < (xj - xi) * (point.y - yi) / (yj - yi) + xi)) {
      inside = !inside;
    }
  }

  return inside;
}

/**
 * Check if a point is inside a binary mask
 */
export async function isPointInMask(
  point: Point,
  maskBase64: string
): Promise<boolean> {
  const imageData = await decodeBase64ToImageData(maskBase64);
  const { data, width, height } = imageData;

  const x = Math.floor(point.x);
  const y = Math.floor(point.y);

  if (x < 0 || x >= width || y < 0 || y >= height) {
    return false;
  }

  const idx = (y * width + x) * 4;
  return data[idx] > 128; // Red channel > 128 = inside mask
}
