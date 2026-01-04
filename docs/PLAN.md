# SAM3 Drawing Zone Segmenter - Development Plan

**Last Updated:** 2026-01-04 (Session 2)
**Current Phase:** Phase 2.5 - Playground SAM3 Input Modes
**Status:** 🔄 IN PROGRESS (60% Complete)

### Quick Summary
✅ **Completed Today:** Point Prompts, Bounding Box (single/multi), Mask Prompts, Auto-run Inference
🔄 **In Progress:** Combined Mode validation
📋 **Next:** Visual Exemplars (Phase 3)

---

## 🎯 Product Vision

An interactive web application for automatically segmenting engineering drawings into semantic zones using Meta's SAM3 model, with visual exemplar-based refinement and LLM-assisted zone classification.

**Target Users:** Engineers, architects, construction managers analyzing structural drawings, MEP plans, and construction documents.

---

## 📊 Overall Progress

```
Phase 0: SAM3 Migration        ████████████████████ 100% ✅
Phase 1: MVP                   ████████████████████ 100% ✅
Phase 2: Interactive UI        ████████████████████ 100% ✅
Phase 2.5: Playground Modes    ████████████░░░░░░░░  60% 🔄
Phase 3: Exemplar Management   ░░░░░░░░░░░░░░░░░░░░   0% 📋
Phase 4: LLM Integration       ░░░░░░░░░░░░░░░░░░░░   0% 🔮
```

---

## 🗓️ Development Phases

### Phase 0: License Compliance & SAM3 Migration ✅ COMPLETE
**Duration:** 2026-01-03
**Status:** Production Ready

- [x] Migrate from Ultralytics (AGPL) to Meta SAM3 (MIT-style)
- [x] Update dependencies and package metadata
- [x] Comprehensive testing and verification
- [x] Documentation completion

**📄 Details:** [FINAL_VERIFICATION_REPORT.md](FINAL_VERIFICATION_REPORT.md)

---

### Phase 1: MVP - Basic Segmentation UI ✅ COMPLETE
**Duration:** 2026-01-03
**Status:** Functional MVP Deployed

- [x] FastAPI backend with SAM3 integration
- [x] Next.js frontend with image upload
- [x] Basic zone detection and listing
- [x] Visual zone overlay with bounding boxes
- [x] Page type classification
- [x] Health status indicators

**📄 Details:** [MVP_QUICKSTART.md](MVP_QUICKSTART.md)

**🎨 Features Delivered:**
- Upload engineering drawings (PNG/JPEG)
- Automatic segmentation into 10+ zone types
- Color-coded zone visualization
- Confidence scores per zone
- GPU-accelerated inference (~2-4s per image)

---

### Phase 2: Interactive UI Enhancements ✅ COMPLETE (100%)
**Duration:** 2026-01-03 to 2026-01-04
**Completion Date:** 2026-01-04
**Priority:** HIGH

#### Architecture Refactor ✅ COMPLETE
- [x] **Multi-page Application**
  - Dashboard page with document library
  - Viewer page with drawing canvas
  - React Router for navigation
  - Vite build system (replaced Next.js)

- [x] **State Management**
  - Zustand store with persistence
  - Document management (upload, delete)
  - UI state (sidebar, search, filters)

- [x] **Left Navigation Sidebar**
  - Collapsible navigation (Dashboard, Viewer, Settings)
  - Document counter
  - Smooth transitions

#### Session 1: Core Interactivity ✅ COMPLETE
- [x] **Confidence Threshold Slider**
  - Live filtering (0-100% range)
  - Real-time zone count update
  - Visual feedback on canvas

- [x] **Zone Type Filtering**
  - Checkbox group for each zone type
  - "Select All" / "Deselect All" toggles
  - Show/hide specific zone types on visualization

- [x] **Interactive Highlighting**
  - Hover on list item → highlight zone on image
  - Click zone on canvas → highlight in list
  - Auto-scroll to selected zone
  - Bi-directional state synchronization

