#!/usr/bin/env python3
from __future__ import annotations

import os
import signal
import socket
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
TROPIC_MODEL_PORT = 28992
TROPIC_MODEL_WAIT_TIME = 10
CONFIGS_DIR = TROPIC_MODEL_DIR / "configs"
CONFIG_CURRENT = CONFIGS_DIR / "current.yml"
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


def _parse_version(parts: list[str]) -> tuple[int, int, int] | None:
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return None
    return int(parts[0]), int(parts[1]), int(parts[2])


def _get_versioned_configs() -> list[tuple[tuple[int, int, int], Path]]:
    """Return configs named by version (e.g. 2_12_1.yml), sorted ascending."""
    configs = []
    for path in CONFIGS_DIR.glob("[0-9]*_[0-9]*_[0-9]*.yml"):
        parsed = _parse_version(path.stem.split("_"))
        if parsed is not None:
            configs.append((parsed, path))
    return sorted(configs)


def _get_config_for_version(version: str) -> Path:
    normalized = version.strip()

    # Emulator binaries may include a suffix like "-arm".
    if normalized.endswith("-arm"):
        normalized = normalized[: -len("-arm")]

    # "2-main" should always use the current config.
    if normalized == "2-main":
        return CONFIG_CURRENT

    # Tags may include a leading "v" (for example "v2.12.2").
    if normalized.startswith("v"):
        normalized = normalized[1:]

    parts = normalized.split(".")
    parsed = _parse_version(parts)
    if parsed is None:
        log(
            f"Unknown Tropic version format '{version}', defaulting to current config",
            "yellow",
        )
        return CONFIG_CURRENT

    versioned_configs = _get_versioned_configs()
    for config_version, config_path in versioned_configs:
        if config_version >= parsed:
            return config_path
    return CONFIG_CURRENT


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


def _wait_until_ready(timeout: float = TROPIC_MODEL_WAIT_TIME) -> None:
    """Wait for the Tropic model server to accept TCP connections."""
    assert TROPIC_SERVER is not None, "Tropic model not started"
    log(f"Waiting for Tropic model to come up on port {TROPIC_MODEL_PORT}...")
    start = time.monotonic()
    while True:
        try:
            with socket.create_connection(("127.0.0.1", TROPIC_MODEL_PORT), timeout=1):
                # Even if the model is listening for connections it sometimes
                # needs up to 2 seconds more before it correctly processes
                # requests.
                # TODO: https://github.com/trezor/trezor-firmware/pull/6128
                time.sleep(2)
                break
        except OSError:
            pass
        if TROPIC_SERVER.poll() is not None:
            raise RuntimeError("Tropic model process died")
        elapsed = time.monotonic() - start
        if elapsed >= timeout:
            raise TimeoutError("Can't connect to Tropic model")
        time.sleep(0.1)
    log(f"Tropic model ready after {time.monotonic() - start:.3f} seconds")


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
    command_list = ["uv", "run", "python", str(START_LAUNCHER), str(config_path)]

    # Spawn the process, optionally redirecting output to logfile
    if output_to_logfile:
        log_file = open(helpers.TROPIC_MODEL_LOG, "a")
        log(f"All tropic model output redirected to {helpers.TROPIC_MODEL_LOG}")
        try:
            TROPIC_SERVER = Popen(
                command_list,
                stdout=log_file,
                stderr=log_file,
                start_new_session=True,
            )
        finally:
            log_file.close()
    else:
        TROPIC_SERVER = Popen(command_list, start_new_session=True)

    log(f"Tropic server spawned: {TROPIC_SERVER}. CMD: {TROPIC_SERVER.cmdline()}")

    try:
        _wait_until_ready()
    except TimeoutError:
        log(
            f"Tropic model did not come up after {TROPIC_MODEL_WAIT_TIME} seconds",
            "red",
        )
        TROPIC_SERVER.kill()
        TROPIC_SERVER = None
        raise RuntimeError("Can't connect to Tropic model")

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
