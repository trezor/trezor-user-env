#!/usr/bin/env python3
"""Launcher for the MCP server subprocess.

The MCP server runs in its own uv-managed virtual environment (src/mcp/)
to avoid dependency conflicts with the main trezor-user-env environment
(tvl requires pydantic<2, mcp requires pydantic>=2).
"""

import subprocess
from pathlib import Path
from typing import Optional

import helpers

MCP_DIR = Path(__file__).parent / "mcp"
LOG_COLOR = "magenta"

_process: Optional[subprocess.Popen] = None


def log(text: str, color: str = LOG_COLOR) -> None:
    helpers.log(f"MCP: {text}", color)


def start() -> None:
    """Start the MCP server as a background subprocess via uv."""
    global _process
    log("Starting MCP server subprocess (uv run src/mcp/server.py)")
    _process = subprocess.Popen(
        ["uv", "run", "--project", str(MCP_DIR), "python", str(MCP_DIR / "server.py")],
        stdout=subprocess.DEVNULL,
        stderr=None,  # inherit stderr so MCP logs are visible
    )
    log("MCP server available at http://localhost:9003/sse")


def stop() -> None:
    global _process
    if _process is None:
        return
    log("Stopping MCP server subprocess")
    _process.terminate()
    try:
        _process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _process.kill()
        _process.wait()
    _process = None
