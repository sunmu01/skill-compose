"""
LLM-based intent parsing for natural language skill matching.
Uses Claude API to understand user intent and match to available skills.
"""
import json
import re
from typing import Optional

from anthropic import Anthropic

from app.models.skill import Skill, IntentMatchResult
from app.core.skill_manager import generate_skills_xml


INTENT_MATCHING_PROMPT = """You are an intelligent assistant that analyzes user requests and matches them to available skills.

## Available Skills

{skills_xml}

## User Request

{query}

## Additional Context

{context}

## Task

Analyze the user's request, understand their intent, and select the most appropriate skill from the available options.

Return your response as JSON:
{{
    "skill_name": "matched skill name, or null if no match",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation of why this skill was chosen",
    "alternatives": ["other potentially relevant skill names"]
}}

Guidelines:
1. Read each skill's description carefully
2. If the request mentions a file type (PDF, Excel, etc.), prioritize matching skills
3. Choose the most relevant skill even if not a perfect match
4. Set confidence based on match certainty
5. Return null for skill_name if truly no skill applies

Return JSON only:"""


class IntentParser:
    """Parse user intent using Claude LLM"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def match_skill(
        self,
        query: str,
        available_skills: list[Skill],
        context: Optional[str] = None,
    ) -> IntentMatchResult:
        """
        Match user query to the most appropriate skill.

        Args:
            query: Natural language user request
            available_skills: List of available skills
            context: Optional additional context

        Returns:
            IntentMatchResult with matched skill and confidence
        """
        if not available_skills:
            return IntentMatchResult(
                matched_skill=None,
                confidence=0.0,
                reasoning="No skills available",
            )

        # Build prompt
        skills_xml = generate_skills_xml(available_skills)
        prompt = INTENT_MATCHING_PROMPT.format(
            skills_xml=skills_xml,
            query=query,
            context=context or "None",
        )

        # Call Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse response
        return self._parse_response(response.content[0].text, available_skills)

    def _parse_response(
        self, response_text: str, available_skills: list[Skill]
    ) -> IntentMatchResult:
        """Parse LLM JSON response"""
        # Try to extract JSON
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return IntentMatchResult(
                    matched_skill=data.get("skill_name"),
                    confidence=float(data.get("confidence", 0.0)),
                    reasoning=data.get("reasoning", ""),
                    alternatives=data.get("alternatives", []),
                )
            except (json.JSONDecodeError, ValueError):
                pass

        # Fallback: simple text matching
        skill_names = [s.name for s in available_skills]
        for name in skill_names:
            if name.lower() in response_text.lower():
                return IntentMatchResult(
                    matched_skill=name,
                    confidence=0.5,
                    reasoning="Matched by text search",
                )

        return IntentMatchResult(
            matched_skill=None,
            confidence=0.0,
            reasoning="Could not parse LLM response",
        )
