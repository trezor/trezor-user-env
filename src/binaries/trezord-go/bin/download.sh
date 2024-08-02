#!/usr/bin/env bash
set -e

SYSTEM_ARCH=$(uname -m)

# TODO: fetch trezord-go from nix

if [[ $SYSTEM_ARCH == x86_64* ]]; then
    FILES="-name \"trezord-*\" -not -name \"*-arm\""
elif [[ $SYSTEM_ARCH == aarch64* ]]; then
    FILES="trezord-*-arm"
else
   echo "Not a supported arch - $SYSTEM_ARCH"
   exit 1
fi

# nix-shell --run "autoPatchelf $FILES"
