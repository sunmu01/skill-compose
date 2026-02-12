"""
Tests for the System Export/Import API.
"""
import io
import json
import zipfile

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import make_skill, make_skill_version, make_skill_file, make_preset


@pytest_asyncio.fixture
async def user_skill_with_version(db_session: AsyncSession):
    """Create a user skill with a version and file."""
    skill = make_skill(
        name="export-test-skill",
        description="Test skill for export",
        skill_type="user",
        tags=["test", "export"],
    )
    db_session.add(skill)
    await db_session.flush()

    version = make_skill_version(
        skill_id=skill.id,
        version="1.0.0",
        skill_md="# Export Test Skill\n\nThis is a test.",
    )
    db_session.add(version)
    await db_session.flush()

    # Update current_version
    skill.current_version = "1.0.0"

    file = make_skill_file(
        version_id=version.id,
        file_path="scripts/test.py",
        file_type="script",
        content=b"print('hello')",
    )
    db_session.add(file)
    await db_session.flush()

    return skill


@pytest_asyncio.fixture
async def meta_skill(db_session: AsyncSession):
    """Create a meta skill (should be excluded from export)."""
    skill = make_skill(
        name="skill-creator",
        description="Meta skill",
        skill_type="meta",
    )
    db_session.add(skill)
    await db_session.flush()
    return skill


@pytest_asyncio.fixture
async def user_preset(db_session: AsyncSession):
    """Create a user preset for export."""
    preset = make_preset(
        name="export-test-preset",
        description="Test preset for export",
        is_system=False,
        skill_ids=["export-test-skill"],
        mcp_servers=["fetch"],
        max_turns=30,
    )
    db_session.add(preset)
    await db_session.flush()
    return preset


@pytest_asyncio.fixture
async def system_preset(db_session: AsyncSession):
    """Create a system preset (should be excluded from export)."""
    preset = make_preset(
        name="default-agent",
        description="System preset",
        is_system=True,
    )
    db_session.add(preset)
    await db_session.flush()
    return preset


class TestSystemExport:
    """Tests for POST /api/v1/system/export"""

    @pytest.mark.asyncio
    async def test_export_empty_system(self, client: AsyncClient):
        """Test export when no user data exists."""
        response = await client.post("/api/v1/system/export")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

        # Verify zip structure
        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            files = zf.namelist()
            assert "manifest.json" in files
            assert "db/skills.json" in files
            assert "db/agent_presets.json" in files

            # Check manifest
            manifest = json.loads(zf.read("manifest.json"))
            assert manifest["export_version"] == "1.0"
            assert manifest["statistics"]["skills"] == 0
            assert manifest["statistics"]["agent_presets"] == 0

    @pytest.mark.asyncio
    async def test_export_with_user_data(
        self, client: AsyncClient, user_skill_with_version, user_preset
    ):
        """Test export with user skills and presets."""
        response = await client.post("/api/v1/system/export")
        assert response.status_code == 200

        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            # Check manifest statistics
            manifest = json.loads(zf.read("manifest.json"))
            assert manifest["statistics"]["skills"] == 1
            assert manifest["statistics"]["skill_versions"] == 1
            assert manifest["statistics"]["skill_files"] == 1
            assert manifest["statistics"]["agent_presets"] == 1

            # Check skills.json content
            skills_data = json.loads(zf.read("db/skills.json"))
            assert len(skills_data["skills"]) == 1
            skill = skills_data["skills"][0]
            assert skill["name"] == "export-test-skill"
            assert skill["skill_type"] == "user"
            assert len(skill["versions"]) == 1
            assert skill["versions"][0]["version"] == "1.0.0"
            assert len(skill["versions"][0]["files"]) == 1

            # Check presets.json content
            presets_data = json.loads(zf.read("db/agent_presets.json"))
            assert len(presets_data["presets"]) == 1
            preset = presets_data["presets"][0]
            assert preset["name"] == "export-test-preset"
            assert preset["skill_ids"] == ["export-test-skill"]

    @pytest.mark.asyncio
    async def test_export_excludes_meta_skills(
        self, client: AsyncClient, user_skill_with_version, meta_skill
    ):
        """Test that meta skills are excluded from export."""
        response = await client.post("/api/v1/system/export")
        assert response.status_code == 200

        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            skills_data = json.loads(zf.read("db/skills.json"))
            skill_names = [s["name"] for s in skills_data["skills"]]
            assert "export-test-skill" in skill_names
            assert "skill-creator" not in skill_names

    @pytest.mark.asyncio
    async def test_export_excludes_system_presets(
        self, client: AsyncClient, user_preset, system_preset
    ):
        """Test that system presets are excluded from export."""
        response = await client.post("/api/v1/system/export")
        assert response.status_code == 200

        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            presets_data = json.loads(zf.read("db/agent_presets.json"))
            preset_names = [p["name"] for p in presets_data["presets"]]
            assert "export-test-preset" in preset_names
            assert "default-agent" not in preset_names


