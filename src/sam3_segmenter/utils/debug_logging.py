"""Debug logging utility for SAM3 segmentation runs.

Saves verbose debug information to storage directory for each run including:
- All configuration settings
- Input data (points, boxes, prompts, image info)
- Output data (masks, scores, bounding boxes)
- Timing information
- Raw mask images for visual inspection
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np
from PIL import Image

from ..config import settings

logger = logging.getLogger(__name__)


class DebugLogger:
    """Handles verbose debug logging for SAM3 runs."""

    def __init__(self, storage_path: Optional[Path] = None, run_id: Optional[str] = None):
        """
        Initialize debug logger.

        Args:
            storage_path: Path to document storage directory (e.g., storage/doc_id/)
            run_id: Unique identifier for this run (auto-generated if None)
        """
        self.enabled = settings.enable_debug_logging
        self.log_masks = settings.debug_log_masks
        self.log_inputs = settings.debug_log_inputs

        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.start_time = time.time()
        self.log_data: dict[str, Any] = {
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "settings": {},
            "inputs": {},
            "outputs": {},
            "timing": {},
            "errors": [],
        }

        # Set up debug directory
        self.debug_dir: Optional[Path] = None
        if storage_path and self.enabled:
            self.debug_dir = Path(storage_path) / "debug_logs" / self.run_id
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Debug logging enabled: {self.debug_dir}")

    def log_settings(self) -> None:
        """Log all current configuration settings."""
        if not self.enabled:
            return

        self.log_data["settings"] = {
            # Model settings
            "model_path": settings.model_path,
            "default_confidence_threshold": settings.default_confidence_threshold,
            "device": settings.device,
            # Precision mode settings (Smart Select / engineering drawings)
            "enable_precision_mode": settings.enable_precision_mode,
            "precision_mode_multimask": settings.precision_mode_multimask,
            "mask_selection_mode": settings.mask_selection_mode,
            "mask_binarization_threshold": settings.mask_binarization_threshold,
            "enable_complexity_scoring": settings.enable_complexity_scoring,
            "complexity_weight": settings.complexity_weight,
            "component_complexity_bonus": settings.component_complexity_bonus,
            "enable_precision_dilation": settings.enable_precision_dilation,
            "precision_dilation_pixels": settings.precision_dilation_pixels,
            "enable_precision_smoothing": settings.enable_precision_smoothing,
            "precision_smoothing_kernel": settings.precision_smoothing_kernel,
            "enable_candidate_union": settings.enable_candidate_union,
            "candidate_union_topk": settings.candidate_union_topk,
            # Mask post-processing
            "enable_mask_postprocessing": settings.enable_mask_postprocessing,
            "mask_min_component_area": settings.mask_min_component_area,
            "mask_fill_holes": settings.mask_fill_holes,
            "mask_max_hole_area": settings.mask_max_hole_area,
            "mask_apply_morphology": settings.mask_apply_morphology,
            "mask_morphology_kernel_size": settings.mask_morphology_kernel_size,
            # Drawing-specific post-processing
            "enable_drawing_mode": settings.enable_drawing_mode,
            "drawing_keep_largest_only": settings.drawing_keep_largest_only,
            "drawing_fill_all_holes": settings.drawing_fill_all_holes,
            "drawing_min_area_ratio": settings.drawing_min_area_ratio,
            "drawing_fill_method": settings.drawing_fill_method,
            "drawing_morphology_kernel": settings.drawing_morphology_kernel,
            # Advanced filtering
            "enable_stability_filtering": settings.enable_stability_filtering,
            "stability_score_thresh": settings.stability_score_thresh,
            "enable_nms": settings.enable_nms,
            "nms_iou_threshold": settings.nms_iou_threshold,
            "enable_edge_rejection": settings.enable_edge_rejection,
            "edge_tolerance_pixels": settings.edge_tolerance_pixels,
            "enable_non_overlapping": settings.enable_non_overlapping,
            "enable_iou_filtering": settings.enable_iou_filtering,
            "min_iou_score": settings.min_iou_score,
            # Box behavior
            "force_single_mask_for_box": settings.force_single_mask_for_box,
            "enable_box_constraint": settings.enable_box_constraint,
            "box_constraint_margin": settings.box_constraint_margin,
            # Debug settings
            "enable_debug_logging": settings.enable_debug_logging,
            "debug_log_masks": settings.debug_log_masks,
            "debug_log_inputs": settings.debug_log_inputs,
        }
        logger.debug(f"Settings logged: {len(self.log_data['settings'])} parameters")

    def log_input_image(
        self,
        image: Image.Image,
        image_base64: Optional[str] = None,
    ) -> None:
        """Log input image information."""
        if not self.enabled:
            return

        self.log_data["inputs"]["image"] = {
            "width": image.size[0],
            "height": image.size[1],
            "mode": image.mode,
            "format": getattr(image, "format", None),
        }

        if self.log_inputs and image_base64:
            # Store truncated base64 for reference (first/last 100 chars)
            self.log_data["inputs"]["image"]["base64_preview"] = (
                f"{image_base64[:100]}...{image_base64[-100:]}"
                if len(image_base64) > 200
                else image_base64
            )
            self.log_data["inputs"]["image"]["base64_length"] = len(image_base64)

        # Save input image to debug directory
        if self.debug_dir and self.log_masks:
            input_path = self.debug_dir / "input_image.png"
            image.save(input_path)
            self.log_data["inputs"]["image"]["saved_to"] = str(input_path)

        logger.debug(f"Input image: {image.size[0]}x{image.size[1]} {image.mode}")

    def log_prompts(
        self,
        point_coords: Optional[np.ndarray] = None,
        point_labels: Optional[np.ndarray] = None,
        box: Optional[np.ndarray] = None,
        mask_input: Optional[np.ndarray] = None,
        multimask_output: bool = True,
    ) -> None:
        """Log all prompt inputs."""
        if not self.enabled:
            return

        prompts = {
            "multimask_output": multimask_output,
        }

        if point_coords is not None:
            prompts["points"] = {
                "coords": point_coords.tolist(),
                "labels": point_labels.tolist() if point_labels is not None else None,
                "count": len(point_coords),
                "positive_count": int(np.sum(point_labels == 1)) if point_labels is not None else 0,
                "negative_count": int(np.sum(point_labels == 0)) if point_labels is not None else 0,
            }
            logger.debug(
                f"Points: {len(point_coords)} total, "
                f"{prompts['points']['positive_count']} positive, "
                f"{prompts['points']['negative_count']} negative"
            )

        if box is not None:
            box_list = box.tolist()
            prompts["box"] = {
                "coords": box_list,
                "x1": box_list[0],
                "y1": box_list[1],
                "x2": box_list[2],
                "y2": box_list[3],
                "width": box_list[2] - box_list[0],
                "height": box_list[3] - box_list[1],
                "area": (box_list[2] - box_list[0]) * (box_list[3] - box_list[1]),
            }
            logger.debug(
                f"Box: [{box_list[0]:.1f}, {box_list[1]:.1f}, {box_list[2]:.1f}, {box_list[3]:.1f}] "
                f"({prompts['box']['width']:.1f}x{prompts['box']['height']:.1f})"
            )

        if mask_input is not None:
            prompts["mask_input"] = {
                "shape": list(mask_input.shape),
                "dtype": str(mask_input.dtype),
                "min": float(mask_input.min()),
                "max": float(mask_input.max()),
                "mean": float(mask_input.mean()),
                "nonzero_pixels": int(np.sum(mask_input > 0)),
            }
            logger.debug(f"Mask input: shape={mask_input.shape}, nonzero={prompts['mask_input']['nonzero_pixels']}")

            # Save mask input image
            if self.debug_dir and self.log_masks:
                mask_img = Image.fromarray((mask_input.squeeze() * 255).astype(np.uint8))
                mask_path = self.debug_dir / "input_mask.png"
                mask_img.save(mask_path)
                prompts["mask_input"]["saved_to"] = str(mask_path)

        self.log_data["inputs"]["prompts"] = prompts

    def log_raw_sam_output(
        self,
        masks: list[np.ndarray],
        iou_scores: list[float],
        stage: str = "raw",
    ) -> None:
        """Log raw SAM3 output before any post-processing."""
        if not self.enabled:
            return

        output_key = f"sam_output_{stage}"
        self.log_data["outputs"][output_key] = {
            "num_masks": len(masks),
            "iou_scores": iou_scores,
            "masks": [],
        }

        for i, mask in enumerate(masks):
            mask_info = {
                "index": i,
                "iou_score": iou_scores[i] if i < len(iou_scores) else None,
                "shape": list(mask.shape),
                "dtype": str(mask.dtype),
                "nonzero_pixels": int(np.sum(mask > 0)),
                "total_pixels": int(mask.size),
                "coverage_percent": float(np.sum(mask > 0) / mask.size * 100),
            }

            # Calculate bounding box from mask
            if mask.any():
                ys, xs = np.where(mask)
                mask_info["bbox"] = {
                    "x1": int(xs.min()),
                    "y1": int(ys.min()),
                    "x2": int(xs.max()),
                    "y2": int(ys.max()),
                    "width": int(xs.max() - xs.min()),
                    "height": int(ys.max() - ys.min()),
                }

            self.log_data["outputs"][output_key]["masks"].append(mask_info)

            # Save mask image
            if self.debug_dir and self.log_masks:
                mask_img = Image.fromarray((mask.astype(np.uint8) * 255))
                mask_path = self.debug_dir / f"mask_{stage}_{i}_iou{iou_scores[i]:.3f}.png"
                mask_img.save(mask_path)
                mask_info["saved_to"] = str(mask_path)

            logger.debug(
                f"Mask {i} ({stage}): iou={iou_scores[i]:.3f}, "
                f"coverage={mask_info['coverage_percent']:.1f}%, "
                f"shape={mask.shape}"
            )

    def log_postprocessing_step(
        self,
        step_name: str,
        mask_before: np.ndarray,
        mask_after: np.ndarray,
        mask_index: int = 0,
    ) -> None:
        """Log a post-processing step showing before/after."""
        if not self.enabled:
            return

        if "postprocessing_steps" not in self.log_data["outputs"]:
            self.log_data["outputs"]["postprocessing_steps"] = []

        before_nonzero = int(np.sum(mask_before > 0))
        after_nonzero = int(np.sum(mask_after > 0))
        change = after_nonzero - before_nonzero

        step_info = {
            "step": step_name,
            "mask_index": mask_index,
            "pixels_before": before_nonzero,
            "pixels_after": after_nonzero,
            "pixels_changed": change,
            "percent_change": float(change / before_nonzero * 100) if before_nonzero > 0 else 0,
        }

        self.log_data["outputs"]["postprocessing_steps"].append(step_info)

        # Save before/after images
        if self.debug_dir and self.log_masks:
            step_dir = self.debug_dir / "postprocessing"
            step_dir.mkdir(exist_ok=True)

            before_path = step_dir / f"{mask_index:02d}_{step_name}_before.png"
            after_path = step_dir / f"{mask_index:02d}_{step_name}_after.png"

            Image.fromarray((mask_before.astype(np.uint8) * 255)).save(before_path)
            Image.fromarray((mask_after.astype(np.uint8) * 255)).save(after_path)

            step_info["before_saved_to"] = str(before_path)
            step_info["after_saved_to"] = str(after_path)

        logger.debug(
            f"PostProcess {step_name}: {before_nonzero} -> {after_nonzero} pixels "
            f"({change:+d}, {step_info['percent_change']:+.1f}%)"
        )

    def log_final_output(
        self,
        masks: list[np.ndarray],
        iou_scores: list[float],
        bboxes: list[tuple],
    ) -> None:
        """Log final output after all processing."""
        if not self.enabled:
            return

        self.log_data["outputs"]["final"] = {
            "num_masks": len(masks),
            "iou_scores": iou_scores,
            "bboxes": [list(b) for b in bboxes],
            "masks": [],
        }

        for i, (mask, iou, bbox) in enumerate(zip(masks, iou_scores, bboxes)):
            mask_info = {
                "index": i,
                "iou_score": iou,
                "bbox": list(bbox),
                "nonzero_pixels": int(np.sum(mask > 0)),
                "coverage_percent": float(np.sum(mask > 0) / mask.size * 100),
            }
            self.log_data["outputs"]["final"]["masks"].append(mask_info)

            # Save final mask
            if self.debug_dir and self.log_masks:
                mask_img = Image.fromarray((mask.astype(np.uint8) * 255))
                mask_path = self.debug_dir / f"mask_final_{i}_iou{iou:.3f}.png"
                mask_img.save(mask_path)
                mask_info["saved_to"] = str(mask_path)

            logger.debug(
                f"Final mask {i}: iou={iou:.3f}, bbox={bbox}, "
                f"coverage={mask_info['coverage_percent']:.1f}%"
            )

    def log_error(self, error: Exception, context: str = "") -> None:
        """Log an error that occurred during processing."""
        if not self.enabled:
            return

        error_info = {
            "type": type(error).__name__,
            "message": str(error),
            "context": context,
            "timestamp": datetime.now().isoformat(),
        }
        self.log_data["errors"].append(error_info)
        logger.error(f"Debug log error [{context}]: {error}")

    def log_timing(self, stage: str, duration_ms: float) -> None:
        """Log timing for a processing stage."""
        if not self.enabled:
            return

        self.log_data["timing"][stage] = duration_ms
        logger.debug(f"Timing [{stage}]: {duration_ms:.2f}ms")

    def save(self) -> Optional[Path]:
        """Save the debug log to a JSON file."""
        if not self.enabled or not self.debug_dir:
            return None

        # Add total duration
        self.log_data["timing"]["total_ms"] = (time.time() - self.start_time) * 1000

        # Save JSON log
        log_path = self.debug_dir / "debug_log.json"
        with open(log_path, "w") as f:
            json.dump(self.log_data, f, indent=2, default=str)

        logger.info(f"Debug log saved to: {log_path}")
        return log_path

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the debug log data."""
        return {
            "run_id": self.run_id,
            "debug_dir": str(self.debug_dir) if self.debug_dir else None,
            "num_input_points": len(self.log_data.get("inputs", {}).get("prompts", {}).get("points", {}).get("coords", [])),
            "has_box": "box" in self.log_data.get("inputs", {}).get("prompts", {}),
            "has_mask_input": "mask_input" in self.log_data.get("inputs", {}).get("prompts", {}),
            "num_output_masks": self.log_data.get("outputs", {}).get("final", {}).get("num_masks", 0),
            "total_time_ms": self.log_data.get("timing", {}).get("total_ms"),
            "errors": len(self.log_data.get("errors", [])),
        }


def create_debug_logger(
    storage_path: Optional[str] = None,
    run_id: Optional[str] = None,
) -> DebugLogger:
    """
    Factory function to create a debug logger.

    Args:
        storage_path: Path to document storage directory
        run_id: Optional run identifier

    Returns:
        DebugLogger instance (logging may be disabled based on settings)
    """
    path = Path(storage_path) if storage_path else None
    return DebugLogger(storage_path=path, run_id=run_id)
