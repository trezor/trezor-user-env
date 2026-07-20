#!/usr/bin/env python3
from __future__ import annotations

import os
import signal
import time
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from psutil import Popen

import helpers

if TYPE_CHECKING:
    from typing_extensions import TypedDict

    class StatusResponse(TypedDict):
        is_running: bool
        version: str | None


TROPIC_SERVER: Popen | None = None
VERSION_RUNNING: str | None = None

LOG_COLOR = "yellow"
ROOT_DIR = Path(__file__).resolve().parent.parent
TROPIC_MODEL_DIR = ROOT_DIR / "tropic_model"
START_LAUNCHER = TROPIC_MODEL_DIR / "start-emulator.py"
MODEL_STATE_FILES = [
    TROPIC_MODEL_DIR / ".model_config_save.yaml",
    TROPIC_MODEL_DIR / "model_config_save.yaml",
]
DEFAULT_TROPIC_VERSION = "2-main"
CONFIG_NEW = TROPIC_MODEL_DIR / "config.yml"
CONFIG_OLD = TROPIC_MODEL_DIR / "config_old.yml"
OLD_CONFIG_UNTIL_VERSION = (2, 12, 1)
StartOutcome = Literal["started", "already_running"]


def log(text: str, color: str = LOG_COLOR) -> None:
    helpers.log(f"TROPIC_MODEL: {text}", color)


def is_running() -> bool:
    """Check if tropic model server process is running"""
    if TROPIC_SERVER is None:
        return False
    return TROPIC_SERVER.is_running()


def get_status() -> "StatusResponse":
    """Return status dict with running state and version"""
    return {"is_running": is_running(), "version": VERSION_RUNNING}


def _get_config_for_version(version: str) -> Path:
    normalized = version.strip()

    # Emulator binaries may include a suffix like "-arm".
    if normalized.endswith("-arm"):
        normalized = normalized[: -len("-arm")]

    # "2-main" should always use the new config.
    if normalized == "2-main":
        return CONFIG_NEW

    # Tags may include a leading "v" (for example "v2.12.2").
    if normalized.startswith("v"):
        normalized = normalized[1:]

    parts = normalized.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        log(
            f"Unknown Tropic version format '{version}', defaulting to old config",
            "yellow",
        )
        return CONFIG_OLD

    parsed = tuple(int(part) for part in parts)
    return CONFIG_OLD if parsed <= OLD_CONFIG_UNTIL_VERSION else CONFIG_NEW


def needs_restart_for_version_change(
    current_version: str | None, requested_version: str
) -> bool:
    """Return True only when Tropic config file selection changes.

    This allows version switches within the same config bucket
    (e.g. 2.10.0 -> 2.9.6) without restarting model_server.
    """
    if current_version is None:
        return True
    return _get_config_for_version(current_version) != _get_config_for_version(
        requested_version
    )


def start(
    version: str = DEFAULT_TROPIC_VERSION, output_to_logfile: bool = True
) -> StartOutcome:
    """Start the Tropic Square model server"""
    log(f"Starting for firmware version {version}")
    global TROPIC_SERVER
    global VERSION_RUNNING

    # In case the server was killed outside of the stop() function
    #   (for example manually by the user), we need to reflect the situation
    if TROPIC_SERVER is not None and not is_running():
        log("Tropic server was probably killed manually, resetting local state")
        stop()

    if TROPIC_SERVER is not None:
        # Keep version intent in sync even when process is reused.
        VERSION_RUNNING = version
        log(
            "WARNING: Tropic model server is already running, not spawning a new one",
            "red",
        )
        return "already_running"

    # Verify the launcher exists
    if not START_LAUNCHER.exists():
        raise RuntimeError(f"Tropic model launcher does not exist at {START_LAUNCHER}")

    config_path = _get_config_for_version(version)
    if not config_path.exists():
        raise RuntimeError(f"Tropic config does not exist at {config_path}")

    # model_server persists mutable chip state on shutdown. Remove old state so
    # version switches start from the selected config file instead of residuals.
    for state_file in MODEL_STATE_FILES:
        if state_file.exists():
            state_file.unlink()
            log(f"Removed persisted model state: {state_file}")

    # Build command to run the Python launcher through uv.
    command_list = ["uv", "run", "python", str(START_LAUNCHER), config_path.name]

    # Spawn the process, optionally redirecting output to logfile
    if output_to_logfile:
        log_file = open(helpers.TROPIC_MODEL_LOG, "a")
        log(f"All tropic model output redirected to {helpers.TROPIC_MODEL_LOG}")
        TROPIC_SERVER = Popen(
            command_list,
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
        )
    else:
        TROPIC_SERVER = Popen(command_list, start_new_session=True)

    log(f"Tropic server spawned: {TROPIC_SERVER}. CMD: {TROPIC_SERVER.cmdline()}")

    # Verifying if the server is really running
    time.sleep(1.0)
    if not TROPIC_SERVER.is_running():
        TROPIC_SERVER = None
        raise RuntimeError("Tropic model server is unable to run!")

    VERSION_RUNNING = version
    log("Tropic model server started successfully")
    return "started"


def stop() -> None:
    """Stop the Tropic Square model server"""
    log("Stopping")
    global TROPIC_SERVER
    global VERSION_RUNNING

    if TROPIC_SERVER is None:
        log("WARNING: Attempting to stop tropic server, but it is not running", "red")
    else:
        try:
            # model_server writes final state on graceful SIGINT shutdown.
            # Signal the whole process group so the child process receives it too.
            os.killpg(TROPIC_SERVER.pid, signal.SIGINT)
            TROPIC_SERVER.wait(timeout=5)
        except Exception as e:
            log(f"Termination failed: {repr(e)}, killing process.", "yellow")
            try:
                os.killpg(TROPIC_SERVER.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            TROPIC_SERVER.wait()

        # Ensuring all child processes are cleaned up
        for child in TROPIC_SERVER.children(recursive=True):
            log(f"Killing child process {child.pid}")
            child.kill()
            child.wait()

        TROPIC_SERVER = None
        VERSION_RUNNING = None
        log("Tropic model server stopped")
