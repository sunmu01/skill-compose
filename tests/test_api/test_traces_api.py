"""
Tests for Traces API.

Endpoints tested:
- GET    /api/v1/traces
- GET    /api/v1/traces/{id}
- DELETE /api/v1/traces/{id}
"""

import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentTraceDB

API = "/api/v1/traces"


class TestListTraces:
    """Tests for GET /api/v1/traces."""

    async def test_list_traces_empty(self, client: AsyncClient):
        """With no traces, should return empty list and total=0."""
        response = await client.get(API)
        assert response.status_code == 200
        data = response.json()
        assert data["traces"] == []
        assert data["total"] == 0

    async def test_list_traces_with_data(
        self, client: AsyncClient, sample_trace: AgentTraceDB
    ):
        """With one sample trace, should return a list of length 1."""
        response = await client.get(API)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["traces"]) == 1
        assert data["traces"][0]["id"] == sample_trace.id

    async def test_list_traces_pagination(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Create 3 traces, then fetch with offset=1, limit=1 -> 1 result."""
        now = datetime.utcnow()
        for i in range(3):
            trace = AgentTraceDB(
                id=str(uuid.uuid4()),
                request=f"Request {i}",
                skills_used=[],
                model="claude-sonnet-4-5-20250929",
                status="completed",
                success=True,
                total_turns=1,
                total_input_tokens=100,
                total_output_tokens=50,
                created_at=now + timedelta(seconds=i),
            )
            db_session.add(trace)
        await db_session.commit()

        response = await client.get(API, params={"offset": 1, "limit": 1})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["traces"]) == 1
        assert data["offset"] == 1
        assert data["limit"] == 1

    async def test_list_traces_filter_success_true(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Filtering success=true should return only successful traces."""
        # Create one successful and one failed trace
        for success in [True, False]:
            trace = AgentTraceDB(
                id=str(uuid.uuid4()),
                request="Test request",
                model="claude-sonnet-4-5-20250929",
                status="completed" if success else "failed",
                success=success,
                total_turns=1,
                total_input_tokens=100,
                total_output_tokens=50,
                created_at=datetime.utcnow(),
            )
            db_session.add(trace)
        await db_session.commit()

        response = await client.get(API, params={"success": True})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for trace in data["traces"]:
            assert trace["success"] is True

    async def test_list_traces_filter_success_false(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Filtering success=false should return only failed traces."""
        trace = AgentTraceDB(
            id=str(uuid.uuid4()),
            request="Failing request",
            model="claude-sonnet-4-5-20250929",
            status="failed",
            success=False,
            error="Something went wrong",
            total_turns=1,
            total_input_tokens=100,
            total_output_tokens=50,
            created_at=datetime.utcnow(),
        )
        db_session.add(trace)
        await db_session.commit()

        response = await client.get(API, params={"success": False})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for trace in data["traces"]:
            assert trace["success"] is False

    async def test_list_traces_filter_by_skill(
        self, client: AsyncClient, sample_trace: AgentTraceDB
    ):
        """Filtering by skill_name should return traces that used that skill."""
        response = await client.get(
            API, params={"skill_name": "test-skill"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        # The sample_trace has skills_used=["test-skill"]
        found = any(t["id"] == sample_trace.id for t in data["traces"])
        assert found


class TestGetTrace:
    """Tests for GET /api/v1/traces/{id}."""

    async def test_get_trace_detail(
        self, client: AsyncClient, sample_trace: AgentTraceDB
    ):
        """Fetching a trace by ID should return full detail with steps."""
        response = await client.get(f"{API}/{sample_trace.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_trace.id
        assert data["request"] == sample_trace.request
        assert data["success"] is True
        assert data["model"] == sample_trace.model
        assert data["total_turns"] == 3
        assert data["steps"] is not None
        assert len(data["steps"]) == 2

    async def test_get_trace_not_found(self, client: AsyncClient):
        """Fetching a nonexistent trace ID should return 404."""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"{API}/{fake_id}")
        assert response.status_code == 404


class TestDeleteTrace:
    """Tests for DELETE /api/v1/traces/{id}."""

    async def test_delete_trace(
        self, client: AsyncClient, sample_trace: AgentTraceDB
    ):
        """Deleting an existing trace should return 200."""
        response = await client.delete(f"{API}/{sample_trace.id}")
        assert response.status_code == 200

        # Verify it is gone
        get_response = await client.get(f"{API}/{sample_trace.id}")
        assert get_response.status_code == 404

    async def test_delete_trace_not_found(self, client: AsyncClient):
        """Deleting a nonexistent trace should return 404."""
        fake_id = str(uuid.uuid4())
        response = await client.delete(f"{API}/{fake_id}")
        assert response.status_code == 404
