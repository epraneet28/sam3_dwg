# SAM3 Drawing Zone Segmenter

A FastAPI microservice using Meta's **SAM3 (Segment Anything Model 3)** to segment engineering drawings into semantic zones.

**📜 License:** MIT License (permissive, commercial use allowed) - uses Meta's official SAM3 implementation

## Core Capabilities

- **Zero-shot segmentation** with text prompts (Promptable Concept Segmentation)
- **Pre-configured prompts** for structural/construction drawings
- **Page type classification** (plans, elevations, sections, details, spec sheets, schedules)
- **Visual exemplars** for improved accuracy
- **Batch processing** and **REST API** with OpenAPI docs
- **Docker deployment** with GPU support

## Supported Zone Types

`title_block`, `revision_block`, `plan_view`, `elevation_view`, `section_view`, `detail_view`, `schedule_table`, `notes_area`, `legend`, `grid_system`, `unknown`

**Note:** Additional types (`dimension_string`, `north_arrow`, `scale_bar`) defined in prompts but not yet in ZoneType enum.

## Processing Pipeline

1. **Image Ingestion** → 2. **Pre-processing** → 3. **SAM3 Inference** → 4. **Post-processing** → 5. **Classification** → 6. **Response Assembly**

---

# Quick Reference

## Installation & Setup

```bash
# Prerequisites: Python 3.10+, CUDA 12.1+ (for GPU)
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Install Meta's official SAM3
cd sam3_reference && pip install -e . && cd ..

# Download SAM3 model (requires Hugging Face access)
python scripts/download_model.py
```

**Note:** SAM3 model requires approval from Meta on Hugging Face. See `scripts/download_model.py` for details.

## Run Service

```bash
# Local
uvicorn src.sam3_segmenter.main:app --reload --port 8001

# Docker
docker-compose up -d

# Verify
curl http://localhost:8001/health
```

## Common Commands

- **Tests**: `pytest tests/ -v` (with coverage: `--cov=src/sam3_segmenter`)
- **Test prompts**: `python scripts/test_prompts.py -i <image> --structural`
- **Environment vars**: All use `SAM3_` prefix (see Configuration section)

## Development Without GPU

Service auto-uses `MockSAM3Model` if GPU/model unavailable. Allows API development and testing without ML inference.

---

# Project Guidelines

## Code Style

- PEP 8, enforced with `ruff` or `black --line-length 100`
- Type hints required for all function signatures
- Pydantic models for all data structures requiring validation

## File Organization

- **Target: < 500 lines** per file
- **Hard limit: 600 lines** (ML model wrappers may exceed with approval)
- **Module structure**:
  - `models.py` - Pydantic schemas
  - `config.py` - Settings via pydantic-settings
  - `segmenter.py` - SAM3 wrapper
  - `zone_classifier.py` - Post-processing
  - `prompts/` - Domain prompt configs
  - `utils/` - Helper functions
- **Naming**: snake_case files, PascalCase classes, SCREAMING_SNAKE constants
- **Imports**: Standard lib → Third-party → Local (relative)

## Editing & Patching

- Always patch existing code before creating new files
- Model weights in `models/` (never commit to git)
- Exemplar images in `exemplars/<zone_type>/`
- Temp files in `temp/` (delete when done)

## Common Pitfalls

### Error Handling Anti-Patterns

**Silent Exception Swallowing** ❌
```python
# BAD: Hides failures
try:
    result = segment_image(image)
except Exception:
    pass  # Silent failure!
```

**CORRECT**: Always log caught exceptions with stack traces:
```python
# GOOD: Explicit error handling
try:
    result = segment_image(image)
except Exception as e:
    logger.error(f"Segmentation failed: {e}", exc_info=True)  # ← exc_info=True!
    raise
```

**Missing Stack Traces** ⚠️
```python
# BAD: Logs message but no stack trace
except Exception as e:
    logger.warning(f"Operation failed: {e}")  # Where did this happen?
```

**CORRECT**: Add `exc_info=True` to capture full stack trace:
```python
# GOOD: Full debugging context
except Exception as e:
    logger.warning(f"Operation failed: {e}", exc_info=True)
```

**WARNING Level Overuse** ⚠️
```python
# BAD: Normal operation shouldn't warn
if not checkpoint_exists:
    logger.warning("Checkpoint not found")  # Expected condition!
    return None
```

**CORRECT**: Use DEBUG for expected conditions:
```python
# GOOD: Appropriate log level
if not checkpoint_exists:
    logger.debug("Checkpoint not found (expected for optional stages)")
    return None
```

