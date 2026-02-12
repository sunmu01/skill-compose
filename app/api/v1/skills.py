"""Skills API endpoints"""
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.core.skill_manager import find_all_skills, read_skill
from app.models.skill import Skill, SkillContent, SkillListResponse

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("/", response_model=SkillListResponse)
async def list_skills():
    """
    List all installed skills.
    """
    skills = find_all_skills()
    return SkillListResponse(skills=skills, total=len(skills))


@router.get("/{skill_name}", response_model=SkillContent)
async def get_skill(skill_name: str):
    """
    Get skill content by name.
    """
    skill = read_skill(skill_name)
    if not skill:
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_name}' not found. "
            "Searched: .agent/skills/, ~/.agent/skills/, .claude/skills/, ~/.claude/skills/",
        )
    return skill


@router.get("/{skill_name}/resources/{resource_type}/{filename:path}", response_class=PlainTextResponse)
async def get_resource_file(skill_name: str, resource_type: str, filename: str):
    """
    Get the content of a resource file from a skill.

    resource_type: scripts, references, or assets
    filename: the name of the file to read
    """
    # Validate resource type
    if resource_type not in ["scripts", "references", "assets"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid resource type '{resource_type}'. Must be 'scripts', 'references', or 'assets'."
        )

    # Get skill to find base directory
    skill = read_skill(skill_name)
    if not skill:
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_name}' not found."
        )

    # Construct file path
    base_dir = Path(skill.base_dir)
    file_path = base_dir / resource_type / filename

    # Security check: ensure file is within skill directory
    try:
        file_path = file_path.resolve()
        base_dir = base_dir.resolve()
        if not str(file_path).startswith(str(base_dir)):
            raise HTTPException(
                status_code=403,
                detail="Access denied: path traversal detected"
            )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid file path"
        )

    # Check if file exists
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found in {resource_type}"
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=400,
            detail=f"'{filename}' is not a file"
        )

    # Read and return file content
    try:
        content = file_path.read_text(encoding="utf-8")
        return content
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File is not a text file or has encoding issues"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading file: {str(e)}"
        )
