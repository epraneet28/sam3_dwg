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
    # Find Similar Methods
    # =========================================================================

    def extract_region_features(
        self,
        inference_state: dict,
        bbox: tuple[float, float, float, float],
        mask: Optional[np.ndarray] = None,
        feature_level: int = 1,
        pool_size: int = 7,
    ) -> np.ndarray:
        """
        Extract SAM3 backbone features for a specific region.

        Args:
            inference_state: State from processor.set_image() containing backbone_out
            bbox: Region bounding box [x1, y1, x2, y2] in image coordinates
            mask: Optional mask to apply within bbox (for masked average pooling)
            feature_level: FPN level to use (0=highest res, 2=lowest res)
            pool_size: Output size for RoI pooling

        Returns:
            Feature vector (1D numpy array, normalized for cosine similarity)
        """
        import torch.nn.functional as F

        backbone_out = inference_state.get("backbone_out", {})
        backbone_fpn = backbone_out.get("backbone_fpn", [])

        if not backbone_fpn or feature_level >= len(backbone_fpn):
            raise ValueError(
                f"Feature level {feature_level} not available. "
                f"backbone_fpn has {len(backbone_fpn)} levels."
            )

        # Get feature map at requested level
        # Shape: [1, C, H, W] where H, W are feature map dimensions
        feat_map = backbone_fpn[feature_level]
        _, channels, feat_h, feat_w = feat_map.shape

        # Get original image dimensions from inference state
        orig_h = inference_state.get("original_height", 1024)
        orig_w = inference_state.get("original_width", 1024)

        # Convert bbox to feature map coordinates
        x1, y1, x2, y2 = bbox
        scale_x = feat_w / orig_w
        scale_y = feat_h / orig_h

        fx1 = int(x1 * scale_x)
        fy1 = int(y1 * scale_y)
        fx2 = int(x2 * scale_x)
        fy2 = int(y2 * scale_y)

        # Clamp to valid range
        fx1 = max(0, min(fx1, feat_w - 1))
        fy1 = max(0, min(fy1, feat_h - 1))
        fx2 = max(fx1 + 1, min(fx2, feat_w))
        fy2 = max(fy1 + 1, min(fy2, feat_h))

        # Extract region features
        region_feats = feat_map[:, :, fy1:fy2, fx1:fx2]

        # Apply mask if provided (masked average pooling)
        if mask is not None and mask.size > 0:
            # Resize mask to feature map region size
            y1_int, y2_int = int(y1), int(y2)
            x1_int, x2_int = int(x1), int(x2)
            mask_region = mask[y1_int:y2_int, x1_int:x2_int]
            if mask_region.size > 0:
                mask_resized = cv2.resize(
                    mask_region.astype(np.float32),
                    (fx2 - fx1, fy2 - fy1),
                    interpolation=cv2.INTER_NEAREST,
                )
                mask_tensor = torch.from_numpy(mask_resized).to(feat_map.device)
                mask_tensor = mask_tensor.unsqueeze(0).unsqueeze(0)  # [1, 1, H, W]

                # Apply mask and compute weighted average
                masked_feats = region_feats * mask_tensor
                mask_sum = mask_tensor.sum()
                if mask_sum > 0:
                    feature_vector = masked_feats.sum(dim=(2, 3)) / mask_sum
                else:
                    feature_vector = F.adaptive_avg_pool2d(region_feats, 1).squeeze(-1).squeeze(-1)
            else:
                feature_vector = F.adaptive_avg_pool2d(region_feats, 1).squeeze(-1).squeeze(-1)
        else:
            # Use adaptive average pooling for uniform pooling
            pooled = F.adaptive_avg_pool2d(region_feats, pool_size)
            feature_vector = pooled.mean(dim=(2, 3))  # [1, C]

        # Normalize for cosine similarity
        feature_vector = F.normalize(feature_vector, p=2, dim=-1)

        return feature_vector.cpu().numpy().flatten()

    def find_similar(
        self,
        image: Image.Image,
        exemplar_mask: np.ndarray,
        exemplar_bbox: Optional[tuple[float, float, float, float]] = None,
        max_results: int = 10,
        similarity_threshold: float = 0.7,
        nms_threshold: float = 0.5,
        grid_stride: int = 32,
        scale_factors: Optional[list[float]] = None,
        feature_level: int = 1,
    ) -> tuple[list[dict], int, int]:
        """
        Find regions similar to the exemplar mask.

        Args:
            image: PIL Image to search
            exemplar_mask: Binary mask of the exemplar region
            exemplar_bbox: Optional bbox, computed from mask if not provided
            max_results: Maximum number of results to return
            similarity_threshold: Minimum cosine similarity (0-1)
            nms_threshold: IoU threshold for NMS
            grid_stride: Stride for grid-based scanning
            scale_factors: List of scale factors to search (relative to exemplar size)
            feature_level: FPN level for feature extraction

        Returns:
            Tuple of (results list, regions_scanned, regions_above_threshold)
            Each result dict has: region_id, bbox, similarity, mask, iou_score, low_res_logits
        """
        if scale_factors is None:
            scale_factors = [0.5, 0.75, 1.0, 1.25, 1.5]

        img_width, img_height = image.size

        # Compute exemplar bbox from mask if not provided
        if exemplar_bbox is None:
            ys, xs = np.where(exemplar_mask > 0)
            if len(xs) == 0:
                logger.warning("Empty exemplar mask, cannot find similar")
                return [], 0, 0
            exemplar_bbox = (
                float(xs.min()),
                float(ys.min()),
                float(xs.max()),
                float(ys.max()),
            )

        ex1, ey1, ex2, ey2 = exemplar_bbox
        exemplar_width = ex2 - ex1
        exemplar_height = ey2 - ey1

        logger.info(
            f"find_similar: exemplar bbox={exemplar_bbox}, "
            f"searching {len(scale_factors)} scales with stride={grid_stride}"
        )

        # Set image and extract exemplar features
        inference_state = self.processor.set_image(image)

        # Store original dimensions in state for feature extraction
        inference_state["original_width"] = img_width
        inference_state["original_height"] = img_height

        exemplar_features = self.extract_region_features(
            inference_state,
            exemplar_bbox,
            mask=exemplar_mask,
            feature_level=feature_level,
        )

        # Scan image with grid at multiple scales
        candidates = []
        regions_scanned = 0

        for scale in scale_factors:
            window_w = int(exemplar_width * scale)
            window_h = int(exemplar_height * scale)

            # Skip if window is too small or too large
            if window_w < 16 or window_h < 16:
                continue
            if window_w > img_width * 0.9 or window_h > img_height * 0.9:
                continue

            # Scan with grid
            for y in range(0, img_height - window_h, grid_stride):
                for x in range(0, img_width - window_w, grid_stride):
                    # Skip if overlaps significantly with exemplar
                    candidate_bbox = (float(x), float(y), float(x + window_w), float(y + window_h))
                    iou_with_exemplar = self._compute_bbox_iou(candidate_bbox, exemplar_bbox)
                    if iou_with_exemplar > 0.5:
                        continue  # Skip the exemplar region itself

                    regions_scanned += 1

                    # Extract features for candidate
                    try:
                        candidate_features = self.extract_region_features(
                            inference_state,
                            candidate_bbox,
                            feature_level=feature_level,
                        )

                        # Compute cosine similarity
                        similarity = float(np.dot(exemplar_features, candidate_features))

                        if similarity >= similarity_threshold:
                            candidates.append({
                                "bbox": candidate_bbox,
                                "similarity": similarity,
                                "scale": scale,
                            })
                    except Exception as e:
                        logger.debug(f"Feature extraction failed for region {candidate_bbox}: {e}")
                        continue

        regions_above_threshold = len(candidates)
        logger.info(
            f"find_similar: scanned {regions_scanned} regions, "
            f"found {regions_above_threshold} above threshold {similarity_threshold}"
        )

        if not candidates:
            return [], regions_scanned, 0

        # Sort by similarity (best first)
        candidates.sort(key=lambda c: c["similarity"], reverse=True)

        # Apply NMS
        kept_candidates = self._apply_bbox_nms(candidates, nms_threshold)

        # Limit results
        kept_candidates = kept_candidates[:max_results]

        # Run SAM3 segmentation on each kept candidate to get masks
        results = []
        for i, candidate in enumerate(kept_candidates):
            bbox = candidate["bbox"]
            try:
                masks, iou_scores, bboxes, low_res_logits = self.segment_interactive(
                    image=image,
                    box=np.array(bbox),
                    multimask_output=False,  # Single best mask
                )

                if len(masks) > 0:
                    results.append({
                        "region_id": f"similar_{i:03d}",
                        "bbox": bboxes[0],
                        "similarity": candidate["similarity"],
                        "mask": masks[0],
                        "iou_score": iou_scores[0],
                        "low_res_logits": low_res_logits[0] if low_res_logits else None,
                    })
            except Exception as e:
                logger.warning(f"Segmentation failed for similar region {i}: {e}")
                continue

        logger.info(f"find_similar: returning {len(results)} segmented regions")
        return results, regions_scanned, regions_above_threshold

    def _compute_bbox_iou(
        self,
        box1: tuple[float, float, float, float],
        box2: tuple[float, float, float, float],
    ) -> float:
        """Compute IoU between two bounding boxes."""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        if x2 <= x1 or y2 <= y1:
            return 0.0

        intersection = (x2 - x1) * (y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0

    def _apply_bbox_nms(
        self,
        candidates: list[dict],
        iou_threshold: float,
    ) -> list[dict]:
        """Apply Non-Maximum Suppression to candidates."""
        if len(candidates) <= 1:
            return candidates

        kept = []
        for candidate in candidates:
            should_keep = True
            for kept_candidate in kept:
                iou = self._compute_bbox_iou(candidate["bbox"], kept_candidate["bbox"])
                if iou > iou_threshold:
                    should_keep = False
                    break
            if should_keep:
                kept.append(candidate)

        return kept

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
