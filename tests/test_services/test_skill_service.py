"""
Tests for app.services.skill_service.SkillService.

Uses the db_session fixture from conftest.py (SQLite in-memory, transactional
isolation per test) and the factories helper to insert test data.
"""

import pytest
import pytest_asyncio

from app.services.skill_service import (
    SkillService,
    SkillNotFoundError,
    SkillAlreadyExistsError,
    VersionNotFoundError,
)
from tests.factories import make_skill, make_skill_version


SAMPLE_SKILL_MD = """\
---
name: test-skill
description: A test skill for service tests
version: 0.0.1
---

# Test Skill

This skill is used for testing the skill service layer thoroughly and completely.

## Details

Detailed information about the skill purpose and behaviour in tests.
"""


@pytest_asyncio.fixture
async def service(db_session):
    """Create a SkillService bound to the transactional test session."""
    return SkillService(db_session)


@pytest_asyncio.fixture
async def skill_in_db(db_session):
    """Insert a single skill via factory and return it."""
    skill = make_skill(name="alpha-skill", description="Alpha skill for testing")
    db_session.add(skill)
    await db_session.flush()
    return skill


@pytest_asyncio.fixture
async def skill_with_version(db_session):
    """Insert a skill with an initial version."""
    skill = make_skill(name="versioned-skill", description="Has a version")
    db_session.add(skill)
    await db_session.flush()

    version = make_skill_version(
        skill_id=skill.id,
        version="0.0.1",
        skill_md=SAMPLE_SKILL_MD,
        commit_message="Initial version",
    )
    db_session.add(version)
    await db_session.flush()
    return skill


# ---------------------------------------------------------------------------
# list_skills
# ---------------------------------------------------------------------------


async def test_list_skills_empty(service: SkillService):
    result = await service.list_skills()
    assert result.total == 0
    assert result.skills == []


async def test_list_skills_with_data(service: SkillService, skill_in_db):
    result = await service.list_skills()
    assert result.total == 1
    assert result.skills[0].name == "alpha-skill"


async def test_list_skills_filter_by_status(service: SkillService, db_session):
    active = make_skill(name="active-one", status="active")
    draft = make_skill(name="draft-one", status="draft")
    db_session.add_all([active, draft])
    await db_session.flush()

    result = await service.list_skills(status="active")
    assert result.total == 1
    assert result.skills[0].name == "active-one"


# ---------------------------------------------------------------------------
# get_skill
# ---------------------------------------------------------------------------


async def test_get_skill(service: SkillService, skill_in_db):
    skill = await service.get_skill("alpha-skill")
    assert skill.name == "alpha-skill"
    assert skill.description == "Alpha skill for testing"


async def test_get_skill_not_found(service: SkillService):
    with pytest.raises(SkillNotFoundError):
        await service.get_skill("nonexistent-skill")


# ---------------------------------------------------------------------------
# update_skill
# ---------------------------------------------------------------------------


async def test_update_skill_description(service: SkillService, skill_in_db):
    updated = await service.update_skill("alpha-skill", description="Updated desc")
    assert updated.description == "Updated desc"


async def test_update_skill_status(service: SkillService, skill_in_db):
    updated = await service.update_skill("alpha-skill", status="active")
    assert updated.status == "active"


async def test_update_skill_not_found(service: SkillService):
    with pytest.raises(SkillNotFoundError):
        await service.update_skill("ghost-skill", description="nope")


# ---------------------------------------------------------------------------
# delete_skill
# ---------------------------------------------------------------------------


async def test_delete_skill(service: SkillService, skill_in_db):
    result = await service.delete_skill("alpha-skill")
    assert result is True

    # Confirm it is gone
    with pytest.raises(SkillNotFoundError):
        await service.get_skill("alpha-skill")


async def test_delete_skill_not_found(service: SkillService):
    with pytest.raises(SkillNotFoundError):
        await service.delete_skill("nonexistent-skill")


# ---------------------------------------------------------------------------
# search_skills
# ---------------------------------------------------------------------------


async def test_search_skills_by_name(service: SkillService, skill_in_db):
    result = await service.search_skills("alpha")
    assert result.total == 1
    assert result.skills[0].name == "alpha-skill"


async def test_search_skills_by_description(service: SkillService, skill_in_db):
    result = await service.search_skills("testing")
    assert result.total == 1


async def test_search_skills_no_match(service: SkillService, skill_in_db):
    result = await service.search_skills("zzz-nothing")
    assert result.total == 0


# ---------------------------------------------------------------------------
# create_version
# ---------------------------------------------------------------------------


async def test_create_version(service: SkillService, skill_with_version):
    version = await service.create_version(
        skill_name="versioned-skill",
        version="0.0.2",
        skill_md=SAMPLE_SKILL_MD,
        commit_message="Second version",
    )
    assert version.version == "0.0.2"
    assert version.parent_version == "0.0.1"
    assert version.commit_message == "Second version"


async def test_create_version_skill_not_found(service: SkillService):
    with pytest.raises(SkillNotFoundError):
        await service.create_version(
            skill_name="nonexistent",
            version="1.0.0",
            skill_md=SAMPLE_SKILL_MD,
        )


async def test_create_version_invalid_version_string(
    service: SkillService, skill_with_version
):
    from app.services.skill_service import ValidationError

    with pytest.raises(ValidationError):
        await service.create_version(
            skill_name="versioned-skill",
            version="bad-version",
            skill_md=SAMPLE_SKILL_MD,
        )


# ---------------------------------------------------------------------------
# list_versions / get_version
# ---------------------------------------------------------------------------


async def test_list_versions(service: SkillService, skill_with_version):
    result = await service.list_versions("versioned-skill")
    assert result.total == 1
    assert result.versions[0].version == "0.0.1"


async def test_get_version(service: SkillService, skill_with_version):
    version = await service.get_version("versioned-skill", "0.0.1")
    assert version.version == "0.0.1"
    assert version.skill_md == SAMPLE_SKILL_MD


async def test_get_version_not_found(service: SkillService, skill_with_version):
    with pytest.raises(VersionNotFoundError):
        await service.get_version("versioned-skill", "9.9.9")


# ---------------------------------------------------------------------------
# changelogs
# ---------------------------------------------------------------------------


async def test_get_changelogs_empty(service: SkillService, skill_in_db):
    result = await service.get_changelogs("alpha-skill")
    assert result.total == 0
