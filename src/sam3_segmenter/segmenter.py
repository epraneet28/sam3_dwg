"""SAM3 wrapper class for drawing segmentation using Meta's official SAM3."""

import logging
from pathlib import Path
from typing import Optional, Union

import numpy as np
import torch
from PIL import Image

from .config import settings
from .models import ZoneResult
from .prompts.structural import STRUCTURAL_ZONE_PROMPTS, get_zone_type_from_prompt
from .utils.geometry import normalize_bbox, calculate_area_ratio
from .utils.image import encode_mask_to_base64, crop_image_to_bbox, encode_image_to_base64

logger = logging.getLogger(__name__)


class DrawingSegmenter:
    """SAM3-based segmenter for engineering drawings using Meta's official implementation."""

    def __init__(
        self,
        model_path: str = "sam3.pt",
        device: Optional[str] = None,
        confidence_threshold: float = 0.3,
    ):
        """
        Initialize the DrawingSegmenter.

        Args:
            model_path: Path to SAM3 model weights
            device: Device to use ('cuda' or 'cpu'). None for auto-detect.
            confidence_threshold: Default minimum confidence threshold
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.confidence_threshold = confidence_threshold
        self.model_path = model_path
        self._model = None
        self._processor = None
        self._exemplars: dict[str, list[np.ndarray]] = {}

        logger.info(f"Initializing DrawingSegmenter on device: {self.device}")

    @property
    def model(self):
        """Lazy-load the SAM3 model."""
        if self._model is None:
            self._load_model()
        return self._model

    @property
    def processor(self):
        """Get the SAM3 processor."""
        if self._processor is None:
            # Processor is created when model is loaded
            _ = self.model
        return self._processor

    def _load_model(self):
        """Load the SAM3 model using Meta's official implementation."""
        try:
            from sam3 import build_sam3_image_model
            from sam3.model.sam3_image_processor import Sam3Processor

            logger.info(f"Loading SAM3 model from {self.model_path}")

            # Build SAM3 model with instance interactivity enabled for point/box prompts
            self._model = build_sam3_image_model(
                checkpoint_path=self.model_path,
                device=self.device,
                eval_mode=True,
                enable_segmentation=True,
                enable_inst_interactivity=True,
            )

            # Create processor
            self._processor = Sam3Processor(
                model=self._model,
                device=self.device,
                confidence_threshold=self.confidence_threshold,
            )

            logger.info("SAM3 model loaded successfully")
        except ImportError as e:
            logger.warning(
                f"SAM3 not available: {e}. Using mock implementation for development."
            )
            self._model = MockSAM3Model()
            self._processor = None
        except Exception as e:
            logger.error(f"Failed to load SAM3 model: {e}")
            raise

    def segment(
        self,
        image: Image.Image,
        prompts: list[str],
        exemplars: Optional[list[np.ndarray]] = None,
        confidence_threshold: Optional[float] = None,
        return_masks: bool = True,
        return_crops: bool = False,
    ) -> list[ZoneResult]:
        """
        Segment an image using SAM3 with text prompts.

        Args:
            image: PIL Image to segment
            prompts: List of text prompts describing zones to find
            exemplars: Optional list of example image crops (currently not implemented)
            confidence_threshold: Override default threshold
            return_masks: Include base64 encoded masks in results
            return_crops: Include base64 encoded crops in results

        Returns:
            List of ZoneResult objects
        """
        threshold = confidence_threshold or self.confidence_threshold
        img_width, img_height = image.size

        # Handle mock model case
        if isinstance(self._model, MockSAM3Model):
            return self._segment_with_mock(image, prompts, threshold, return_masks, return_crops)

        zones = []
        zone_counter = 0

        try:
            # Set the image in the processor (this processes the backbone)
            state = self.processor.set_image(image)

            # Process each prompt
            for prompt_text in prompts:
                try:
                    # Reset prompts from previous iteration
                    self.processor.reset_all_prompts(state)

                    # Set text prompt and run grounding inference
                    # This updates the state with boxes, masks, and scores
                    state = self.processor.set_text_prompt(prompt_text, state)

                    # Extract predictions from state
                    pred_boxes = state.get("boxes", torch.tensor([]))
                    scores = state.get("scores", torch.tensor([]))
                    pred_masks = state.get("masks", torch.tensor([]))

                    # Process each detection
                    num_detections = len(pred_boxes) if len(pred_boxes.shape) > 0 else 0
                    for idx in range(num_detections):
                        try:
                            score = float(scores[idx].cpu().item()) if idx < len(scores) else 0.5

                            if score < threshold:
                                continue

                            # Get bounding box (already in [x1, y1, x2, y2] format and original image coords)
                            box = pred_boxes[idx]
                            if isinstance(box, torch.Tensor):
                                box = box.cpu().numpy()

                            bbox = [float(box[0]), float(box[1]), float(box[2]), float(box[3])]

                            # Get mask if available
                            mask_b64 = None
                            if return_masks and idx < len(pred_masks):
                                mask = pred_masks[idx]
                                if isinstance(mask, torch.Tensor):
                                    # Mask shape is (1, H, W), squeeze to (H, W)
                                    mask = mask.squeeze(0).cpu().numpy()
                                mask_b64 = encode_mask_to_base64(mask)

                            # Get crop if requested
                            crop_b64 = None
                            if return_crops:
                                crop = crop_image_to_bbox(image, bbox, padding=5)
                                crop_b64 = encode_image_to_base64(crop)

                            # Create zone result
                            zone = ZoneResult(
                                zone_id=f"zone_{zone_counter:03d}",
                                zone_type=get_zone_type_from_prompt(prompt_text),
                                prompt_matched=prompt_text,
                                confidence=score,
                                bbox=bbox,
                                bbox_normalized=normalize_bbox(bbox, img_width, img_height),
                                area_ratio=calculate_area_ratio(bbox, img_width, img_height),
                                mask_base64=mask_b64,
                                crop_base64=crop_b64,
                            )
                            zones.append(zone)
                            zone_counter += 1

                        except Exception as e:
                            logger.warning(f"Failed to process detection {idx} for prompt '{prompt_text}': {e}", exc_info=True)
                            continue

                except Exception as e:
                    logger.warning(f"Failed to process prompt '{prompt_text}': {e}", exc_info=True)
                    continue

        except Exception as e:
            logger.error(f"SAM3 inference failed: {e}", exc_info=True)
            raise

        return zones

    def _segment_with_mock(
        self,
        image: Image.Image,
        prompts: list[str],
        threshold: float,
        return_masks: bool,
        return_crops: bool,
    ) -> list[ZoneResult]:
        """Segment using mock model for development."""
        img_width, img_height = image.size
        results = self._model(image, prompts=prompts)

        zones = []
        zone_counter = 0

        if hasattr(results, "__iter__") and len(results) > 0:
            result = results[0] if isinstance(results, list) else results
            boxes = getattr(result, "boxes", None)
            masks = getattr(result, "masks", None)

            if boxes is not None:
                for i in range(len(boxes)):
                    try:
                        box = boxes[i]
                        conf = float(box.conf.cpu().numpy().item()) if hasattr(box, "conf") else 0.5

                        if conf < threshold:
                            continue

                        bbox = [float(v) for v in box.xyxy[0].cpu().numpy()] if hasattr(box, "xyxy") else None
                        if bbox is None:
                            continue

                        prompt_idx = min(i, len(prompts) - 1)
                        matched_prompt = prompts[prompt_idx]

                        mask_b64 = None
                        if return_masks and masks is not None and i < len(masks):
                            mask = masks[i]
                            if hasattr(mask, "data"):
                                mask = mask.data
                            mask_b64 = encode_mask_to_base64(mask)

                        crop_b64 = None
                        if return_crops:
                            crop = crop_image_to_bbox(image, bbox, padding=5)
                            crop_b64 = encode_image_to_base64(crop)

                        zone = ZoneResult(
                            zone_id=f"zone_{zone_counter:03d}",
                            zone_type=get_zone_type_from_prompt(matched_prompt),
                            prompt_matched=matched_prompt,
                            confidence=conf,
                            bbox=bbox,
                            bbox_normalized=normalize_bbox(bbox, img_width, img_height),
                            area_ratio=calculate_area_ratio(bbox, img_width, img_height),
                            mask_base64=mask_b64,
                            crop_base64=crop_b64,
                        )
                        zones.append(zone)
                        zone_counter += 1

                    except Exception as e:
                        logger.warning(f"Failed to process detection {i}: {e}")
                        continue

        return zones

    def segment_structural(
        self,
        image: Image.Image,
        return_masks: bool = True,
        return_crops: bool = False,
        prompt_config: Optional[list] = None,
    ) -> list[ZoneResult]:
        """
        Segment using pre-configured structural drawing prompts.

        Args:
            image: PIL Image to segment
            return_masks: Include masks in results
            return_crops: Include crops in results
            prompt_config: Optional list of ZonePromptConfig dicts to use instead of defaults.
                           If provided, only enabled prompts will be used.

        Returns:
            List of detected zones
        """
        # Use custom config if provided, otherwise use defaults
        if prompt_config is not None:
            # Filter to only enabled prompts
            prompts = [
                p["primary_prompt"]
                for p in prompt_config
                if p.get("enabled", True)
            ]
        else:
            # Use all default prompts
            prompts = [config["primary_prompt"] for config in STRUCTURAL_ZONE_PROMPTS.values()]

        zones = self.segment(
            image=image,
            prompts=prompts,
            return_masks=return_masks,
            return_crops=return_crops,
        )

        return zones

    def segment_interactive(
        self,
        image: Image.Image,
        point_coords: Optional[np.ndarray] = None,
        point_labels: Optional[np.ndarray] = None,
        box: Optional[np.ndarray] = None,
        mask_input: Optional[np.ndarray] = None,
        multimask_output: bool = True,
    ) -> tuple[list[np.ndarray], list[float], list[tuple[float, float, float, float]]]:
        """
        Segment using point and/or box prompts (PVS mode).

        This uses SAM3's Promptable Visual Segmentation capability for
        instance-specific segmentation at specified locations.

        Args:
            image: PIL Image to segment
            point_coords: Nx2 array of point coordinates [[x, y], ...]
            point_labels: N array of point labels (1=positive, 0=negative)
            box: Box prompt [x1, y1, x2, y2]
            mask_input: Previous mask to refine, low-resolution logits shape [1, H, W]
            multimask_output: Return multiple mask candidates

        Returns:
            Tuple of (masks, iou_scores, bboxes) where:
            - masks: List of binary mask arrays
            - iou_scores: List of predicted IOU scores
            - bboxes: List of bounding boxes [x1, y1, x2, y2]
        """
        # For mock model, generate mock results
        if isinstance(self._model, MockSAM3Model):
            return self._generate_mock_interactive_results(
                image, point_coords, point_labels, box, multimask_output
            )

        # Check that interactive predictor is available
        if self.model.inst_interactive_predictor is None:
            raise RuntimeError(
                "Interactive predictor not available. Model must be built with "
                "enable_inst_interactivity=True"
            )

        # Use processor to set image and get inference_state with backbone features
        inference_state = self.processor.set_image(image)

        # Call predict_inst on the model with the inference_state
        # This uses the shared backbone features and routes to the interactive predictor
        masks, iou_preds, _ = self.model.predict_inst(
            inference_state,
            point_coords=point_coords,
            point_labels=point_labels,
            box=box,
            mask_input=mask_input,
            multimask_output=multimask_output,
        )

        # Build output - masks is numpy array from predict_inst()
        result_masks = []
        result_ious = []
        result_bboxes = []

        for i in range(len(masks)):
            mask = masks[i]
            iou = iou_preds[i]

            # Get bounding box from mask
            ys, xs = np.where(mask)
            if len(xs) > 0 and len(ys) > 0:
                x1, y1 = xs.min(), ys.min()
                x2, y2 = xs.max(), ys.max()
                bbox = (float(x1), float(y1), float(x2), float(y2))
            else:
                bbox = (0.0, 0.0, 0.0, 0.0)

            result_masks.append(mask)
            result_ious.append(float(iou))
            result_bboxes.append(bbox)

        return result_masks, result_ious, result_bboxes

    def _generate_mock_interactive_results(
        self,
        image: Image.Image,
        point_coords: Optional[np.ndarray],
        point_labels: Optional[np.ndarray],
        box: Optional[np.ndarray],
        multimask_output: bool,
    ) -> tuple[list[np.ndarray], list[float], list[tuple[float, float, float, float]]]:
        """Generate mock results for interactive segmentation (testing without GPU)."""
        img_width, img_height = image.size

        # Determine region of interest from prompts
        if box is not None:
            x1, y1, x2, y2 = box
        elif point_coords is not None and len(point_coords) > 0:
            # Create a box around the points
            xs = point_coords[:, 0]
            ys = point_coords[:, 1]
            cx, cy = xs.mean(), ys.mean()
            # Create a region around the center
            size = min(img_width, img_height) * 0.3
            x1 = max(0, cx - size)
            y1 = max(0, cy - size)
            x2 = min(img_width, cx + size)
            y2 = min(img_height, cy + size)
        else:
            # Default to center region
            x1 = img_width * 0.25
            y1 = img_height * 0.25
            x2 = img_width * 0.75
            y2 = img_height * 0.75

        # Generate mock masks with different sizes
        num_masks = 3 if multimask_output else 1
        masks = []
        ious = []
        bboxes = []

        for i in range(num_masks):
            # Create mask with slightly different sizes
            scale = 1.0 - (i * 0.15)
            mask = np.zeros((img_height, img_width), dtype=bool)

            # Calculate scaled region
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            w = (x2 - x1) * scale
            h = (y2 - y1) * scale

            mx1 = int(max(0, cx - w / 2))
            my1 = int(max(0, cy - h / 2))
            mx2 = int(min(img_width, cx + w / 2))
            my2 = int(min(img_height, cy + h / 2))

            mask[my1:my2, mx1:mx2] = True

            masks.append(mask)
            ious.append(0.95 - (i * 0.1))  # Decreasing IOU scores
            bboxes.append((float(mx1), float(my1), float(mx2), float(my2)))

        return masks, ious, bboxes

    def load_exemplar(self, zone_type: str, image_path: Union[str, Path]):
        """
        Load a visual exemplar for a zone type.

        Args:
            zone_type: Type of zone this exemplar represents
            image_path: Path to the exemplar image
        """
        img = Image.open(image_path)
        if img.mode != "RGB":
            img = img.convert("RGB")

        if zone_type not in self._exemplars:
            self._exemplars[zone_type] = []

        self._exemplars[zone_type].append(np.array(img))
        logger.info(f"Loaded exemplar for {zone_type}: {image_path}")

    def load_exemplars_from_directory(self, directory: Union[str, Path]):
        """
        Load all exemplars from a directory structure.

        Expected structure:
            directory/
                zone_type_1/
                    image1.png
                    image2.png
                zone_type_2/
                    image1.png
        """
        directory = Path(directory)
        if not directory.exists():
            logger.warning(f"Exemplars directory does not exist: {directory}")
            return

        for zone_dir in directory.iterdir():
            if zone_dir.is_dir():
                zone_type = zone_dir.name
                for img_path in zone_dir.glob("*.png"):
                    self.load_exemplar(zone_type, img_path)
                for img_path in zone_dir.glob("*.jpg"):
                    self.load_exemplar(zone_type, img_path)

    def get_exemplars(self, zone_type: str) -> list[np.ndarray]:
        """Get loaded exemplars for a zone type."""
        return self._exemplars.get(zone_type, [])

    @property
    def is_gpu_available(self) -> bool:
        """Check if GPU is available."""
        return torch.cuda.is_available()

    @property
    def gpu_info(self) -> dict:
        """Get GPU information."""
        if not self.is_gpu_available:
            return {"available": False}

        return {
            "available": True,
            "name": torch.cuda.get_device_name(0),
            "memory_allocated_mb": torch.cuda.memory_allocated(0) // (1024 * 1024),
            "memory_reserved_mb": torch.cuda.memory_reserved(0) // (1024 * 1024),
        }


