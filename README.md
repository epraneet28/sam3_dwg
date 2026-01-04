# SAM3 Drawing Zone Segmenter

A FastAPI microservice that uses Meta's **SAM3 (Segment Anything Model 3)** to segment engineering and structural drawings into semantic zones.

## Features

- **6 SAM3 input modalities** - Text, Points, Boxes, Masks, Visual Exemplars, Combined
- **Zero-shot segmentation** using SAM3's text prompt capabilities
- **Pre-configured prompts** optimized for structural/construction drawings
- **Interactive Playground** for experimenting with all input types
- **Visual exemplars** support for improved accuracy
- **Batch processing** for multiple images
- **Docker deployment** with GPU support

## Supported Zone Types

| Zone Type | Description |
|-----------|-------------|
| `title_block` | Project info, drawing number, engineer stamp |
| `revision_block` | Revision history table |
| `plan_view` | Floor plans, framing plans, foundation plans |
| `elevation_view` | Building elevations |
| `section_view` | Section cuts |
| `detail_view` | Construction details |
| `schedule_table` | Beam, column, material schedules |
| `notes_area` | General notes and specifications |
| `legend` | Symbol legends and abbreviations |
| `grid_system` | Column grid lines with bubble markers |

## Quick Start

### Prerequisites

- Python 3.10+
- NVIDIA GPU with CUDA support (recommended)
- Docker (optional)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd sam3-drawing-segmenter

# Install dependencies
pip install -e ".[dev]"

# Download SAM3 model weights
python scripts/download_model.py
```

### Running the Server

```bash
# Development mode with auto-reload
uvicorn src.sam3_segmenter.main:app --reload --port 8001

# Production mode
uvicorn src.sam3_segmenter.main:app --host 0.0.0.0 --port 8001
```

### Using Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Development mode with hot reload
docker-compose --profile dev up sam3-segmenter-dev
```

## API Usage

### Health Check

```bash
curl http://localhost:8001/health
```

Response:
```json
{
  "status": "healthy",
  "model": "sam3",
  "model_loaded": true,
  "gpu_available": true,
  "gpu_name": "NVIDIA RTX 4090",
  "gpu_memory_used_mb": 2048
}
```

### Segment with Custom Prompts

```bash
curl -X POST http://localhost:8001/segment \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "<base64_image>",
    "prompts": ["title block", "construction detail"],
    "return_masks": false,
    "confidence_threshold": 0.3
  }'
```

### Segment Structural Drawing

```bash
curl -X POST http://localhost:8001/segment/structural \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "<base64_image>",
    "classify_page_type": true
  }'
```

Response:
```json
{
  "page_type": "details",
  "page_type_confidence": 0.85,
  "zones": [
    {
      "zone_id": "zone_001",
      "zone_type": "title_block",
      "prompt_matched": "title block with project name...",
      "confidence": 0.92,
      "bbox": [1450, 900, 1700, 1100],
      "bbox_normalized": [0.85, 0.82, 1.0, 1.0],
      "area_ratio": 0.045
    }
  ],
  "image_size": [1700, 1100],
  "processing_time_ms": 245.3
}
```

### Batch Processing

```bash
curl -X POST http://localhost:8001/segment/batch \
  -H "Content-Type: application/json" \
  -d '{
    "images": [
      {"image_base64": "<image1>", "page_id": "S-1.1"},
      {"image_base64": "<image2>", "page_id": "S-1.2"}
    ],
    "prompts": ["title block", "detail drawing"]
  }'
```

## Python Client

```python
import httpx
import base64

class SAM3Client:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=60.0)

    def segment_structural(self, image_path: str) -> dict:
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

        response = self.client.post(
            f"{self.base_url}/segment/structural",
            json={
                "image_base64": image_b64,
                "return_masks": False,
                "classify_page_type": True
            }
        )
        response.raise_for_status()
        return response.json()

# Usage
client = SAM3Client()
result = client.segment_structural("drawings/S-1.1.png")
print(f"Page type: {result['page_type']}")
for zone in result['zones']:
    print(f"  {zone['zone_type']}: {zone['confidence']:.2f}")
```

## Configuration

