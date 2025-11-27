#!/usr/bin/env python3
from __future__ import annotations

import shutil
import socket
import time
from shlex import split
from typing import TYPE_CHECKING

from psutil import Popen

import binaries
import helpers

if TYPE_CHECKING:
    from typing_extensions import TypedDict

    class StatusResponse(TypedDict):
        is_running: bool
        version: str | None


BRIDGE_PORT = 21325

# TODO: consider creating a class from this module to avoid these globals
BRIDGE: Popen | None = None
VERSION_RUNNING: str | None = None

LOG_COLOR = "magenta"


def log(text: str, color: str = LOG_COLOR) -> None:
    helpers.log(f"BRIDGE: {text}", color)


def is_running() -> bool:
    return is_port_in_use(BRIDGE_PORT)


def is_node_bridge_running() -> bool:
    if VERSION_RUNNING is None:
        return False
    return "node" in VERSION_RUNNING


def get_status() -> "StatusResponse":
    if helpers.physical_trezor():
        return {
            "is_running": is_running(),
            "version": f"{VERSION_RUNNING} - PHYSICAL_TREZOR",
        }
    else:
        return {"is_running": is_running(), "version": VERSION_RUNNING}


def is_port_in_use(port: int) -> bool:
    """Checks if a certain port is listening on localhost"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("0.0.0.0", port)) == 0


def check_bridge_status() -> None:
    """Reporting the status of bridge, for debugging purposes"""
    log(f"Is bridge running - {is_port_in_use(BRIDGE_PORT)}")


def start(version: str, output_to_logfile: bool = True) -> None:
    log("Starting")
    global BRIDGE
    global VERSION_RUNNING

    # When we are on ARM, include appropriate suffix for the version if not there
    # Not doing this for node bridge
    if (
        binaries.IS_ARM
        and not version.endswith(binaries.ARM_IDENTIFIER)
        and "node" not in version
    ):
        log("ARM detected, adding suffix to bridge version", "yellow")
        version += binaries.ARM_IDENTIFIER

    # In case the bridge was killed outside of the stop() function
    #   (for example manually by the user), we need to reflect the situation
    #   not to still think the bridge is running
    if BRIDGE is not None and not is_running():
        log("Bridge was probably killed by user manually, resetting local state")
        stop()

    if BRIDGE is not None:
        log("WARNING: Bridge is already running, not spawning a new one", "red")
        return

    def get_command_list() -> list[str]:
        # Special handling of node-js bridge (experimental)
        if version == binaries.NODE_BRIDGE_ID:
            path = binaries.NODE_BRIDGE_BIN_JS
            log(f"Using local bridge from {path}")
            if not path.exists():
                raise RuntimeError(f"Node bridge does not exist under {path}")
            return ["node", str(path), "udp"]
        elif version == binaries.LOCAL_SUITE_NODE_BRIDGE_ID:
            path = binaries.LOCAL_SUITE_NODE_BRIDGE_BIN_JS
            if not path.exists():
                raise RuntimeError(
                    f"Local Suite node bridge does not exist under {path}"
                )
            log(f"Using local Suite bridge from {path}")
            transformed_path = binaries.NODE_BRIDGE_DIR / "bin_suite.js"
            shutil.copyfile(path, transformed_path)
            proc = Popen(
                [
                    f"{binaries.NODE_BRIDGE_DIR}/modify_node_bin_js.sh",
                    str(transformed_path),
                ]
            )
            proc.wait()
            if proc.returncode != 0:
                raise RuntimeError(
                    f"Failed to modify the node bridge binary: {proc.returncode}"
                )
            return ["node", str(transformed_path), "udp"]
        else:
            bridge_location = binaries.BRIDGE_BIN_DIR / f"trezord-go-v{version}"
            if not bridge_location.exists():
                raise RuntimeError(
                    f"Bridge does not exist for version {version} under {bridge_location}"
                )

            # In case user wants to use a physical device, not adding any arguments
            # to the bridge. These arguments make the bridge optimized for emulators.
            command = (
                str(bridge_location)
                if helpers.physical_trezor()
                else f"{bridge_location} -ed 21324:21325 -u=false"
            )
            # Conditionally redirecting the output to a logfile instead of terminal/stdout
            return split(command)

    command_list = get_command_list()

    if output_to_logfile:
        log_file = open(helpers.EMU_BRIDGE_LOG, "a")
        log(f"All the bridge debug output redirected to {helpers.EMU_BRIDGE_LOG}")
        BRIDGE = Popen(command_list, stdout=log_file, stderr=log_file)
    else:
        BRIDGE = Popen(command_list)

    log(f"Bridge spawned: {BRIDGE}. CMD: {BRIDGE.cmdline()}")

    # Verifying if the bridge is really running
    time.sleep(0.5)
    if not BRIDGE.is_running():
        BRIDGE = None
        raise RuntimeError(f"Bridge version {version} is unable to run!")

    VERSION_RUNNING = version

    time.sleep(0.5)
    check_bridge_status()


def stop() -> None:
    log("Stopping")
    global BRIDGE
    global VERSION_RUNNING

    if BRIDGE is None:
        log("WARNING: Attempting to stop a bridge, but it is not running", "red")
    else:
        try:
            BRIDGE.terminate()
            BRIDGE.wait(timeout=5)
        except Exception as e:
            log(f"Termination failed: {repr(e)}, killing process.", "yellow")
            BRIDGE.kill()
            BRIDGE.wait()

        # Ensuring all child processes are cleaned up
        for child in BRIDGE.children(recursive=True):
            log(f"Killing child process {child.pid}")
            child.kill()
            child.wait()

        BRIDGE = None
        VERSION_RUNNING = None

    time.sleep(0.5)
    check_bridge_status()
