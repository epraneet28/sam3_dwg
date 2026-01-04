"""Pytest fixtures and configuration."""

import base64
from io import BytesIO

import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient


@pytest.fixture
def sample_image() -> Image.Image:
    """Create a simple test image simulating a drawing sheet."""
    # Create a white background (typical drawing sheet)
    img = Image.new("RGB", (1700, 1100), color="white")
    draw = ImageDraw.Draw(img)

    # Draw a border (drawing sheet border)
    draw.rectangle([10, 10, 1690, 1090], outline="black", width=2)

    # Draw a title block area (bottom right)
    draw.rectangle([1200, 850, 1680, 1080], outline="black", width=2)
    draw.text((1300, 900), "TITLE BLOCK", fill="black")

    # Draw a detail area (top left)
    draw.rectangle([50, 50, 400, 350], outline="black", width=1)
    draw.text((150, 150), "DETAIL 1", fill="black")

    # Draw another detail (top right)
    draw.rectangle([450, 50, 800, 350], outline="black", width=1)
    draw.text((550, 150), "DETAIL 2", fill="black")

    # Draw a notes area (left side)
    draw.rectangle([50, 400, 350, 800], outline="black", width=1)
    draw.text((100, 450), "GENERAL NOTES", fill="black")

    # Draw a schedule table area (right side)
    draw.rectangle([1300, 400, 1680, 800], outline="black", width=1)
    draw.text((1400, 450), "SCHEDULE", fill="black")

    return img


@pytest.fixture
def sample_image_base64(sample_image: Image.Image) -> str:
    """Convert sample image to base64."""
    buffer = BytesIO()
    sample_image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    from src.sam3_segmenter.main import app

    return TestClient(app)


@pytest.fixture
def small_image_base64() -> str:
    """Create a minimal test image."""
    img = Image.new("RGB", (100, 100), color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


@pytest.fixture
def invalid_base64() -> str:
    """Return invalid base64 string."""
    return "not_valid_base64!!!"
