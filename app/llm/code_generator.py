"""
LLM-based code generator.
Generates executable Python code based on skill content and user request.
"""
from anthropic import Anthropic


CODE_GENERATION_PROMPT = """You are a code generator. Based on the skill documentation and user request, generate executable Python code.

## Skill Documentation

{skill_content}

## User Request

{query}

## Requirements

1. Generate ONLY executable Python code
2. Use the APIs and patterns shown in the skill documentation
3. Print the final result clearly
4. Store the main result in a variable called `result`
5. Handle any necessary imports
6. If the task requires external tools (like XTB), simulate or mock the result if the tool is not available

## Important

- Output ONLY the Python code, no explanations
- The code should be ready to execute
- Use print() to show intermediate steps and final results

Generate the Python code:
```python
"""


class CodeGenerator:
    """Generate executable code using LLM"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def generate_code(self, skill_content: str, query: str) -> str:
        """
        Generate executable Python code based on skill and user request.

        Args:
            skill_content: The SKILL.md content
            query: User's natural language request

        Returns:
            Generated Python code
        """
        prompt = CODE_GENERATION_PROMPT.format(
            skill_content=skill_content,
            query=query,
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract code from response
        code = response.content[0].text

        # Clean up code (remove markdown code blocks if present)
        if code.startswith("```python"):
            code = code[9:]
        if code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]

        return code.strip()
