"""SAM3 wrapper class for drawing segmentation using Meta's official SAM3."""

import logging
from pathlib import Path
from typing import Optional, Union

import cv2
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

            # Configure interactive predictor transforms based on settings
            # In precision mode (default), we use 0 for both to preserve raw SAM output
            # For zone segmentation workflows, higher values smooth the output
            try:
                from sam3.model.utils.sam1_utils import SAM2Transforms

                if self._model.inst_interactive_predictor is not None:
                    predictor = self._model.inst_interactive_predictor
                    # Use configurable settings (default: 0,0 for precision mode)
                    max_hole = settings.interactive_max_hole_area
                    max_sprinkle = settings.interactive_max_sprinkle_area
                    predictor._transforms = SAM2Transforms(
                        resolution=predictor.model.image_size,
                        mask_threshold=0.0,
                        max_hole_area=max_hole,
                        max_sprinkle_area=max_sprinkle,
                    )
                    if max_hole == 0 and max_sprinkle == 0:
                        logger.info(
                            "SAM3 interactive predictor: raw mode (no hole/sprinkle removal) "
                            "for pixel-precise masks"
                        )
                    else:
                        logger.info(
                            f"SAM3 interactive predictor configured: "
                            f"max_hole_area={max_hole}, max_sprinkle_area={max_sprinkle}"
                        )
            except Exception as e:
                logger.warning(f"Could not configure SAM transforms: {e}", exc_info=True)

        except ImportError as e:
            logger.error(
                f"SAM3 not available: {e}. "
                "Please install SAM3: cd sam3_reference && pip install -e ."
            )
            raise ImportError(
                f"SAM3 is required but not installed: {e}. "
                "Install with: cd sam3_reference && pip install -e ."
            ) from e
        except Exception as e:
            logger.error(f"Failed to load SAM3 model: {e}", exc_info=True)
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
                                box = box.float().cpu().numpy()  # bfloat16→float32

                            bbox = [float(box[0]), float(box[1]), float(box[2]), float(box[3])]

                            # Get mask if available
                            mask_b64 = None
                            if return_masks and idx < len(pred_masks):
                                mask = pred_masks[idx]
                                if isinstance(mask, torch.Tensor):
                                    # Mask shape is (1, H, W), squeeze to (H, W)
                                    # Convert to float32 first (SAM3 may output bfloat16)
                                    mask = mask.squeeze(0).float().cpu().numpy()
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
    ) -> tuple[list[np.ndarray], list[float], list[tuple[float, float, float, float]], list[np.ndarray]]:
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
            multimask_output: Return multiple mask candidates. Note: For box prompts
                (with or without points), this is automatically set to False to return
                SAM3's single best mask, following Meta's recommendation that
                non-ambiguous prompts should use single mask output for better quality.

        Returns:
            Tuple of (masks, iou_scores, bboxes, low_res_logits) where:
            - masks: List of binary mask arrays (full resolution)
            - iou_scores: List of predicted IOU scores
            - bboxes: List of bounding boxes [x1, y1, x2, y2]
            - low_res_logits: List of 256x256 logit arrays for refinement
        """
        # SAM3 best practice: Box prompts are "non-ambiguous" and should use single mask
        # output (multimask_output=False) for better quality. When multimask_output=True,
        # SAM3 returns 3 candidate masks and uses IoU-based selection which may pick
        # suboptimal masks (e.g., background-fill instead of precise object outline).
        # See sam1_task_predictor.py lines 254-259 for Meta's documentation.
        # This behavior is configurable via SAM3_FORCE_SINGLE_MASK_FOR_BOX env var.
        if box is not None and multimask_output and settings.force_single_mask_for_box:
            logger.debug(
                "Box prompt detected, using multimask_output=False for higher quality "
                "(SAM3 recommendation for non-ambiguous prompts). "
                "Set SAM3_FORCE_SINGLE_MASK_FOR_BOX=false to enable multi-mask for boxes."
            )
            multimask_output = False

        # Check that interactive predictor is available
        if self.model.inst_interactive_predictor is None:
            raise RuntimeError(
                "Interactive predictor not available. Model must be built with "
                "enable_inst_interactivity=True"
            )

        # Use processor to compute backbone features from the main model
        # The inference_state contains backbone_out with sam2_backbone_out features
        inference_state = self.processor.set_image(image)

        # Log the inference state structure for debugging
        logger.debug(f"Inference state keys: {inference_state.keys()}")
        if "backbone_out" in inference_state:
            logger.debug(f"backbone_out keys: {inference_state['backbone_out'].keys()}")

        # Call predict_inst which:
        # 1. Extracts backbone features from inference_state
        # 2. Sets them up on the interactive predictor
        # 3. Calls the interactive predictor's predict method
        # Returns: (masks, iou_predictions, low_res_masks)
        # low_res_masks are 256x256 logits used for refinement
        masks, iou_preds, low_res_masks = self.model.predict_inst(
            inference_state,
            point_coords=point_coords,
            point_labels=point_labels,
            box=box,
            mask_input=mask_input,
            multimask_output=multimask_output,
        )

        # Log dimensions for debugging coordinate/mask issues
        img_width, img_height = image.size
        if len(masks) > 0:
            mask_shape = masks[0].shape if hasattr(masks[0], 'shape') else 'unknown'
            logger.debug(
                f"Interactive segmentation: image=({img_width}x{img_height}), "
                f"mask_shape={mask_shape}, num_masks={len(masks)}, "
                f"box={box.tolist() if box is not None else None}"
            )
            # Verify mask dimensions match image (height, width order for numpy)
            if hasattr(masks[0], 'shape') and masks[0].shape != (img_height, img_width):
                logger.warning(
                    f"MASK DIMENSION MISMATCH! mask={masks[0].shape}, "
                    f"expected=({img_height}, {img_width}). This may cause display issues."
                )

        # Build output - masks is numpy array from predict_inst()
        result_masks = []
        result_ious = []
        result_bboxes = []
        result_low_res = []

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

            # Include low-res logits for refinement (shape: [H, W] typically 256x256)
            if i < len(low_res_masks):
                result_low_res.append(low_res_masks[i])
            else:
                result_low_res.append(None)

        return result_masks, result_ious, result_bboxes, result_low_res

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

    # =========================================================================
    # Find Similar - SAM3 Native Exemplar Detection
    # =========================================================================

    def find_similar_native(
        self,
        image: Image.Image,
        exemplar_bbox: tuple[float, float, float, float],
        max_results: int = 10,
        confidence_threshold: float = 0.3,
        exclude_overlap_threshold: float = 0.5,
    ) -> tuple[list[dict], int]:
        """
        Find similar regions using SAM3's native exemplar detection.

        This is the CORRECT approach - SAM3's DETR-based detector has built-in
        support for visual exemplars via geometric prompts. No custom similarity
        computation needed.

        How it works:
        1. Provide exemplar bbox as positive geometric prompt
        2. SAM3 internally uses "visual" as text prompt (no text needed)
        3. DETR detector finds ALL similar objects in one forward pass
        4. Filter out the original exemplar by overlap

        This replaces the custom Per-SAM style dense similarity approach (v1-v5)
        which incorrectly used FPN features for similarity matching.

        Args:
            image: PIL Image to search
            exemplar_bbox: Bounding box of exemplar [x1, y1, x2, y2] in pixels
            max_results: Maximum results to return (excluding exemplar)
            confidence_threshold: SAM3 detection confidence threshold
            exclude_overlap_threshold: IoU threshold to exclude exemplar

        Returns:
            Tuple of (results list, total_detections)
            Each result has: region_id, bbox, mask, similarity (confidence score)
        """
        img_width, img_height = image.size
        ex1, ey1, ex2, ey2 = exemplar_bbox

        # Convert bbox from [x1, y1, x2, y2] to normalized [cx, cy, w, h]
        # SAM3 expects center format normalized to [0, 1]
        cx = ((ex1 + ex2) / 2) / img_width
        cy = ((ey1 + ey2) / 2) / img_height
        w = (ex2 - ex1) / img_width
        h = (ey2 - ey1) / img_height
        norm_box = [cx, cy, w, h]

        logger.info(
            f"find_similar_native: exemplar bbox={exemplar_bbox}, "
            f"normalized={norm_box}, confidence={confidence_threshold}"
        )

        # Set image and get backbone features
        inference_state = self.processor.set_image(image)

        # Reset any previous prompts
        self.processor.reset_all_prompts(inference_state)

        # Set confidence threshold
        self.processor.set_confidence_threshold(confidence_threshold, inference_state)

        # Add exemplar as POSITIVE geometric prompt
        # SAM3 will automatically use "visual" as text prompt internally
        inference_state = self.processor.add_geometric_prompt(
            box=norm_box,
            label=True,  # Positive prompt = find similar
            state=inference_state,
        )

        # Extract results from inference state
        if "masks" not in inference_state or len(inference_state["masks"]) == 0:
            logger.info("find_similar_native: no detections found")
            return [], 0

        masks = inference_state["masks"]  # [N, 1, H, W] boolean
        boxes = inference_state["boxes"]  # [N, 4] in [x1, y1, x2, y2] pixel coords
        scores = inference_state["scores"]  # [N] confidence scores
        masks_logits = inference_state.get("masks_logits")  # [N, 1, H, W] float

        total_detections = len(masks)
        logger.info(f"find_similar_native: SAM3 returned {total_detections} detections")

        results = []
        for i in range(total_detections):
            # Get mask and bbox
            # Note: masks is bool (from >0.5 comparison), others may be bfloat16
            # Must convert bfloat16 to float32 before .numpy() since numpy doesn't support bfloat16
            mask = masks[i].squeeze().cpu().numpy()  # [H, W] - bool, no conversion needed
            bbox = boxes[i].float().cpu().numpy()  # [x1, y1, x2, y2] - bfloat16→float32
            score = float(scores[i].float().cpu().numpy())  # bfloat16→float32

            rx1, ry1, rx2, ry2 = bbox

            # Check overlap with exemplar to exclude the exemplar itself
            # Compute IoU between result bbox and exemplar bbox
            ix1 = max(ex1, rx1)
            iy1 = max(ey1, ry1)
            ix2 = min(ex2, rx2)
            iy2 = min(ey2, ry2)

            if ix2 > ix1 and iy2 > iy1:
                intersection = (ix2 - ix1) * (iy2 - iy1)
                exemplar_area = (ex2 - ex1) * (ey2 - ey1)
                result_area = (rx2 - rx1) * (ry2 - ry1)
                union = exemplar_area + result_area - intersection
                iou = intersection / union if union > 0 else 0

                if iou > exclude_overlap_threshold:
                    logger.debug(f"Detection {i} excluded: IoU {iou:.2f} with exemplar")
                    continue

            # Get low-res logits if available
            # masks_logits may be bfloat16, convert to float32 for numpy
            low_res_logits = None
            if masks_logits is not None:
                low_res_logits = masks_logits[i].squeeze().float().cpu().numpy()

            results.append({
                "region_id": f"similar_{len(results):03d}",
                "bbox": bbox,
                "mask": mask,
                "similarity": score,  # SAM3's confidence score
                "iou_score": score,
                "low_res_logits": low_res_logits,
            })

            if len(results) >= max_results:
                break

        # Sort by confidence (already sorted by SAM3, but ensure)
        results.sort(key=lambda r: r["similarity"], reverse=True)

        logger.info(
            f"find_similar_native: returning {len(results)} results "
            f"(excluded {total_detections - len(results)} as exemplar/low-score)"
        )

        return results, total_detections

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
