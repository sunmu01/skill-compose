"""
Pydantic models for Skill Package structure.

A Skill Package is the complete deliverable unit containing:
- SKILL.md (required)
- schema.json (required)
- manifest.json (required)
- resources/ (optional)
- scripts/ (optional)
- tests/ (optional)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SkillSchema(BaseModel):
    """JSON Schema for skill input/output validation."""

    input: Optional[Dict[str, Any]] = Field(
        default=None, description="JSON Schema for input validation"
    )
    output: Optional[Dict[str, Any]] = Field(
        default=None, description="JSON Schema for output validation"
    )


class SkillDependencies(BaseModel):
    """Dependencies required by the skill."""

    mcp: List[str] = Field(default_factory=list, description="Required MCP servers")
    tools: List[str] = Field(default_factory=list, description="Required tools")
    skills: List[str] = Field(default_factory=list, description="Required skills")


class SkillManifest(BaseModel):
    """Manifest metadata for a skill package (manifest.json)."""

    name: str = Field(..., description="Skill name (lowercase, hyphenated)")
    version: str = Field(..., description="SemVer version string")
    description: str = Field(..., description="Short description")
    author: Optional[str] = Field(default=None, description="Author name or team")
    license: Optional[str] = Field(default="proprietary", description="License type")
    dependencies: Optional[SkillDependencies] = Field(
        default=None, description="Required dependencies"
    )
    triggers: List[str] = Field(
        default_factory=list, description="Natural language triggers"
    )
    tags: List[str] = Field(default_factory=list, description="Categorization tags")
    created: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated: Optional[datetime] = Field(default=None, description="Last update timestamp")


class SkillFile(BaseModel):
    """A file within the skill package."""

    path: str = Field(..., description="Relative path within package")
    file_type: str = Field(
        ..., description="File type: resource, script, test, other"
    )
    content: Optional[str] = Field(
        default=None, description="File content (text files only)"
    )
    content_bytes: Optional[bytes] = Field(
        default=None, description="Binary content", exclude=True
    )
    size_bytes: Optional[int] = Field(default=None, description="File size in bytes")
    content_hash: Optional[str] = Field(default=None, description="SHA256 hash")


class SkillTestCase(BaseModel):
    """A test case for the skill."""

    name: str = Field(..., description="Test case name")
    description: Optional[str] = Field(default=None, description="Test description")
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="Test input")
    expected_output: Optional[Dict[str, Any]] = Field(
        default=None, description="Expected output"
    )
    is_golden: bool = Field(default=False, description="Is this a golden test case")


class SkillPackage(BaseModel):
    """
    Complete skill package structure.

    This represents the full deliverable unit that can be:
    - Imported from a zip file
    - Exported to a zip file
    - Stored in the database as a version
    """

    # Required fields
    skill_md: str = Field(..., description="SKILL.md content")
    schema: SkillSchema = Field(..., description="Input/output schema")
    manifest: SkillManifest = Field(..., description="Package manifest")

    # Optional fields
    files: List[SkillFile] = Field(
        default_factory=list, description="Additional files (resources, scripts)"
    )
    tests: List[SkillTestCase] = Field(
        default_factory=list, description="Test cases"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "skill_md": "---\nname: example-skill\ndescription: An example skill\n---\n\n# Example Skill\n\nThis skill does...",
                "schema": {
                    "input": {
                        "type": "object",
                        "properties": {"file_path": {"type": "string"}},
                        "required": ["file_path"],
                    },
                    "output": {
                        "type": "object",
                        "properties": {"result": {"type": "string"}},
                    },
                },
                "manifest": {
                    "name": "example-skill",
                    "version": "1.0.0",
                    "description": "An example skill",
                    "tags": ["example"],
                },
            }
        }


# API Request/Response Models

class CreateSkillRequest(BaseModel):
    """Request to create a new skill."""

    name: str = Field(
        ...,
        description="Skill name (lowercase, hyphenated)",
        pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$",
        min_length=2,
        max_length=128,
    )
    description: Optional[str] = Field(
        default=None, description="Short description", max_length=500
    )
    skill_type: str = Field(
        default="user", description="Skill type: user or meta"
    )
    tags: Optional[List[str]] = Field(
        default=None, description="Categorization tags"
    )
    category: Optional[str] = Field(
        default=None, description="Skill category", max_length=64
    )


class UpdateSkillRequest(BaseModel):
    """Request to update a skill."""

    description: Optional[str] = Field(
        default=None, description="Short description", max_length=500
    )
    status: Optional[str] = Field(
        default=None, description="Status: draft, active, deprecated"
    )
    tags: Optional[List[str]] = Field(
        default=None, description="Categorization tags"
    )
    icon_url: Optional[str] = Field(
        default=None, description="URL to skill icon image"
    )
    category: Optional[str] = Field(
        default=None, description="Skill category", max_length=64
    )
    source: Optional[str] = Field(
        default=None, description="Import source URL", max_length=1024
    )
    author: Optional[str] = Field(
        default=None, description="Author name", max_length=256
    )


class CreateVersionRequest(BaseModel):
    """Request to create a new version."""

    version: Optional[str] = Field(
        default=None,
        description="SemVer version string. If omitted, auto-increments from the highest existing version.",
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$",
    )
    skill_md: Optional[str] = Field(default=None, description="SKILL.md content")
    schema_json: Optional[Dict[str, Any]] = Field(
        default=None, description="Input/output schema"
    )
    manifest_json: Optional[Dict[str, Any]] = Field(
        default=None, description="Package manifest"
    )
    commit_message: Optional[str] = Field(
        default=None, description="Version description", max_length=500
    )
    files_content: Optional[Dict[str, str]] = Field(
        default=None, description="Additional file contents keyed by file path (e.g. scripts/foo.py)"
    )


class RollbackRequest(BaseModel):
    """Request to rollback to a previous version."""

    version: str = Field(..., description="Target version to rollback to")
    comment: Optional[str] = Field(
        default=None, description="Rollback reason", max_length=500
    )


class SkillResponse(BaseModel):
    """Response for a single skill."""

    id: str
    name: str
    description: Optional[str]
    owner_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    current_version: Optional[str]
    status: str
    skill_type: str = "user"  # user or meta
    tags: List[str] = []
    icon_url: Optional[str] = None  # URL to skill icon image
    source: Optional[str] = None  # Import source URL (e.g., GitHub URL)
    author: Optional[str] = None  # Author or organization name
    category: Optional[str] = None  # Skill category
    is_pinned: bool = False  # Whether skill is pinned to top


class SkillListResponse(BaseModel):
    """Response for skill list."""

    skills: List[SkillResponse]
    total: int
    offset: int = 0
    limit: int = 100


class VersionResponse(BaseModel):
    """Response for a single version."""

    id: str
    skill_id: str
    version: str
    parent_version: Optional[str]
    skill_md: Optional[str]
    schema_json: Optional[Dict[str, Any]]
    manifest_json: Optional[Dict[str, Any]]
    created_at: datetime
    created_by: Optional[str]
    commit_message: Optional[str]


class VersionListResponse(BaseModel):
    """Response for version list."""

    versions: List[VersionResponse]
    total: int


class ChangelogResponse(BaseModel):
    """Response for a changelog entry."""

    id: str
    skill_id: str
    version_from: Optional[str]
    version_to: Optional[str]
    change_type: str
    diff_content: Optional[str]
    changed_by: Optional[str]
    changed_at: datetime
    comment: Optional[str]


class ChangelogListResponse(BaseModel):
    """Response for changelog list."""

    changelogs: List[ChangelogResponse]
    total: int


class DiffResponse(BaseModel):
    """Response for diff between versions."""

    skill_name: str
    from_version: str
    to_version: str
    diff: str
    files_changed: int = 0


# Tools API Models

class ToolResponse(BaseModel):
    """Response for a single tool."""

    id: str
    name: str
    description: str
    category: str
    input_schema: Dict[str, Any]


class ToolCategoryResponse(BaseModel):
    """Response for a tool category."""

    id: str
    name: str
    description: str
    icon: str


class ToolListResponse(BaseModel):
    """Response for tools list."""

    tools: List[ToolResponse]
    categories: Dict[str, ToolCategoryResponse]
    total: int


