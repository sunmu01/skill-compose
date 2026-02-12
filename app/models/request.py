"""Request models"""
from typing import Optional
from pydantic import BaseModel, Field


class NaturalLanguageRequest(BaseModel):
    """Natural language execution request"""
    query: str = Field(..., min_length=1, description="Natural language request")
    context: Optional[str] = Field(None, description="Additional context")
    file_ids: Optional[list[str]] = Field(None, description="Uploaded file IDs")


class SkillCreateRequest(BaseModel):
    """Create skill request"""
    name: str = Field(..., pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    description: str = Field(..., min_length=5)
    content: str = Field(..., description="SKILL.md markdown content")
    location: str = Field("project", description="project or global")
