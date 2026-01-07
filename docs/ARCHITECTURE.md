# SAM3 Drawing Segmenter - Architecture

## Overview

Interactive segmentation for engineering drawings using Meta's SAM3. Three segmentation modes:
1. **Smart Select** - Click/box to select regions with iterative refinement
2. **Text Prompts** - Zero-shot segmentation via text descriptions
3. **Find Similar** - Feature-based search for similar regions

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Frontend (React/TypeScript)                       │
│  Pages: Dashboard | Viewer | Playground | Settings                  │
│  State: Zustand + localStorage persistence                          │
│  Hooks: useSmartSelect | useDocumentSync | useZoomPan               │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP/JSON (Axios, 60s timeout)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI/Python)                          │
│  ┌──────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────────┐ │
│  │ main.py  │──│segmenter.py│──│mask_process│──│ zone_classifier  │ │
│  │  (API)   │  │(SAM3 Wrap) │  │  (utils)   │  │ (post-process)   │ │
│  └──────────┘  └────────────┘  └────────────┘  └──────────────────┘ │
│       │              │                                               │
│       ▼              ▼                                               │
│  ┌──────────┐  ┌────────────┐                                       │
│  │ Database │  │ SAM3 Model │                                       │
│  │ (SQLite) │  │  (PyTorch) │                                       │
│  └──────────┘  └────────────┘                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/segment/interactive` | POST | Smart Select - points/boxes/masks |
| `/segment/find-similar` | POST | Find regions similar to exemplar |
| `/segment` | POST | Text prompt segmentation |
| `/segment/structural` | POST | Pre-configured structural prompts |
| `/segment/batch` | POST | Batch processing (per-image errors) |
| `/documents/*` | GET/POST/DELETE | Upload, list, retrieve documents |
| `/documents/{id}/playground/sessions/*` | GET/POST | Session persistence |
| `/exemplars/*` | GET/POST/DELETE | Exemplar management |
| `/config/prompts` | GET/PUT | Runtime prompt configuration |
| `/zones/types` | GET | Zone types with exemplar counts |
| `/health` | GET | Service health + GPU memory |

## Smart Select Pipeline

```
Input (points/box/mask) → SAM3 Inference → 3 candidates + logits
                                ↓
                    Candidate Sorting (by mode)
                                ↓
                    Candidate Union (top-k OR)
                                ↓
                    Binarization (threshold 0.25)
                                ↓
                    Dilation → Smoothing → PNG + logits
```

**Mask Selection Modes:**
- `largest` - Max pixel count (default, captures grid bubbles)
- `smallest` - Min pixel count (tight selection)
- `combined` - IoU + complexity scoring
- `iou` - SAM3's confidence scores

**Multi-Box Mode:** Multiple boxes merged via OR. Single box uses `force_single_mask_for_box` (Meta recommendation).

**Refinement:** Send `mask_logits_base64` (256x256 float) with subsequent clicks for high-quality iterative refinement.

## Find Similar Pipeline

Uses SAM3's native exemplar detection via geometric prompts. SAM3's DETR-based detector has built-in support for visual exemplars - no custom similarity computation needed.

```
Exemplar bbox → processor.add_geometric_prompt(box, label=True)
                        ↓
SAM3 DETR detector finds ALL similar objects (single forward pass)
                        ↓
Filter results (exclude original exemplar, apply thresholds)
                        ↓
Return masks, boxes, scores
```

**How it works:**
1. Convert exemplar bbox to normalized [cx, cy, w, h] format
2. Call `add_geometric_prompt(box, label=True, state)` - positive exemplar
3. SAM3 internally uses `"visual"` as text prompt when no text is provided
4. DETR-based detector finds all visually similar objects in one pass
5. Filter out the original exemplar by overlap check

**Config:** `find_similar_confidence_threshold`, `find_similar_exclude_overlap_threshold`

## Post-Processing Options

| Stage | Setting | Default | Purpose |
|-------|---------|---------|---------|
| Binarization | `mask_binarization_threshold` | 0.25 | Float→binary (lower=more edges) |
| Union | `enable_candidate_union` | true | Merge top-k candidates |
| Dilation | `precision_dilation_pixels` | 4 | Expand boundaries |
| Smoothing | `precision_smoothing_kernel` | 5 | Morphological closing |
| Stability | `enable_stability_filtering` | false | Filter unstable masks |
| NMS | IoU threshold | 0.7 | Remove overlapping masks |
| Edge reject | `edge_tolerance` | - | Reject masks touching edges |
| Box constraint | `box_constraint_margin` | 15% | Constrain mask to box region |

**Modes:** Precision mode (minimal post-processing) vs Drawing mode (aggressive fills via `box_fill`/`morphological`/`convex_hull`).

## Database Models

| Model | Purpose |
|-------|---------|
| `Exemplar` | Visual exemplar metadata + usage stats |
| `PromptConfig` | Zone-type prompts (DB-stored, versioned) |
| `InferenceConfig` | Global inference settings (singleton) |
| `Drawing` | Document metadata + segmentation results |

Config versioning tracks which settings were used for each segmentation.

## Zone Types

```
title_block, revision_block, plan_view, elevation_view, section_view,
detail_view, schedule_table, notes_area, legend, grid_system,
dimension_string, north_arrow, scale_bar, unknown
```

**Page Type Classification:** Rule-based detection using zone presence/absence patterns.

## File Structure

```
src/sam3_segmenter/
├── main.py              # API endpoints
├── segmenter.py         # SAM3 wrapper (singleton)
├── config.py            # 50+ settings (SAM3_* env vars)
├── models.py            # Pydantic schemas
├── database.py          # SQLAlchemy models
├── zone_classifier.py   # Page type detection
└── utils/
    ├── mask_processing.py   # Sorting, filtering, NMS
    └── debug_logging.py     # Per-run debug logs

frontend/src/
├── pages/
│   ├── Dashboard.tsx    # Upload & document list
│   ├── Viewer.tsx       # View segmentation results
│   ├── Playground.tsx   # Interactive segmentation
│   └── Settings.tsx     # Prompt configuration
├── hooks/
│   ├── useSmartSelect.ts    # Selection state machine
│   ├── useDocumentSync.ts   # Backend sync
│   └── useZoomPan.ts        # Canvas controls
├── stores/              # Zustand state (persisted)
├── api/client.ts        # Axios client
└── utils/polygonExtraction.ts  # Client-side polygon conversion
```

## Configuration Reference

```bash
# Core
SAM3_ENABLE_PRECISION_MODE=true       # Smart Select mode
SAM3_MASK_SELECTION_MODE=largest      # Candidate selection
SAM3_MASK_BINARIZATION_THRESHOLD=0.25

# Post-processing
SAM3_ENABLE_CANDIDATE_UNION=true
SAM3_CANDIDATE_UNION_TOPK=2
SAM3_ENABLE_PRECISION_DILATION=true
SAM3_PRECISION_DILATION_PIXELS=4
SAM3_ENABLE_PRECISION_SMOOTHING=true
SAM3_PRECISION_SMOOTHING_KERNEL=5

# Box handling
SAM3_FORCE_SINGLE_MASK_FOR_BOX=true   # Meta recommendation
SAM3_ENABLE_BOX_CONSTRAINT=false
SAM3_BOX_CONSTRAINT_MARGIN=0.15

# Find Similar
SAM3_FIND_SIMILAR_CONFIDENCE_THRESHOLD=0.3
SAM3_FIND_SIMILAR_EXCLUDE_OVERLAP_THRESHOLD=0.5

# Storage
SAM3_DOCUMENTS_DIR=./storage
SAM3_MAX_DOCUMENT_SIZE_MB=50

# Debug
SAM3_ENABLE_DEBUG_LOGGING=true
```

## Debug Logging

When enabled, saves to `storage/<doc_id>/debug_logs/<timestamp>/`:
- `debug_log.json` - Settings, inputs, timing
- `mask_raw_*.png` - Raw SAM3 output
- `mask_final_*.png` - After post-processing

Compare raw vs final to identify SAM3 vs post-processing issues.

## Performance

| Operation | Time | Notes |
|-----------|------|-------|
| SAM3 inference | 200-400ms | GPU-bound |
| Post-processing | 10-50ms | CPU (cv2) |
| Total round-trip | 300-600ms | Interactive |
| Model cold start | <30s | Singleton |

## Error Handling

| Code | Cause |
|------|-------|
| 400 | Invalid input (bad base64, malformed image) |
| 422 | Pydantic validation |
| 500 | SAM3 inference failure |
| 503 | Model not loaded |

Batch processing: per-image `error` field (doesn't fail entire batch).

## Known Limitations

1. **Disconnected regions** - Elements far from click may not be included
2. **Thin lines (<2px)** - May be lost; increase `precision_dilation_pixels`
3. **Large images (>4096px)** - SAM3 resizes internally, loses detail
4. **Refinement drift** - Many cycles degrade quality; reset if needed
5. **Find Similar** - Requires good exemplar; sensitive to scale mismatch
