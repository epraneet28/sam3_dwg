# Testing Guide - SAM3 Drawing Segmenter

Complete testing reference for the SAM3 Drawing Segmenter, covering installation, test scripts, expected results, and troubleshooting.

---

## Quick Start

### 1. Without Dependencies (Syntax Check Only)
```bash
# Validates Python syntax and code structure
python scripts/basic_import_test.py
```

### 2. With Dependencies (Full Testing)
```bash
# Install dependencies first
pip install -e .

# Run comprehensive migration check
python scripts/check_migration.py

# Run detailed runtime tests
python scripts/test_runtime.py

# Run pytest suite
pytest tests/ -v --cov=src/sam3_segmenter
```

### 3. Start Development Server
```bash
# Local development
uvicorn src.sam3_segmenter.main:app --reload --port 8001

# Access API docs
open http://localhost:8001/docs

# Test health endpoint
curl http://localhost:8001/health
```

---

## Installation

### Step 1: Create Virtual Environment
```bash
# Create venv
python -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### Step 2: Install Dependencies
```bash
# Install package
pip install -e .

# Install with dev dependencies (for pytest, black, etc.)
pip install -e ".[dev]"

# Verify installation
pip list | grep -E "(torch|fastapi|pydantic)"
```

### Step 3: Configure Environment (Optional)
```bash
# Copy example environment file
cp .env.example .env

# Edit if needed (defaults work for most cases)
nano .env
```

### Step 4: Download Model (Optional)
```bash
# Service works without model (uses MockSAM3Model)
# Download only if you need real segmentation
python scripts/download_model.py

# Verify
ls -lh models/sam3.pt
```

---

## Test Scripts

### 1. Basic Import Test - `scripts/basic_import_test.py`

**Purpose**: Validates code structure and syntax without requiring dependencies.

**What it tests**:
- Python syntax validation for all source files
- Import statement analysis
- Module structure verification

**When to use**: Before installing dependencies, quick syntax check

**Run with**:
```bash
python scripts/basic_import_test.py
```

**Expected output (without dependencies)**:
```
✓ All source files have valid Python syntax
✓ Import analysis completes
⚠ Cannot import modules - missing dependencies
```

**Expected output (with dependencies)**:
```
✓ All source files have valid Python syntax
✓ Standard library imports work
✓ All modules imported successfully
```

**Time**: ~1 second
**Requires**: Python 3.10+ only (no third-party packages)

---

### 2. Migration Check - `scripts/check_migration.py`

**Purpose**: Comprehensive verification of the migration with dependency checks.

**What it tests**:
1. Project structure (all expected files present)
2. Python dependencies availability
3. Module imports
4. Pydantic model validation
5. Configuration loading
6. Prompt configurations
7. API endpoint structure
8. GPU availability
9. Model file existence
10. DrawingSegmenter initialization

**When to use**: After installing dependencies, comprehensive verification

**Run with**:
```bash
python scripts/check_migration.py
```

**Expected results (with all dependencies)**:
```
[1] Checking project structure...
    ✓ All expected files present

[2] Checking Python dependencies...
    ✓ torch
    ✓ PIL
    ✓ fastapi
    ✓ pydantic
    ✓ numpy
    ✓ cv2

[3] Testing module imports...
    ✓ models module
    ✓ config module
    ✓ segmenter module
    ✓ zone_classifier module
    ✓ main (API) module
    ✓ prompts.structural module

[4] Testing Pydantic models...
    ✓ ZoneType enum: 11 types
    ✓ SegmentationRequest validates
    ✓ DetectedZone creation works
    ✓ SegmentationResponse works

[5] Testing configuration...
    ✓ Settings loaded
      - Model path: sam3.pt
      - Device: auto
      - Port: 8001

[6] Testing prompt configurations...
    ✓ Structural prompts: 11 zone types
    ✓ Page type rules: 6 page types
    ✓ Sample prompt for 'title_block':
      'title block with project name and engineer stamp'

[7] Testing API structure...
    ✓ FastAPI app created with 7 endpoints
      GET      /
      GET      /health
      POST     /segment
      POST     /segment/structural
      POST     /segment/batch
      GET      /prompts/structural
      GET      /exemplars