class MockSAM3Model:
    """Mock SAM3 model for development/testing when SAM3 is not available."""

    def __call__(self, image, prompts=None, **kwargs):
        """Return mock results for testing."""
        logger.warning("Using MockSAM3Model - results are not real segmentation")

        # Create mock results
        if isinstance(image, Image.Image):
            width, height = image.size
        else:
            height, width = image.shape[:2]

        mock_results = MockResults(width, height, prompts or [])
        return [mock_results]


class MockResults:
    """Mock results object for testing."""

    def __init__(self, width: int, height: int, prompts: list[str]):
        self.boxes = MockBoxes(width, height, len(prompts))
        self.masks = MockMasks(width, height, len(prompts))


class MockBoxes:
    """Mock boxes for testing."""

    def __init__(self, width: int, height: int, num_boxes: int):
        self.width = width
        self.height = height
        self.num_boxes = num_boxes

    def __len__(self):
        return self.num_boxes

    def __getitem__(self, idx):
        # Return a mock box in a typical location
        if idx == 0:  # Title block - bottom right
            x1, y1 = self.width * 0.7, self.height * 0.8
            x2, y2 = self.width * 0.98, self.height * 0.98
        else:
            # Random position for other boxes
            x1 = self.width * (0.1 + 0.2 * (idx % 4))
            y1 = self.height * (0.1 + 0.2 * (idx // 4))
            x2 = x1 + self.width * 0.2
            y2 = y1 + self.height * 0.2

        return MockBox([x1, y1, x2, y2], conf=0.5 + 0.1 * (idx % 5))


class MockBox:
    """Mock single box for testing."""

    def __init__(self, coords: list[float], conf: float = 0.5):
        self.xyxy = [torch.tensor(coords)]
        self.conf = torch.tensor([conf])


class MockMasks:
    """Mock masks for testing."""

    def __init__(self, width: int, height: int, num_masks: int):
        self.width = width
        self.height = height
        self.num_masks = num_masks

    def __len__(self):
        return self.num_masks

    def __getitem__(self, idx):
        # Return a simple mock mask
        mask = np.zeros((self.height, self.width), dtype=np.float32)
        # Fill a region
        y1, y2 = int(self.height * 0.3), int(self.height * 0.7)
        x1, x2 = int(self.width * 0.3), int(self.width * 0.7)
        mask[y1:y2, x1:x2] = 1.0
        return MockMask(mask)


class MockMask:
    """Mock single mask for testing."""

    def __init__(self, data: np.ndarray):
        self.data = torch.tensor(data)
