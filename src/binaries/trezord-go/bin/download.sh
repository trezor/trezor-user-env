#!/usr/bin/env bash
set -e

# TODO: fetch trezord-go from nix

# Bridge needs an older glibc so we are pinning to nixos-21.05 (stable) as of 2021-07-02
nix-shell -p autoPatchelfHook -I "nixpkgs=https://github.com/NixOS/nixpkgs/archive/e9148dc1c30e02aae80cc52f68ceb37b772066f3.tar.gz" --run "autoPatchelf trezord-*"
