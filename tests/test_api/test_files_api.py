"""
Tests for Files API.

Endpoints tested:
- POST   /api/v1/files/upload
- GET    /api/v1/files/{file_id}
- DELETE /api/v1/files/{file_id}

Note: The files API uses an in-memory registry (_file_registry).
We clear it in a module-scoped autouse fixture to prevent state leakage between tests.
"""

import pytest
from httpx import AsyncClient

from app.api.v1 import files as files_module

API = "/api/v1/files"


@pytest.fixture(autouse=True)
def _clear_file_registries():
    """Clear in-memory file registries before each test."""
    files_module._file_registry.clear()
    yield
    files_module._file_registry.clear()


# ---------------------------------------------------------------------------
# Upload helpers
# ---------------------------------------------------------------------------
async def _upload_text_file(client: AsyncClient) -> dict:
    """Helper: upload a simple text file and return the response JSON."""
    response = await client.post(
        f"{API}/upload",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 200
    return response.json()


# ---------------------------------------------------------------------------
# Upload file tests
# ---------------------------------------------------------------------------
class TestUploadFile:
    """Tests for POST /api/v1/files/upload."""

    async def test_upload_file(self, client: AsyncClient):
        """Uploading a file should return 200 with a file_id."""
        data = await _upload_text_file(client)
        assert "file_id" in data
        assert data["file_id"]  # non-empty string

    async def test_upload_file_returns_info(self, client: AsyncClient):
        """Returned FileInfo should contain all expected fields."""
        data = await _upload_text_file(client)
        assert data["filename"] == "test.txt"
        assert data["size"] == len(b"hello world")
        assert data["content_type"] == "text/plain"
        assert "path" in data
        assert "uploaded_at" in data


# ---------------------------------------------------------------------------
# Get / delete uploaded file tests
# ---------------------------------------------------------------------------
class TestGetAndDeleteFile:
    """Tests for GET and DELETE /api/v1/files/{file_id}."""

    async def test_get_file_info(self, client: AsyncClient):
        """After uploading, GET /files/{file_id} should return 200."""
        uploaded = await _upload_text_file(client)
        file_id = uploaded["file_id"]

        response = await client.get(f"{API}/{file_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["file_id"] == file_id
        assert data["filename"] == "test.txt"

    async def test_get_file_not_found(self, client: AsyncClient):
        """GET /files/nonexistent should return 404."""
        response = await client.get(f"{API}/nonexistent-id")
        assert response.status_code == 404

    async def test_delete_file(self, client: AsyncClient):
        """DELETE /files/{file_id} should return 204."""
        uploaded = await _upload_text_file(client)
        file_id = uploaded["file_id"]

        response = await client.delete(f"{API}/{file_id}")
        assert response.status_code == 204

        # Verify it is gone
        get_response = await client.get(f"{API}/{file_id}")
        assert get_response.status_code == 404

    async def test_delete_file_not_found(self, client: AsyncClient):
        """DELETE /files/nonexistent should return 404."""
        response = await client.delete(f"{API}/nonexistent-id")
        assert response.status_code == 404
