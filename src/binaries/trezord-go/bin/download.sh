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

# Older bridge (<= 31) needs older glibc so we are pinning to nixos-21.05 (stable) as of 2021-07-02
# nix-shell -p autoPatchelfHook -I "nixpkgs=https://github.com/NixOS/nixpkgs/archive/e9148dc1c30e02aae80cc52f68ceb37b772066f3.tar.gz" --run "autoPatchelf $FILES"
