#!/usr/bin/env bash

FILE_DIR="$(dirname "${0}")"
cd ${FILE_DIR}

nix-shell --run "autoPatchelf src/binaries/firmware/bin"
