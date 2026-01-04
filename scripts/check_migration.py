#!/usr/bin/env python3
"""
Quick migration check - tests what can be checked without full dependencies.
"""
import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

print("="*70)
print("  SAM3 Drawing Segmenter - Migration Verification")
print("="*70)

# Test 1: Check project structure
print("\n[1] Checking project structure...")
expected_files = [
    "src/sam3_segmenter/__init__.py",
    "src/sam3_segmenter/main.py",
    "src/sam3_segmenter/models.py",
    "src/sam3_segmenter/config.py",
    "src/sam3_segmenter/segmenter.py",
    "src/sam3_segmenter/zone_classifier.py",
    "src/sam3_segmenter/prompts/__init__.py",
    "src/sam3_segmenter/prompts/structural.py",
    "pyproject.toml",
    "README.md",
    "CLAUDE.md",
]

missing = []
for file_path in expected_files:
    full_path = project_root / file_path
    if full_path.exists():
        print(f"    ✓ {file_path}")
    else:
        print(f"    ✗ {file_path} MISSING")
        missing.append(file_path)

if missing:
    print(f"\n✗ Missing files: {len(missing)}")
    sys.exit(1)
else:
    print(f"✓ All expected files present")

# Test 2: Check dependency availability
print("\n[2] Checking Python dependencies...")
deps_status = {}
critical_deps = ['torch', 'PIL', 'fastapi', 'pydantic', 'numpy', 'cv2']

for dep in critical_deps:
    try:
        __import__(dep)
        print(f"    ✓ {dep}")
        deps_status[dep] = True
    except ImportError:
        print(f"    ✗ {dep} - not installed")
        deps_status[dep] = False

all_deps = all(deps_status.values())
if not all_deps:
    print("\n⚠ Some dependencies not installed. Install with: pip install -e .")
    print("  Continuing with limited tests...\n")

