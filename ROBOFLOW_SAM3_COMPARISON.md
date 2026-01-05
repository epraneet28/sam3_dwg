# Roboflow Smart Polygon vs Our SAM3 Implementation

## Executive Summary

This document compares Roboflow's "Smart Polygon with SAM" feature against our current SAM3 Playground implementation, identifying gaps and planning implementation of missing features.

---

## Feature Comparison Matrix

| Feature | Roboflow | Our Implementation | Status |
|---------|----------|-------------------|--------|
| **Input Modes** |
| Single click segmentation | Yes | Yes (Points mode) | DONE |
| Bounding box drawing | Yes | Yes (Box mode) | DONE |
| Text prompts | Limited | Yes (full PCS) | BETTER |
| Multiple point prompts | Yes | Yes | DONE |
| Positive/negative points | Yes | Yes | DONE |
| **Output Formats** |
| Pixel mask output | Yes | Yes (default) | DONE |
| Polygon output | Yes | No | MISSING |
| Polygon/Pixels toggle | Yes | No | MISSING |
| **Refinement** |
| Click outside to add | Yes | No | MISSING |
| Click inside to remove | Yes | No | MISSING |
| Mask input for refinement | Implicit | Yes (explicit) | DONE |
| **History/Editing** |
| Undo | Yes | No | MISSING |
| Redo | Yes | No | MISSING |
| Delete current selection | Yes | Partial (Clear All) | PARTIAL |
| **Mask Quality** |
| Multiple mask candidates | SAM default (3) | Yes (3 candidates) | DONE |
| IoU score display | Unknown | Yes | BETTER |
| Polygon complexity control | Yes | No | MISSING |
| **UX Features** |
| Preview mask on hover | Yes | No | MISSING |
| Enter to confirm | Yes | No | MISSING |
| Model selection dropdown | Yes | No (single model) | N/A |
| **Auto-run** |
| Auto-segment on input | Unknown | Yes (toggle) | DONE |

---

## Detailed Analysis

### 1. Output Format Toggle (Polygon vs Pixels)

**Roboflow:** Provides a toggle between "Polygon" and "Pixels" modes.
- **Polygon mode:** Converts the mask to simplified polygon vertices
- **Pixels mode:** Raw pixel mask (what we currently have)

**Our Implementation:** Only supports pixel masks. We display the mask as colored overlay on canvas.

**Gap:** Need to add:
1. Toggle UI component (Polygon | Pixels)
2. Polygon extraction algorithm from binary mask
3. SVG polygon overlay renderer
4. Polygon simplification with complexity control

### 2. Interactive Refinement (Click to Add/Remove)

**Roboflow:** After initial selection:
- Click **outside** the mask area = expand selection (add region)
- Click **inside** the mask area = contract selection (remove region)

**Our Implementation:**
- We have mask input for refinement (`maskInputBase64`)
- But it requires explicit "Use as Mask Input" button click
- Then user must add more points manually

**Gap:** Need automatic refinement mode where:
1. After initial mask, switch to "refinement mode"
2. Detect if click is inside/outside mask
3. Automatically add positive/negative point
4. Auto-run inference with mask input

### 3. Undo/Redo History

**Roboflow:** Full undo/redo for mask editing operations.

**Our Implementation:** None. Only "Clear All" which wipes everything.

**Gap:** Need:
1. History stack for mask states
2. Undo button (Ctrl+Z)
3. Redo button (Ctrl+Shift+Z)
4. History limit (e.g., 20 states)

### 4. Polygon Complexity Control

**Roboflow:** Allows adjusting polygon simplification level.

**Our Implementation:** None (no polygon output).

**Gap:** Need:
1. Douglas-Peucker or similar algorithm
2. Slider UI for tolerance/complexity
3. Real-time polygon preview

### 5. Mask Preview on Hover

**Roboflow:** Shows preview mask when hovering, before committing.

**Our Implementation:** Shows mask only after clicking "Run".

**Gap:** Need:
1. Debounced hover detection
2. Lightweight "preview" inference (maybe lower resolution)
3. Preview overlay (different style from confirmed mask)

### 6. Keyboard Shortcuts

**Roboflow:** Enter to confirm/finish selection.

**Our Implementation:**
- Escape to clear (in points/box modes)
- No Enter to confirm

**Gap:** Need:
1. Enter key handler
2. "Finish" action (save annotation, move to next)
3. Visual indication of confirmation

