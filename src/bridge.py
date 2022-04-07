#!/usr/bin/env python3
import os
import signal
import socket
import time
from subprocess import Popen

import binaries
import bridge_proxy
import helpers
from bridge_proxy import PORT as BRIDGE_PROXY_PORT

BRIDGE_PORT = 21325

# TODO: consider creating a class from this module to avoid these globals
proc = None
version_running = None

LOG_COLOR = "magenta"


def log(text: str, color: str = LOG_COLOR) -> None:
    helpers.log(f"BRIDGE: {text}", color)


def is_running() -> bool:
    return is_port_in_use(BRIDGE_PORT)


def get_status() -> dict:
    return {"is_running": is_running(), "version": version_running}


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
    global proc
    global version_running

    # When we are on ARM, include appropriate suffix for the version if not there
    if binaries.IS_ARM and not version.endswith(binaries.ARM_IDENTIFIER):
        log("ARM detected, adding suffix to bridge version", "yellow")
        version += binaries.ARM_IDENTIFIER

    # In case the bridge was killed outside of the stop() function
    #   (for example manually by the user), we need to reflect the situation
    #   not to still think the bridge is running
    if proc is not None and not is_running():
        log("Bridge was probably killed by user manually, resetting local state")
        stop(proxy=proxy)

    if proc is not None:
        log("WARNING: Bridge is already running, not spawning a new one", "red")
        return

    # normalize path to be relative to this folder, not pwd
    path = os.path.join(os.path.dirname(__file__), "../src/binaries/trezord-go/bin")

    command = f"{path}/trezord-go-v{version} -ed 21324:21325 -u=false"

    if output_to_logfile:
        # Conditionally redirecting the output to a logfile instead of terminal/stdout
        log_file = open(helpers.EMU_BRIDGE_LOG, "a")
        log(f"All the bridge debug output redirected to {helpers.EMU_BRIDGE_LOG}")
        proc = Popen(
            command, shell=True, preexec_fn=os.setsid, stdout=log_file, stderr=log_file
        )
    else:
        proc = Popen(command, shell=True, preexec_fn=os.setsid)

    version_running = version

    if proxy:
        bridge_proxy.start()

    time.sleep(0.5)
    check_bridge_and_proxy_status()


def stop(proxy: bool = True) -> None:
    log("Stopping")
    global proc
    global version_running

    if proc is None:
        log("WARNING: Attempting to stop a brige, but it is not running", "red")
    else:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc = None
        version_running = None

    if proxy:
        bridge_proxy.stop()

    time.sleep(0.5)
    check_bridge_and_proxy_status()
