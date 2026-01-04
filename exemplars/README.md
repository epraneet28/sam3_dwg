# Visual Exemplars

This directory contains visual exemplar images for improving zone detection accuracy.

## Directory Structure

```
exemplars/
├── title_block/
│   ├── exemplar_001.png
│   └── exemplar_002.png
├── detail/
│   └── exemplar_001.png
├── schedule_table/
│   └── exemplar_001.png
└── ...
```

## Adding Exemplars

1. Create a subdirectory named after the zone type (e.g., `title_block`, `detail_view`)
2. Add cropped images of good examples for that zone type
3. Images should be PNG or JPEG format
4. Exemplars will be automatically loaded on service startup

## Zone Types

Available zone types for exemplars:

- `title_block` - Title blocks with project info
- `revision_block` - Revision history blocks
- `plan_view` - Floor plans, framing plans
- `elevation_view` - Building elevations
- `section_view` - Section cuts
- `detail_view` - Construction details
- `schedule_table` - Beam, column, material schedules
- `notes_area` - General notes text areas
- `legend` - Symbol legends
- `grid_system` - Column grid markers

## API Upload

You can also upload exemplars via the API:

```bash
curl -X POST http://localhost:8001/exemplars/upload \
  -H "Content-Type: application/json" \
  -d '{
    "zone_type": "title_block",
    "image_base64": "<base64_encoded_image>"
  }'
```
