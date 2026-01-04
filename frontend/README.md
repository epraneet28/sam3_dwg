# SAM3 React Frontend

A modern React + Vite frontend for the SAM3 Drawing Zone Segmenter, styled after the docling-interactive UI.

## Features

- 🎨 **Dark Theme UI** - Professional slate color palette
- 📤 **Image Upload** - Drag & drop or click to upload engineering drawings
- 🤖 **Auto Segmentation** - SAM3 model automatically detects zones
- 🎚️ **Confidence Slider** - Filter zones by confidence threshold
- ✅ **Zone Filtering** - Select/deselect specific zone types
- 🔍 **Results Display** - View detected zones with confidence scores
- 💡 **Hover Highlighting** - Interactive zone highlighting
- ⚡ **GPU Status** - Real-time health monitoring

## Tech Stack

- **React 18** - UI library
- **Vite** - Build tool
- **TypeScript** - Type safety
- **TanStack Query** - Data fetching & caching
- **Tailwind CSS v4** - Styling
- **Heroicons** - Icons
- **Axios** - HTTP client

## Quick Start

### Prerequisites

- Node.js 18+
- Backend running on `http://localhost:8001`

### Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Start dev server (runs on port 3006)
npm run dev
```

### Build for Production

```bash
npm run build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/          # API client (axios)
│   ├── components/   # UI components from docling-interactive
│   │   └── ui/       # Button, Badge, Card, etc.
│   ├── pages/        # SAM3Page - main application
│   ├── types/        # TypeScript definitions
│   ├── utils/        # Constants & helpers
│   ├── App.tsx       # Main app with React Query
│   ├── main.tsx      # Entry point
│   └── index.css     # Dark theme styles
├── index.html
├── vite.config.ts
└── package.json
```

## API Integration

The frontend connects to the SAM3 FastAPI backend:

- **Health Check**: `GET /health`
- **Segment**: `POST /segment/structural`

Configure the API URL in `.env`:

```env
VITE_API_URL=http://localhost:8001
```

## Usage

1. **Start Backend**:
   ```bash
   cd ..
   uvicorn src.sam3_segmenter.main:app --reload --port 8001
   ```

2. **Start Frontend** (in this directory):
   ```bash
   npm run dev
   ```

3. **Open Browser**: http://localhost:3006

4. **Upload Drawing**: Click or drag a PNG/JPEG engineering drawing

5. **Segment**: Click "Segment Drawing" button

6. **Filter Results**: Use confidence slider and zone type checkboxes

7. **Explore**: Hover over zones in the list to highlight them

## Zone Types Supported

- Title Block
- Revision Block
- Plan View
- Elevation View
- Section View
- Detail View
- Schedule Table
- Notes Area
- Legend
- Grid System

## Development

### Component Library

UI components are adapted from docling-interactive:

- `Button` - Solid, outline, and plain variants
- `Badge` - Color-coded status indicators
- `Card` - Container with dark theme styling
- `EmptyState` - Placeholder for empty data

### Adding New Features

1. Add types to `src/types/index.ts`
2. Add API methods to `src/api/client.ts`
3. Create components in `src/components/`
4. Use React Query hooks for data fetching

## Dark Theme

Colors optimized for dark backgrounds:

- Primary BG: `#0f172a` (slate-900)
- Card BG: `#1e293b` (slate-800)
- Border: `#475569` (slate-600)
- Text: `#e2e8f0` (slate-200)

Zone colors use -400 variants for visibility on dark backgrounds.

## License

MIT - See LICENSE file

## Support

For issues or questions about the frontend, check:
1. Backend is running on port 8001
2. CORS is configured correctly
3. `.env` file has correct `VITE_API_URL`
4. Console for error messages
