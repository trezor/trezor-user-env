#!/usr/bin/env python3
import os
from subprocess import Popen


def start(version: str) -> None:
    # normalize path to be relative to this folder, not pwd
    path = os.path.join(os.path.dirname(__file__), "../suite/bin")
    command = (
        'nix-shell -p appimage-run --run "appimage-run '
        + path
        + "/Trezor\ Beta\ Wallet-"
        + version
        + '-beta.AppImage"'
    )
    Popen(command, shell=True, preexec_fn=os.setsid)
