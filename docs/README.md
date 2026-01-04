# SAM3 Drawing Zone Segmenter - Documentation

**Interactive web application for segmenting engineering drawings into semantic zones using Meta's SAM3 model.**

**Current Phase:** Phase 2 - Interactive UI Enhancements
**Status:** 🟢 Active Development
**Last Updated:** 2026-01-04

---

## 📋 Quick Navigation

### 🎯 Primary Documents

| Document | Purpose | Start Here? |
|----------|---------|-------------|
| **[PLAN.md](PLAN.md)** | Development roadmap and phase tracking | ⭐ For planning |
| **[MVP_QUICKSTART.md](reference/MVP_QUICKSTART.md)** | How to run the application | ⭐ For users |
| **[UI_ARCHITECTURE.md](reference/UI_ARCHITECTURE.md)** | Frontend architecture guide | ⭐ For developers |
| **[README.md](README.md)** | This index (you are here) | 📍 Overview |

### 📚 Reference Documents

Located in [`reference/`](reference/):

| Document | Purpose |
|----------|---------|
| [MVP_QUICKSTART.md](reference/MVP_QUICKSTART.md) | How to run the application |
| [UI_ARCHITECTURE.md](reference/UI_ARCHITECTURE.md) | Frontend architecture guide |
| [PHASE2_COMPLETION_SUMMARY.md](reference/PHASE2_COMPLETION_SUMMARY.md) | Phase 2 completion report |
| [TESTING.md](reference/TESTING.md) | Comprehensive testing guide with expected outputs |

---

## 🚀 Quick Start

### New Users - Get Started
1. Read [MVP_QUICKSTART.md](reference/MVP_QUICKSTART.md) to run the application
2. Start backend: `uvicorn src.sam3_segmenter.main:app --reload --port 8001`
3. Start frontend: `cd frontend && npm run dev`
4. Access UI: http://localhost:3007

### Developers - Current Work
1. Review [PLAN.md](PLAN.md) for current phase and tasks
2. Check [UI_ARCHITECTURE.md](reference/UI_ARCHITECTURE.md) for frontend structure
3. See Phase 2 completion summary in [reference/PHASE2_COMPLETION_SUMMARY.md](reference/PHASE2_COMPLETION_SUMMARY.md)
4. See testing guides in `reference/` folder

### QA/Testing
1. Review [TESTING.md](reference/TESTING.md)
2. Run test scripts from project root:
   ```bash
   python scripts/basic_import_test.py
   python scripts/check_migration.py
   pytest tests/ -v
   ```

---

## 📊 Project Status

### Phase Completion

- ✅ **Phase 0:** SAM3 Migration (COMPLETE)
- ✅ **Phase 1:** MVP - Basic Segmentation UI (COMPLETE)
- ✅ **Phase 2:** Interactive UI Enhancements (COMPLETE - 100%)
  - ✅ Dashboard page with document management
  - ✅ Viewer page with zone canvas and sidebar
  - ✅ Left navigation sidebar
  - ✅ Confidence threshold slider
  - ✅ Zone type filtering
  - ✅ Interactive hover highlighting
  - ✅ Pan and zoom controls
  - ✅ Export functionality (JSON, CSV)
  - ✅ Zone details modal
  - ✅ Keyboard shortcuts
- 📋 **Phase 3:** Exemplar Management (PLANNED)
- 🔮 **Phase 4:** LLM Integration (FUTURE)

**See [PLAN.md](PLAN.md) for detailed roadmap.**

---

## 🎯 What This Project Does

The SAM3 Drawing Zone Segmenter automatically analyzes engineering drawings and identifies:

- **Title blocks** - Project information, stamps, signatures
- **Plan views** - Floor plans, structural layouts
- **Elevations** - Building elevations, facades
- **Sections** - Cross-section drawings
- **Details** - Detailed callouts and connections
- **Schedules** - Door/window/finish schedules
- **Notes areas** - Specifications and general notes
- **Legends** - Symbol explanations
- **Grid systems** - Reference grid lines
- **And more...** (10+ zone types supported)

**Key Features:**
- Multi-page document management
- Dashboard with upload and document library
- Interactive viewer with zone canvas
- Confidence threshold filtering (0-100%)
- Zone type filtering with checkboxes
- Bi-directional hover highlighting (list ↔ canvas)
- Zero-shot segmentation with text prompts
- GPU-accelerated inference (~2-4s per image)
- Visual zone overlay with bounding boxes
- Page type classification
- REST API with OpenAPI docs
- MIT-style licensed (commercial use permitted)

---

## 🏗️ Technical Architecture

### Stack
- **Backend:** FastAPI + SAM3 (Meta) + PyTorch + CUDA
- **Frontend:** Vite + React 18 + React Router + Zustand + Tailwind v4
- **Database:** SQLite (development) + localStorage (temporary)
- **Model:** Meta SAM3 (3.3GB, MIT-style license)
- **GPU:** NVIDIA RTX 3060 (12GB VRAM)