**Log Level Guidelines**:
- **DEBUG**: Expected conditions, optional file checks, fallback paths
- **INFO**: Successful operations, state changes
- **WARNING**: Unexpected but recoverable (e.g., retry succeeded)
- **ERROR**: Failures affecting functionality

### FastAPI Parameter Gotchas

**Optional Wrapper on Injectable Types** ❌
```python
# BAD: FastAPI can't inject Request as optional
async def endpoint(request: Optional[Request] = None):  # Breaks at import!
    ...
```

**CORRECT**: Injectable types must be required:
```python
# GOOD: FastAPI injects automatically
async def endpoint(request: Request):
    ...
```

Affected types: `Request`, `WebSocket`, `Response`, `BackgroundTasks`, `SecurityScopes`

**Positional Argument Mismatch** ⚠️
```python
# Function with multiple optional params
async def run_stage(doc_id: str, http_request: Request = None, request: StageRunRequest = None):
    ...

# BAD: Silent bug - options goes to wrong parameter
await handler(doc_id, options)  # → http_request gets options!

# GOOD: Explicit keyword argument
await handler(doc_id, request=options)  # → request gets options ✓
```

**Rule**: Always use keyword arguments when calling functions with 2+ optional parameters.

## Testing Best Practices

- **Hard assertions only** - tests must fail when wrong
- **Mock model for unit tests**: Use `MockSAM3Model` (no GPU required)
- **Test fixtures**: `client`, `sample_image_base64` in `conftest.py`
- **ML testing**: Test confidence boundaries, synthetic images, schema validation
- **Batch testing**: Mix success/failure scenarios

---

# GPU & Performance

## Device Selection

- Auto-detect: `SAM3_DEVICE=` (empty)
- Force GPU: `SAM3_DEVICE=cuda` or `SAM3_DEVICE=cuda:0`
- Force CPU: `SAM3_DEVICE=cpu` (slow, for debugging only)

## Memory Management

- **Single model instance** - global singleton, never per-request
- **Clear cache**: `torch.cuda.empty_cache()` between large batches
- **Monitor**: Health endpoint shows `gpu_memory_used_mb`
- **Batch limits**: `max_batch_size=10` prevents OOM

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Single inference | < 500ms | RTX 4090 equivalent |
| Batch of 10 | < 3s | Sequential |
| Model load | < 30s | Cold start |
| Health check | < 50ms | Doesn't load model |

---

# API Guidelines

## Endpoints

- **POST**: `/segment`, `/segment/structural`, `/segment/batch`
- **GET**: `/health`, `/prompts/structural`, `/prompts/page-types`, `/exemplars`
- Always specify `response_model` in decorators
- Include `processing_time_ms` in responses

## Error Codes

- **400**: Invalid input (bad base64, malformed image)
- **422**: Pydantic validation errors
- **500**: Model inference failures
- **503**: Model not loaded

## Response Patterns

