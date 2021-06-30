#!/usr/bin/env python3
import http.client
import os
import signal
from subprocess import PIPE, Popen

proc = None


def is_running() -> bool:
    try:
        conn = http.client.HTTPConnection("0.0.0.0", 21325)
        conn.request("GET", "/status/")
        r = conn.getresponse()
        if r.status == 200:
            return True
        return False
    except:
        return False


def start(version: str) -> None:
    global proc
    if proc is not None:
        raise RuntimeError("Bridge is already running, not spawning a new one")

    # normalize path to be relative to this folder, not pwd
    path = os.path.join(os.path.dirname(__file__), "../trezord-go/bin")

    command = f"{path}/trezord-go-v{version} -ed 21324:21325 -u=false"
    print("command", command)

    proc = Popen(command, shell=True, preexec_fn=os.setsid)


def stop(cleanup: bool = False) -> None:
    global proc
    # In case of cleanup it may happen that the bridge will not run - and it is fine
    if proc is None:
        if not cleanup:
            raise RuntimeError("Bridge is not running, cannot be stopped")
    else:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc = None
