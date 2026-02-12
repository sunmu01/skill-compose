"""
IPython Kernel wrapper for persistent code execution (executor container version).

Standalone module that does not depend on app.tools — used inside Docker
executor containers.
"""
import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


@dataclass
class ExecutionResult:
    """Result of kernel code execution."""
    success: bool
    output: str
    error: Optional[str] = None
    return_value: Optional[str] = None


class IPythonKernel:
    """
    Persistent IPython kernel backed by jupyter_client.

    Variables, imports, and state persist across execute() calls until
    shutdown() is called.
    """

    def __init__(
        self,
        startup_timeout: int = 30,
        execute_timeout: int = 300,
        max_output_chars: int = 100000,
        working_dir: Optional[str] = None,
        env: Optional[dict] = None,
    ):
        self._startup_timeout = startup_timeout
        self._execute_timeout = execute_timeout
        self._max_output_chars = max_output_chars
        self._working_dir = working_dir
        self._env = env
        self._km = None
        self._kc = None

    def start(self) -> None:
        """Start the IPython kernel process."""
        from jupyter_client import KernelManager

        self._km = KernelManager(kernel_name="python3")
        if self._working_dir:
            self._km.cwd = self._working_dir
        kw = {}
        if self._env is not None:
            kw["env"] = self._env
        self._km.start_kernel(**kw)
        self._kc = self._km.client()
        self._kc.start_channels()
        try:
            self._kc.wait_for_ready(timeout=self._startup_timeout)
        except Exception:
            self.shutdown()
            raise
        # Force kernel cwd — KernelManager.cwd may not work in all environments
        if self._working_dir:
            self.execute(f"import os; os.chdir({self._working_dir!r})")

    @property
    def is_alive(self) -> bool:
        return self._km is not None and self._km.is_alive()

    def execute(self, code: str) -> ExecutionResult:
        """Execute code in the persistent kernel."""
        if not self.is_alive:
            return ExecutionResult(
                success=False,
                output="",
                error="Kernel is not running",
            )

        msg_id = self._kc.execute(code)

        stdout_parts = []
        stderr_parts = []
        error_parts = []
        display_parts = []

        while True:
            try:
                msg = self._kc.get_iopub_msg(timeout=self._execute_timeout)
            except Exception:
                return ExecutionResult(
                    success=False,
                    output="".join(stdout_parts),
                    error=f"Execution timed out after {self._execute_timeout} seconds",
                )

            if msg.get("parent_header", {}).get("msg_id") != msg_id:
                continue

            msg_type = msg.get("msg_type", "")
            content = msg.get("content", {})

            if msg_type == "stream":
                name = content.get("name", "")
                text = content.get("text", "")
                if name == "stdout":
                    stdout_parts.append(text)
                elif name == "stderr":
                    stderr_parts.append(text)

            elif msg_type == "execute_result":
                data = content.get("data", {})
                text = data.get("text/plain", "")
                if text:
                    display_parts.append(text)

            elif msg_type == "display_data":
                data = content.get("data", {})
                text = data.get("text/plain", "")
                if text:
                    display_parts.append(text)

            elif msg_type == "error":
                traceback = content.get("traceback", [])
                clean_tb = [_ANSI_RE.sub("", line) for line in traceback]
                error_parts.append("\n".join(clean_tb))

            elif msg_type == "status":
                if content.get("execution_state") == "idle":
                    break

        output_parts = []
        if stdout_parts:
            output_parts.append("".join(stdout_parts))
        if display_parts:
            output_parts.append("\n".join(display_parts))
        if stderr_parts:
            output_parts.append("".join(stderr_parts))

        output = "\n".join(output_parts).strip() if output_parts else ""

        if len(output) > self._max_output_chars:
            output = output[: self._max_output_chars] + "\n... [OUTPUT TRUNCATED]"

        has_error = bool(error_parts)
        error_text = "\n".join(error_parts) if has_error else None
        if error_text and len(error_text) > self._max_output_chars:
            error_text = error_text[: self._max_output_chars] + "\n... [ERROR TRUNCATED]"

        if has_error:
            full_output = (output + "\n" + error_text).strip() if output else error_text
        else:
            full_output = output

        return ExecutionResult(
            success=not has_error,
            output=full_output,
            error=error_text,
        )

    def shutdown(self) -> None:
        """Shutdown kernel channels and process."""
        try:
            if self._kc is not None:
                self._kc.stop_channels()
                self._kc = None
        except Exception:
            pass
        try:
            if self._km is not None:
                self._km.shutdown_kernel(now=True)
                self._km = None
        except Exception:
            pass