- No detections → empty `zones: []` (not an error)
- Low confidence → return all zones (let client filter)
- Batch errors → per-image `error` field (don't fail entire batch)

## Payload Limits

- Max single image: ~10MB base64 (7.5MB decoded)
- Max batch total: 50MB

---

# Prompt Engineering

## Structure Requirements

Each zone type needs:
- **primary_prompt**: Descriptive phrase (not single word)
- **alternate_prompts**: Variations for testing
- **typical_location**: Expected position (bottom_right, center, etc.)
- **expected_per_page**: Cardinality (1 or "variable")
- **priority**: Lower = higher priority

## Best Practices

- Use phrases: "title block with project name and engineer stamp"
- Include location hints when applicable
- Test with: `python scripts/test_prompts.py`
- Document working confidence thresholds

---

# Configuration

## Environment Variables (all use `SAM3_` prefix)

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_PATH` | `sam3.pt` | Path to model weights |
| `DEVICE` | (auto) | `cuda`, `cpu`, or empty |
| `DEFAULT_CONFIDENCE_THRESHOLD` | `0.3` | Default threshold |
| `MAX_BATCH_SIZE` | `10` | Max images per batch |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8001` | Server port |
| `CORS_ORIGINS` | `["http://localhost:3000", "http://localhost:8000"]` | Allowed origins |
| `EXEMPLARS_DIR` | `./exemplars` | Exemplars directory |
| `LOG_LEVEL` | `INFO` | Logging level |

## Adding New Settings

1. Add to `Settings` class in `config.py` with type hint and default
2. Add validators if needed
3. Update `.env.example`
4. Document here

---

# How-To Guides

## Add New Zone Type

1. Add to `ZoneType` enum in `models.py`: `NEW_ZONE = "new_zone"`
2. Add config to `STRUCTURAL_ZONE_PROMPTS` in `prompts/structural.py`
3. (Optional) Add to `PAGE_TYPE_RULES` if affects classification
4. Create directory: `mkdir -p exemplars/new_zone`
5. Test: `python scripts/test_prompts.py -i test.png --structural`

## Add New API Endpoint

1. Define request/response models in `models.py`
2. Add endpoint in `main.py`:
   - Check `if segmenter is None: raise HTTPException(503)`
   - Wrap in try/except: `ValueError` → 400, `Exception` → 500
   - Return response with `processing_time_ms`
3. Add tests in `test_api.py`

## Add New Prompt Domain

1. Create `prompts/mechanical.py` with `MECHANICAL_ZONE_PROMPTS` dict
2. Export from `prompts/__init__.py`
3. Add `segment_mechanical()` method to `segmenter.py`
4. Add API endpoint (follow "Add New API Endpoint")
5. Test with domain-specific drawings

## Write Tests

```python
# Use fixtures from conftest.py
def test_feature(client, sample_image_base64):
    response = client.post("/segment", json={...})
    assert response.status_code == 200
    assert "zones" in response.json()

# Run specific test
pytest tests/test_api.py::test_feature -v
```

---

# Docker

## Build & Run

```bash
docker-compose up -d                                    # Production
docker-compose --profile dev up sam3-segmenter-dev      # Dev with hot reload
docker-compose logs -f sam3-segmenter                   # View logs
```

## Key Points

- Base: `nvidia/cuda:12.1-runtime-ubuntu22.04`
- Multi-stage build (builder + runtime)
- Mount models: `./models:/app/models:ro` (never bake into image)
- GPU access requires NVIDIA Container Toolkit on host
- Health check waits 60s for model load

---

# Troubleshooting

## Model Issues

- **Model not found**: `python scripts/download_model.py`
- **SAM3 import error**: Install official Meta SAM3: `cd sam3_reference && pip install -e .`
- **Uses MockSAM3Model**: Check model file exists, verify `SAM3_MODEL_PATH`

## GPU Issues

- **CUDA unavailable**: Check `nvidia-smi`, verify CUDA 12.1, test `python -c "import torch; print(torch.cuda.is_available())"`
- **OOM**: Reduce `SAM3_MAX_BATCH_SIZE`, restart service, use smaller images
- **Docker GPU access**: Verify `nvidia-container-toolkit` installed, check docker-compose GPU reservation

## API Errors

- **400 Invalid image**: Verify base64 encoding, remove data URI prefix, check format (PNG/JPEG), size < 10MB
- **503 Model not loaded**: Wait for startup (check `/health`), verify model file exists
- **Slow first request**: Expected (lazy loading), subsequent requests fast

## No Detections

- Lower confidence threshold (try 0.1)
- Use `test_prompts.py` to visualize
- Verify image quality (resolution, contrast)
- Try different prompts or add exemplars

## Development

- **Import errors**: `pip install -e .`, activate venv, check PYTHONPATH
- **Docker build fails**: Check syntax, verify pyproject.toml exists, try `--no-cache`

---

# Key Files Reference

| Purpose | File |
|---------|------|
| API Endpoints | `src/sam3_segmenter/main.py` |
| Request/Response Models | `src/sam3_segmenter/models.py` |
| SAM3 Wrapper | `src/sam3_segmenter/segmenter.py` |
| Configuration | `src/sam3_segmenter/config.py` |
| Structural Prompts | `src/sam3_segmenter/prompts/structural.py` |
| Zone Classifier | `src/sam3_segmenter/zone_classifier.py` |
| Test Fixtures | `tests/conftest.py` |

---

# Code Review & Git

- Use sub-agents for unbiased code review on complex changes
- Orchestrator pattern: You coordinate, sub-agents analyze independently
- Never reference Claude/Anthropic/AI in commits
- Use conventional commit format: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`

---

# Future Considerations

- **API Versioning**: `/v1/segment` for breaking changes
- **Rate Limiting**: Per-IP or per-API-key limits
- **Authentication**: API keys or JWT for production
- **Metrics**: Prometheus for latency, throughput, GPU utilization
- **Request Tracing**: Request IDs for log correlation
