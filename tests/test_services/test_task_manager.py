"""
Tests for app.services.task_manager — Task dataclass and TaskStatus enum.

These tests validate the in-memory data structures without touching the
database (TaskManager itself uses AsyncSessionLocal directly, which makes
it difficult to test with the transactional session fixture).
"""

from datetime import datetime
from unittest.mock import MagicMock

from app.services.task_manager import Task, TaskStatus


# ---------------------------------------------------------------------------
# TaskStatus enum
# ---------------------------------------------------------------------------


class TestTaskStatus:
    def test_pending_value(self):
        assert TaskStatus.PENDING.value == "pending"

    def test_running_value(self):
        assert TaskStatus.RUNNING.value == "running"

    def test_completed_value(self):
        assert TaskStatus.COMPLETED.value == "completed"

    def test_failed_value(self):
        assert TaskStatus.FAILED.value == "failed"

    def test_all_members(self):
        expected = {"pending", "running", "completed", "failed"}
        actual = {s.value for s in TaskStatus}
        assert actual == expected

    def test_is_str_subclass(self):
        """TaskStatus inherits from str, so values can be used directly as strings."""
        assert isinstance(TaskStatus.PENDING, str)
        assert TaskStatus.PENDING == "pending"

    def test_construct_from_value(self):
        assert TaskStatus("completed") is TaskStatus.COMPLETED


# ---------------------------------------------------------------------------
# Task dataclass
# ---------------------------------------------------------------------------


class TestTask:
    def test_creation_minimal(self):
        now = datetime.utcnow()
        task = Task(
            id="task-1",
            task_type="create_skill",
            status=TaskStatus.PENDING,
            created_at=now,
        )
        assert task.id == "task-1"
        assert task.task_type == "create_skill"
        assert task.status == TaskStatus.PENDING
        assert task.created_at == now
        assert task.started_at is None
        assert task.completed_at is None
        assert task.result is None
        assert task.error is None
        assert task.metadata == {}

    def test_creation_full(self):
        now = datetime.utcnow()
        task = Task(
            id="task-2",
            task_type="evolve_skill",
            status=TaskStatus.COMPLETED,
            created_at=now,
            started_at=now,
            completed_at=now,
            result={"skill_name": "test-skill"},
            error=None,
            metadata={"trace_id": "abc-123"},
        )
        assert task.result == {"skill_name": "test-skill"}
        assert task.metadata == {"trace_id": "abc-123"}

    def test_creation_failed_with_error(self):
        now = datetime.utcnow()
        task = Task(
            id="task-3",
            task_type="create_skill",
            status=TaskStatus.FAILED,
            created_at=now,
            error="Something went wrong",
        )
        assert task.status == TaskStatus.FAILED
        assert task.error == "Something went wrong"


# ---------------------------------------------------------------------------
# Task.from_db
# ---------------------------------------------------------------------------


class TestTaskFromDb:
    def _make_db_task_mock(self, **overrides):
        """Create a mock BackgroundTaskDB with sensible defaults."""
        now = datetime.utcnow()
        defaults = dict(
            id="db-task-1",
            task_type="create_skill",
            status="pending",
            created_at=now,
            started_at=None,
            completed_at=None,
            result_json=None,
            error=None,
            metadata_json=None,
        )
        defaults.update(overrides)
        mock = MagicMock()
        for key, value in defaults.items():
            setattr(mock, key, value)
        return mock

    def test_from_db_pending(self):
        db_task = self._make_db_task_mock()
        task = Task.from_db(db_task)

        assert task.id == "db-task-1"
        assert task.task_type == "create_skill"
        assert task.status == TaskStatus.PENDING
        assert task.result is None
        assert task.error is None
        assert task.metadata == {}

    def test_from_db_completed(self):
        now = datetime.utcnow()
        db_task = self._make_db_task_mock(
            status="completed",
            started_at=now,
            completed_at=now,
            result_json={"skill_name": "new-skill"},
        )
        task = Task.from_db(db_task)

        assert task.status == TaskStatus.COMPLETED
        assert task.result == {"skill_name": "new-skill"}
        assert task.started_at == now
        assert task.completed_at == now

    def test_from_db_failed(self):
        now = datetime.utcnow()
        db_task = self._make_db_task_mock(
            status="failed",
            started_at=now,
            completed_at=now,
            error="Timeout exceeded",
        )
        task = Task.from_db(db_task)

        assert task.status == TaskStatus.FAILED
        assert task.error == "Timeout exceeded"

    def test_from_db_with_metadata(self):
        db_task = self._make_db_task_mock(
            metadata_json={"skill_name": "evolve-target", "trace_id": "xyz"},
        )
        task = Task.from_db(db_task)

        assert task.metadata == {"skill_name": "evolve-target", "trace_id": "xyz"}

    def test_from_db_status_mapping(self):
        """Verify all status strings map correctly to TaskStatus enum."""
        for status_value in ["pending", "running", "completed", "failed"]:
            db_task = self._make_db_task_mock(status=status_value)
            task = Task.from_db(db_task)
            assert task.status == TaskStatus(status_value)
