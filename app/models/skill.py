"""Skill models for Skill Composer."""
from typing import Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Skill(BaseModel):
    """Skill info - from types.ts"""
    name: str
    description: str
    location: Literal["project", "global"]
    path: str
    skill_type: Literal["user", "meta"] = "user"  # user or meta


class SkillLocation(BaseModel):
    """Skill location info - from types.ts"""
    path: str       # Full path to SKILL.md
    base_dir: str   # Skill directory
    source: str     # Source search directory


class SkillResources(BaseModel):
    """Skill bundled resources"""
    scripts: list[str] = []      # Executable scripts in scripts/
    references: list[str] = []   # Reference docs in references/
    assets: list[str] = []       # Asset files in assets/
    other: list[str] = []        # Files in other directories (e.g., rules/)


class SkillContent(BaseModel):
    """Full skill content"""
    name: str
    description: str
    content: str    # Full SKILL.md content
    base_dir: str   # For resolving relative paths
    resources: Optional[SkillResources] = None  # Bundled resources


class SkillListResponse(BaseModel):
    """Response for listing skills"""
    skills: list[Skill]
    total: int


class IntentMatchResult(BaseModel):
    """LLM intent matching result"""
    matched_skill: Optional[str] = None
    confidence: float = 0.0
    reasoning: str = ""
    alternatives: list[str] = []


class ExecuteResponse(BaseModel):
    """Execution response"""
    success: bool
    skill_name: Optional[str] = None
    skill_content: Optional[str] = None
    base_dir: Optional[str] = None
    intent: Optional[IntentMatchResult] = None
    message: str