class TestSystemImport:
    """Tests for POST /api/v1/system/import"""

    def _create_export_zip(
        self,
        skills: list = None,
        presets: list = None,
        export_version: str = "1.0",
    ) -> bytes:
        """Helper to create a valid export zip for testing."""
        skills = skills or []
        presets = presets or []

        manifest = {
            "export_version": export_version,
            "exported_at": "2024-01-01T00:00:00",
            "statistics": {
                "skills": len(skills),
                "skill_versions": sum(len(s.get("versions", [])) for s in skills),
                "skill_files": sum(
                    len(v.get("files", []))
                    for s in skills
                    for v in s.get("versions", [])
                ),
                "agent_presets": len(presets),
            },
        }

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest))
            zf.writestr("db/skills.json", json.dumps({"skills": skills}))
            zf.writestr("db/agent_presets.json", json.dumps({"presets": presets}))

        return zip_buffer.getvalue()

    @pytest.mark.asyncio
    async def test_import_empty_bundle(self, client: AsyncClient):
        """Test importing an empty export bundle."""
        zip_content = self._create_export_zip()

        response = await client.post(
            "/api/v1/system/import",
            files={"file": ("export.zip", zip_content, "application/zip")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["imported"]["skills"] == 0
        assert data["imported"]["agent_presets"] == 0

    @pytest.mark.asyncio
    async def test_import_skill(self, client: AsyncClient):
        """Test importing a skill."""
        import base64

        skills = [
            {
                "name": "imported-skill",
                "description": "An imported skill",
                "status": "active",
                "skill_type": "user",
                "tags": ["imported"],
                "current_version": "1.0.0",
                "versions": [
                    {
                        "version": "1.0.0",
                        "skill_md": "# Imported Skill\n\nTest content.",
                        "files": [
                            {
                                "file_path": "scripts/run.py",
                                "file_type": "script",
                                "content_base64": base64.b64encode(
                                    b"print('imported')"
                                ).decode(),
                                "size_bytes": 17,
                            }
                        ],
                    }
                ],
            }
        ]
        zip_content = self._create_export_zip(skills=skills)

        response = await client.post(
            "/api/v1/system/import",
            files={"file": ("export.zip", zip_content, "application/zip")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["imported"]["skills"] == 1
        assert data["imported"]["skill_versions"] == 1
        assert data["imported"]["skill_files"] == 1

        # Verify skill was created
        skill_response = await client.get("/api/v1/registry/skills/imported-skill")
        assert skill_response.status_code == 200
        skill_data = skill_response.json()
        assert skill_data["name"] == "imported-skill"
        assert skill_data["current_version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_import_preset(self, client: AsyncClient):
        """Test importing an agent preset."""
        presets = [
            {
                "name": "imported-preset",
                "description": "An imported preset",
                "system_prompt": "You are helpful.",
                "skill_ids": [],
                "mcp_servers": ["fetch"],
                "max_turns": 50,
                "is_published": False,
            }
        ]
        zip_content = self._create_export_zip(presets=presets)

        response = await client.post(
            "/api/v1/system/import",
            files={"file": ("export.zip", zip_content, "application/zip")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["imported"]["agent_presets"] == 1

        # Verify preset was created
        preset_response = await client.get("/api/v1/agents/by-name/imported-preset")
        assert preset_response.status_code == 200
        preset_data = preset_response.json()
        assert preset_data["name"] == "imported-preset"
        assert preset_data["max_turns"] == 50

    @pytest.mark.asyncio
    async def test_import_skips_existing_skill(
        self, client: AsyncClient, user_skill_with_version
    ):
        """Test that existing skills are skipped during import."""
        skills = [
            {
                "name": "export-test-skill",  # Same name as fixture
                "description": "Duplicate skill",
                "status": "active",
                "skill_type": "user",
                "current_version": "2.0.0",
                "versions": [],
            }
        ]
        zip_content = self._create_export_zip(skills=skills)

        response = await client.post(
            "/api/v1/system/import",
            files={"file": ("export.zip", zip_content, "application/zip")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imported"]["skills"] == 0
        assert data["skipped"]["skills"] == 1

    @pytest.mark.asyncio
    async def test_import_skips_existing_preset(self, client: AsyncClient, user_preset):
        """Test that existing presets are skipped during import."""
        presets = [
            {
                "name": "export-test-preset",  # Same name as fixture
                "description": "Duplicate preset",
            }
        ]
        zip_content = self._create_export_zip(presets=presets)

        response = await client.post(
            "/api/v1/system/import",
            files={"file": ("export.zip", zip_content, "application/zip")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imported"]["agent_presets"] == 0
        assert data["skipped"]["agent_presets"] == 1

    @pytest.mark.asyncio
    async def test_import_invalid_file_extension(self, client: AsyncClient):
        """Test that non-zip files are rejected."""
        response = await client.post(
            "/api/v1/system/import",
            files={"file": ("export.txt", b"not a zip", "text/plain")},
        )
        assert response.status_code == 400
        assert "must be a .zip" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_import_invalid_zip(self, client: AsyncClient):
        """Test that invalid zip files are rejected."""
        response = await client.post(
            "/api/v1/system/import",
            files={"file": ("export.zip", b"not a valid zip", "application/zip")},
        )
        assert response.status_code == 400
        assert "Invalid zip" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_import_missing_manifest(self, client: AsyncClient):
        """Test that zips without manifest.json are rejected."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("db/skills.json", "{}")
        zip_content = zip_buffer.getvalue()

        response = await client.post(
            "/api/v1/system/import",
            files={"file": ("export.zip", zip_content, "application/zip")},
        )
        assert response.status_code == 400
        assert "missing manifest.json" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_import_unsupported_version(self, client: AsyncClient):
        """Test that unsupported export versions are rejected."""
        zip_content = self._create_export_zip(export_version="99.0")

        response = await client.post(
            "/api/v1/system/import",
            files={"file": ("export.zip", zip_content, "application/zip")},
        )
        assert response.status_code == 400
        assert "Unsupported export version" in response.json()["detail"]


class TestExportImportRoundTrip:
    """Test the complete export -> import workflow."""

    @pytest.mark.asyncio
    async def test_export_import_roundtrip(self, client: AsyncClient):
        """Test that exported data can be imported into a fresh system."""
        import base64

        # Create test data via import first
        skills = [
            {
                "name": "roundtrip-skill",
                "description": "Roundtrip test skill",
                "status": "active",
                "skill_type": "user",
                "tags": ["test"],
                "current_version": "1.0.0",
                "versions": [
                    {
                        "version": "1.0.0",
                        "skill_md": "# Roundtrip\n\nTest.",
                        "commit_message": "Initial",
                        "files": [
                            {
                                "file_path": "scripts/main.py",
                                "file_type": "script",
                                "content_base64": base64.b64encode(b"# main").decode(),
                                "size_bytes": 6,
                            }
                        ],
                    }
                ],
            }
        ]
        presets = [
            {
                "name": "roundtrip-preset",
                "description": "Roundtrip test preset",
                "skill_ids": ["roundtrip-skill"],
                "max_turns": 42,
            }
        ]

        # Import initial data
        zip_content = TestSystemImport._create_export_zip(
            TestSystemImport(), skills=skills, presets=presets
        )
        import_response = await client.post(
            "/api/v1/system/import",
            files={"file": ("export.zip", zip_content, "application/zip")},
        )
        assert import_response.status_code == 200
        assert import_response.json()["imported"]["skills"] == 1

        # Export the data
        export_response = await client.post("/api/v1/system/export")
        assert export_response.status_code == 200

        # Verify exported content matches what was imported
        zip_buffer = io.BytesIO(export_response.content)
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            exported_skills = json.loads(zf.read("db/skills.json"))
            exported_presets = json.loads(zf.read("db/agent_presets.json"))

            assert len(exported_skills["skills"]) == 1
            assert exported_skills["skills"][0]["name"] == "roundtrip-skill"
            assert exported_skills["skills"][0]["tags"] == ["test"]

            assert len(exported_presets["presets"]) == 1
            assert exported_presets["presets"][0]["name"] == "roundtrip-preset"
            assert exported_presets["presets"][0]["max_turns"] == 42