Environment variables (prefix with `SAM3_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_PATH` | `sam3.pt` | Path to SAM3 model weights |
| `DEFAULT_CONFIDENCE_THRESHOLD` | `0.3` | Default confidence threshold |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8001` | Server port |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins |
| `EXEMPLARS_DIR` | `./exemplars` | Visual exemplars directory |
| `LOG_LEVEL` | `INFO` | Logging level |

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src/sam3_segmenter --cov-report=html

# Test specific module
pytest tests/test_api.py -v
```

## Interactive Prompt Testing

```bash
# Test with structural prompts
python scripts/test_prompts.py -i drawing.png --structural

# Test with custom prompts
python scripts/test_prompts.py -i drawing.png -p "title block" "beam schedule"

# Save visualization
python scripts/test_prompts.py -i drawing.png --structural -o result.png
```

## Project Structure

```
sam3-drawing-segmenter/
├── src/sam3_segmenter/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Settings
│   ├── models.py            # Pydantic schemas
│   ├── segmenter.py         # SAM3 wrapper
│   ├── zone_classifier.py   # Page type classification
│   ├── prompts/             # Prompt configurations
│   └── utils/               # Image/geometry utilities
├── tests/                   # Test suite
├── scripts/                 # Utility scripts
├── exemplars/               # Visual exemplars
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## SAM3 Notes

SAM3 (released November 2025) introduces:
- **Native text prompts**: Direct text/concept input for segmentation
- **Promptable Concept Segmentation (PCS)**: Natural language zone detection
- **Visual exemplars**: Example-based prompt enhancement
- **848M parameters**: Requires ~3-4GB VRAM

## SAM3 Input Types

SAM3 supports **6 distinct input modalities** organized into two paradigms:

### Promptable Concept Segmentation (PCS)
Find all instances of a concept across the image.

| Input Type | API Method | Description |
|------------|------------|-------------|
| **Text Prompts** | `processor.set_text_prompt(prompt, state)` | Natural language descriptions like "title block", "beam schedule" |
| **Visual Exemplars** | `visual_prompt_embed` | Image regions that represent the concept to find |

### Promptable Visual Segmentation (PVS)
Segment specific instances at specified locations.

| Input Type | API Method | Description |
|------------|------------|-------------|
| **Point Prompts** | `predictor.predict(point_coords, point_labels)` | Click points: positive (include) or negative (exclude) |
| **Bounding Box** | `processor.add_geometric_prompt(box, label, state)` | Draw rectangle to specify region of interest |
| **Mask Prompts** | `predictor.predict(mask_input=mask)` | Feed previous mask for iterative refinement |
| **Combined Mode** | Chain multiple `add_*_prompt()` calls | Multiple modalities in single inference |

### Input Type Details

#### 1. Text Prompts (Implemented)
```python
# API Example
POST /segment
{
  "image_base64": "<base64>",
  "prompts": ["title block", "construction detail", "beam schedule"],
  "confidence_threshold": 0.3
}
```

#### 2. Point Prompts (Planned)
Click positive points to include, negative points to exclude.
```python
# Positive point (label=1) + Negative point (label=0)
point_coords = [[250, 125], [400, 300]]
point_labels = [1, 0]  # Include first, exclude second
```

#### 3. Bounding Box (Planned)
Draw rectangle to define region of interest.
```python
# Box format: [x1, y1, x2, y2]
box = [100, 50, 400, 200]
```

#### 4. Mask Prompts (Planned)
Use previous segmentation mask as input for refinement.
```python
# Feed previous output mask as new input
mask_input = previous_result.mask
```

#### 5. Visual Exemplars (Planned)
Select image regions as visual examples of the concept.
```python
# Crop region becomes exemplar for finding similar areas
exemplar = image[y1:y2, x1:x2]
```

#### 6. Combined Mode (Planned)
Combine multiple input types for maximum precision.
```json
{
  "prompts": ["title block"],
  "boxes": [[100, 50, 400, 200]],
  "points": [[250, 125]],
  "point_labels": [1]
}
```

### Playground Interface

The **Playground** page (`/playground`) provides interactive access to all 6 input types:

| Mode | Status | Description |
|------|--------|-------------|
| Text | ✅ Available | Enter text prompts, comma-separated for multiple |
| Points | ⏳ Coming | Click canvas to add positive/negative points |
| Box | ⏳ Coming | Drag to draw bounding box |
| Mask | ⏳ Coming | Use previous result as refinement input |
| Exemplar | ⏳ Coming | Select regions as visual exemplars |
| Combined | ⏳ Coming | Mix multiple input types |

## License

MIT License
