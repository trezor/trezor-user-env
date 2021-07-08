#!/usr/bin/env python3
import os
import signal
from subprocess import Popen

import requests
from requests.exceptions import ConnectionError

import bridge_proxy
import helpers

# TODO: consider creating a class from this module to avoid these globals
proc = None
version_running = None

LOG_COLOR = "magenta"


def log(text: str, color: str = LOG_COLOR) -> None:
    helpers.log(f"BRIDGE: {text}", color)


def is_running() -> bool:
    try:
        r = requests.get("http://0.0.0.0:21325/status/")
        return r.status_code == 200
    except ConnectionError:
        return False
    except Exception as e:
        log(
            f"Unexpected error when checking the bridge: {type(e).__name__} - {e}",
            "red",
        )
        return False


def get_status() -> dict:
    return {"is_running": is_running(), "version": version_running}


def start(version: str, proxy: bool = False) -> None:
    global proc
    global version_running

    # In case the bridge was killed outside of the stop() function
    #   (for example manually by the user), we need to reflect the situation
    #   not to still think the bridge is running
    if proc is not None and not is_running():
        log("Bridge was probably killed by user manually, resetting local state")
        stop(cleanup=True, proxy=proxy)

    if proc is not None:
        raise RuntimeError("Bridge is already running, not spawning a new one")

    # normalize path to be relative to this folder, not pwd
    path = os.path.join(os.path.dirname(__file__), "../src/binaries/trezord-go/bin")

    command = f"{path}/trezord-go-v{version} -ed 21324:21325 -u=false"

    proc = Popen(command, shell=True, preexec_fn=os.setsid)

    version_running = version

    if proxy:
        bridge_proxy.start()


def stop(cleanup: bool = False, proxy: bool = True) -> None:
    log("Stopping")
    global proc
    global version_running

    # In case of cleanup it may happen that the bridge will not run - and it is fine
    if proc is None:
        if not cleanup:
            raise RuntimeError("Bridge is not running, cannot be stopped")
    else:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc = None
        version_running = None

    if proxy:
        bridge_proxy.stop(cleanup=cleanup)
