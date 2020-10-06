#!/usr/bin/env bash
set -e

SITE="https://firmware.corp.sldev.cz/releases/emulators/"
CORE_LATEST_BUILD="https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/jobs/artifacts/master/download?job=core%20unix%20frozen%20debug%20build"
LEGACY_LATEST_BUILD="https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/jobs/artifacts/master/download?job=legacy%20emu%20regular%20debug%20build"

cd "$(dirname "$0")"

# download all released emulators
wget -e robots=off --no-verbose --no-clobber --no-parent --cut-dirs=2 --no-host-directories --recursive --reject "index.html*" $SITE

# download emulator from master
mkdir tmp
cd tmp

wget -O trezor-emu-core-master.zip $CORE_LATEST_BUILD
unzip -q trezor-emu-core-master.zip
mv core/build/unix/trezor-emu-core ../trezor-emu-core-v2-master

wget -O trezor-emu-legacy-master.zip $LEGACY_LATEST_BUILD
unzip -q trezor-emu-legacy-master.zip
mv legacy/firmware/trezor.elf ../trezor-emu-legacy-v1-master

cd ..
rm -r tmp

# mark as executable and patch for Nix
chmod u+x trezor-emu-*
nix-shell -p autoPatchelfHook SDL2 SDL2_image --run "autoPatchelf trezor-emu-*"

# no need for Mac builds
rm -rf macos

ls > download-index.txt
date > download-date.txt
