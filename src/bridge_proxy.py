#!/usr/bin/env python3

"""
HTTPServer used as proxy for trezord calls from the outside of docker container
This is workaround for original ip not beeing passed to the container:
    https://github.com/docker/for-mac/issues/180
Listening on port 21326 and routes requests to the trezord with changed Origin header
"""
import os
import signal
from subprocess import Popen

import helpers

IP = "0.0.0.0"
PORT = 21326
SERVER = None
LOG_COLOR = "green"


def log(text: str, color: str = LOG_COLOR) -> None:
    helpers.log(f"BRIDGE PROXY: {text}", color)


def start() -> None:
    log(
        f"Starting at {IP}:{PORT}. All requests will be forwarded to Bridge.",
    )
    global SERVER
    if SERVER is not None:
        log("WARNING: Bridge proxy is already initialized, cannot be run again", "red")
        return

    file_path = os.path.join(os.path.dirname(__file__), "bridge_proxy_server.py")

    command = f"python {file_path}"

    SERVER = Popen(command, shell=True, preexec_fn=os.setsid)


def stop() -> None:
    log("Stopping")
    global SERVER
    if SERVER is None:
        log("WARNING: Attempting to stop a bridge proxy, but it is not running", "red")
    else:
        os.killpg(os.getpgid(SERVER.pid), signal.SIGTERM)
        SERVER = None
