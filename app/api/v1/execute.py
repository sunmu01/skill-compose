"""Execute API endpoints - natural language skill matching"""
import sys
import traceback
from io import StringIO
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.config import get_settings, Settings
from app.agent.tools import _fetch_skills_from_registry, _fetch_skill_content_from_registry
from app.llm.intent_parser import IntentParser
from app.llm.code_generator import CodeGenerator
from app.models.skill import Skill, SkillContent, SkillResources, ExecuteResponse, IntentMatchResult
from app.models.request import NaturalLanguageRequest

router = APIRouter(prefix="/execute", tags=["Execute"])


def _find_all_skills_from_db() -> list[Skill]:
    """Get all skills from the database (single source of truth)."""
    return [
        Skill(
            name=s["name"],
            description=s.get("description", ""),
            location="global",
            path="",
            skill_type="user",
        )
        for s in _fetch_skills_from_registry()
    ]


def _read_skill_from_db(skill_name: str):
    """Read skill content from the database (single source of truth)."""
    registry_skill = _fetch_skill_content_from_registry(skill_name)
    if registry_skill:
        return SkillContent(
            name=registry_skill["name"],
            description=registry_skill.get("description", ""),
            content=registry_skill.get("content", ""),
            base_dir="",
            resources=SkillResources(),
        )
    return None


class AutoExecuteResponse(BaseModel):
    """Response for auto execution"""
    success: bool
    skill_name: Optional[str] = None
    generated_code: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None
    message: str


def get_intent_parser(settings: Settings = Depends(get_settings)) -> IntentParser:
    """Dependency: get intent parser with API key"""
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY not configured",
        )
    return IntentParser(settings.anthropic_api_key, settings.claude_model)


@router.post("/natural", response_model=ExecuteResponse)
async def execute_natural_language(
    request: NaturalLanguageRequest,
    parser: IntentParser = Depends(get_intent_parser),
):
    """
    Execute skill via natural language.

    Flow:
    1. Get all available skills
    2. Use Claude to analyze intent and match skill
    3. Return matched skill content

    Example:
        Input: {"query": "Help me parse this PDF file"}
        Output: Matches "pdf" skill, returns skill content
    """
    # 1. Get available skills
    skills = _find_all_skills_from_db()
    if not skills:
        return ExecuteResponse(
            success=False,
            message="No skills installed. Create skills using the skill-creator agent.",
        )

    # 2. Match skill using LLM
    intent = parser.match_skill(
        query=request.query,
        available_skills=skills,
        context=request.context,
    )

    # 3. No match found
    if not intent.matched_skill:
        return ExecuteResponse(
            success=False,
            intent=intent,
            message=f"No matching skill found: {intent.reasoning}",
        )

    # 4. Load skill content
    skill_content = _read_skill_from_db(intent.matched_skill)
    if not skill_content:
        return ExecuteResponse(
            success=False,
            skill_name=intent.matched_skill,
            intent=intent,
            message=f"Skill '{intent.matched_skill}' found but could not be read",
        )

    # 5. Success
    return ExecuteResponse(
        success=True,
        skill_name=intent.matched_skill,
        skill_content=skill_content.content,
        base_dir=skill_content.base_dir,
        intent=intent,
        message=f"Matched skill: {intent.matched_skill}",
    )


@router.post("/skill/{skill_name}", response_model=ExecuteResponse)
async def execute_skill_directly(skill_name: str):
    """
    Execute specific skill directly (skip LLM matching).
    """
    skill_content = _read_skill_from_db(skill_name)
    if not skill_content:
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_name}' not found",
        )

    return ExecuteResponse(
        success=True,
        skill_name=skill_name,
        skill_content=skill_content.content,
        base_dir=skill_content.base_dir,
        message=f"Loaded skill: {skill_name}",
    )


@router.post("/analyze", response_model=IntentMatchResult)
async def analyze_intent(
    request: NaturalLanguageRequest,
    parser: IntentParser = Depends(get_intent_parser),
):
    """
    Analyze intent only (don't execute).
    Useful for debugging and previewing matches.
    """
    skills = _find_all_skills_from_db()
    if not skills:
        return IntentMatchResult(
            matched_skill=None,
            confidence=0.0,
            reasoning="No skills available",
        )

    return parser.match_skill(
        query=request.query,
        available_skills=skills,
        context=request.context,
    )


@router.post("/auto", response_model=AutoExecuteResponse)
async def auto_execute(
    request: NaturalLanguageRequest,
    settings: Settings = Depends(get_settings),
):
    """
    Fully automated execution: natural language → skill → code → result.

    Flow:
    1. Match skill based on user query
    2. Generate Python code using LLM
    3. Execute the code
    4. Return results

    Example:
        POST /execute/auto
        {"query": "Calculate the interaction energy of salicylic acid and niacinamide (xtb level)"}
    """
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    # Step 1: Match skill
    parser = IntentParser(settings.anthropic_api_key, settings.claude_model)
    skills = _find_all_skills_from_db()

    if not skills:
        return AutoExecuteResponse(
            success=False,
            message="No skills installed",
        )

    intent = parser.match_skill(
        query=request.query,
        available_skills=skills,
        context=request.context,
    )

    if not intent.matched_skill:
        return AutoExecuteResponse(
            success=False,
            message=f"No matching skill: {intent.reasoning}",
        )

    # Step 2: Load skill content
    skill_content = _read_skill_from_db(intent.matched_skill)
    if not skill_content:
        return AutoExecuteResponse(
            success=False,
            skill_name=intent.matched_skill,
            message=f"Could not read skill: {intent.matched_skill}",
        )

    # Step 3: Generate code
    generator = CodeGenerator(settings.anthropic_api_key, settings.claude_model)
    try:
        code = generator.generate_code(skill_content.content, request.query)
    except Exception as e:
        return AutoExecuteResponse(
            success=False,
            skill_name=intent.matched_skill,
            message=f"Code generation failed: {str(e)}",
        )

    # Step 4: Execute code
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    captured_output = StringIO()
    captured_error = StringIO()

    sys.stdout = captured_output
    sys.stderr = captured_error

    exec_error = None
    try:
        exec_globals = {"__builtins__": __builtins__, "__name__": "__main__"}
        exec(code, exec_globals)
    except Exception as e:
        exec_error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    output = captured_output.getvalue()
    stderr = captured_error.getvalue()
    if stderr:
        output += f"\n[stderr]\n{stderr}"

    if exec_error:
        return AutoExecuteResponse(
            success=False,
            skill_name=intent.matched_skill,
            generated_code=code,
            output=output,
            error=exec_error,
            message="Code execution failed",
        )

    return AutoExecuteResponse(
        success=True,
        skill_name=intent.matched_skill,
        generated_code=code,
        output=output,
        message="Execution completed",
    )
