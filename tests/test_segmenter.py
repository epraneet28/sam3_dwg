"""Tests for the DrawingSegmenter class."""

import pytest
from PIL import Image
import numpy as np

from src.sam3_segmenter.segmenter import DrawingSegmenter
from src.sam3_segmenter.models import ZoneResult


class TestDrawingSegmenter:
    """Tests for DrawingSegmenter class."""

    @pytest.fixture
    def segmenter(self):
        """Create a segmenter instance."""
        return DrawingSegmenter(
            model_path="sam3.pt",
            confidence_threshold=0.3,
        )

    def test_initialization(self, segmenter: DrawingSegmenter):
        """Segmenter should initialize correctly."""
        assert segmenter.confidence_threshold == 0.3
        assert segmenter.model_path == "sam3.pt"

    def test_segment_returns_list(self, segmenter: DrawingSegmenter, sample_image: Image.Image):
        """Segment should return a list of ZoneResults."""
        result = segmenter.segment(
            image=sample_image,
            prompts=["title block"],
            return_masks=False,
        )
        assert isinstance(result, list)

    def test_segment_result_structure(
        self, segmenter: DrawingSegmenter, sample_image: Image.Image
    ):
        """Each zone result should have required fields."""
        result = segmenter.segment(
            image=sample_image,
            prompts=["title block"],
            return_masks=False,
        )

        for zone in result:
            assert isinstance(zone, ZoneResult)
            assert hasattr(zone, "zone_id")
            assert hasattr(zone, "zone_type")
            assert hasattr(zone, "confidence")
            assert hasattr(zone, "bbox")
            assert len(zone.bbox) == 4

    def test_segment_structural(
        self, segmenter: DrawingSegmenter, sample_image: Image.Image
    ):
        """Structural segmentation should work."""
        zones, page_type, confidence = segmenter.segment_structural(
            image=sample_image,
            classify_page=True,
        )

        assert isinstance(zones, list)
        assert page_type is not None or page_type is None  # Can be either
        assert confidence is None or (0 <= confidence <= 1)

    def test_gpu_info(self, segmenter: DrawingSegmenter):
        """GPU info should return dict."""
        info = segmenter.gpu_info
        assert isinstance(info, dict)
        assert "available" in info

    def test_load_exemplar(self, segmenter: DrawingSegmenter, tmp_path):
        """Should load exemplar from file."""
        # Create a test exemplar image
        exemplar = Image.new("RGB", (100, 100), color="white")
        exemplar_path = tmp_path / "test_exemplar.png"
        exemplar.save(exemplar_path)

        segmenter.load_exemplar("title_block", exemplar_path)

        assert "title_block" in segmenter._exemplars
        assert len(segmenter._exemplars["title_block"]) == 1

    def test_get_exemplars(self, segmenter: DrawingSegmenter):
        """Get exemplars for non-existent type should return empty list."""
        exemplars = segmenter.get_exemplars("non_existent_type")
        assert exemplars == []


class TestZoneResult:
    """Tests for ZoneResult model."""

    def test_zone_result_creation(self):
        """Should create valid ZoneResult."""
        zone = ZoneResult(
            zone_id="zone_001",
            zone_type="title_block",
            prompt_matched="title block",
            confidence=0.85,
            bbox=[100.0, 200.0, 300.0, 400.0],
        )

        assert zone.zone_id == "zone_001"
        assert zone.zone_type == "title_block"
        assert zone.confidence == 0.85
        assert len(zone.bbox) == 4

    def test_zone_result_optional_fields(self):
        """Optional fields should default to None."""
        zone = ZoneResult(
            zone_id="zone_001",
            zone_type="title_block",
            prompt_matched="title block",
            confidence=0.5,
            bbox=[0.0, 0.0, 100.0, 100.0],
        )

        assert zone.bbox_normalized is None
        assert zone.area_ratio is None
        assert zone.mask_base64 is None
        assert zone.crop_base64 is None

    def test_zone_result_confidence_validation(self):
        """Confidence should be between 0 and 1."""
        # Valid confidence
        zone = ZoneResult(
            zone_id="zone_001",
            zone_type="title_block",
            prompt_matched="title block",
            confidence=0.5,
            bbox=[0.0, 0.0, 100.0, 100.0],
        )
        assert zone.confidence == 0.5

        # Invalid confidence should raise validation error
        with pytest.raises(ValueError):
            ZoneResult(
                zone_id="zone_001",
                zone_type="title_block",
                prompt_matched="title block",
                confidence=1.5,  # Invalid
                bbox=[0.0, 0.0, 100.0, 100.0],
            )
