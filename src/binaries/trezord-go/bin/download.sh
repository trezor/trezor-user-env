#!/usr/bin/env bash
set -e

# TODO: fetch trezord-go from nix

# Bridge needs an older glibc so we are pinning to nixos-21.05 (stable) as of 2021-07-02
nix-shell -p autoPatchelfHook -I "nixpkgs=https://github.com/NixOS/nixpkgs/archive/e9148dc1c30e02aae80cc52f68ceb37b772066f3.tar.gz" --run "autoPatchelf trezord-*"
nix-shell -p autoPatchelfHook --run "patchelf --set-interpreter /nix/store/34k9b4lsmr7mcmykvbmwjazydwnfkckk-glibc-2.33-50/lib/ld-linux-aarch64.so.1 ./src/binaries/trezord-go/bin/*-arm64"
