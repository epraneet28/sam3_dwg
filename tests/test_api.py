"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client: TestClient):
        """Health endpoint should return 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client: TestClient):
        """Health response should have required fields."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "model" in data
        assert "model_loaded" in data
        assert "gpu_available" in data
        assert data["model"] == "sam3"

    def test_health_status_values(self, client: TestClient):
        """Health status should be valid."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] in ["healthy", "loading"]


class TestSegmentEndpoint:
    """Tests for the /segment endpoint."""

    def test_segment_valid_request(self, client: TestClient, sample_image_base64: str):
        """Segment endpoint should process valid requests."""
        response = client.post(
            "/segment",
            json={
                "image_base64": sample_image_base64,
                "prompts": ["title block", "detail drawing"],
                "return_masks": False,
            },
        )
        assert response.status_code == 200

    def test_segment_response_structure(self, client: TestClient, sample_image_base64: str):
        """Segment response should have required fields."""
        response = client.post(
            "/segment",
            json={
                "image_base64": sample_image_base64,
                "prompts": ["title block"],
                "return_masks": False,
            },
        )
        data = response.json()

        assert "zones" in data
        assert "image_size" in data
        assert "processing_time_ms" in data
        assert "model_version" in data
        assert isinstance(data["zones"], list)
        assert isinstance(data["image_size"], list)
        assert len(data["image_size"]) == 2

    def test_segment_invalid_image(self, client: TestClient, invalid_base64: str):
        """Segment endpoint should reject invalid images."""
        response = client.post(
            "/segment",
            json={
                "image_base64": invalid_base64,
                "prompts": ["title block"],
            },
        )
        assert response.status_code == 400
        assert "Invalid image" in response.json()["detail"]

    def test_segment_empty_prompts(self, client: TestClient, sample_image_base64: str):
        """Segment endpoint should reject empty prompts."""
        response = client.post(
            "/segment",
            json={
                "image_base64": sample_image_base64,
                "prompts": [],
            },
        )
        assert response.status_code == 422  # Validation error

    def test_segment_confidence_threshold(self, client: TestClient, sample_image_base64: str):
        """Confidence threshold should filter results."""
        # High threshold should return fewer results
        high_threshold_response = client.post(
            "/segment",
            json={
                "image_base64": sample_image_base64,
                "prompts": ["title block", "detail drawing"],
                "confidence_threshold": 0.9,
                "return_masks": False,
            },
        )
        assert high_threshold_response.status_code == 200


class TestStructuralSegmentEndpoint:
    """Tests for the /segment/structural endpoint."""

    def test_structural_segment_valid_request(
        self, client: TestClient, sample_image_base64: str
    ):
        """Structural segment endpoint should process valid requests."""
        response = client.post(
            "/segment/structural",
            json={
                "image_base64": sample_image_base64,
                "classify_page_type": True,
            },
        )
        assert response.status_code == 200

    def test_structural_segment_response_structure(
        self, client: TestClient, sample_image_base64: str
    ):
        """Structural segment response should include page type."""
        response = client.post(
            "/segment/structural",
            json={
                "image_base64": sample_image_base64,
                "classify_page_type": True,
            },
        )
        data = response.json()

        assert "zones" in data
        assert "page_type" in data
        assert "page_type_confidence" in data

    def test_structural_segment_without_classification(
        self, client: TestClient, sample_image_base64: str
    ):
        """Can disable page type classification."""
        response = client.post(
            "/segment/structural",
            json={
                "image_base64": sample_image_base64,
                "classify_page_type": False,
            },
        )
        data = response.json()
        assert data["page_type"] is None


class TestBatchSegmentEndpoint:
    """Tests for the /segment/batch endpoint."""

    def test_batch_segment_single_image(self, client: TestClient, sample_image_base64: str):
        """Batch endpoint should handle single image."""
        response = client.post(
            "/segment/batch",
            json={
                "images": [{"image_base64": sample_image_base64, "page_id": "page_001"}],
                "prompts": ["title block"],
                "return_masks": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["page_id"] == "page_001"

    def test_batch_segment_multiple_images(
        self, client: TestClient, sample_image_base64: str
    ):
        """Batch endpoint should handle multiple images."""
        response = client.post(
            "/segment/batch",
            json={
                "images": [
                    {"image_base64": sample_image_base64, "page_id": "page_001"},
                    {"image_base64": sample_image_base64, "page_id": "page_002"},
                ],
                "prompts": ["title block"],
                "return_masks": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert "total_processing_time_ms" in data


class TestPromptsEndpoint:
    """Tests for the /prompts endpoints."""

    def test_structural_prompts(self, client: TestClient):
        """Should return structural prompts configuration."""
        response = client.get("/prompts/structural")
        assert response.status_code == 200
        data = response.json()

        # Check for expected zone types
        assert "title_block" in data
        assert "detail_view" in data
        assert "plan_view" in data
        assert "schedule_table" in data

    def test_page_type_rules(self, client: TestClient):
        """Should return page type rules."""
        response = client.get("/prompts/page-types")
        assert response.status_code == 200
        data = response.json()

        assert "plan" in data
        assert "elevation" in data
        assert "details" in data


class TestExemplarsEndpoint:
    """Tests for exemplar management endpoints."""

    def test_list_exemplars(self, client: TestClient):
        """Should list loaded exemplars."""
        response = client.get("/exemplars")
        assert response.status_code == 200
        data = response.json()
        assert "exemplars" in data
