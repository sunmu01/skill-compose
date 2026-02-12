"""
Executors API endpoints.

Provides read-only endpoints for:
- Listing available executors and their online/offline status
- Getting executor details
- Health checking executor containers
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import ExecutorDB
from app.services.executor_client import ExecutorClient
from app.services.executor_config import get_builtin_executor_defs


router = APIRouter(prefix="/executors", tags=["executors"])


# Response models
class ExecutorResponse(BaseModel):
    """Response model for executor."""
    id: str
    name: str
    description: Optional[str] = None
    image: str
    port: int
    memory_limit: Optional[str] = None
    cpu_limit: Optional[float] = None
    gpu_required: bool
    is_builtin: bool
    status: str  # online, offline
    created_at: datetime
    updated_at: datetime


class ExecutorListResponse(BaseModel):
    """Response for listing executors."""
    executors: List[ExecutorResponse]
    total: int


class ExecutorHealthResponse(BaseModel):
    """Response for executor health check."""
    healthy: bool
    executor: Optional[str] = None
    python_version: Optional[str] = None
    package_count: Optional[int] = None
    error: Optional[str] = None


async def ensure_builtin_executors(db: AsyncSession):
    """Ensure built-in executors exist in database."""
    for executor_def in get_builtin_executor_defs():
        result = await db.execute(
            select(ExecutorDB).where(ExecutorDB.name == executor_def["name"])
        )
        existing = result.scalar_one_or_none()

        if not existing:
            executor = ExecutorDB(
                name=executor_def["name"],
                description=executor_def["description"],
                image=executor_def["image"],
                memory_limit=executor_def["memory_limit"],
                gpu_required=executor_def["gpu_required"],
                is_builtin=True,
            )
            db.add(executor)

    await db.commit()


async def _get_executor_status(name: str) -> str:
    """Check if executor is online via HTTP health check."""
    try:
        client = ExecutorClient(name)
        health = await client.health_check()
        return "online" if health.get("healthy") else "offline"
    except Exception:
        return "offline"


@router.get("", response_model=ExecutorListResponse)
async def list_executors(
    db: AsyncSession = Depends(get_db),
):
    """
    List all available executors with their online/offline status.

    Returns executors ordered by: built-in first, then by name.
    Status is determined by HTTP health check to each executor.
    """
    await ensure_builtin_executors(db)

    result = await db.execute(
        select(ExecutorDB).order_by(desc(ExecutorDB.is_builtin), ExecutorDB.name)
    )
    executors = result.scalars().all()

    executor_responses = []
    for e in executors:
        status = await _get_executor_status(e.name)
        executor_responses.append(
            ExecutorResponse(
                id=e.id,
                name=e.name,
                description=e.description,
                image=e.image,
                port=e.port,
                memory_limit=e.memory_limit,
                cpu_limit=e.cpu_limit,
                gpu_required=e.gpu_required,
                is_builtin=e.is_builtin,
                status=status,
                created_at=e.created_at,
                updated_at=e.updated_at,
            )
        )

    return ExecutorListResponse(
        executors=executor_responses,
        total=len(executor_responses),
    )


@router.get("/health/all")
async def check_all_executors_health():
    """
    Check health of all known executors.

    Returns health status for each executor.
    """
    return await ExecutorClient.check_all_executors()


@router.get("/{name}", response_model=ExecutorResponse)
async def get_executor(
    name: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get executor details by name.
    """
    result = await db.execute(
        select(ExecutorDB).where(ExecutorDB.name == name)
    )
    executor = result.scalar_one_or_none()

    if not executor:
        raise HTTPException(status_code=404, detail="Executor not found")

    status = await _get_executor_status(executor.name)

    return ExecutorResponse(
        id=executor.id,
        name=executor.name,
        description=executor.description,
        image=executor.image,
        port=executor.port,
        memory_limit=executor.memory_limit,
        cpu_limit=executor.cpu_limit,
        gpu_required=executor.gpu_required,
        is_builtin=executor.is_builtin,
        status=status,
        created_at=executor.created_at,
        updated_at=executor.updated_at,
    )


@router.get("/{name}/health", response_model=ExecutorHealthResponse)
async def check_executor_health(
    name: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Check health of an executor container.
    """
    result = await db.execute(
        select(ExecutorDB).where(ExecutorDB.name == name)
    )
    executor = result.scalar_one_or_none()

    if not executor:
        raise HTTPException(status_code=404, detail="Executor not found")

    client = ExecutorClient(name)
    health = await client.health_check()

    return ExecutorHealthResponse(**health)
