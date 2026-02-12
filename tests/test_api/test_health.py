"""
Tests for health and root endpoints.

Endpoints tested:
- GET /health
- GET /
- GET /docs
- POST /health (method not allowed)
"""

import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Tests for GET /health."""

    async def test_health_returns_200(self, client: AsyncClient):
        """GET /health should return 200 with {"status": "healthy"}."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "healthy"}

    async def test_health_method_not_allowed(self, client: AsyncClient):
        """POST /health should return 405 Method Not Allowed."""
        response = await client.post("/health")
        assert response.status_code == 405


class TestRootEndpoint:
    """Tests for GET /."""

    async def test_root_returns_api_info(self, client: AsyncClient):
        """GET / should return API name, version, docs URL, and endpoints."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Skills API"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"
        assert "endpoints" in data
        # Verify key endpoint paths are listed
        endpoints = data["endpoints"]
        assert "skills" in endpoints
        assert "files" in endpoints


class TestDocsEndpoint:
    """Tests for GET /docs."""

    async def test_docs_endpoint_exists(self, client: AsyncClient):
        """GET /docs should return 200 (Swagger UI page)."""
        response = await client.get("/docs")
        assert response.status_code == 200
