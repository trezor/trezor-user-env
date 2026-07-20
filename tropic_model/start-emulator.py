#!/usr/bin/env python3
"""Start Tropic Square emulator via model_server."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from tvl.server.server import main


def run() -> int:
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)
    config_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("config.yml")

    if not config_file.is_absolute():
        config_file = script_dir / config_file

    print("=========================================")
    print("Starting Tropic Square Emulator")
    print("=========================================")
    print()

    if not config_file.exists():
        print(f"ERROR: Config file not found: {config_file}")
        return 1

    sys.argv = ["model_server", "tcp", "-c", str(config_file)]

    try:
        result = main()
    except KeyboardInterrupt:
        return 0

    if result is None:
        return 0
    return int(result)


if __name__ == "__main__":
    raise SystemExit(run())
