"""
API endpoint tests.

Tests for REST API endpoints (FastAPI).
"""

import pytest
from fastapi.testclient import TestClient


# API client will be created when FastAPI application is implemented
# @pytest.fixture
# def client() -> TestClient:
#     from src.api.main import app
#     return TestClient(app)


class TestAPIEndpoints:
    """Test REST API endpoints."""

    @pytest.mark.skip(reason="FastAPI app not yet implemented")
    def test_get_reports(self) -> None:
        """Test GET /api/reports endpoint."""
        pass

    @pytest.mark.skip(reason="FastAPI app not yet implemented")
    def test_create_report(self) -> None:
        """Test POST /api/reports endpoint."""
        pass

    @pytest.mark.skip(reason="FastAPI app not yet implemented")
    def test_get_report_by_id(self) -> None:
        """Test GET /api/reports/{id} endpoint."""
        pass

    @pytest.mark.skip(reason="FastAPI app not yet implemented")
    def test_export_report(self) -> None:
        """Test POST /api/reports/{id}/export endpoint."""
        pass
