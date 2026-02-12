"""PTY session manager for interactive terminal WebSocket."""

import asyncio
import fcntl
import logging
import os
import pty
import signal
import struct
import termios

logger = logging.getLogger(__name__)


class PTYSession:
    """Wraps a PTY-backed bash process."""

    def __init__(self, cols: int = 80, rows: int = 24):
        self.cols = cols
        self.rows = rows
        self.master_fd: int | None = None
        self.child_pid: int | None = None

    def start(self) -> None:
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        env["COLORTERM"] = "truecolor"

        pid, fd = pty.fork()
        if pid == 0:
            # Child process
            os.chdir(os.environ.get("PROJECT_ROOT", "/app"))
            os.execvpe("/bin/bash", ["/bin/bash", "--login"], env)
        else:
            # Parent process
            self.master_fd = fd
            self.child_pid = pid
            # Set non-blocking
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            # Set initial size
            self._set_winsize(self.cols, self.rows)
            logger.info("PTY session started: pid=%d, fd=%d", pid, fd)

    def _set_winsize(self, cols: int, rows: int) -> None:
        if self.master_fd is not None:
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)

    def resize(self, cols: int, rows: int) -> None:
        self.cols = cols
        self.rows = rows
        self._set_winsize(cols, rows)

    def write(self, data: str) -> None:
        if self.master_fd is not None:
            os.write(self.master_fd, data.encode())

    def read(self, size: int = 65536) -> bytes | None:
        if self.master_fd is None:
            return None
        try:
            return os.read(self.master_fd, size)
        except OSError:
            return None

    def is_alive(self) -> bool:
        if self.child_pid is None:
            return False
        try:
            pid, status = os.waitpid(self.child_pid, os.WNOHANG)
            return pid == 0
        except ChildProcessError:
            return False

    def terminate(self) -> int | None:
        if self.child_pid is None:
            return None
        try:
            os.kill(self.child_pid, signal.SIGTERM)
            _, status = os.waitpid(self.child_pid, 0)
            exit_code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
        except (ChildProcessError, ProcessLookupError):
            exit_code = -1
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
        logger.info("PTY session terminated: pid=%d, exit=%s", self.child_pid, exit_code)
        self.master_fd = None
        self.child_pid = None
        return exit_code


class PTYManager:
    """Singleton manager for a single PTY session."""

    def __init__(self) -> None:
        self._session: PTYSession | None = None
        self._lock = asyncio.Lock()

    async def get_or_create(self, cols: int = 80, rows: int = 24) -> PTYSession:
        async with self._lock:
            if self._session is not None and self._session.is_alive():
                return self._session
            # Clean up dead session
            if self._session is not None:
                self._session.terminate()
            session = PTYSession(cols, rows)
            session.start()
            self._session = session
            return session

    async def terminate(self) -> int | None:
        async with self._lock:
            if self._session is None:
                return None
            exit_code = self._session.terminate()
            self._session = None
            return exit_code


pty_manager = PTYManager()
