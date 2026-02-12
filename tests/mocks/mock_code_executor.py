"""
Mock code executor for testing without Jupyter kernel.
"""
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class MockExecutionResult:
    success: bool = True
    output: str = ""
    error: str = ""
    return_value: str = None


class MockCodeExecutor:
    """Mock code executor that records calls and returns preset results."""

    def __init__(self, default_output: str = "mock output"):
        self.calls: List[Tuple[str, str]] = []  # (method, input)
        self.default_output = default_output
        self._results = {}

    def set_result(self, code_or_command: str, result: MockExecutionResult):
        """Set a specific result for a specific input."""
        self._results[code_or_command] = result

    def execute(self, code: str) -> MockExecutionResult:
        """Mock execute code."""
        self.calls.append(("execute", code))
        if code in self._results:
            return self._results[code]
        return MockExecutionResult(success=True, output=self.default_output)

    def execute_command(self, command: str) -> MockExecutionResult:
        """Mock execute command."""
        self.calls.append(("execute_command", command))
        if command in self._results:
            return self._results[command]
        return MockExecutionResult(success=True, output=self.default_output)

    def reset(self):
        """Mock kernel reset."""
        self.calls.append(("reset", ""))

    def shutdown(self):
        """Mock shutdown."""
        self.calls.append(("shutdown", ""))
