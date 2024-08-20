#!/usr/bin/env python3
from __future__ import annotations

import os
import socket
import time
from shlex import split
from typing import TYPE_CHECKING

from psutil import Popen

import binaries
import bridge_proxy
import helpers
from bridge_proxy import PORT as BRIDGE_PROXY_PORT

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


def check_bridge_and_proxy_status() -> None:
    """Reporting the status of bridge and proxy, for debugging purposes"""
    log(f"Is bridge running - {is_port_in_use(BRIDGE_PORT)}")
    log(f"Is bridge proxy running - {is_port_in_use(BRIDGE_PROXY_PORT)}")


def start(version: str, proxy: bool = False, output_to_logfile: bool = True) -> None:
    log("Starting")
    global BRIDGE
    global VERSION_RUNNING

    # When we are on ARM, include appropriate suffix for the version if not there
    if binaries.IS_ARM and not version.endswith(binaries.ARM_IDENTIFIER):
        log("ARM detected, adding suffix to bridge version", "yellow")
        version += binaries.ARM_IDENTIFIER

    # In case the bridge was killed outside of the stop() function
    #   (for example manually by the user), we need to reflect the situation
    #   not to still think the bridge is running
    if BRIDGE is not None and not is_running():
        log("Bridge was probably killed by user manually, resetting local state")
        stop(proxy=proxy)

    if BRIDGE is not None:
        log("WARNING: Bridge is already running, not spawning a new one", "red")
        return

    # normalize path to be relative to this folder, not pwd
    path = os.path.join(os.path.dirname(__file__), "../src/binaries/trezord-go/bin")

    bridge_location = f"{path}/trezord-go-v{version}"
    if not os.path.isfile(bridge_location):
        raise RuntimeError(
            f"Bridge does not exist for version {version} under {bridge_location}"
        )

    # In case user wants to use a physical device, not adding any arguments
    # to the bridge. These arguments make the bridge optimized for emulators.
    command = (
        bridge_location
        if helpers.physical_trezor()
        else f"{bridge_location} -ed 21324:21325 -u=false"
    )
    # Conditionally redirecting the output to a logfile instead of terminal/stdout
    command_list = split(command)
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

    if proxy:
        bridge_proxy.start()

    time.sleep(0.5)
    check_bridge_and_proxy_status()


def stop(proxy: bool = True) -> None:
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
            log(f"Termination failed: {e}, killing process.", "yellow")
            BRIDGE.kill()
            BRIDGE.wait()

        # Ensuring all child processes are cleaned up
        for child in BRIDGE.children(recursive=True):
            log(f"Killing child process {child.pid}")
            child.kill()
            child.wait()

        BRIDGE = None
        VERSION_RUNNING = None

    if proxy:
        bridge_proxy.stop()

    time.sleep(0.5)
    check_bridge_and_proxy_status()
