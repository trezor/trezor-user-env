"""VNC server management for the emulator display.

Provides a virtual display (Xvfb) with VNC access via x11vnc and
a browser-based viewer via websockify + noVNC. The VNC output
streams only the emulator window so only the device screen is visible.
"""

from __future__ import annotations

import os
import subprocess
import time
from subprocess import PIPE

from psutil import Popen

import helpers

DISPLAY = ":42"
NOVNC_URL = "http://localhost:6080/vnc_embed.html"

_xvfb_process: Popen | None = None
_x11vnc_process: Popen | None = None
_websockify_process: Popen | None = None


def _log(text: str) -> None:
    helpers.log(f"VNC: {text}", "magenta")


def _kill_process(proc: Popen | None, name: str) -> None:
    """Terminate a process and wait for it to exit."""
    if proc is None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()
        proc.wait(timeout=2)
    _log(f"{name} stopped")


def _find_window_id() -> str | None:
    """Find the emulator window on the VNC display and return its X window ID."""
    env = {**os.environ, "DISPLAY": DISPLAY}

    for _ in range(10):
        try:
            result = subprocess.run(
                ["xdotool", "search", "--onlyvisible", "--name", ""],
                capture_output=True,
                text=True,
                timeout=2,
                env=env,
            )
            window_ids = [
                wid for wid in result.stdout.strip().split("\n") if wid.strip()
            ]
            if not window_ids:
                time.sleep(0.5)
                continue

            window_id = window_ids[-1]
            _log(f"Emulator window detected: {window_id}")
            return window_id
        except Exception as e:
            _log(f"Window detection failed: {e}")
        time.sleep(0.5)

    return None


def start_display() -> None:
    """Start Xvfb and websockify. Restarts cleanly if already running."""
    if stop():
        time.sleep(1)  # Let TCP ports (6080, 5900) fully release

    global _xvfb_process, _websockify_process

    _log("Starting Xvfb virtual display...")
    _xvfb_process = Popen(
        ["Xvfb", DISPLAY, "-screen", "0", "1024x768x24"],
        stdout=PIPE,
        stderr=PIPE,
    )
    time.sleep(0.5)

    _log("Starting websockify + noVNC web viewer...")
    _websockify_process = Popen(
        ["websockify", "--web=/usr/share/novnc", "6080", "localhost:5900"],
        stdout=PIPE,
        stderr=PIPE,
    )
    time.sleep(0.5)


def start_capture() -> None:
    """Start x11vnc, streaming only the emulator window by its ID."""
    global _x11vnc_process

    if _x11vnc_process is not None:
        _kill_process(_x11vnc_process, "x11vnc")
        _x11vnc_process = None

    window_id = _find_window_id()

    cmd = ["x11vnc", "-display", DISPLAY, "-forever", "-nopw", "-shared"]
    if window_id:
        cmd += ["-id", window_id]
    else:
        _log("Could not detect emulator window, serving full display")

    _x11vnc_process = Popen(cmd, stdout=PIPE, stderr=PIPE)
    time.sleep(0.5)
    _log(f"noVNC viewer available at {NOVNC_URL}")


def stop() -> bool:
    """Stop all VNC processes (websockify, x11vnc, Xvfb).

    Returns True if any process was actually killed.
    """
    global _xvfb_process, _x11vnc_process, _websockify_process

    was_running = any(
        p is not None for p in (_websockify_process, _x11vnc_process, _xvfb_process)
    )

    _kill_process(_websockify_process, "websockify")
    _websockify_process = None
    _kill_process(_x11vnc_process, "x11vnc")
    _x11vnc_process = None
    _kill_process(_xvfb_process, "Xvfb")
    _xvfb_process = None

    return was_running


def setup_env() -> None:
    """Set environment variables for VNC display mode."""
    os.environ["DISPLAY"] = DISPLAY
    os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
    _log(f"Using VNC display {DISPLAY}")
