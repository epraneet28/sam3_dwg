# SAM3 Drawing Segmenter - Quick Start Guide

**Last Updated:** 2026-01-04
**Version:** 2.0 (Phase 2 - Dashboard + Viewer)

---

## Prerequisites

- **Python 3.10+** with virtual environment
- **Node.js 18+** and npm
- **CUDA 12.1+** (for GPU support)
- **SAM3 model** downloaded to `models/sam3.pt`
- **Engineering drawings** (PNG, JPEG, or PDF)

---

## Starting the Application

### 1. Start Backend Server

```bash
# From project root (/home/erusuadmin/sam3_dwg)
source .venv/bin/activate
uvicorn src.sam3_segmenter.main:app --reload --port 8001
```

**Expected output**:
```
INFO:     Started server process [PID]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Verify backend is running**:
```bash
curl http://localhost:8001/health
```

Should return:
```json
{
  "status": "healthy",
  "model": "sam3",
  "model_loaded": true,
  "gpu_available": true,
  "gpu_name": "NVIDIA GeForce RTX 3060",
  "gpu_memory_used_mb": 4523
}
```

### 2. Start Frontend Server

```bash
# From frontend directory
cd frontend
npm run dev
```

**Expected output**:
```
VITE v6.4.1  ready in 173 ms

