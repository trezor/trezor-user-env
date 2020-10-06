#!/usr/bin/env bash
set -e

# TODO: fetch trezord-go from nix

nix-shell -p autoPatchelfHook --run "autoPatchelf trezord-*"

ls > download-index.txt
date > download-date.txt
