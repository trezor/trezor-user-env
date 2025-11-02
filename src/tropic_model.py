#!/usr/bin/env python3
from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

from psutil import Popen

import helpers

if TYPE_CHECKING:
    from typing_extensions import TypedDict

    class StatusResponse(TypedDict):
        is_running: bool
        version: str | None


CURRENT_TVL_VERSION = "tvl-2.3"

TROPIC_SERVER: Popen | None = None
VERSION_RUNNING: str | None = None

LOG_COLOR = "yellow"
ROOT_DIR = Path(__file__).resolve().parent.parent
TROPIC_MODEL_DIR = ROOT_DIR / "tropic_model"
START_SCRIPT = TROPIC_MODEL_DIR / "start-emulator.sh"


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


def start(output_to_logfile: bool = True) -> None:
    """Start the Tropic Square model server"""
    log("Starting")
    global TROPIC_SERVER
    global VERSION_RUNNING

    # In case the server was killed outside of the stop() function
    #   (for example manually by the user), we need to reflect the situation
    if TROPIC_SERVER is not None and not is_running():
        log("Tropic server was probably killed manually, resetting local state")
        stop()

    if TROPIC_SERVER is not None:
        log(
            "WARNING: Tropic model server is already running, not spawning a new one",
            "red",
        )
        return

    # Verify the start script exists
    if not START_SCRIPT.exists():
        raise RuntimeError(
            f"Tropic model start script does not exist at {START_SCRIPT}"
        )

    # Build command to run the start script
    command_list = ["bash", str(START_SCRIPT)]

    # Spawn the process, optionally redirecting output to logfile
    if output_to_logfile:
        log_file = open(helpers.TROPIC_MODEL_LOG, "a")
        log(f"All tropic model output redirected to {helpers.TROPIC_MODEL_LOG}")
        TROPIC_SERVER = Popen(command_list, stdout=log_file, stderr=log_file)
    else:
        TROPIC_SERVER = Popen(command_list)

    log(f"Tropic server spawned: {TROPIC_SERVER}. CMD: {TROPIC_SERVER.cmdline()}")

    # Verifying if the server is really running
    time.sleep(1.0)
    if not TROPIC_SERVER.is_running():
        TROPIC_SERVER = None
        raise RuntimeError("Tropic model server is unable to run!")

    VERSION_RUNNING = CURRENT_TVL_VERSION
    log("Tropic model server started successfully")


def stop() -> None:
    """Stop the Tropic Square model server"""
    log("Stopping")
    global TROPIC_SERVER
    global VERSION_RUNNING

    if TROPIC_SERVER is None:
        log("WARNING: Attempting to stop tropic server, but it is not running", "red")
    else:
        try:
            TROPIC_SERVER.terminate()
            TROPIC_SERVER.wait(timeout=5)
        except Exception as e:
            log(f"Termination failed: {repr(e)}, killing process.", "yellow")
            TROPIC_SERVER.kill()
            TROPIC_SERVER.wait()

        # Ensuring all child processes are cleaned up
        for child in TROPIC_SERVER.children(recursive=True):
            log(f"Killing child process {child.pid}")
            child.kill()
            child.wait()

        TROPIC_SERVER = None
        VERSION_RUNNING = None
        log("Tropic model server stopped")
