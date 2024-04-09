#!/usr/bin/env sh

DIR=$(dirname "$0")
cd "${DIR}"

SYSTEM_ARCH=$(uname -m)
if [[ $SYSTEM_ARCH == aarch64* ]]; then
    # Patch trezord after the container starts to prevent flaky behavior with arm version.
    nix-shell -p bash --run "cd ./src/binaries/trezord-go/bin/ && ./download.sh"
fi

echo "Starting trezor-user-env server"
nix-shell --run "poetry run python src/main.py"