- [x] **Pan and Zoom Controls**
  - Zoom in/out buttons + scroll wheel
  - Pan via drag gesture
  - Fit to page button

#### Session 2: Export & Details ✅ COMPLETE
- [x] **Export Results**
  - JSON export (full metadata with options)
  - CSV export (tabular format with proper escaping)
  - Export options (toggle confidence/coordinates)

- [x] **Zone Details Modal**
  - Click zone → show detailed information
  - Full metadata display (type, ID, confidence)
  - Bounding box coordinates (pixels)
  - Dimensions (width, height, area)
  - Normalized coordinates (0-1 scale)
  - Center point calculation

#### Session 2.5: Keyboard Shortcuts ✅ COMPLETE (Bonus Feature)
- [x] **Arrow Left/Right** - Navigate between pages
- [x] **Escape** - Deselect zone / close modals
- [x] **+/=** - Zoom in (multiplicative 1.2x)
- [x] **-** - Zoom out (÷1.2)
- [x] Cross-platform support (Mac Cmd = Ctrl)
- [x] Input field detection (shortcuts don't fire while typing)

#### Deferred Features (Not in Phase 2)
- **Multi-page PDF Support** - Requires backend implementation
- **PNG export with annotations** - Requires canvas rendering work
- **Batch Processing UI** - Validate demand first

**📄 Details:** [reference/UI_ARCHITECTURE.md](reference/UI_ARCHITECTURE.md)
**📄 Completion Summary:** [reference/PHASE2_COMPLETION_SUMMARY.md](reference/PHASE2_COMPLETION_SUMMARY.md)

---

### Phase 2.5: Playground SAM3 Input Modes 🔄 IN PROGRESS
**Start Date:** 2026-01-04
**Priority:** HIGH

The Playground page enables experimentation with all 6 SAM3 input modalities. Unlike the Viewer (which uses pre-configured prompts), the Playground allows direct interaction with SAM3's full API surface.

#### SAM3 Input Types Overview

SAM3 supports two paradigms:
- **PCS (Promptable Concept Segmentation)**: Text and visual exemplar prompts for finding concepts
- **PVS (Promptable Visual Segmentation)**: Points and boxes for instance-specific segmentation

| # | Input Type | Paradigm | Status | Description |
|---|------------|----------|--------|-------------|
| 1 | Text Prompts | PCS | ✅ Complete | Natural language descriptions ("title block", "schedule table") |
| 2 | Point Prompts | PVS | ✅ Complete | Click positive/negative points on the image |
| 3 | Bounding Box | PVS | ✅ Complete | Draw rectangle with single/multi box mode |
| 4 | Mask Prompts | PVS | ✅ Complete | Use previous mask as input for refinement |
| 5 | Visual Exemplars | PCS | ⏳ Planned | Crop regions as visual examples for concept matching |
| 6 | Combined/Multi-modal | Both | ⏳ Planned | Multiple modalities in single inference |

#### Input Type 1: Text Prompts ✅ COMPLETE

**API Method:** `processor.set_text_prompt(prompt, state)`

**Frontend Implementation:**
- [x] Text input field with submit button
- [x] Enter key submission
- [x] Multi-prompt support (comma-separated)
- [x] Results display in floating sidebar
- [x] Confidence threshold slider

**Backend Implementation:**
- [x] `/segment` endpoint accepts `prompts` array
- [x] SAM3 processor text encoding
- [x] Zone detection and confidence scoring

---

#### Input Type 2: Point Prompts ✅ COMPLETE

**API Method:** `predictor.predict(point_coords=[[x,y]], point_labels=[1])`

**Concept:** User clicks on the image to add positive points (include this) or negative points (exclude this). SAM3 generates a mask covering the positive points while avoiding negative points.

**Frontend Implementation:**
- [x] Click handler on canvas for point placement (PlaygroundCanvas)
- [x] Visual point markers (green=positive, red=negative) via PointOverlay
- [x] Mode toggle: Positive (+) / Negative (-)
- [x] Point list in sidebar with delete buttons
- [x] Clear all points button
- [x] Auto-run inference (opt-in toggle with 500ms debounce)

**Backend Implementation:**
- [x] Endpoint `/segment/interactive` accepts points
- [x] Accept `points: [{x, y, label}, ...]`
- [x] Return multiple mask candidates with IoU scores
- [x] Mask selection UI with "Use as Mask Input" for refinement

**Key Files:**
- `frontend/src/components/playground/PointOverlay.tsx` - SVG overlay
- `frontend/src/components/playground/PlaygroundCanvas.tsx` - Click handling
- `src/sam3_segmenter/main.py` - `/segment/interactive` endpoint

---

#### Input Type 3: Bounding Box ✅ COMPLETE

**API Method:** `predictor.predict(box=[x1,y1,x2,y2])`

**Concept:** User draws a rectangle to specify a region. SAM3 segments the primary object within that box.

**Frontend Implementation:**
- [x] Mouse drag to draw rectangle overlay (BoxOverlay)
- [x] Visual preview during drag (dashed line)
- [x] Solid rectangle after completion with corner handles
- [x] Single box mode (replace on new draw)
- [x] Multi-box mode toggle (accumulate boxes)
- [x] Delete individual boxes (click to remove)
- [x] Auto-run inference (opt-in toggle with 500ms debounce)

**Backend Implementation:**
- [x] `/segment/interactive` accepts `box: [x1, y1, x2, y2]`
- [x] Return multiple mask candidates with IoU scores
- [x] Mask selection UI with "Use as Mask Input" for refinement

**Key Files:**
- `frontend/src/components/playground/BoxOverlay.tsx` - SVG overlay
- `frontend/src/components/playground/PlaygroundCanvas.tsx` - Drag handling
- `frontend/src/pages/Playground.tsx` - Box mode state (single/multi)

---

#### Input Type 4: Mask Prompts ✅ COMPLETE

**API Method:** `predictor.predict(mask_input=previous_mask)`

**Concept:** Feed a previous mask back to SAM3 for refinement. Enables iterative refinement workflows.

**Frontend Implementation:**
- [x] "Use as Mask Input for Refinement" button on mask candidates
- [x] Mask input indicator (amber) when active with "Clear" button
- [x] Mask visualization via MaskOverlay component
- [x] Combine with additional points or boxes for refinement

**Backend Implementation:**
- [x] Accept `mask_input_base64` in InteractiveSegmentRequest
- [x] Decode to binary mask with shape [1, H, W]
- [x] Pass to SAM3 predictor for refinement
- [x] Works with points and/or box prompts

**Key Files:**
- `frontend/src/pages/Playground.tsx` - maskInputBase64 state, handleUseMaskAsInput
- `frontend/src/api/client.ts` - segmentInteractive with maskInput option
- `src/sam3_segmenter/models.py` - mask_input_base64 field
- `src/sam3_segmenter/main.py` - Mask decoding and passing to segmenter

---

#### Input Type 5: Visual Exemplars ⏳ PLANNED

**API Method:** Visual exemplar → backbone → `visual_prompt_embed`

**Concept:** User selects a region of the image as an exemplar. SAM3 finds all similar regions (concept-based matching via PCS).

**Frontend Implementation:**
- [ ] Draw box to select exemplar region
- [ ] Exemplar preview thumbnail
- [ ] Multiple exemplar support
- [ ] Exemplar library (save/load from DB)
- [ ] Zone type association

**Backend Implementation:**
- [ ] `/exemplars/create-from-crop` endpoint
- [ ] Image backbone feature extraction
- [ ] Exemplar storage in database
- [ ] Integration with segment workflow

**UI Controls:**
```
┌─────────────────────────────────┐
│ Visual Exemplars                │
├─────────────────────────────────┤
│ Select a region to use as an   │
│ exemplar for finding similar   │
│ regions in the image.          │
│                                 │
│ Active Exemplars (2):          │
│ ┌────┐ ┌────┐                  │
│ │ 🖼️ │ │ 🖼️ │   [+ Add More]    │
│ └────┘ └────┘                  │
│ title   detail                 │
│                                 │
│ [Clear All]    [Find Similar]  │
└─────────────────────────────────┘
```

---

#### Input Type 6: Combined/Multi-modal ⏳ PLANNED

**API Method:** Chain multiple `add_*_prompt()` calls before inference

**Concept:** Combine multiple input types in a single inference pass for maximum precision.

**Frontend Implementation:**
- [ ] Multi-mode panel (toggle each input type on/off)
- [ ] Combined prompt preview
- [ ] Weight/priority sliders per modality (if supported)
- [ ] Clear all button

**Backend Implementation:**
- [ ] Accept multiple prompt types in single request
- [ ] Proper state management between prompts
- [ ] Priority ordering if needed

**Example Combined Request:**
```json
{
  "prompts": ["title block"],
  "boxes": [[100, 50, 400, 200]],
  "points": [[250, 125]],
  "point_labels": [1]
}
```

---

#### Implementation Priority

**Phase 2.5.1:** Text Prompts ✅ COMPLETE
**Phase 2.5.2:** Point Prompts + Bounding Box ✅ COMPLETE
**Phase 2.5.3:** Mask Prompts ✅ COMPLETE
**Phase 2.5.4:** Visual Exemplars (deferred to Phase 3)
**Phase 2.5.5:** Combined Mode (needs SAM3 API validation)

#### Playground UI Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ MinimalTopBar: "Playground" | [Upload Image] [Clear]            │
├───────────────────────────────────────────────────┬─────────────┤
│                                                   │ Input Mode  │
│                                                   │ ┌─────────┐ │
│                                                   │ │📝 Text  │ │
│                                                   │ │📍 Points│ │
│             Drawing Canvas                        │ │⬜ Box   │ │
│          (Same as Viewer: zoom/pan)               │ │🎭 Mask  │ │
│                                                   │ │🖼️ Exemp │ │
│                                                   │ │🔀 Multi │ │
│                                                   │ └─────────┘ │
│                                                   │             │
│                                                   │ [Controls]  │
│                                                   │             │
│                                                   │ Results (5) │
│                                                   │ ├─ zone_1   │
│                                                   │ ├─ zone_2   │
│                                                   │ └─ ...      │
└───────────────────────────────────────────────────┴─────────────┘
```

#### Success Criteria (Phase 2.5)

- [x] 4 of 6 input types functional in Playground (Text, Points, Box, Mask)
- [x] Unified results display for all input types (mask candidates with IoU scores)
- [ ] Consistent keyboard shortcuts across modes (partial)
- [x] Backend accepts all prompt combinations via `/segment/interactive`
- [x] Performance: <500ms for point/box inference
- [ ] Mobile-responsive controls (not tested)

**📄 Details:** [reference/PLAYGROUND_SPEC.md](reference/PLAYGROUND_SPEC.md) *(to be created)*

---

### Phase 3: Exemplar Management UI 📋 PLANNED
**Start Date:** TBD (after Phase 2)
**Priority:** MEDIUM

- [ ] Exemplar upload interface
- [ ] Zone type tagging system
- [ ] Exemplar library viewer
- [ ] Re-run segmentation with exemplars
- [ ] Accuracy comparison (with/without exemplars)
- [ ] Exemplar management CRUD operations

**📄 Details:** [EXEMPLAR_MANAGEMENT_SPEC.md](EXEMPLAR_MANAGEMENT_SPEC.md) *(to be created)*

**🎯 Success Criteria:**
- Upload exemplar images per zone type
- Store exemplars in database
- Use exemplars to improve SAM3 accuracy
- Measure accuracy delta (before/after exemplars)

---

### Phase 4: LLM Agent Integration 🔮 FUTURE
**Start Date:** TBD
**Priority:** LOW

- [ ] LLM-based zone classification refinement
- [ ] Natural language query interface
- [ ] Intelligent zone merging/splitting
- [ ] Drawing content analysis (text extraction)
- [ ] Automated report generation

**📄 Details:** [LLM_INTEGRATION_SPEC.md](LLM_INTEGRATION_SPEC.md) *(to be created)*

---

## 🎯 Current Focus

### Active Work
**Phase 2.5: Playground SAM3 Input Modes** - 🔄 IN PROGRESS (60%)

### Current Tasks (Phase 2.5)
1. ✅ Text Prompts - Complete and functional
2. ✅ Point Prompts - Canvas click handler, positive/negative mode, auto-run
3. ✅ Bounding Box - Rectangle drawing with single/multi box mode, auto-run
4. ✅ Mask Prompts - Feed previous mask for refinement
5. 📋 Visual Exemplars - Select regions as exemplars (deferred to Phase 3)
6. 📋 Combined Mode - Multiple input types in one pass (needs SAM3 validation)

### Completed (Phase 2)
1. ✅ Complete UI architecture refactor (Dashboard + Viewer + Left Nav)
2. ✅ Confidence threshold slider with live filtering
3. ✅ Zone type filter checkboxes with Select All/Deselect All
4. ✅ Bi-directional hover highlighting (list ↔ canvas)
5. ✅ Pan and zoom controls
6. ✅ Export functionality (JSON, CSV with options)
7. ✅ Zone details modal (comprehensive metadata)
8. ✅ Keyboard shortcuts (navigation, zoom, deselect)

### Next Steps (Prioritized)

#### Immediate (Phase 2.5 Completion)
1. [ ] **Combined Mode** - Test if SAM3 supports multiple prompt types in single inference
   - Validate PCS + PVS can be combined
   - If supported, add UI for multi-modal prompts
   - If not, document limitation

#### Short-term (Phase 3)
2. [ ] **Visual Exemplars** - Crop regions as visual examples
   - Draw box to select exemplar region
   - Exemplar preview thumbnails
   - Backend feature extraction endpoint
3. [ ] **Exemplar Library** - Persist and manage exemplars
   - Database storage for exemplar embeddings
   - Zone type association
   - Accuracy comparison UI

#### Medium-term (Phase 4)
4. [ ] **LLM Integration** - AI-assisted zone classification
   - Natural language query interface
   - Zone merging/splitting suggestions
   - Drawing content analysis

### Technical Debt / Deferred
- Backend document management endpoints (currently using localStorage mock)
- Multi-page PDF support (requires backend PDF extraction)
- PNG export with annotations (requires additional canvas work)
- Batch processing UI (validate demand first)
- Keyboard shortcuts for Playground modes (P for positive/negative, B for box)
- Mobile-responsive controls

---

## 📐 Technical Architecture

### Current Stack
- **Backend:** FastAPI + SAM3 (Meta) + PyTorch + CUDA
- **Frontend:** Vite + React 18 + React Router v6 + Zustand + Tailwind v4
- **Database:** SQLite (development) + localStorage (temporary)
- **Deployment:** Docker + NVIDIA Container Toolkit

### Key Technologies
- **SAM3:** Zero-shot segmentation with text prompts
- **GPU:** NVIDIA RTX 3060 (12GB VRAM)
- **License:** MIT-style (commercial use permitted)
- **Canvas Rendering:** HTML5 Canvas for zone overlays
- **State Management:** Zustand with persistence

### UI Architecture
- **Dashboard** (`/`): Document library with upload and search
- **Viewer** (`/viewer/:docId`): Drawing canvas + zone sidebar
- **Left Navigation**: App-level routing sidebar
- **State Persistence:** localStorage for documents (temporary)

**📄 Full Details:** [reference/UI_ARCHITECTURE.md](reference/UI_ARCHITECTURE.md)

---

## 🧪 Testing Strategy

### Current Coverage
- ✅ Unit tests (pytest)
- ✅ API integration tests
- ✅ End-to-end segmentation tests
- ✅ GPU/CPU compatibility tests
- ⏳ UI component tests (to be added in Phase 2)
- ⏳ Performance benchmarks (to be added in Phase 2)

### Test Metrics
- Backend: 85%+ coverage target
- Frontend: 70%+ coverage target (after Phase 2)

---

## 📈 Performance Targets

### Current Performance (MVP)
- **Model Load:** ~10s (cold start)
- **Segmentation:** 2-4s per image (GPU)
- **Zone Detection:** 15-30 zones per drawing
- **API Response:** <50ms overhead

### Phase 2 Targets
- **Client-side Filtering:** <100ms (confidence/type)
- **Hover Latency:** <16ms (60 FPS)
- **Export Generation:** <2s (JSON/CSV/PNG)

---

## 📚 Reference Documents

### User Guides
- [reference/MVP_QUICKSTART.md](reference/MVP_QUICKSTART.md) - How to run the application
- [reference/UI_ARCHITECTURE.md](reference/UI_ARCHITECTURE.md) - Frontend architecture guide
- [reference/PHASE2_COMPLETION_SUMMARY.md](reference/PHASE2_COMPLETION_SUMMARY.md) - Phase 2 completion report

### Testing
- [reference/TESTING.md](reference/TESTING.md) - Testing procedures and expected outputs

### API Documentation
- [../CLAUDE.md](../CLAUDE.md) - Developer guidelines
- OpenAPI Spec: `http://localhost:8001/docs`

---

## 🔄 Change Log

### 2026-01-04 (Phase 2.5 Continued - 60% Complete)
- ✅ Point Prompts implemented with PointOverlay component
- ✅ Bounding Box implemented with BoxOverlay component
- ✅ Single/Multi box mode toggle
- ✅ Auto-run inference (opt-in with 500ms debounce)
- ✅ Mask Prompts implemented (use previous mask for refinement)
- ✅ PlaygroundCanvas wrapper for interactive modes
- ✅ Mask selection UI with IoU scores and "Use as Mask Input" button
- ✅ Backend `/segment/interactive` endpoint with mask_input support
- 📄 Updated PLAN.md with completion status

### 2026-01-04 (Phase 2.5 Started)
- 🔄 Started Phase 2.5: Playground SAM3 Input Modes
- ✅ Text Prompts implemented in Playground
- 📄 Documented all 6 SAM3 input types with API methods and UI specs
- 📄 Created comprehensive implementation plan for each input type
- 🗂️ Playground page redesigned to mirror Viewer layout

### 2026-01-04 (Phase 2 Completion)
- ✅ Complete UI architecture refactor (Dashboard + Viewer)
- ✅ Migrated from Next.js to Vite
- ✅ Implemented React Router v6 multi-page architecture
- ✅ Added Zustand state management with persistence
- ✅ Built left navigation sidebar
- ✅ Implemented confidence threshold slider
- ✅ Implemented zone type filtering with checkboxes
- ✅ Implemented bi-directional hover highlighting
- ✅ Added pan/zoom controls
- ✅ **Implemented export functionality (JSON, CSV with options)**
- ✅ **Implemented zone details modal (comprehensive metadata)**
- ✅ **Implemented keyboard shortcuts (navigation, zoom, deselect)**
- 📄 Created PHASE2_COMPLETION_SUMMARY.md
- 📄 Reorganized documentation (moved detailed docs to reference/)
- 📄 Updated README.md and PLAN.md to reflect completion
- 🗂️ Deleted obsolete UI enhancement planning docs

### 2026-01-03
- ✅ Completed Phase 0 (SAM3 Migration)
- ✅ Completed Phase 1 (MVP)
- ✅ Added visual zone overlay with bounding boxes
- 🔄 Started Phase 2 planning
- 📄 Created PLAN.md

---

## 🎓 Lessons Learned

### Phase 0 & 1
1. **SAM3 API complexity** - Required careful study of Meta's processor API
2. **CORS configuration** - .env file takes precedence over code defaults
3. **Canvas rendering** - Better UX than static image + CSS overlays
4. **React Query** - Excellent for API state management

### Phase 2
1. **Vite vs Next.js** - Vite offers faster HMR and simpler config for SPAs
2. **Zustand vs Redux** - Lightweight state management perfect for this scale
3. **HTML5 Canvas performance** - Much faster than SVG for 100+ zones
4. **localStorage limitations** - Works for prototyping, need backend persistence
5. **Bi-directional sync** - useEffect + scrollIntoView elegant for list↔canvas
6. **React Router Layout pattern** - Clean separation of app shell from pages
7. **CSV escaping is non-trivial** - Must handle quotes, commas, newlines with double-quote escaping
8. **Cross-platform keyboard support** - Mac Cmd vs Ctrl, platform detection required
9. **Keyboard shortcut conflicts** - Must check for input focus and avoid browser defaults
10. **Modal UX consistency** - Escape key should close all modals uniformly
11. **TypeScript strict mode catches bugs** - Unused parameters, null checks prevent runtime errors

### Phase 2.5
1. **Wrapper component pattern** - PlaygroundCanvas wraps DrawingCanvas to avoid regressions in Viewer
2. **SVG overlays for prompts** - PointOverlay/BoxOverlay use SVG with viewBox matching image dimensions
3. **Coordinate transformation** - screenToImageCoords utility handles zoom/pan → image space conversion
4. **Debounced auto-run** - 500ms delay with useRef for timeout prevents excessive API calls
5. **Opt-in features** - Auto-run toggle lets users choose between manual and real-time inference
6. **SAM3 mask format** - Expects `[1, H, W]` shape with float32, decoded from PNG grayscale
7. **IoU scoring** - Multiple mask candidates sorted by IoU gives users choice of precision levels
8. **Iterative refinement** - Mask input enables progressive refinement workflow (segment → refine → refine)
9. **Single vs Multi mode** - Box mode toggle addresses different use cases (quick single vs accumulative)

---

## 🚀 Success Metrics

### MVP Acceptance Criteria ✅
- [x] Successfully segment engineering drawings
- [x] Detect 10+ zone types
- [x] Page type classification accuracy >70%
- [x] GPU processing time <5s per image
- [x] Zero CORS/connectivity errors

### Phase 2 Acceptance Criteria ✅
- [x] Multi-page architecture (Dashboard + Viewer)
- [x] Left navigation sidebar with collapse/expand
- [x] Confidence slider functional and responsive (0-100%)
- [x] Zone filtering works for all 10+ types
- [x] Hover highlighting smooth (<16ms latency)
- [x] Bi-directional sync (list ↔ canvas)
- [x] Pan and zoom controls functional
- [x] Export features generate valid files (JSON, CSV)
- [x] Zone details modal with comprehensive metadata
- [x] Keyboard shortcuts for navigation and zoom

**Deferred (Not Phase 2 Requirements)**:
- Multi-page PDF support (requires backend)
- PNG export with annotations (requires additional canvas work)

### Phase 2.5 Acceptance Criteria 🔄 (60% Complete)
- [x] Text Prompts functional with confidence slider
- [x] Point Prompts with positive/negative toggle
- [x] Bounding Box with single/multi mode
- [x] Mask Prompts for iterative refinement
- [x] Mask candidates with IoU score selection
- [x] Auto-run inference with debounce (opt-in)
- [x] Backend `/segment/interactive` endpoint
- [ ] Visual Exemplars (deferred to Phase 3)
- [ ] Combined Mode (needs SAM3 validation)
- [ ] Keyboard shortcuts for Playground modes

---

**📧 Questions or Feedback?** Update this plan as the project evolves.

**🔗 Quick Commands:**
```bash
# View plan
cat docs/PLAN.md

# Update plan
nano docs/PLAN.md
```
