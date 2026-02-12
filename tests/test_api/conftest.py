"""
API test fixtures providing pre-created database records.
"""
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import (
    make_skill,
    make_skill_version,
    make_skill_file,
    make_trace,
    make_preset,
    make_changelog,
    make_background_task,
    make_published_session,
)


@pytest_asyncio.fixture
async def sample_skill(db_session: AsyncSession):
    """Create a sample skill in the database."""
    skill = make_skill(name="test-skill", description="A test skill")
    db_session.add(skill)
    await db_session.flush()
    return skill


@pytest_asyncio.fixture
async def sample_skill_version(db_session: AsyncSession, sample_skill):
    """Create a sample skill version."""
    version = make_skill_version(skill_id=sample_skill.id)
    db_session.add(version)
    await db_session.flush()
    return version


@pytest_asyncio.fixture
async def sample_skill_file(db_session: AsyncSession, sample_skill_version):
    """Create a sample skill file."""
    file = make_skill_file(version_id=sample_skill_version.id)
    db_session.add(file)
    await db_session.flush()
    return file


@pytest_asyncio.fixture
async def sample_preset(db_session: AsyncSession):
    """Create a sample user preset."""
    preset = make_preset(name="test-preset", description="A test preset")
    db_session.add(preset)
    await db_session.flush()
    return preset


@pytest_asyncio.fixture
async def system_preset(db_session: AsyncSession):
    """Create a system preset."""
    preset = make_preset(
        name="system-preset",
        description="A system preset",
        is_system=True,
    )
    db_session.add(preset)
    await db_session.flush()
    return preset


@pytest_asyncio.fixture
async def sample_trace(db_session: AsyncSession):
    """Create a sample execution trace."""
    trace = make_trace()
    db_session.add(trace)
    await db_session.flush()
    return trace


@pytest_asyncio.fixture
async def sample_changelog(db_session: AsyncSession, sample_skill):
    """Create a sample changelog entry."""
    changelog = make_changelog(skill_id=sample_skill.id)
    db_session.add(changelog)
    await db_session.flush()
    return changelog


@pytest_asyncio.fixture
async def sample_background_task(db_session: AsyncSession):
    """Create a sample background task."""
    task = make_background_task()
    db_session.add(task)
    await db_session.flush()
    return task


@pytest_asyncio.fixture
async def published_preset(db_session: AsyncSession):
    """Create a published (is_published=True) user preset."""
    preset = make_preset(
        name="published-preset",
        description="A published preset",
        is_published=True,
    )
    db_session.add(preset)
    await db_session.flush()
    return preset


@pytest_asyncio.fixture
async def sample_session(db_session: AsyncSession, published_preset):
    """Create a sample published session."""
    session = make_published_session(
        agent_id=published_preset.id,
        messages=[
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "Hi there!"},
        ],
    )
    db_session.add(session)
    await db_session.flush()
    return session