[8] Checking GPU availability...
    PyTorch version: 2.x.x
    CUDA available: True/False
    [If True] GPU: NVIDIA GeForce RTX ...
    [If True] GPU memory: XX.X GB

[9] Checking model file...
    ✓ Model file found: /path/to/models/sam3.pt
      Size: X.XX GB
    [OR]
    ✗ Model file not found at /path/to/models/sam3.pt
      Run: python scripts/download_model.py

[10] Testing DrawingSegmenter initialization...
    ✓ DrawingSegmenter initialized
      Model type: SAM3Model [OR] MockSAM3Model
      Device: cuda:0 [OR] cpu
      [If Mock] ⚠ Using MockSAM3Model (real model not loaded)
```

**Expected results (without dependencies)**:
```
[1] Checking project structure...
    ✓ All expected files present

[2] Checking Python dependencies...
    ✗ Some dependencies not installed

⚠ Skipping advanced tests - dependencies not installed
   Install with: pip install -e .
```

**Time**: ~5-10 seconds
**Requires**: All dependencies installed

---

### 3. Full Runtime Test - `scripts/test_runtime.py`

**Purpose**: Comprehensive runtime functionality testing including actual operations.

**What it tests**:
1. Dependency availability
2. Module imports
3. Pydantic model creation and validation
4. Configuration loading
5. Prompt configurations
6. DrawingSegmenter initialization (with real or mock model)
7. Mock segmentation operations
8. API structure and endpoints
9. Zone classifier functionality

**When to use**: Full functionality testing before deployment

**Run with**:
```bash
python scripts/test_runtime.py
```

**Expected output**:
```
============================================================
  SAM3 Drawing Segmenter - Runtime Functionality Tests
============================================================

============================================================
  Test 1: Checking Dependencies
============================================================
✓ PyTorch              installed
✓ Pillow               installed
✓ FastAPI              installed
✓ Pydantic             installed
✓ NumPy                installed
✓ OpenCV               installed

✓ All dependencies installed

============================================================
  Test 2: Testing Module Imports
============================================================
✓ Data Models                  imported
✓ Configuration                imported
✓ DrawingSegmenter             imported
✓ ZoneClassifier               imported
✓ FastAPI App                  imported

[... continues through all 9 tests ...]

============================================================
  Test Summary
============================================================
  ✓ PASS  Dependencies
  ✓ PASS  Imports
  ✓ PASS  Pydantic Models
  ✓ PASS  Configuration
  ✓ PASS  Prompt Configs
  ✓ PASS  Segmenter Init
  ✓ PASS  Mock Segmentation
  ✓ PASS  API Structure
  ✓ PASS  Zone Classifier

  Results: 9/9 tests passed

