#!/usr/bin/env sh

DIR=$(dirname "$0")
cd "${DIR}"

echo "Starting trezor-user-env server"
nix-shell --run "uv run python src/main.py"
