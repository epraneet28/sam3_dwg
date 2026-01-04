# Test Scripts Directory

This directory contains test and utility scripts for the SAM3 Drawing Segmenter project.

## Runtime Test Scripts

### `basic_import_test.py`
**Purpose**: Quick syntax and structure validation (no dependencies required)

**Run**:
```bash
python scripts/basic_import_test.py
```

**Tests**:
- Python syntax validation
- Import statement analysis
- File structure verification

**Requires**: Python 3.10+ only (no third-party packages)
**Time**: ~1 second

---

### `check_migration.py`
**Purpose**: Comprehensive migration verification (requires dependencies)

**Run**:
```bash
python scripts/check_migration.py
```

**Tests**:
1. Project structure
2. Dependencies availability
3. Module imports
4. Pydantic models
5. Configuration
6. Prompt configurations
7. API structure
8. GPU availability
9. Model file check
10. DrawingSegmenter initialization

**Requires**: All dependencies installed (`pip install -e .`)
**Time**: ~5-10 seconds

---

### `test_runtime.py`
**Purpose**: Detailed runtime functionality testing (requires dependencies)

**Run**:
```bash
python scripts/test_runtime.py
```

**Tests**:
1. Dependency check
2. Module imports
3. Pydantic models
4. Configuration
5. Prompts
6. Segmenter initialization
7. Mock segmentation
8. API structure
9. Zone classifier

**Requires**: All dependencies installed (`pip install -e .`)
**Time**: ~10-20 seconds

---

## Utility Scripts

### `download_model.py`
**Purpose**: Download SAM3 model weights

**Run**:
```bash
python scripts/download_model.py
```

**Note**: Service works without model (uses MockSAM3Model). Only needed for real segmentation.

---

### `test_prompts.py`
**Purpose**: Test zone prompts on real images with visualization

**Run**:
```bash
python scripts/test_prompts.py -i path/to/drawing.png --structural
```

**Options**:
- `-i, --image`: Path to input image
- `--structural`: Use structural zone prompts
- `--confidence`: Confidence threshold (default 0.3)
- `--save`: Save annotated output image

**Requires**: Model file + dependencies

---

## Quick Reference

### First Time Setup
```bash
# 1. Install dependencies
pip install -e .

# 2. Run basic test (no deps needed)
python scripts/basic_import_test.py

# 3. Run full migration check
python scripts/check_migration.py

# 4. Run runtime tests
python scripts/test_runtime.py

# 5. Optional: Download model
python scripts/download_model.py
```

### Regular Development
```bash
# Quick syntax check
python scripts/basic_import_test.py

# Full verification before commit
python scripts/check_migration.py && pytest tests/
```

---

## Test Script Comparison

| Script | Dependencies | Time | Coverage | Use Case |
|--------|--------------|------|----------|----------|
| `basic_import_test.py` | None | 1s | Syntax only | Quick check |
| `check_migration.py` | All | 5-10s | Comprehensive | Pre-deployment |
| `test_runtime.py` | All | 10-20s | Detailed ops | Full testing |

---

## Expected Output

### Success (All Tests Pass)
```
✓ All source files have valid Python syntax
✓ All dependencies installed
✓ All modules imported successfully
✓ Pydantic models work
✓ Configuration loaded
✓ API structure verified
✓ DrawingSegmenter initialized
```

### Partial (No Dependencies)
```
✓ All source files have valid Python syntax
✗ Dependencies not installed
⚠ Install with: pip install -e .
```

### Failure
```
✗ Syntax error in file X
✗ Import failed: Module Y not found
✗ Model test failed: ...
```

---

## Troubleshooting

### `No module named 'torch'`
Install dependencies: `pip install -e .`

### `Model file not found`
Either:
- Download model: `python scripts/download_model.py`
- Or continue (service uses mock model)

### `CUDA unavailable`
Expected if no GPU. Service will use CPU or mock model.

---

## See Also

- **TESTING_GUIDE.md** - Comprehensive testing guide
- **RUNTIME_TEST_RESULTS.md** - Expected test outputs
- **ai_report/runtime_test_report.md** - Detailed analysis

---

**Last Updated**: 2026-01-03
