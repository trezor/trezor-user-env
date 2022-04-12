#!/usr/bin/env python3

"""
HTTPServer used as proxy for trezord calls from the outside of docker container
This is workaround for original ip not beeing passed to the container:
    https://github.com/docker/for-mac/issues/180
Listening on port 21326 and routes requests to the trezord with changed Origin header
"""
import os
import time

from psutil import Popen

import helpers

IP = "0.0.0.0"
PORT = 21326
BRIDGE_PROXY = None
LOG_COLOR = "green"


def log(text: str, color: str = LOG_COLOR) -> None:
    helpers.log(f"BRIDGE PROXY: {text}", color)


def start() -> None:
    log(
        f"Starting at {IP}:{PORT}. All requests will be forwarded to Bridge.",
    )
    global BRIDGE_PROXY
    if BRIDGE_PROXY is not None:
        log("WARNING: Bridge proxy is already initialized, cannot be run again", "red")
        return

    file_path = os.path.join(os.path.dirname(__file__), "bridge_proxy_server.py")

    command = f"python {file_path}"

    BRIDGE_PROXY = Popen(command, shell=True)
    log(f"Bridge proxy spawned: {BRIDGE_PROXY}. CMD: {BRIDGE_PROXY.cmdline()}")

    # Verifying if the proxy is really running
    time.sleep(0.5)
    if not BRIDGE_PROXY.is_running():
        BRIDGE_PROXY = None
        raise RuntimeError("Bridge proxy is unable to run!")


def stop() -> None:
    log("Stopping")
    global BRIDGE_PROXY
    if BRIDGE_PROXY is None:
        log("WARNING: Attempting to stop a bridge proxy, but it is not running", "red")
    else:
        BRIDGE_PROXY.kill()
        log(f"Bridge proxy killed: {BRIDGE_PROXY}")
        BRIDGE_PROXY = None
