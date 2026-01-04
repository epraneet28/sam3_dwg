#!/usr/bin/env python3
"""Interactive prompt testing script for SAM3 segmentation."""

import argparse
import base64
import logging
import sys
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_image(image_path: str) -> Image.Image:
    """Load an image from file."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    img = Image.open(path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img


def visualize_results(
    image: Image.Image,
    zones: list[dict],
    output_path: Optional[str] = None,
) -> Image.Image:
    """
    Visualize segmentation results on the image.

    Args:
        image: Original image
        zones: List of zone dictionaries with bbox and zone_type
        output_path: Optional path to save the visualization

    Returns:
        Annotated image
    """
    # Create a copy for visualization
    vis_img = image.copy()
    draw = ImageDraw.Draw(vis_img)

    # Color palette for different zone types
    colors = {
        "title_block": "#FF0000",
        "revision_block": "#00FF00",
        "plan_view": "#0000FF",
        "elevation_view": "#FFFF00",
        "section_view": "#FF00FF",
        "detail_view": "#00FFFF",
        "schedule_table": "#FFA500",
        "notes_area": "#800080",
        "legend": "#008000",
        "grid_system": "#808080",
        "unknown": "#C0C0C0",
    }

    for zone in zones:
        bbox = zone.get("bbox", [])
        zone_type = zone.get("zone_type", "unknown")
        confidence = zone.get("confidence", 0)

        if len(bbox) != 4:
            continue

        x1, y1, x2, y2 = [int(v) for v in bbox]
        color = colors.get(zone_type, "#C0C0C0")

        # Draw bounding box
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

        # Draw label
        label = f"{zone_type}: {confidence:.2f}"
        draw.rectangle([x1, y1 - 20, x1 + len(label) * 7, y1], fill=color)
        draw.text((x1 + 2, y1 - 18), label, fill="white")

    if output_path:
        vis_img.save(output_path)
        logger.info(f"Visualization saved to {output_path}")

    return vis_img


def test_with_api(
    image_path: str,
    prompts: list[str],
    api_url: str = "http://localhost:8001",
) -> dict:
    """
    Test prompts using the API.

    Args:
        image_path: Path to test image
        prompts: List of prompts to test
        api_url: Base URL of the API

    Returns:
        API response dictionary
    """
    import httpx

    image = load_image(image_path)

    # Encode image
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    image_b64 = base64.b64encode(buffer.getvalue()).decode()

    # Make request
    client = httpx.Client(timeout=60.0)
    response = client.post(
        f"{api_url}/segment",
        json={
            "image_base64": image_b64,
            "prompts": prompts,
            "return_masks": False,
        },
    )

    if response.status_code != 200:
        logger.error(f"API error: {response.text}")
        sys.exit(1)

    return response.json()


def test_structural(
    image_path: str,
    api_url: str = "http://localhost:8001",
) -> dict:
    """
    Test structural segmentation using the API.

    Args:
        image_path: Path to test image
        api_url: Base URL of the API

    Returns:
        API response dictionary
    """
    import httpx

    image = load_image(image_path)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    image_b64 = base64.b64encode(buffer.getvalue()).decode()

    client = httpx.Client(timeout=60.0)
    response = client.post(
        f"{api_url}/segment/structural",
        json={
            "image_base64": image_b64,
            "classify_page_type": True,
            "return_masks": False,
        },
    )

    if response.status_code != 200:
        logger.error(f"API error: {response.text}")
        sys.exit(1)

    return response.json()


def main():
    parser = argparse.ArgumentParser(
        description="Test SAM3 segmentation prompts on drawings"
    )
    parser.add_argument(
        "-i",
        "--image",
        type=str,
        required=True,
        help="Path to test drawing image",
    )
    parser.add_argument(
        "-p",
        "--prompts",
        type=str,
        nargs="+",
        help="Custom prompts to test (uses structural prompts if not specified)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output path for visualization",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8001",
        help="API base URL (default: http://localhost:8001)",
    )
    parser.add_argument(
        "--structural",
        action="store_true",
        help="Use pre-configured structural prompts",
    )

    args = parser.parse_args()

    # Load image
    image = load_image(args.image)
    logger.info(f"Loaded image: {args.image} ({image.size[0]}x{image.size[1]})")

    # Test segmentation
    if args.structural or not args.prompts:
        logger.info("Testing with structural prompts...")
        result = test_structural(args.image, args.api_url)
        print(f"\nPage type: {result.get('page_type')} "
              f"(confidence: {result.get('page_type_confidence', 0):.2f})")
    else:
        logger.info(f"Testing with custom prompts: {args.prompts}")
        result = test_with_api(args.image, args.prompts, args.api_url)

    # Print results
    print(f"\nProcessing time: {result.get('processing_time_ms', 0):.1f}ms")
    print(f"Found {len(result.get('zones', []))} zones:\n")

    for zone in result.get("zones", []):
        print(f"  - {zone['zone_type']}")
        print(f"    Confidence: {zone['confidence']:.2f}")
        print(f"    Bbox: {zone['bbox']}")
        print(f"    Area ratio: {zone.get('area_ratio', 'N/A')}")
        print()

    # Visualize results
    output_path = args.output or f"{Path(args.image).stem}_annotated.png"
    visualize_results(image, result.get("zones", []), output_path)


if __name__ == "__main__":
    main()