✓ All runtime tests passed!
```

**Time**: ~10-20 seconds
**Requires**: All dependencies installed

---

## Expected Behavior by Scenario

### Scenario 1: Fresh Install (No Dependencies)

**Test**: `basic_import_test.py`
- ✓ Syntax validation passes
- ✗ Module imports fail (expected)
- **Action**: Install dependencies

**Test**: `check_migration.py`
- ✓ Project structure check passes
- ✗ Dependency check fails
- ⚠ Skips advanced tests
- **Action**: Install dependencies

### Scenario 2: Dependencies Installed, No Model

**Test**: `check_migration.py`
- ✓ All checks pass
- ✗ Model file not found
- ✓ DrawingSegmenter uses MockSAM3Model
- **Status**: PASS (mock model allows development)

**Test**: `test_runtime.py`
- ✓ All tests pass
- ⚠ Using MockSAM3Model
- **Status**: PASS (can develop without model)

### Scenario 3: Full Install (Dependencies + Model)

**Test**: `check_migration.py`
- ✓ All checks pass
- ✓ Model file found
- ✓ DrawingSegmenter uses real SAM3
- **Status**: PASS (production ready)

**Test**: `test_runtime.py`
- ✓ All tests pass
- ✓ Using real SAM3Model
- **Status**: PASS (fully functional)

### Scenario 4: GPU Available

**Additional output**:
- CUDA available: True
- GPU: NVIDIA GeForce RTX 4090 (example)
- GPU memory: 24.0 GB
- Device: cuda:0

### Scenario 5: No GPU (CPU only)

**Additional output**:
- CUDA available: False
- Device: cpu
- ⚠ Inference will be slower on CPU

---

## Configuration

Environment variables (all use `SAM3_` prefix):
- `MODEL_PATH` - Path to model weights (default: sam3.pt)
- `DEVICE` - cuda/cpu/auto (default: auto)
- `DEFAULT_CONFIDENCE_THRESHOLD` - Default 0.3
- `MAX_BATCH_SIZE` - Default 10
- `PORT` - Default 8001
- `HOST` - Default 0.0.0.0
- `CORS_ORIGINS` - JSON array of allowed origins
- `EXEMPLARS_DIR` - Default ./exemplars
- `LOG_LEVEL` - Default INFO

---

## Development Workflow

### 1. Make Code Changes
```bash
# Edit files in src/sam3_segmenter/
nano src/sam3_segmenter/main.py
```

### 2. Run Quick Tests
```bash
# Syntax check (fast)
python scripts/basic_import_test.py

# Full verification
python scripts/check_migration.py
```

### 3. Run Pytest
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_api.py -v

# With coverage
pytest tests/ --cov=src/sam3_segmenter --cov-report=html
```

### 4. Test API Manually
```bash
# Start server with auto-reload
uvicorn src.sam3_segmenter.main:app --reload --port 8001

# In another terminal, test endpoints
curl http://localhost:8001/health
```

### 5. Format Code
```bash
# Format with black
black src/ tests/ --line-length 100

# Lint with ruff
ruff check src/ tests/
```

---

## Docker Testing

### Build and Run
```bash
# Build image
docker-compose build

# Run container
docker-compose up -d

# View logs
docker-compose logs -f sam3-segmenter

# Test health
curl http://localhost:8001/health

# Stop container
docker-compose down
```

### Development Mode (with hot reload)
```bash
# Run dev container
docker-compose --profile dev up sam3-segmenter-dev

# Code changes auto-reload
```

---

## Performance Testing

### Benchmark Segmentation Speed
```bash
# Use test_prompts.py for timing
python scripts/test_prompts.py -i path/to/drawing.png --structural

# Expected times:
# - GPU (RTX 4090): < 500ms per image
# - CPU: < 3s per image
# - Mock: ~100-200ms (instant, just random data)
```

### Load Testing (requires additional tools)
```bash
# Install locust
pip install locust

# Create locustfile.py for load testing
# Run concurrent requests
locust -f locustfile.py --host http://localhost:8001
```

---

## Troubleshooting

### Import Errors

**Error**: `No module named 'torch'`
**Cause**: Dependencies not installed
**Solution**:
```bash
pip install -e .
```

**Error**: `No module named 'src.sam3_segmenter'`
**Cause**: Package not installed in development mode
**Solution**: Run from project root or install package:
```bash
pip install -e .
```

### Model Loading Issues

**Warning**: `Using MockSAM3Model`
**Cause**: Model file not found OR GPU unavailable
**Impact**: API works, returns synthetic segmentation results
**Solution** (if you need real model):
```bash
python scripts/download_model.py
```

### GPU Issues

**Error**: `CUDA unavailable`
**Check**:
```bash
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"
```
**Solution**: Install CUDA-enabled PyTorch or use CPU mode

**Check GPU memory**:
```bash
nvidia-smi --query-gpu=memory.used --format=csv
```

### API Errors

**Error**: Import errors in `main.py`
**Check**: Dependencies installed, especially FastAPI, Pydantic
**Solution**:
```bash
pip install fastapi uvicorn pydantic
```

### Tests Pass But API Fails

**Check**:
1. Virtual environment activated? `which python`
2. Server running? `ps aux | grep uvicorn`
3. Port available? `lsof -i :8001`
4. Firewall blocking? `sudo ufw status`

