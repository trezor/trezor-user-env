#!/usr/bin/env bash

set -euo pipefail

DIR=$(dirname "$0")
cd "${DIR}"

SYSTEM_ARCH=$(uname -m)

echo "Preparing firmware emulator binaries"
RELEASE_MINOR_LIMIT=5 nix-shell --run "uv run python src/binaries/firmware/bin/download.py releases"
nix-shell --run "uv run python src/binaries/firmware/bin/download.py nightly"

if [[ $SYSTEM_ARCH == aarch64* ]]; then
    # Patch trezord after the container starts to prevent flaky behavior with arm version.
    nix-shell --run "cd ./src/binaries/trezord-go/bin/ && ./download.sh"
fi

echo "Preparing node bridge"
nix-shell --run "./src/binaries/node-bridge/download.sh"

echo "Patching firmware emulator binaries for Nix"
nix-shell --run "./src/binaries/firmware/bin/patch-bin.sh ./src/binaries/firmware/bin"

echo "Starting trezor-user-env server"
nix-shell --run "PYTHONUNBUFFERED=1 uv run python src/main.py"
