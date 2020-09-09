#!/usr/bin/env python3
import http.client
import os
import signal
import time
from subprocess import PIPE, Popen

from trezorlib.transport.bridge import BridgeTransport

proc = None


def start(version):
    # normalize path to be relative to this folder, not pwd
    path = os.path.join(os.path.dirname(__file__), "../suite/bin")
    command = "nix-shell -p appimage-run --run \"appimage-run " + path + "/Trezor\ Beta\ Wallet-" + version + "-beta.AppImage\""
    Popen(command, shell=True, preexec_fn=os.setsid)
