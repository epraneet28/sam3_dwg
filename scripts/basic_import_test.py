#!/usr/bin/env python3
"""
Minimal import test - checks code structure without dependencies.
"""
import sys
import ast
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

print("SAM3 Drawing Segmenter - Basic Import Test")
print("=" * 60)

# Test 1: Check Python version
print(f"\n[1] Python Environment")
print(f"    Python: {sys.version.split()[0]}")
print(f"    Executable: {sys.executable}")

# Test 2: Check file syntax
print(f"\n[2] Checking Python syntax...")
source_files = [
    "src/sam3_segmenter/__init__.py",
    "src/sam3_segmenter/main.py",
    "src/sam3_segmenter/models.py",
    "src/sam3_segmenter/config.py",
    "src/sam3_segmenter/segmenter.py",
    "src/sam3_segmenter/zone_classifier.py",
    "src/sam3_segmenter/prompts/__init__.py",
    "src/sam3_segmenter/prompts/structural.py",
]

syntax_errors = []
for file_path in source_files:
    full_path = project_root / file_path
    if not full_path.exists():
        print(f"    ✗ {file_path} - NOT FOUND")
        syntax_errors.append(file_path)
        continue

    try:
        with open(full_path, 'r') as f:
            code = f.read()
        ast.parse(code)
        print(f"    ✓ {file_path}")
    except SyntaxError as e:
        print(f"    ✗ {file_path} - SYNTAX ERROR: {e}")
        syntax_errors.append(file_path)

if syntax_errors:
    print(f"\n✗ {len(syntax_errors)} file(s) have syntax errors")
    sys.exit(1)
else:
    print(f"✓ All source files have valid Python syntax")

# Test 3: Check imports (without executing)
print(f"\n[3] Analyzing imports...")

def extract_imports(file_path):
    """Extract import statements from a file."""
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())

    imports = {'stdlib': [], 'third_party': [], 'local': []}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports['third_party'].append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            if module.startswith('.') or module.startswith('src.'):
                imports['local'].append(module)
            elif module.split('.')[0] in ['os', 'sys', 'pathlib', 'typing', 'enum']:
                imports['stdlib'].append(module)
            else:
                imports['third_party'].append(module)

    return imports

all_third_party = set()
for file_path in source_files:
    full_path = project_root / file_path
    if full_path.exists():
        imports = extract_imports(full_path)
        all_third_party.update(imports['third_party'])

print(f"    Required third-party packages:")
for pkg in sorted(all_third_party):
    print(f"      - {pkg.split('.')[0]}")

# Test 4: Try actual imports (will fail if deps missing)
print(f"\n[4] Attempting imports...")

try:
    # These should work without external deps
    import sys
    import os
    from pathlib import Path
    from typing import List, Optional
    from enum import Enum
    print("    ✓ Standard library imports work")
except Exception as e:
    print(f"    ✗ Standard library imports failed: {e}")
    sys.exit(1)

# Try third-party (may fail)
third_party_status = {}
for pkg in ['pydantic', 'fastapi', 'torch', 'PIL', 'numpy', 'cv2']:
    try:
        __import__(pkg)
        third_party_status[pkg] = True
        print(f"    ✓ {pkg}")
    except ImportError:
        third_party_status[pkg] = False
        print(f"    ✗ {pkg} - not installed")

# Test 5: Try importing our modules
print(f"\n[5] Importing sam3_segmenter modules...")

if all(third_party_status.values()):
    try:
        # Try models first (least dependencies)
        from src.sam3_segmenter.models import ZoneType
        print(f"    ✓ models.ZoneType imported")
        print(f"      Zone types: {', '.join([z.value for z in list(ZoneType)[:3]])}...")

        from src.sam3_segmenter.config import Settings
        print(f"    ✓ config.Settings imported")

        from src.sam3_segmenter.prompts import STRUCTURAL_ZONE_PROMPTS
        print(f"    ✓ prompts imported ({len(STRUCTURAL_ZONE_PROMPTS)} zones)")

        from src.sam3_segmenter.segmenter import DrawingSegmenter
        print(f"    ✓ segmenter.DrawingSegmenter imported")

        from src.sam3_segmenter.zone_classifier import ZoneClassifier
        print(f"    ✓ zone_classifier.ZoneClassifier imported")

        from src.sam3_segmenter.main import app
        print(f"    ✓ main.app (FastAPI) imported")

        print("\n✓ All modules imported successfully!")

    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
else:
    missing = [pkg for pkg, status in third_party_status.items() if not status]
    print(f"\n⚠ Cannot import modules - missing dependencies: {', '.join(missing)}")
    print(f"   Install with: pip install -e .")
    print(f"\n   Syntax check passed - code structure is valid")

print("\n" + "=" * 60)
print("Basic import test complete")
print("=" * 60)
