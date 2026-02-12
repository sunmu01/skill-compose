"""
Task Manager - Database-backed async task management for long-running operations.

Tasks are persisted to the database to survive server restarts.
"""

import uuid
import asyncio
import threading
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal, SyncSessionLocal
from app.db.models import BackgroundTaskDB


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """In-memory representation of a task."""
    id: str
    task_type: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_db(cls, db_task: BackgroundTaskDB) -> "Task":
        """Create Task from database model."""
        return cls(
            id=db_task.id,
            task_type=db_task.task_type,
            status=TaskStatus(db_task.status),
            created_at=db_task.created_at,
            started_at=db_task.started_at,
            completed_at=db_task.completed_at,
            result=db_task.result_json,
            error=db_task.error,
            metadata=db_task.metadata_json or {},
        )


class TaskManager:
    """Database-backed task manager for async operations."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def _run_sync(self, coro):
        """Run async coroutine from sync context (background thread)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    async def create_task_async(
        self,
        task_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Create a new task in the database (async version for FastAPI endpoints)."""
        task_id = str(uuid.uuid4())
        now = datetime.utcnow()

        async with AsyncSessionLocal() as session:
            db_task = BackgroundTaskDB(
                id=task_id,
                task_type=task_type,
                status=TaskStatus.PENDING.value,
                metadata_json=metadata or {},
                created_at=now,
            )
            session.add(db_task)
            await session.commit()

            return Task(
                id=task_id,
                task_type=task_type,
                status=TaskStatus.PENDING,
                created_at=now,
                metadata=metadata or {},
            )

    def create_task(
        self,
        task_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Create a new task (sync version - only use from sync context)."""
        return self._run_sync(self.create_task_async(task_type, metadata))

    async def get_task_async(self, task_id: str) -> Optional[Task]:
        """Get task by ID from database (async version)."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(BackgroundTaskDB).where(BackgroundTaskDB.id == task_id)
            )
            db_task = result.scalar_one_or_none()
            if db_task:
                return Task.from_db(db_task)
            return None

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID (sync version - only use from sync context)."""
        return self._run_sync(self.get_task_async(task_id))

    async def _update_task_status_async(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update task status in database."""
        async with AsyncSessionLocal() as session:
            now = datetime.utcnow()
            update_data = {"status": status.value}

            if status == TaskStatus.RUNNING:
                update_data["started_at"] = now
            elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                update_data["completed_at"] = now

            if result is not None:
                update_data["result_json"] = result
            if error is not None:
                update_data["error"] = error

            await session.execute(
                update(BackgroundTaskDB)
                .where(BackgroundTaskDB.id == task_id)
                .values(**update_data)
            )
            await session.commit()

    def _update_task_status_sync(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update task status using sync DB session (safe for background threads)."""
        with SyncSessionLocal() as session:
            now = datetime.utcnow()
            update_data = {"status": status.value}

            if status == TaskStatus.RUNNING:
                update_data["started_at"] = now
            elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                update_data["completed_at"] = now

            if result is not None:
                update_data["result_json"] = result
            if error is not None:
                update_data["error"] = error

            session.execute(
                update(BackgroundTaskDB)
                .where(BackgroundTaskDB.id == task_id)
                .values(**update_data)
            )
            session.commit()

    def start_task(self, task_id: str) -> None:
        """Mark task as running (sync - for background threads)."""
        self._update_task_status_sync(task_id, TaskStatus.RUNNING)

    def complete_task(self, task_id: str, result: Any = None) -> None:
        """Mark task as completed (sync - for background threads)."""
        self._update_task_status_sync(task_id, TaskStatus.COMPLETED, result=result)

    def fail_task(self, task_id: str, error: str) -> None:
        """Mark task as failed (sync - for background threads)."""
        self._update_task_status_sync(task_id, TaskStatus.FAILED, error=error)

    def run_in_background(
        self,
        task_id: str,
        func: Callable,
        *args,
        **kwargs
    ) -> None:
        """Run a function in a background thread."""
        def wrapper():
            self.start_task(task_id)
            try:
                result = func(*args, **kwargs)
                self.complete_task(task_id, result)
            except Exception as e:
                import traceback
                error_msg = f"{str(e)}\n{traceback.format_exc()}"
                self.fail_task(task_id, error_msg)

        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()

    async def list_tasks_async(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> list[Task]:
        """List tasks with optional status filter."""
        async with AsyncSessionLocal() as session:
            query = select(BackgroundTaskDB).order_by(
                BackgroundTaskDB.created_at.desc()
            ).limit(limit)

            if status:
                query = query.where(BackgroundTaskDB.status == status.value)

            result = await session.execute(query)
            db_tasks = result.scalars().all()
            return [Task.from_db(t) for t in db_tasks]

    async def cleanup_old_tasks_async(self, days: int = 7) -> int:
        """Delete completed/failed tasks older than specified days."""
        from datetime import timedelta
        from sqlalchemy import delete

        async with AsyncSessionLocal() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)
            result = await session.execute(
                delete(BackgroundTaskDB).where(
                    BackgroundTaskDB.completed_at < cutoff,
                    BackgroundTaskDB.status.in_([
                        TaskStatus.COMPLETED.value,
                        TaskStatus.FAILED.value
                    ])
                )
            )
            await session.commit()
            return result.rowcount


# Global instance
task_manager = TaskManager()