# Test 3: Try importing modules (only if deps available)
if all_deps:
    print("\n[3] Testing module imports...")
    try:
        from src.sam3_segmenter import models
        print("    ✓ models module")
    except Exception as e:
        print(f"    ✗ models module: {e}")

    try:
        from src.sam3_segmenter import config
        print("    ✓ config module")
    except Exception as e:
        print(f"    ✗ config module: {e}")

    try:
        from src.sam3_segmenter import segmenter
        print("    ✓ segmenter module")
    except Exception as e:
        print(f"    ✗ segmenter module: {e}")

    try:
        from src.sam3_segmenter import zone_classifier
        print("    ✓ zone_classifier module")
    except Exception as e:
        print(f"    ✗ zone_classifier module: {e}")

    try:
        from src.sam3_segmenter import main
        print("    ✓ main (API) module")
    except Exception as e:
        print(f"    ✗ main module: {e}")

    try:
        from src.sam3_segmenter.prompts import structural
        print("    ✓ prompts.structural module")
    except Exception as e:
        print(f"    ✗ prompts.structural: {e}")

    # Test 4: Check models work
    print("\n[4] Testing Pydantic models...")
    try:
        from src.sam3_segmenter.models import (
            ZoneType, SegmentationRequest, DetectedZone, SegmentationResponse
        )

        # Test enum
        zone_types = list(ZoneType)
        print(f"    ✓ ZoneType enum: {len(zone_types)} types")

        # Test request model
        req = SegmentationRequest(image_base64="test", confidence_threshold=0.3)
        print(f"    ✓ SegmentationRequest validates")

        # Test zone model
        zone = DetectedZone(
            zone_type=ZoneType.TITLE_BLOCK,
            confidence=0.95,
            bbox=[0, 0, 100, 100]
        )
        print(f"    ✓ DetectedZone creation works")

        # Test response model
        resp = SegmentationResponse(zones=[zone], processing_time_ms=100.0)
        print(f"    ✓ SegmentationResponse works")

    except Exception as e:
        print(f"    ✗ Model tests failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 5: Check config
    print("\n[5] Testing configuration...")
    try:
        from src.sam3_segmenter.config import get_settings
        settings = get_settings()
        print(f"    ✓ Settings loaded")
        print(f"      - Model path: {settings.model_path}")
        print(f"      - Device: {settings.device or 'auto'}")
        print(f"      - Port: {settings.port}")
    except Exception as e:
        print(f"    ✗ Config failed: {e}")

    # Test 6: Check prompts
    print("\n[6] Testing prompt configurations...")
    try:
        from src.sam3_segmenter.prompts import STRUCTURAL_ZONE_PROMPTS, PAGE_TYPE_RULES
        print(f"    ✓ Structural prompts: {len(STRUCTURAL_ZONE_PROMPTS)} zone types")
        print(f"    ✓ Page type rules: {len(PAGE_TYPE_RULES)} page types")

        # Show sample
        sample_zone = list(STRUCTURAL_ZONE_PROMPTS.keys())[0]
        sample_config = STRUCTURAL_ZONE_PROMPTS[sample_zone]
        print(f"    ✓ Sample prompt for '{sample_zone}':")
        print(f"      '{sample_config.primary_prompt}'")
    except Exception as e:
        print(f"    ✗ Prompts failed: {e}")

    # Test 7: Check API structure
    print("\n[7] Testing API structure...")
    try:
        from src.sam3_segmenter.main import app
        routes = [r for r in app.routes if hasattr(r, 'methods')]
        print(f"    ✓ FastAPI app created with {len(routes)} endpoints")
        for route in routes:
            methods = ', '.join(route.methods)
            print(f"      {methods:<8} {route.path}")
    except Exception as e:
        print(f"    ✗ API structure failed: {e}")

    # Test 8: Check GPU
    print("\n[8] Checking GPU availability...")
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        print(f"    PyTorch version: {torch.__version__}")
        print(f"    CUDA available: {cuda_available}")
        if cuda_available:
            print(f"    GPU: {torch.cuda.get_device_name(0)}")
            mem_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"    GPU memory: {mem_gb:.1f} GB")
        else:
            print("    ⚠ No GPU detected (will use CPU/mock)")
    except Exception as e:
        print(f"    ✗ GPU check failed: {e}")

    # Test 9: Check model file
    print("\n[9] Checking model file...")
    model_path = project_root / "models" / "sam3.pt"
    if model_path.exists():
        size_gb = model_path.stat().st_size / 1e9
        print(f"    ✓ Model file found: {model_path}")
        print(f"      Size: {size_gb:.2f} GB")
    else:
        print(f"    ✗ Model file not found at {model_path}")
        print(f"      Run: python scripts/download_model.py")

    # Test 10: Try initializing segmenter
    print("\n[10] Testing DrawingSegmenter initialization...")
    try:
        from src.sam3_segmenter.segmenter import DrawingSegmenter

        # Try to initialize (will use mock if model not available)
        segmenter = DrawingSegmenter()
        model_type = type(segmenter.model).__name__
        print(f"    ✓ DrawingSegmenter initialized")
        print(f"      Model type: {model_type}")
        print(f"      Device: {segmenter.device}")

        if "Mock" in model_type:
            print("      ⚠ Using MockSAM3Model (real model not loaded)")
        else:
            print("      ✓ Using real SAM3 model")
    except Exception as e:
        print(f"    ✗ Segmenter initialization failed: {e}")
        import traceback
        traceback.print_exc()

else:
    print("\n⚠ Skipping advanced tests - dependencies not installed")
    print("   Install with: pip install -e .")

# Summary
print("\n" + "="*70)
print("  Migration Verification Complete")
print("="*70)

if all_deps:
    print("✓ Full verification completed - all dependencies available")
    print("  Next: Run pytest tests/ -v")
else:
    print("⚠ Partial verification - install dependencies for full testing")
    print("  Next: pip install -e . && python scripts/check_migration.py")

print("="*70)