### UI Architecture
- **Dashboard Page** (`/`): Document list, upload zone, search
- **Viewer Page** (`/viewer/:docId`): Drawing canvas + zone sidebar
- **Left Navigation**: App-level routing (Dashboard, Viewer, Settings)
- **State Management**: Zustand with localStorage persistence
- **Canvas Rendering**: HTML5 Canvas for zone overlays
- **Routing**: React Router v6 with nested routes

### Key Components
- **SAM3 Processor:** Zero-shot segmentation with promptable concept detection
- **Zone Classifier:** Post-processing and page type classification
- **Drawing Canvas:** HTML5 Canvas with pan/zoom and zone overlays
- **Zone Sidebar:** Filters (confidence, zone types) and scrollable zone list
- **REST API:** 11 endpoints for segmentation, health, exemplars

---

## 📖 Documentation Structure

```
docs/
├── PLAN.md                           # Development roadmap (updated frequently)
├── README.md                         # This file - documentation index
└── reference/                        # Technical reference docs
    ├── MVP_QUICKSTART.md             # How to run the application
    ├── UI_ARCHITECTURE.md            # Frontend architecture guide
    ├── PHASE2_COMPLETION_SUMMARY.md  # Phase 2 completion report
    └── TESTING.md                    # Testing procedures and expected outputs
```

**Note:** All Phase 0-2 implementation is complete. Phase 3 (Exemplar Management) and Phase 4 (LLM Integration) are planned for future development.

---

## 🧪 Testing

### Quick Tests
```bash
# Basic import test (no dependencies required)
python scripts/basic_import_test.py

# Comprehensive migration check
python scripts/check_migration.py

# Runtime functionality tests
python scripts/test_runtime.py

# Unit tests
pytest tests/ -v
```

### Test Coverage
- Backend API: ✅ Verified
- SAM3 Integration: ✅ Verified
- Frontend Dashboard: ✅ Functional
- Frontend Viewer: ✅ Functional
- Navigation Sidebar: ✅ Functional
- GPU Support: ✅ Working (RTX 3060)

See [reference/TESTING.md](reference/TESTING.md) for comprehensive testing procedures.

---

## 🔧 Development Workflow

### Current Status
**Phase 2 Complete!** All interactive UI enhancements delivered:
- ✅ Multi-page architecture (Dashboard + Viewer)
- ✅ Left navigation sidebar
- ✅ Confidence threshold slider
- ✅ Zone type filtering
- ✅ Interactive hover highlighting
- ✅ Pan/zoom controls
- ✅ Export (JSON, CSV)
- ✅ Zone details modal
- ✅ Keyboard shortcuts

See [PHASE2_COMPLETION_SUMMARY.md](reference/PHASE2_COMPLETION_SUMMARY.md) for details.

### Typical Workflow
1. Check [PLAN.md](PLAN.md) for current tasks
2. Start backend and frontend servers
3. Make changes (hot reload enabled)
4. Test with real engineering drawings
5. Run tests before committing

### Running Servers
```bash
# Terminal 1 - Backend
source .venv/bin/activate
uvicorn src.sam3_segmenter.main:app --reload --port 8001

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Access at: http://localhost:3007

---

## 📦 External Resources

- **[Meta SAM3 Repository](https://github.com/facebookresearch/sam3)** - Official SAM3 implementation
- **[SAM3 License](https://github.com/facebookresearch/sam3/blob/main/LICENSE)** - MIT-style license
- **[SAM3 on Hugging Face](https://huggingface.co/facebook/sam3)** - Model downloads
- **[SAM3 Paper](https://arxiv.org/abs/2511.16719)** - Research publication
- **[Project CLAUDE.md](../CLAUDE.md)** - Developer guidelines

---

## 🎯 Key Links Summary

**Want to...** | **Read this:**
--- | ---
Run the application | [reference/MVP_QUICKSTART.md](reference/MVP_QUICKSTART.md)
See what's planned | [PLAN.md](PLAN.md)
See Phase 2 completion | [reference/PHASE2_COMPLETION_SUMMARY.md](reference/PHASE2_COMPLETION_SUMMARY.md)
Understand UI structure | [reference/UI_ARCHITECTURE.md](reference/UI_ARCHITECTURE.md)
Run tests | [reference/TESTING.md](reference/TESTING.md)
Understand the codebase | [../CLAUDE.md](../CLAUDE.md)
Deploy to production | [reference/MVP_QUICKSTART.md](reference/MVP_QUICKSTART.md)

---

## 📞 Support

For issues or questions:
1. Check [reference/MVP_QUICKSTART.md](reference/MVP_QUICKSTART.md) troubleshooting section
2. Review [reference/TESTING.md](reference/TESTING.md)
3. Check backend logs and error messages
4. Verify GPU availability: `nvidia-smi`

---

**Version:** 2.0 (Phase 2 - Dashboard + Viewer)
**License:** MIT-style (commercial use permitted)
**GPU Required:** NVIDIA with CUDA 12.1+
