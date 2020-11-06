#!/usr/bin/env sh

nix-shell controller/shell.nix --run 'python --version'
nix-shell controller/shell.nix --run 'trezorctl --version'
nix-shell controller/shell.nix --run 'python controller/main.py'
