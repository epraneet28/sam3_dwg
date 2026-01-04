# SAM3 Drawing Segmenter - Frontend

Next.js 14 web application for the SAM3 Drawing Zone Segmenter.

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Data Fetching**: TanStack Query (React Query)
- **HTTP Client**: Axios
- **Icons**: Lucide React

## Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## Project Structure

```
sam3-ui/
├── src/
│   ├── app/              # App Router pages
│   │   ├── layout.tsx    # Root layout with providers
│   │   ├── page.tsx      # Main segmentation page (MVP)
│   │   └── globals.css   # Global styles
│   ├── components/       # React components
│   │   ├── ui/          # shadcn/ui components
│   │   └── providers.tsx # React Query provider
│   └── lib/             # Utilities and API
│       ├── types.ts      # TypeScript types
│       ├── api-client.ts # Axios API client
│       ├── api-hooks.ts  # React Query hooks
│       └── utils.ts      # Helper functions
├── public/              # Static assets
└── .env.local          # Environment variables (not committed)
```

## Available API Hooks

### Health & Status
- `useHealth()` - Get backend health status

### Segmentation
- `useSegment()` - General segmentation with custom prompts
- `useSegmentStructural()` - Structural drawing segmentation

### Zone Types
- `useZoneTypes()` - Get all supported zone types

### Exemplars
- `useExemplars(zoneType)` - List exemplars for a zone type
- `useExemplarDetail(zoneType, id)` - Get exemplar details
- `useUploadExemplar()` - Upload new exemplar
- `useUpdateExemplar()` - Update exemplar metadata
- `useDeleteExemplar()` - Delete an exemplar
- `useTestExemplar()` - Test exemplar effectiveness

### Drawings
- `useUploadDrawing()` - Upload and segment a drawing
- `useDrawingDetail(id)` - Get drawing details
- `useDrawingResults(id)` - Get segmentation results

### Prompts
- `useStructuralPrompts()` - Get structural zone prompts
- `usePageTypeRules()` - Get page type classification rules

## Usage Example

```tsx
import { useSegmentStructural } from "@/lib/api-hooks";

function SegmentButton({ imageBase64 }) {
  const { mutate, isPending } = useSegmentStructural();

  const handleClick = () => {
    mutate(
      {
        image_base64: imageBase64,
        return_masks: false,
        return_crops: false,
        classify_page_type: true,
      },
      {
        onSuccess: (data) => {
          console.log("Zones found:", data.zones);
          console.log("Page type:", data.page_type);
        },
        onError: (error) => {
          console.error("Segmentation failed:", error);
        },
      }
    );
  };

  return (
    <button onClick={handleClick} disabled={isPending}>
      {isPending ? "Processing..." : "Segment Drawing"}
    </button>
  );
}
```

## shadcn/ui Components

The following components are installed:

- `button` - Button component with variants
- `card` - Card with header, content, footer
- `badge` - Badge for labels and status
- `input` - Form input field
- `label` - Form label
- `select` - Dropdown select
- `dialog` - Modal dialog
- `dropdown-menu` - Context/dropdown menu
- `table` - Data table
- `tabs` - Tabbed interface
- `sonner` - Toast notifications
- `tooltip` - Hover tooltips

Add more components:
```bash
npx shadcn@latest add <component-name>
```

## Type Safety

All API requests and responses are fully typed. Types are defined in `src/lib/types.ts` and match the backend Pydantic models.

```typescript
// Example: Typed API response
const { data } = useHealth();
// data is typed as HealthResponse
// data.status, data.model_loaded, data.gpu_available are all typed
```

## Development

### Adding a New Page

1. Create file in `src/app/your-page/page.tsx`
2. Use App Router conventions
3. Import and use API hooks as needed

### Adding a New API Endpoint

1. Add TypeScript types to `src/lib/types.ts`
2. Add method to `SAM3ApiClient` in `src/lib/api-client.ts`
3. Create React Query hook in `src/lib/api-hooks.ts`
4. Use the hook in your component

### Styling

Use Tailwind CSS utility classes:

```tsx
<div className="flex items-center gap-4 p-4 rounded-lg bg-slate-100">
  <span className="text-sm font-medium text-slate-900">Hello</span>
</div>
```

## Backend Integration

The frontend expects the backend API to be running on `http://localhost:8001` (configurable via `NEXT_PUBLIC_API_URL`).

### Backend Endpoints Used

- `GET /health` - Health check
- `POST /segment/structural` - Segment structural drawings
- `GET /zones/types` - Get zone type information
- `GET /exemplars/{zone_type}` - List exemplars
- `POST /exemplars/upload` - Upload exemplar
- `POST /drawings/upload` - Upload and segment drawing
- `GET /drawings/{id}` - Get drawing details
- And more...

## Building for Production

```bash
# Build optimized production bundle
npm run build

# Test production build locally
npm start
```

The production build is optimized with:
- Server-side rendering (SSR) for initial page loads
- Code splitting and lazy loading
- Image optimization
- Static optimization for pages without dynamic data

## License

MIT License - see parent project for details
