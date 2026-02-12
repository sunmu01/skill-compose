"""
Skill Repository - Data access layer for skills.

Provides CRUD operations and queries for the skills table.
"""

from typing import Optional, List
from datetime import datetime

from sqlalchemy import select, update, delete, func, text, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import SkillDB, SkillVersionDB, SkillChangelogDB


class SkillRepository:
    """Repository for Skill CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        name: str,
        description: Optional[str] = None,
        owner_id: Optional[str] = None,
        status: str = "draft",
        skill_type: str = "user",
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        author: Optional[str] = None,
    ) -> SkillDB:
        """Create a new skill."""
        skill = SkillDB(
            name=name,
            description=description,
            owner_id=owner_id,
            status=status,
            skill_type=skill_type,
            tags=tags or [],
            source=source,
            author=author,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.session.add(skill)
        await self.session.flush()
        return skill

    async def get_by_id(
        self,
        skill_id: str,
        include_versions: bool = False,
    ) -> Optional[SkillDB]:
        """Get a skill by ID."""
        stmt = select(SkillDB).where(SkillDB.id == skill_id)

        if include_versions:
            stmt = stmt.options(selectinload(SkillDB.versions))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        name: str,
        include_versions: bool = False,
    ) -> Optional[SkillDB]:
        """Get a skill by name."""
        stmt = select(SkillDB).where(SkillDB.name == name)

        if include_versions:
            stmt = stmt.options(selectinload(SkillDB.versions))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # Whitelist of allowed sort columns
    SORT_COLUMNS = {
        "name": SkillDB.name,
        "updated_at": SkillDB.updated_at,
        "created_at": SkillDB.created_at,
    }

    async def list_all(
        self,
        status: Optional[str] = None,
        owner_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 100,
    ) -> List[SkillDB]:
        """List all skills with optional filtering and sorting."""
        # Determine sort column and direction
        sort_col = self.SORT_COLUMNS.get(sort_by, SkillDB.updated_at)
        order = sort_col.desc() if sort_order == "desc" else sort_col.asc()

        # Pinned skills always appear first
        stmt = select(SkillDB).order_by(SkillDB.is_pinned.desc(), order)

        if status:
            stmt = stmt.where(SkillDB.status == status)
        if owner_id:
            stmt = stmt.where(SkillDB.owner_id == owner_id)
        if tags:
            # Use @> (contains) with OR: tags @> '["t1"]' OR tags @> '["t2"]'
            stmt = stmt.where(or_(*[SkillDB.tags.contains([t]) for t in tags]))
        if category:
            stmt = stmt.where(SkillDB.category == category)

        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self,
        status: Optional[str] = None,
        owner_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
    ) -> int:
        """Count skills with optional filtering."""
        stmt = select(func.count(SkillDB.id))

        if status:
            stmt = stmt.where(SkillDB.status == status)
        if owner_id:
            stmt = stmt.where(SkillDB.owner_id == owner_id)
        if tags:
            stmt = stmt.where(or_(*[SkillDB.tags.contains([t]) for t in tags]))
        if category:
            stmt = stmt.where(SkillDB.category == category)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_all_tags(self) -> List[str]:
        """Get all unique tags across all skills."""
        result = await self.session.execute(
            text(
                "SELECT DISTINCT jsonb_array_elements_text(tags) AS tag "
                "FROM skills WHERE tags IS NOT NULL AND tags != '[]'::jsonb "
                "AND jsonb_typeof(tags) = 'array' "
                "ORDER BY tag"
            )
        )
        return [row[0] for row in result.fetchall()]

    async def get_all_categories(self) -> List[str]:
        """Get all unique categories across all skills."""
        result = await self.session.execute(
            text(
                "SELECT DISTINCT category FROM skills "
                "WHERE category IS NOT NULL AND category != '' "
                "AND skill_type != 'meta' "
                "ORDER BY category"
            )
        )
        return [row[0] for row in result.fetchall()]

    async def update(
        self,
        skill_id: str,
        **kwargs,
    ) -> Optional[SkillDB]:
        """Update a skill by ID."""
        # Always update updated_at
        kwargs["updated_at"] = datetime.utcnow()

        stmt = (
            update(SkillDB)
            .where(SkillDB.id == skill_id)
            .values(**kwargs)
            .returning(SkillDB)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_by_name(
        self,
        name: str,
        **kwargs,
    ) -> Optional[SkillDB]:
        """Update a skill by name."""
        kwargs["updated_at"] = datetime.utcnow()

        stmt = (
            update(SkillDB)
            .where(SkillDB.name == name)
            .values(**kwargs)
            .returning(SkillDB)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, skill_id: str) -> bool:
        """Delete a skill by ID."""
        stmt = delete(SkillDB).where(SkillDB.id == skill_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def delete_by_name(self, name: str) -> bool:
        """Delete a skill by name."""
        stmt = delete(SkillDB).where(SkillDB.name == name)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def exists(self, name: str) -> bool:
        """Check if a skill with the given name exists."""
        stmt = select(func.count(SkillDB.id)).where(SkillDB.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def set_current_version(
        self,
        skill_id: str,
        version: str,
    ) -> Optional[SkillDB]:
        """Set the current version of a skill."""
        return await self.update(skill_id, current_version=version)

    async def search(
        self,
        query: str,
        offset: int = 0,
        limit: int = 100,
    ) -> List[SkillDB]:
        """Search skills by name or description."""
        search_pattern = f"%{query}%"
        stmt = (
            select(SkillDB)
            .where(
                (SkillDB.name.ilike(search_pattern))
                | (SkillDB.description.ilike(search_pattern))
            )
            .order_by(SkillDB.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_changelog(
        self,
        skill_id: str,
        change_type: str,
        version_from: Optional[str] = None,
        version_to: Optional[str] = None,
        diff_content: Optional[str] = None,
        changed_by: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> SkillChangelogDB:
        """Add a changelog entry for a skill."""
        changelog = SkillChangelogDB(
            skill_id=skill_id,
            change_type=change_type,
            version_from=version_from,
            version_to=version_to,
            diff_content=diff_content,
            changed_by=changed_by,
            comment=comment,
            changed_at=datetime.utcnow(),
        )
        self.session.add(changelog)
        await self.session.flush()
        return changelog

    async def get_changelogs(
        self,
        skill_id: str,
        offset: int = 0,
        limit: int = 50,
    ) -> List[SkillChangelogDB]:
        """Get changelog entries for a skill."""
        stmt = (
            select(SkillChangelogDB)
            .where(SkillChangelogDB.skill_id == skill_id)
            .order_by(SkillChangelogDB.changed_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
