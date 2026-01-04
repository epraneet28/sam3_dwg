# SAM3 Frontend Architecture Guide

**Last Updated:** 2026-01-04
**Stack:** Vite + React 18 + React Router v6 + Zustand + Tailwind v4
**Architecture:** Multi-page SPA with Dashboard + Viewer

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Routing Architecture](#routing-architecture)
4. [State Management](#state-management)
5. [Component Hierarchy](#component-hierarchy)
6. [Key Pages](#key-pages)
7. [Shared Components](#shared-components)
8. [API Integration](#api-integration)
9. [Styling System](#styling-system)
10. [Development Workflow](#development-workflow)

---

## Overview

The SAM3 frontend is a modern React application built with Vite for fast development and optimized production builds. It features a multi-page architecture with:

- **Dashboard**: Document library with upload and management
- **Viewer**: Interactive drawing canvas with zone overlays and filters
- **Left Navigation**: App-level sidebar for global navigation

**Key Design Decisions:**
- **Vite** over Next.js for faster HMR and simpler build setup
- **React Router** for client-side routing
- **Zustand** for lightweight state management with persistence
- **HTML5 Canvas** for zone rendering (better performance than SVG)
- **Tailwind v4** with dark theme (zinc palette)

---

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── dashboard/           # Dashboard-specific components
│   │   │   ├── DocumentCard.tsx
│   │   │   ├── UploadZone.tsx
│   │   │   └── index.ts
│   │   ├── viewer/              # Viewer-specific components
│   │   │   ├── DrawingCanvas.tsx
│   │   │   ├── ZoneSidebar.tsx
│   │   │   └── index.ts
│   │   ├── layout/              # App layout components
│   │   │   ├── Layout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── sidebar/
│   │   │   │   └── compounds.tsx
│   │   │   └── index.ts
│   │   ├── shared/              # Shared UI components
│   │   │   ├── MinimalTopBar.tsx
│   │   │   ├── PageBar.tsx
│   │   │   ├── ControlsHint.tsx
│   │   │   └── index.ts
│   │   └── ui/                  # Base UI primitives
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       └── ...
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   └── Viewer.tsx
│   ├── api/
│   │   └── client.ts            # API client with mock implementations
│   ├── store/
│   │   └── index.ts             # Zustand store
│   ├── types/
│   │   └── index.ts             # TypeScript types
│   ├── utils/
│   │   ├── constants.ts         # Zone types, colors, defaults
│   │   └── colors.ts            # Color utilities
│   ├── App.tsx                  # Root component with routing
│   ├── main.tsx                 # Entry point
│   └── index.css                # Global styles
├── public/                      # Static assets
├── package.json
├── vite.config.ts
└── tailwind.config.ts
```

---

## Routing Architecture

### Route Structure

```tsx
<Routes>
  <Route path="/" element={<Layout />}>     {/* Layout wrapper with sidebar */}
    <Route index element={<Dashboard />} /> {/* / - Dashboard */}
    <Route path="viewer/:docId" element={<Viewer />} /> {/* /viewer/:docId - Viewer */}
  </Route>
</Routes>
```

**Route Patterns:**
- `/` - Dashboard (document list)
- `/viewer/:docId` - Viewer for specific document
- Future: `/exemplars`, `/settings`

**Navigation Flow:**
1. User uploads document on Dashboard
2. Auto-segmentation runs
3. Navigates to `/viewer/:docId` on success

### Layout Component Pattern

The `<Layout>` component wraps all pages and provides:
- Left navigation sidebar (collapsible)
- Main content area with `<Outlet />`
- Persistent UI state (sidebar collapsed/expanded)

```tsx
// Simplified Layout structure
<div className="flex h-screen">
  <Sidebar collapsed={sidebarCollapsed} />
  <main className="flex-1">
    <Outlet /> {/* Dashboard or Viewer renders here */}
  </main>
</div>
```

---

## State Management

### Zustand Store

Location: `src/store/index.ts`

**State Shape:**
```typescript
interface AppState {
  // Documents
  documents: SAM3Document[];
  selectedDocument: SAM3Document | null;

  // Dashboard UI
  dashboardSearch: string;

  // Sidebar UI
  sidebarCollapsed: boolean;

  // Actions
  setDocuments: (documents: SAM3Document[]) => void;
  addDocument: (document: SAM3Document) => void;
  updateDocument: (id: string, updates: Partial<SAM3Document>) => void;
  selectDocument: (document: SAM3Document | null) => void;
  deleteDocument: (id: string) => void;
  setDashboardSearch: (search: string) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}
```

**Persistence:**
- Uses `zustand/middleware` with `persist`
- Stores `documents` array in localStorage
- UI state (search, sidebar) NOT persisted (resets on refresh)

**Selectors:**
```typescript
export const useDocuments = () => useStore(state => state.documents);
export const useSelectedDocument = () => useStore(state => state.selectedDocument);
export const useDashboardSearch = () => useStore(state => state.dashboardSearch);
export const useSidebarCollapsed = () => useStore(state => state.sidebarCollapsed);
```

---

## Component Hierarchy

### Dashboard Page

```
Dashboard
├── Header (title + refresh button)
├── UploadZone
│   ├── Drag-and-drop area
│   └── File validation (PDF/PNG/JPEG, max 50MB)
├── Search input
└── Document Grid
    └── DocumentCard[] (for each document)
        ├── Thumbnail (first page image)
        ├── Metadata (name, pages, zones)
        ├── Status badge (segmented/pending/error)
        └── Delete button
```

### Viewer Page

```
Viewer
├── MinimalTopBar
│   ├── Back to Dashboard button
│   ├── Title + subtitle (doc name, page/zone counts)
│   └── Actions slot (page type, processing time)
├── PageBar (if multi-page)
│   ├── Page navigation (prev/next, page selector)
│   └── Zoom controls (zoom in/out, fit to page)
├── Main Content (flex row)
│   ├── DrawingCanvas (flex-1)
│   │   ├── HTML5 Canvas element
│   │   ├── Zone overlays (colored bounding boxes)
│   │   ├── Pan/zoom gestures
│   │   ├── Click detection for zone selection
│   │   └── Hover highlighting
│   ├── ControlsHint (bottom-left overlay)
│   └── ZoneSidebar (right)
│       ├── Zone Filters section
│       │   ├── Confidence threshold slider (0-100%)
│       │   └── Zone type checkboxes (10+ types)
│       └── Zone List (scrollable)
│           └── ZoneItem[] (for each filtered zone)
│               ├── Color indicator
│               ├── Zone type label
│               ├── Confidence percentage
│               └── Dimensions
```

### Layout Structure

```
Layout
├── Sidebar (left, collapsible)
│   ├── Header
│   │   ├── Logo + Brand
│   │   └── Collapse toggle
│   ├── Body (scrollable)
│   │   ├── Navigation section
│   │   │   ├── Dashboard link
│   │   │   ├── Viewer link (disabled if no docs)
│   │   │   ├── Exemplar Management (coming soon)
│   │   │   └── Settings (coming soon)
│   │   └── Status panel (bottom)
│   └── Footer
│       └── Document count
└── Main content area
    └── <Outlet /> (Dashboard or Viewer)
```

---

## Key Pages

### Dashboard (`src/pages/Dashboard.tsx`)

**Purpose:** Document library with upload and management

**Features:**
- Upload zone with drag-and-drop
- Document grid with cards
- Search/filter by name
- Delete documents with confirmation
- Auto-segment on upload → Navigate to viewer

**State:**
- Local: `uploading`, `uploadError`
- Store: `documents`, `dashboardSearch`

**Key Handlers:**
```typescript
handleUpload(file: File) {
  1. Upload file (mock - stores in localStorage)
  2. Create document in store
  3. Auto-segment via API
  4. Update document with results
  5. Navigate to /viewer/:docId
}

handleDelete(doc: SAM3Document) {
  1. Show confirmation dialog
  2. Delete from API (mock - removes from localStorage)
  3. Remove from store
}
```

### Viewer (`src/pages/Viewer.tsx`)

**Purpose:** Interactive drawing viewer with zone canvas and filters

**Features:**
- Top bar with back button and metadata
- Page navigation (for multi-page docs)
- Drawing canvas with zone overlays
- Right sidebar with filters and zone list
- Bi-directional highlighting (list ↔ canvas)

**State:**
- Local: `currentPage`, `zoom`, `pan`, `confidenceThreshold`, `selectedZoneTypes`, `hoveredZoneId`, `selectedZoneId`
- Store: `documents` (finds doc by ID from URL param)

**Key Computed Values:**
```typescript
const filteredZones = useMemo(() => {
  return currentPageData.zones.filter(zone =>
    zone.confidence >= confidenceThreshold &&
    selectedZoneTypes.has(zone.zone_type)
  );
}, [currentPageData.zones, confidenceThreshold, selectedZoneTypes]);
```

---

## Shared Components

### MinimalTopBar (`src/components/shared/MinimalTopBar.tsx`)

**Props:**
```typescript
interface MinimalTopBarProps {
  title: string;
  subtitle?: string;
  onBack?: () => void;
  actions?: React.ReactNode;
  className?: string;
}
```

**Usage:**
```tsx
<MinimalTopBar
  title={document.name}
  subtitle={`${document.totalPages} pages • ${totalZones} zones`}
  onBack={() => navigate('/')}
  actions={<div>Page Type: {pageType}</div>}
/>
```

### PageBar (`src/components/shared/PageBar.tsx`)

**Props:**
```typescript
interface PageBarProps {
  currentPage: number;      // 0-indexed internally
  totalPages: number;
  onPageChange: (page: number) => void;
  zeroIndexed?: boolean;    // Display 0-indexed or 1-indexed
  zoomControls?: {
    zoom: number;
    onZoomIn: () => void;
    onZoomOut: () => void;
    onFitToPage: () => void;
  };
}
```

### DrawingCanvas (`src/components/viewer/DrawingCanvas.tsx`)

**Key Implementation:**
- Renders image + zone overlays on HTML5 Canvas
- Redraws on any state change (zones, hover, selection, zoom, pan)
- Click detection via coordinate math
- Pan via mouse drag (mousedown → mousemove → mouseup)
- Zoom via scroll wheel
- Highlights selected/hovered zones with thicker borders + labels

**Rendering Loop:**
```typescript
useEffect(() => {
  1. Clear canvas
  2. Draw image scaled to fit canvas
  3. For each zone:
     - Draw bounding box (strokeRect)
     - Fill with transparency (fillRect with 20% opacity)
     - If selected/hovered: draw thicker border + label
}, [zones, imageDimensions, hoveredZoneId, selectedZoneId, zoom, pan]);
```

### ZoneSidebar (`src/components/viewer/ZoneSidebar.tsx`)

**Sections:**
1. **Zone Filters**:
   - Confidence slider (0-100%)
   - Zone type checkboxes with Select All/Deselect All

2. **Zone List**:
   - Scrollable list of filtered zones
   - Auto-scroll to selected zone
   - Click to select, hover to highlight

**Auto-scroll Effect:**
```typescript
useEffect(() => {
  if (selectedZoneId) {
    const element = document.getElementById(`zone-${selectedZoneId}`);
    element?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}, [selectedZoneId]);
```

---

## API Integration

### API Client (`src/api/client.ts`)

**Base Configuration:**
```typescript
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8001',
  timeout: 60000, // 60s for segmentation
});
```

**Endpoints:**
```typescript
api.getHealth(): Promise<HealthResponse>
api.segmentStructural(request): Promise<SegmentResponse>

// Mock implementations (backend not ready):
api.uploadDocument(file): Promise<{ docId, totalPages }>
api.listDocuments(): Promise<SAM3Document[]>
api.deleteDocument(docId): Promise<void>
api.segmentDocument(docId, options?): Promise<SegmentDocumentResponse>
api.getPageImageUrl(docId, pageNumber): string
```

**Mock Strategy:**
- Uses localStorage for temporary document storage
- `uploadDocument`: Stores base64-encoded image
- `segmentDocument`: Calls existing `/segment/structural` endpoint
- `getPageImageUrl`: Returns data URL from localStorage

**TODO Comments:**
All mock functions are clearly marked with `TODO: Backend needs to implement...` for backend team.

---

## Styling System

### Tailwind Configuration

**Theme:**
- Dark mode with zinc palette (zinc-900, zinc-800 backgrounds)
- Accent color: blue-600
- Text: white (primary), zinc-400 (secondary), zinc-600 (disabled)

**Key Utilities:**
```css
/* Container patterns */
.flex.h-screen.bg-zinc-900         /* Full-height dark container */
.flex-1.overflow-y-auto            /* Scrollable main content */

/* Interactive states */
.hover:bg-white/5                  /* Subtle hover */
.focus:ring-2.ring-blue-500        /* Focus indicator */
.cursor-pointer                    /* Clickable elements */

/* Transitions */
.transition-all.duration-300       /* Smooth animations */
```

### Color System for Zones

Location: `src/utils/constants.ts`

```typescript
export const ZONE_COLORS: Record<ZoneType, string> = {
  title_block: '#10b981',      // Green
  revision_block: '#a855f7',   // Purple
  plan_view: '#3b82f6',        // Blue
  elevation_view: '#f97316',   // Orange
  section_view: '#ef4444',     // Red
  detail_view: '#f59e0b',      // Amber
  schedule_table: '#ec4899',   // Pink
  notes_area: '#06b6d4',       // Cyan
  legend: '#8b5cf6',           // Violet
  grid_system: '#14b8a6',      // Teal
  unknown: '#6b7280',          // Gray
};
```

---

## Development Workflow

### Running the App

```bash
# Start frontend (in /frontend)
npm run dev

# Vite will start on http://localhost:3007
# Hot Module Replacement (HMR) enabled
```

### Environment Variables

Create `.env` file in `/frontend`:

```bash
VITE_API_URL=http://localhost:8001
```

### Adding a New Page

1. Create page component in `src/pages/`
2. Add route in `src/App.tsx` under `<Layout>`
3. Add navigation item in `src/components/layout/Sidebar.tsx`

### Adding a New Component

1. Create component file in appropriate directory:
   - `components/dashboard/` - Dashboard-specific
   - `components/viewer/` - Viewer-specific
   - `components/shared/` - Shared across pages
   - `components/ui/` - Base primitives

2. Export from `index.ts` in that directory

### State Management

**Adding new state:**
1. Update `AppState` interface in `src/store/index.ts`
2. Add initial value in `create` function
3. Add action functions
4. Create selector if needed

**Using state:**
```typescript
// In component
const documents = useDocuments();
const { addDocument, deleteDocument } = useStore();

// Or full state access
const state = useStore();
```

### API Integration

**Adding new endpoint:**
1. Define types in `src/types/index.ts`
2. Add method to `api` object in `src/api/client.ts`
3. Use in component with try/catch error handling

---

## Key Architectural Patterns

### 1. Compound Component Pattern

Used in Sidebar components for flexibility:

```tsx
<SidebarBody>
  <SidebarSection>
    <SidebarHeading>Navigation</SidebarHeading>
    <SidebarItem to="/">Dashboard</SidebarItem>
  </SidebarSection>
  <SidebarDivider />
  <SidebarSection>
    <SidebarItem to="/settings">Settings</SidebarItem>
  </SidebarSection>
</SidebarBody>
```

### 2. Controlled vs Uncontrolled State

- **Controlled**: Filters, sliders (parent manages state)
- **Uncontrolled**: Canvas pan/zoom (internal state with callback)

### 3. Bi-directional Data Flow

Zone highlighting syncs both ways:
```typescript
// List → Canvas
<ZoneItem onClick={() => setSelectedZoneId(id)} />

// Canvas → List (via useEffect + scrollIntoView)
useEffect(() => {
  const element = document.getElementById(`zone-${selectedZoneId}`);
  element?.scrollIntoView({ behavior: 'smooth' });
}, [selectedZoneId]);
```

### 4. Optimistic UI Updates

```typescript
// Delete document immediately in UI
deleteDocument(docId);

// Then sync with backend
await api.deleteDocument(docId);
```

---

## Performance Considerations

### Canvas Rendering

- **Redraw on demand**: Only redraws when dependencies change
- **No animations**: Static overlays (better performance)
- **Efficient hit testing**: Reverse iteration for top-most zone

### State Management

- **Memoization**: `useMemo` for filtered zones
- **Selective persistence**: Only persist documents, not UI state
- **Selective re-renders**: Zustand selectors prevent unnecessary renders

### Image Loading

- **Lazy loading**: Images load only when needed
- **Data URLs**: Stored directly in localStorage (temporary solution)
- **No preloading**: Future: implement page preloading for multi-page docs

---

## Future Enhancements

### Planned Features
- Export functionality (JSON, CSV, annotated image)
- Multi-page PDF support
- Page thumbnails sidebar
- Keyboard shortcuts (arrow keys, Escape, +/-)
- Fullscreen mode
- Batch processing UI
- Exemplar management pages

### Technical Improvements
- Replace localStorage with backend persistence
- Implement proper image preloading
- Add Canvas worker thread for large documents
- Implement virtual scrolling for zone list
- Add request cancellation for interrupted uploads

---

## Troubleshooting

### Common Issues

**Port 3007 already in use:**
```bash
# Vite will auto-select next available port
# Or manually kill process on port 3007
lsof -ti:3007 | xargs kill -9
```

**CORS errors:**
- Ensure backend CORS includes `http://localhost:3007`
- Check `.env` file has correct `SAM3_CORS_ORIGINS`

**Stale localStorage:**
```javascript
// Clear localStorage in browser console
localStorage.clear();
```

**Zone overlays not showing:**
- Check if zones array is empty (confidence threshold too high)
- Verify image loaded successfully
- Check browser console for Canvas errors

---

## References

- **Vite Documentation**: https://vite.dev/
- **React Router**: https://reactrouter.com/
- **Zustand**: https://zustand-demo.pmnd.rs/
- **Tailwind CSS**: https://tailwindcss.com/
- **Project Guidelines**: `../CLAUDE.md`

---

**Version:** 2.0 (Phase 2)
**Last Updated:** 2026-01-04
**Maintained By:** SAM3 Development Team
