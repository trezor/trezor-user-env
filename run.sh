#!/usr/bin/env sh

DIR=$(dirname "$0")

nix-shell "$DIR/controller/shell.nix" --run "python --version"
nix-shell "$DIR/controller/shell.nix" --run "trezorctl --version"

echo "Starting trezor-user-env server"
nix-shell "$DIR/controller/shell.nix" --run "python $DIR/controller/main.py"
