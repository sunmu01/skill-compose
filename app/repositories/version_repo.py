"""
Version Repository - Data access layer for skill versions.

Provides CRUD operations and queries for the skill_versions table.
"""

from typing import Optional, List
from datetime import datetime

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import SkillVersionDB, SkillFileDB, SkillTestDB


class VersionRepository:
    """Repository for SkillVersion CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        skill_id: str,
        version: str,
        skill_md: Optional[str] = None,
        schema_json: Optional[dict] = None,
        manifest_json: Optional[dict] = None,
        metadata: Optional[dict] = None,
        parent_version: Optional[str] = None,
        created_by: Optional[str] = None,
        commit_message: Optional[str] = None,
    ) -> SkillVersionDB:
        """Create a new version for a skill."""
        ver = SkillVersionDB(
            skill_id=skill_id,
            version=version,
            skill_md=skill_md,
            schema_json=schema_json,
            manifest_json=manifest_json,
            metadata=metadata,
            parent_version=parent_version,
            created_by=created_by,
            commit_message=commit_message,
            created_at=datetime.utcnow(),
        )
        self.session.add(ver)
        await self.session.flush()
        return ver

    async def get_by_id(
        self,
        version_id: str,
        include_files: bool = False,
        include_tests: bool = False,
    ) -> Optional[SkillVersionDB]:
        """Get a version by ID."""
        stmt = select(SkillVersionDB).where(SkillVersionDB.id == version_id)

        options = []
        if include_files:
            options.append(selectinload(SkillVersionDB.files))
        if include_tests:
            options.append(selectinload(SkillVersionDB.tests))
        if options:
            stmt = stmt.options(*options)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_skill_and_version(
        self,
        skill_id: str,
        version: str,
        include_files: bool = False,
        include_tests: bool = False,
    ) -> Optional[SkillVersionDB]:
        """Get a specific version of a skill."""
        stmt = select(SkillVersionDB).where(
            (SkillVersionDB.skill_id == skill_id)
            & (SkillVersionDB.version == version)
        )

        options = []
        if include_files:
            options.append(selectinload(SkillVersionDB.files))
        if include_tests:
            options.append(selectinload(SkillVersionDB.tests))
        if options:
            stmt = stmt.options(*options)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_skill(
        self,
        skill_id: str,
        offset: int = 0,
        limit: int = 50,
    ) -> List[SkillVersionDB]:
        """List all versions of a skill, ordered by creation date (newest first)."""
        stmt = (
            select(SkillVersionDB)
            .where(SkillVersionDB.skill_id == skill_id)
            .order_by(SkillVersionDB.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_max_version(self, skill_id: str) -> Optional[str]:
        """Get the highest version string for a skill (by semver patch number)."""
        stmt = (
            select(SkillVersionDB.version)
            .where(SkillVersionDB.skill_id == skill_id)
        )
        result = await self.session.execute(stmt)
        versions = [row[0] for row in result.all()]
        if not versions:
            return None

        def _version_key(v: str):
            try:
                parts = v.split(".")
                return tuple(int(p) for p in parts[:3])
            except (ValueError, IndexError):
                return (0, 0, 0)

        return max(versions, key=_version_key)

    async def count_by_skill(self, skill_id: str) -> int:
        """Count versions of a skill."""
        stmt = (
            select(func.count(SkillVersionDB.id))
            .where(SkillVersionDB.skill_id == skill_id)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_latest(
        self,
        skill_id: str,
        include_files: bool = False,
    ) -> Optional[SkillVersionDB]:
        """Get the latest version of a skill."""
        stmt = (
            select(SkillVersionDB)
            .where(SkillVersionDB.skill_id == skill_id)
            .order_by(SkillVersionDB.created_at.desc())
            .limit(1)
        )

        if include_files:
            stmt = stmt.options(selectinload(SkillVersionDB.files))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, version_id: str) -> bool:
        """Delete a version by ID."""
        stmt = delete(SkillVersionDB).where(SkillVersionDB.id == version_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def delete_by_skill_and_version(
        self,
        skill_id: str,
        version: str,
    ) -> bool:
        """Delete a specific version of a skill."""
        stmt = delete(SkillVersionDB).where(
            (SkillVersionDB.skill_id == skill_id)
            & (SkillVersionDB.version == version)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def exists(self, skill_id: str, version: str) -> bool:
        """Check if a version exists."""
        stmt = (
            select(func.count(SkillVersionDB.id))
            .where(
                (SkillVersionDB.skill_id == skill_id)
                & (SkillVersionDB.version == version)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    # File operations

    async def add_file(
        self,
        version_id: str,
        file_path: str,
        file_type: str,
        content: Optional[bytes] = None,
        content_hash: Optional[str] = None,
        storage_path: Optional[str] = None,
        size_bytes: Optional[int] = None,
    ) -> SkillFileDB:
        """Add a file to a version."""
        file = SkillFileDB(
            version_id=version_id,
            file_path=file_path,
            file_type=file_type,
            content=content,
            content_hash=content_hash,
            storage_path=storage_path,
            size_bytes=size_bytes,
            created_at=datetime.utcnow(),
        )
        self.session.add(file)
        await self.session.flush()
        return file

    async def get_files(
        self,
        version_id: str,
        file_type: Optional[str] = None,
    ) -> List[SkillFileDB]:
        """Get files for a version."""
        stmt = select(SkillFileDB).where(SkillFileDB.version_id == version_id)

        if file_type:
            stmt = stmt.where(SkillFileDB.file_type == file_type)

        stmt = stmt.order_by(SkillFileDB.file_path)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_file(
        self,
        version_id: str,
        file_path: str,
    ) -> Optional[SkillFileDB]:
        """Get a specific file from a version."""
        stmt = select(SkillFileDB).where(
            (SkillFileDB.version_id == version_id)
            & (SkillFileDB.file_path == file_path)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_file(
        self,
        version_id: str,
        file_path: str,
    ) -> bool:
        """Delete a file from a version."""
        stmt = delete(SkillFileDB).where(
            (SkillFileDB.version_id == version_id)
            & (SkillFileDB.file_path == file_path)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    # Test operations

    async def add_test(
        self,
        version_id: str,
        name: str,
        description: Optional[str] = None,
        input_data: Optional[dict] = None,
        expected_output: Optional[dict] = None,
        is_golden: bool = False,
    ) -> SkillTestDB:
        """Add a test case to a version."""
        test = SkillTestDB(
            version_id=version_id,
            name=name,
            description=description,
            input_data=input_data,
            expected_output=expected_output,
            is_golden=is_golden,
            created_at=datetime.utcnow(),
        )
        self.session.add(test)
        await self.session.flush()
        return test

    async def get_tests(
        self,
        version_id: str,
        is_golden: Optional[bool] = None,
    ) -> List[SkillTestDB]:
        """Get test cases for a version."""
        stmt = select(SkillTestDB).where(SkillTestDB.version_id == version_id)

        if is_golden is not None:
            stmt = stmt.where(SkillTestDB.is_golden == is_golden)

        stmt = stmt.order_by(SkillTestDB.name)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_test(self, test_id: str) -> bool:
        """Delete a test case."""
        stmt = delete(SkillTestDB).where(SkillTestDB.id == test_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0
