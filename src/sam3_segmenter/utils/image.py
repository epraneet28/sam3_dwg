"""Image encoding/decoding utilities."""

import base64
from io import BytesIO
from typing import Optional, Union

import numpy as np
from PIL import Image


def decode_base64_image(image_base64: str) -> Image.Image:
    """
    Decode a base64 encoded image string to a PIL Image.

    Args:
        image_base64: Base64 encoded image string (may include data URI prefix)

    Returns:
        PIL Image in RGB mode

    Raises:
        ValueError: If the image cannot be decoded
    """
    # Remove data URI prefix if present
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]

    try:
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_bytes))
        # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
        if image.mode != "RGB":
            image = image.convert("RGB")
        return image
    except Exception as e:
        raise ValueError(f"Failed to decode image: {e}") from e


def encode_image_to_base64(
    image: Union[Image.Image, np.ndarray],
    format: str = "PNG",
    quality: int = 95,
) -> str:
    """
    Encode an image to a base64 string.

    Args:
        image: PIL Image or numpy array
        format: Output format (PNG or JPEG)
        quality: JPEG quality (1-100), ignored for PNG

    Returns:
        Base64 encoded string
    """
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)

    buffer = BytesIO()
    save_kwargs = {"format": format}
    if format.upper() == "JPEG":
        save_kwargs["quality"] = quality

    image.save(buffer, **save_kwargs)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def encode_mask_to_base64(
    mask: Union[np.ndarray, "torch.Tensor"],  # noqa: F821
    threshold: float = 0.5,
) -> str:
    """
    Encode a segmentation mask to a base64 PNG string.

    Args:
        mask: Binary or probability mask (2D array)
        threshold: Threshold for converting probabilities to binary

    Returns:
        Base64 encoded PNG string
    """
    # Handle torch tensors (convert bfloat16→float32 if needed)
    if hasattr(mask, "cpu"):
        # Check if it's a floating-point tensor (not boolean)
        if hasattr(mask, "is_floating_point") and mask.is_floating_point():
            mask = mask.float().cpu().numpy()
        else:
            mask = mask.cpu().numpy()

    # Ensure 2D
    if mask.ndim > 2:
        mask = mask.squeeze()

    # Convert to binary if needed
    if mask.dtype != bool and mask.max() <= 1.0:
        mask = mask > threshold

    # Convert to uint8
    mask_uint8 = (mask * 255).astype(np.uint8)

    # Create PIL Image and encode
    mask_image = Image.fromarray(mask_uint8, mode="L")
    buffer = BytesIO()
    mask_image.save(buffer, format="PNG")

    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def crop_image_to_bbox(
    image: Union[Image.Image, np.ndarray],
    bbox: list[float],
    padding: int = 0,
) -> Image.Image:
    """
    Crop an image to a bounding box.

    Args:
        image: PIL Image or numpy array
        bbox: Bounding box [x1, y1, x2, y2] in pixels
        padding: Optional padding to add around the crop

    Returns:
        Cropped PIL Image
    """
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)

    x1, y1, x2, y2 = [int(v) for v in bbox]

    # Apply padding with bounds checking
    if padding > 0:
        width, height = image.size
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(width, x2 + padding)
        y2 = min(height, y2 + padding)

    return image.crop((x1, y1, x2, y2))


def resize_image_if_needed(
    image: Image.Image,
    max_size: int = 2048,
) -> tuple[Image.Image, float]:
    """
    Resize image if larger than max_size while maintaining aspect ratio.

    Args:
        image: PIL Image
        max_size: Maximum dimension (width or height)

    Returns:
        Tuple of (resized image, scale factor)
    """
    width, height = image.size
    max_dim = max(width, height)

    if max_dim <= max_size:
        return image, 1.0

    scale = max_size / max_dim
    new_width = int(width * scale)
    new_height = int(height * scale)

    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return resized, scale


def create_composite_visualization(
    image: Image.Image,
    masks: list[np.ndarray],
    colors: Optional[list[tuple[int, int, int]]] = None,
    alpha: float = 0.4,
) -> Image.Image:
    """
    Create a visualization with colored mask overlays.

    Args:
        image: Original PIL Image
        masks: List of binary masks
        colors: Optional list of RGB colors for each mask
        alpha: Transparency of mask overlays

    Returns:
        Composite visualization image
    """
    if colors is None:
        # Default color palette
        default_colors = [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 255, 0),
            (255, 0, 255),
            (0, 255, 255),
            (128, 0, 0),
            (0, 128, 0),
            (0, 0, 128),
            (128, 128, 0),
        ]
        colors = [default_colors[i % len(default_colors)] for i in range(len(masks))]

    # Create overlay
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    overlay_np = np.array(overlay)

    for mask, color in zip(masks, colors):
        if hasattr(mask, "cpu"):
            # Check if it's a floating-point tensor (not boolean)
            if hasattr(mask, "is_floating_point") and mask.is_floating_point():
                mask = mask.float().cpu().numpy()
            else:
                mask = mask.cpu().numpy()
        if mask.ndim > 2:
            mask = mask.squeeze()

        # Resize mask if needed
        if mask.shape[:2] != (image.height, image.width):
            mask_img = Image.fromarray((mask * 255).astype(np.uint8))
            mask_img = mask_img.resize(image.size, Image.Resampling.NEAREST)
            mask = np.array(mask_img) > 127

        # Apply color where mask is True
        overlay_np[mask, :3] = color
        overlay_np[mask, 3] = int(255 * alpha)

    overlay = Image.fromarray(overlay_np, mode="RGBA")
    composite = Image.alpha_composite(image.convert("RGBA"), overlay)

    return composite.convert("RGB")