### Slow Performance

**Causes**:
- Running on CPU (5-10x slower than GPU)
- Large images (resize to max 2048px width)
- Model loading on every request (should cache)

**Solutions**:
- Use GPU if available
- Resize images before sending
- Check model is loaded: `curl http://localhost:8001/health`

---

## API Testing

### Test Health Check
```bash
curl http://localhost:8001/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_type": "SAM3Model" or "MockSAM3Model",
  "device": "cuda:0" or "cpu",
  "gpu_available": true or false
}
```

### Test Segmentation
```bash
# Create test request
cat > test_request.json << 'EOF'
{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "confidence_threshold": 0.3
}
EOF

# Send request
curl -X POST http://localhost:8001/segment/structural \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

### API Endpoints
Expected endpoints:
- `GET /` - Root/welcome
- `GET /health` - Health check
- `POST /segment` - Generic segmentation
- `POST /segment/structural` - Structural drawing segmentation
- `POST /segment/batch` - Batch processing
- `GET /prompts/structural` - Get structural prompts
- `GET /exemplars` - List exemplar images

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run tests
        run: |
          python scripts/basic_import_test.py
          python scripts/check_migration.py
          pytest tests/ -v --cov=src/sam3_segmenter
```

---

## Pre-Deployment Checklist

- [ ] All dependencies installed: `pip list | grep torch`
- [ ] Basic import test passes: `python scripts/basic_import_test.py`
- [ ] Migration check passes: `python scripts/check_migration.py`
- [ ] Runtime tests pass: `python scripts/test_runtime.py`
- [ ] Pytest suite passes: `pytest tests/ -v`
- [ ] Server starts: `uvicorn src.sam3_segmenter.main:app --reload`
- [ ] Health endpoint works: `curl http://localhost:8001/health`
- [ ] API docs accessible: http://localhost:8001/docs
- [ ] Test segmentation request works (see API Testing section)

---

## Test Coverage Summary

| Aspect | Basic Import | Migration Check | Runtime Test |
|--------|--------------|-----------------|--------------|
| Syntax validation | ✓ | - | - |
| File structure | ✓ | ✓ | - |
| Dependencies | - | ✓ | ✓ |
| Module imports | ✓ | ✓ | ✓ |
| Pydantic models | - | ✓ | ✓ |
| Configuration | - | ✓ | ✓ |
| Prompts | - | ✓ | ✓ |
| API structure | - | ✓ | ✓ |
| GPU detection | - | ✓ | - |
| Model loading | - | ✓ | ✓ |
| Segmenter init | - | ✓ | ✓ |
| Zone classifier | - | - | ✓ |
| Mock operations | - | - | ✓ |

---

## Next Steps

### After All Tests Pass
1. **Development**: Start building features on top of the API
2. **Integration**: Connect to frontend or other services
3. **Deployment**: Use Docker for production deployment
4. **Monitoring**: Add logging, metrics, alerts
5. **Scaling**: Load balancer + multiple instances

### If Tests Fail
1. Check error messages carefully
2. Review relevant test script section above
3. Verify dependencies: `pip list`
4. Check Python version: `python --version` (requires ≥3.10)
5. Review error traceback for import/syntax issues

---

## Test File Locations

- `scripts/basic_import_test.py` - Syntax validation
- `scripts/check_migration.py` - Migration verification
- `scripts/test_runtime.py` - Runtime functionality
- `tests/` - Pytest test suite
- `tests/conftest.py` - Test fixtures

---

## Key Configuration Files

- `pyproject.toml` - Package definition
- `.env` - Environment variables
- `docker-compose.yml` - Docker config
- `src/sam3_segmenter/config.py` - Settings class

---

## Quick Reference Commands

```bash
# Install
pip install -e .

# Test
python scripts/check_migration.py

# Run
uvicorn src.sam3_segmenter.main:app --reload

# Test API
curl http://localhost:8001/health

# Docker
docker-compose up -d
```

---

**Last Updated**: 2026-01-04
**Tested On**: Python 3.10+, PyTorch 2.1+, FastAPI 0.109+