---

## Implementation Priority

### Phase 1: Core Roboflow Parity (High Priority)
1. **Polygon/Pixels toggle** - Most visible missing feature from screenshot
2. **Interactive refinement** - Click inside/outside behavior
3. **Delete current selection** - Simple individual mask delete

### Phase 2: Enhanced UX (Medium Priority)
4. **Undo/Redo** - Important for iterative workflows
5. **Enter to confirm** - Quick keyboard workflow
6. **Polygon complexity slider** - When polygon mode is done

### Phase 3: Polish (Lower Priority)
7. **Hover preview** - Nice-to-have, may need backend optimization
8. **Model selection** - Only if we support multiple SAM variants

---

## Technical Implementation Details

### Polygon Extraction from Mask

```typescript
// Algorithm: Marching squares + Douglas-Peucker simplification
interface PolygonOutput {
  points: Array<[number, number]>;  // Simplified polygon vertices
  rawPoints: Array<[number, number]>; // Original contour
  complexity: number; // 0-1 simplification level used
}

// Steps:
// 1. Decode base64 mask to ImageData
// 2. Run marching squares to extract contours
// 3. Apply Douglas-Peucker with tolerance based on complexity
// 4. Return simplified polygon points
```

### Refinement Mode State Machine

```typescript
type RefinementState =
  | 'idle'           // No mask yet
  | 'initial'        // First mask generated
  | 'refining'       // Iteratively refining with clicks
  | 'confirmed';     // User pressed Enter to confirm

interface SmartSelectState {
  state: RefinementState;
  currentMask: MaskCandidate | null;
  maskHistory: MaskCandidate[];
  historyIndex: number;  // For undo/redo
  outputMode: 'polygon' | 'pixels';
  polygonComplexity: number; // 0-1
}
```

### History Management

```typescript
interface HistoryEntry {
  mask: MaskCandidate;
  points: PointPrompt[];
  box: BoxPrompt | null;
}

// Max 20 entries, LIFO stack
// Undo: decrement index, restore state
// Redo: increment index, restore state
// New action: truncate redo stack, push new entry
```

---

## UI Design for Smart Select Panel

Based on Roboflow screenshot, our panel should include:

```
+----------------------------------+
|  Smart Select           [X]      |
+----------------------------------+
|  Model: [SAM3        v]          |  <- Optional, if multi-model
+----------------------------------+
|  [Polygon]  [Pixels*]            |  <- Toggle, Pixels highlighted
+----------------------------------+
|  (i) Click outside to add        |
|      or inside to remove.        |
+----------------------------------+
|  Complexity: [====----] 60%      |  <- Only in Polygon mode
+----------------------------------+
|  [Undo]    [Redo]               |
+----------------------------------+
|  [Delete]     [Finish (Enter)]  |
+----------------------------------+
```

---

## Files to Modify/Create

### New Files
- `frontend/src/components/playground/SmartSelectPanel.tsx` - New unified panel
- `frontend/src/utils/polygonExtraction.ts` - Mask to polygon conversion
- `frontend/src/hooks/useSmartSelectHistory.ts` - Undo/redo logic

### Modified Files
- `frontend/src/pages/Playground.tsx` - Integrate SmartSelectPanel
- `frontend/src/components/playground/PlaygroundCanvas.tsx` - Refinement click handling
- `frontend/src/components/playground/MaskOverlay.tsx` - Polygon rendering mode
- `frontend/src/types/index.ts` - New types for polygon output, history

---

## Backend Considerations

Current backend already supports:
- Point prompts with labels
- Box prompts
- Mask input for refinement
- Multiple mask candidates

**No backend changes required** for Phase 1-2.

For hover preview (Phase 3), may want:
- Lower-resolution preview endpoint
- WebSocket for faster round-trips

---

## Next Steps

1. Read this document and approve the approach
2. Start with Phase 1, Item 1: Polygon/Pixels toggle
3. Implement polygon extraction utility
4. Add toggle to existing panel (or create SmartSelectPanel)
5. Test with various masks
6. Continue to Item 2: Interactive refinement

---

## References

- [Roboflow Smart Polygon Docs](https://docs.roboflow.com/annotate/ai-labeling/enhanced-smart-polygon-with-sam)
- [Marching Squares Algorithm](https://en.wikipedia.org/wiki/Marching_squares)
- [Douglas-Peucker Algorithm](https://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm)
