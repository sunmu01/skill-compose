"""Terminal API - Interactive PTY terminal via WebSocket."""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.terminal.pty_manager import pty_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/terminal", tags=["terminal"])


@router.websocket("/ws")
async def terminal_ws(websocket: WebSocket, cols: int = 80, rows: int = 24):
    """WebSocket endpoint for interactive PTY terminal."""
    await websocket.accept()

    session = await pty_manager.get_or_create(cols, rows)
    loop = asyncio.get_event_loop()
    output_queue: asyncio.Queue[bytes] = asyncio.Queue()
    stop_event = asyncio.Event()

    def _on_pty_readable():
        data = session.read()
        if data:
            output_queue.put_nowait(data)
        elif not session.is_alive():
            stop_event.set()

    # Register PTY fd reader
    loop.add_reader(session.master_fd, _on_pty_readable)

    async def send_output():
        """Forward PTY output to WebSocket."""
        try:
            while not stop_event.is_set():
                try:
                    data = await asyncio.wait_for(output_queue.get(), timeout=0.5)
                    await websocket.send_json({"type": "output", "data": data.decode("utf-8", errors="replace")})
                except asyncio.TimeoutError:
                    # Check if shell is still alive
                    if not session.is_alive():
                        stop_event.set()
                        break
        except (WebSocketDisconnect, RuntimeError):
            pass

    async def recv_input():
        """Forward WebSocket input to PTY."""
        try:
            while not stop_event.is_set():
                raw = await websocket.receive_text()
                msg = json.loads(raw)
                msg_type = msg.get("type")
                if msg_type == "input":
                    session.write(msg["data"])
                elif msg_type == "resize":
                    session.resize(msg["cols"], msg["rows"])
        except (WebSocketDisconnect, RuntimeError):
            pass

    try:
        done, pending = await asyncio.wait(
            [asyncio.create_task(send_output()), asyncio.create_task(recv_input())],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    finally:
        # Remove PTY fd reader (only if fd still valid)
        if session.master_fd is not None:
            try:
                loop.remove_reader(session.master_fd)
            except Exception:
                pass

        # If shell exited, notify client and clean up
        if not session.is_alive():
            exit_code = await pty_manager.terminate()
            try:
                await websocket.send_json({"type": "exit", "code": exit_code or 0})
            except Exception:
                pass