➜  Local:   http://localhost:3007/
➜  Network: use --host to expose
```

### 3. Access the Application

Open your browser to: **http://localhost:3007**

You should see the SAM3 Dashboard with:
- Left navigation sidebar (Dashboard, Viewer, Settings)
- Upload zone in the center
- Empty document library

---

## Using the Application

### Dashboard Page

The Dashboard is your document library and upload center.

#### 1. Upload a Drawing

**Option A: Drag and Drop**
1. Drag an engineering drawing file onto the upload zone
2. Drop to upload
3. File is validated (PDF, PNG, or JPEG; max 50MB)

**Option B: Click to Select**
1. Click the upload zone
2. Select a file from your computer
3. File is automatically validated

**What Happens Next:**
- Document is uploaded and stored
- Automatic segmentation begins (2-4 seconds)
- You're automatically navigated to the Viewer
- Results appear on the canvas with colored zone overlays

#### 2. Browse Documents

The document grid shows all uploaded drawings:
- **Thumbnail**: First page preview
- **Name**: Original filename
- **Metadata**: Page count, zone count
- **Status Badge**:
  - 🟢 **segmented** - Ready to view
  - 🟡 **pending** - Processing
  - 🔴 **error** - Failed (hover for details)

**Click any document card** to open it in the Viewer.

#### 3. Search Documents

Use the search bar to filter by filename:
```
Search drawings... 🔍
```

#### 4. Delete Documents

Click the trash icon on any document card:
- Confirmation dialog appears
- Document and zones are deleted
- Card removed from library

---

### Viewer Page

The Viewer displays your drawing with interactive zone overlays.

#### Layout Overview

```
┌─────────────────────────────────────────────────────────┐
│ ← Back  │  Document Name  │  1 page • 28 zones         │ ← Top Bar
├─────────────────────────────────────────────────────────┤
│                                                 ┌───────┐│
│                                                 │       ││
│      Drawing Canvas                             │ Zone  ││ ← Main Content
│      (with colored zone overlays)               │ Side  ││
│                                                 │ bar   ││
│      Controls: Scroll=zoom, Drag=pan            │       ││
└─────────────────────────────────────────────────┴───────┘│
```

#### Top Bar

- **Back Button** (←): Return to Dashboard
- **Document Name**: Current drawing filename
- **Metadata**: Page count, zone count
- **Page Type**: Detected type (plan, elevation, section, etc.)
- **Processing Time**: Segmentation duration (ms)

#### Drawing Canvas

**Features:**
- Colored bounding boxes for each zone
- Semi-transparent fill (20% opacity)
- Labels on selected/hovered zones
- Click zone to select (highlights in sidebar)
- Hover zone to preview (highlights in sidebar)

**Controls:**
- **Scroll wheel**: Zoom in/out
- **Drag**: Pan image
- **Click zone**: Select and auto-scroll in sidebar

**Hint** (bottom-left corner):
```
Scroll to zoom • Drag to pan • Click zone to select
```

#### Zone Sidebar (Right)

**Zone Filters Section:**

1. **Confidence Threshold Slider**
   - Range: 0% - 100%
   - Real-time filtering
   - Shows: "30%" (current threshold)
   - Only zones with confidence ≥ threshold are shown

2. **Zone Type Checkboxes**
   - 10+ zone types with color indicators
   - Shows count per type (e.g., "plan view (5)")
   - **Select All** / **Deselect All** buttons
   - Toggle visibility per type

**Zone List Section:**

- Scrollable list of all filtered zones
- Each zone shows:
  - Color dot (zone type indicator)
  - Zone type label (e.g., "PLAN VIEW")
  - Confidence percentage (e.g., "66.4%")
  - Dimensions (e.g., "816 × 1132 px")
- **Click zone** → Highlights on canvas + auto-scrolls
- **Hover zone** → Highlights on canvas
- **Selected zone**: Blue ring + highlighted background

---

## Example Workflow

### Scenario: Analyzing a Multi-Sheet Construction Drawing

```
1. Open Dashboard (http://localhost:3007)

2. Upload architectural plan:
   - Drag "floor-plan-A101.png" onto upload zone
   - Auto-upload begins

3. Auto-segmentation (2-3 seconds):
   - Backend processes drawing
   - Detects 28 zones
   - Classifies as "plan" type

4. Auto-navigate to Viewer:
   - Drawing displayed on canvas
   - 28 colored zone overlays visible
   - Sidebar shows all zones

5. Explore results:
   - Adjust confidence slider to 30%
   - 28 zones → 14 zones (filtered)
   - Deselect "unknown" checkbox → 14 zones remain

6. Inspect specific zone:
   - Click "REVISION BLOCK" in sidebar
   - Canvas highlights zone with thick border
   - Label appears: "REVISION BLOCK (64.4%)"
   - Sidebar auto-scrolls to selected zone

7. Pan and zoom:
   - Scroll to zoom into title block
   - Drag to pan around drawing
   - Click "Fit to Page" to reset

8. Return to Dashboard:
   - Click "← Back to Dashboard"
   - Document appears in library with thumbnail
   - Status: "segmented" (green badge)
```

---

## Supported Zone Types

The system detects 10+ engineering drawing zones:

| Zone Type | Description | Color | Typical Location |
|-----------|-------------|-------|------------------|
| **title_block** | Project info, stamps, signatures | 🟢 Green | Bottom right |
| **revision_block** | Revision history table | 🟣 Purple | Top/bottom right |
| **plan_view** | Floor plans, site plans | 🔵 Blue | Center |
| **elevation_view** | Building elevations | 🟠 Orange | Center |
| **section_view** | Cross-section drawings | 🔴 Red | Center |
| **detail_view** | Detailed callouts | 🟡 Amber | Variable |
| **schedule_table** | Door/window/finish schedules | 🩷 Pink | Sides/bottom |
| **notes_area** | General notes, specs | 🩵 Cyan | Left/right |
| **legend** | Symbol legends | 🟣 Violet | Variable |
| **grid_system** | Reference grid lines | 🔷 Teal | Overlaid |
| **unknown** | Unclassified zones | ⚫ Gray | Variable |

---

## Troubleshooting

### Backend Issues

**Port 8001 already in use:**
```bash
# Find and kill existing process
lsof -ti:8001 | xargs kill -9

# Or use different port
uvicorn src.sam3_segmenter.main:app --reload --port 8002
```

**Model not loaded (503 error):**
1. Verify model exists: `ls -lh models/sam3.pt`
2. Download model: `python scripts/download_model.py`
3. Check backend logs for errors
4. Verify CUDA available: `nvidia-smi`

**GPU not detected:**
```bash
# Check CUDA
nvidia-smi

# Check PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"

# If false, reinstall PyTorch with CUDA support
```

**CORS errors:**
1. Check `.env` file has: `SAM3_CORS_ORIGINS=["http://localhost:3007"]`
2. Restart backend after changing .env
3. Clear browser cache

### Frontend Issues

**Port 3007 already in use:**
```bash
# Vite will auto-select next available port (3008, 3009, etc.)
# Or manually kill process
lsof -ti:3007 | xargs kill -9
```

**Cannot connect to backend:**
1. Verify backend running: `curl http://localhost:8001/health`
2. Check frontend `.env`: `VITE_API_URL=http://localhost:8001`
3. Open browser console (F12) → Check for errors
4. Look for CORS errors (red text)

**Upload fails:**
- Verify file is PNG, JPEG, or PDF
- Check file size < 50MB
- Try different image format
- Check browser console for error messages

**No zones detected:**
- Lower confidence threshold (slider to 0%)
- Use actual engineering drawing (not photo)
- Verify drawing has standard elements (title block, grid lines)
- Try different drawing
- Check backend logs for segmentation errors

**Zones not visible on canvas:**
1. Check confidence threshold (not set too high)
2. Verify zone type checkboxes (at least one selected)
3. Check zone count in sidebar ("Showing 0 zones" = filters too strict)
4. Click "Select All" to reset zone type filters
5. Move slider to 0% to reset confidence filter

**Sidebar not scrolling to selected zone:**
- This is a known minor issue
- Manually scroll to find zone
- Zone will have blue ring when selected

---

## API Testing (Without UI)

You can test the backend API directly using curl or Python:

### Python Example

```python
import base64
import requests

# Load and encode image
with open("path/to/drawing.png", "rb") as f:
    base64_image = base64.b64encode(f.read()).decode('utf-8')

# Send segmentation request
response = requests.post(
    "http://localhost:8001/segment/structural",
    json={
        "image_base64": base64_image,
        "return_masks": False,
        "return_crops": False,
        "classify_page_type": True
    },
    timeout=60
)

# Print results
result = response.json()
print(f"Page Type: {result['page_type']}")
print(f"Zones Detected: {len(result['zones'])}")
print(f"Processing Time: {result['processing_time_ms']}ms")

for zone in result['zones']:
    print(f"  - {zone['zone_type']}: {zone['confidence']:.1%}")
```

### curl Example

```bash
# Encode image to base64 (remove newlines)
BASE64=$(base64 -w 0 drawing.png)

# Send request
curl -X POST http://localhost:8001/segment/structural \
  -H "Content-Type: application/json" \
  -d "{
    \"image_base64\": \"$BASE64\",
    \"return_masks\": false,
    \"return_crops\": false,
    \"classify_page_type\": true
  }"
```

---

## Key Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Scroll** | Zoom in/out on canvas |
| **Drag** | Pan canvas |
| **Click zone** | Select zone |
| **Esc** | Deselect zone (planned) |
| **← / →** | Navigate pages (planned, multi-page) |
| **+** / **-** | Zoom in/out (planned) |

---

## Performance Metrics

**Expected performance on NVIDIA RTX 3060:**

| Metric | Target | Actual |
|--------|--------|--------|
| Model load time | < 30s | ~10s (cold start) |
| Single image segmentation | < 5s | 2-4s |
| Zone rendering | < 100ms | < 50ms |
| Hover highlighting | < 16ms | < 10ms (60 FPS) |
| Canvas pan/zoom | 60 FPS | 60 FPS |

---

## Differences from Phase 1 MVP

### Phase 1 (Old - Single Page):
- ❌ Single-page upload → segment → view workflow
- ❌ Manual "Segment Drawing" button
- ❌ Results lost on refresh
- ❌ No document library
- ❌ Next.js framework

### Phase 2 (New - Dashboard + Viewer):
- ✅ Multi-page application (Dashboard + Viewer)
- ✅ Auto-segment on upload
- ✅ Document persistence (localStorage)
- ✅ Document library with search
- ✅ Left navigation sidebar
- ✅ Vite build system (faster HMR)
- ✅ Zustand state management
- ✅ Confidence threshold slider
- ✅ Zone type filtering
- ✅ Bi-directional hover highlighting
- ✅ Pan/zoom controls

---

## Next Steps

### For Users

1. **Test with real engineering drawings**
   - Structural plans, MEP drawings, site plans
   - Note which zones are detected accurately
   - Note which are missed or misclassified

2. **Evaluate accuracy**
   - Do detected zones match actual drawing elements?
   - Are bounding boxes precise?
   - Is page type classification correct?

3. **Provide feedback**
   - Report issues in GitHub Issues
   - Suggest improvements
   - Share difficult drawings for testing

### For Developers

1. **Review architecture** - See [UI_ARCHITECTURE.md](UI_ARCHITECTURE.md)
2. **Implement backend persistence** - Replace localStorage with real document storage
3. **Add export functionality** - JSON, CSV, annotated PNG
4. **Add multi-page PDF support** - Page extraction, thumbnails
5. **Proceed to Phase 3** - Exemplar Management UI

---

## Project Structure

```
sam3_dwg/
├── frontend/                    # React frontend (Vite)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx   # Document library + upload
│   │   │   └── Viewer.tsx      # Drawing viewer + zones
│   │   ├── components/
│   │   │   ├── dashboard/      # Dashboard components
│   │   │   ├── viewer/         # Viewer components (canvas, sidebar)
│   │   │   ├── layout/         # Left navigation sidebar
│   │   │   └── shared/         # Shared components (TopBar, PageBar)
│   │   ├── store/              # Zustand state management
│   │   ├── api/                # API client (mock + real)
│   │   └── types/              # TypeScript types
│   └── package.json
├── src/sam3_segmenter/          # FastAPI backend
│   ├── main.py                 # API endpoints
│   ├── segmenter.py            # SAM3 wrapper
│   └── prompts/                # Zone detection prompts
├── models/
│   └── sam3.pt                 # SAM3 model weights (3.3GB)
├── docs/
│   ├── MVP_QUICKSTART.md       # This guide
│   ├── UI_ARCHITECTURE.md      # Frontend architecture
│   └── PLAN.md                 # Development roadmap
└── README.md
```

---

## Environment Variables

### Backend (`.env`)

```bash
SAM3_MODEL_PATH=models/sam3.pt
SAM3_DEVICE=cuda                    # or 'cpu'
SAM3_DEFAULT_CONFIDENCE_THRESHOLD=0.3
SAM3_CORS_ORIGINS=["http://localhost:3007"]
SAM3_LOG_LEVEL=INFO
```

### Frontend (`frontend/.env`)

```bash
VITE_API_URL=http://localhost:8001
```

---

## License

**SAM3 Drawing Zone Segmenter** - MIT-style License

**Key Dependencies:**
- **React** (MIT)
- **Vite** (MIT)
- **React Router** (MIT)
- **Zustand** (MIT)
- **Tailwind CSS** (MIT)
- **SAM3 Model** (Apache 2.0 from Meta - commercial use permitted)
- **FastAPI** (MIT)
- **PyTorch** (BSD-style)

**Commercial use permitted.** See LICENSE file for details.

---

## Support

**For issues or questions:**

1. Check this troubleshooting section
2. Review [UI_ARCHITECTURE.md](UI_ARCHITECTURE.md) for technical details
3. Check [PLAN.md](PLAN.md) for known issues and planned features
4. Review backend logs: `tail -f <backend_output>`
5. Check browser console (F12) for frontend errors
6. Verify GPU: `nvidia-smi`

**Known Limitations:**
- Document storage uses localStorage (temporary - backend persistence needed)
- Multi-page PDF support not yet implemented
- Export functionality not yet implemented
- No authentication/user management

---

**Version:** 2.0 (Phase 2)
**Last Updated:** 2026-01-04
**Maintained By:** SAM3 Development Team
