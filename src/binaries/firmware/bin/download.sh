#!/usr/bin/env bash
set -e -o pipefail

SYSTEM_ARCH=$(uname -m)

if [[ $SYSTEM_ARCH == x86_64* ]]; then
    SITE="https://data.trezor.io/dev/firmware/releases/emulators/"
    # WARNING: this will download the emulator from the latest SUCCESSFULLY run pipeline from trezor-firmware. If the pipeline fails, it will download from the previous successful run.
    CORE_LATEST_BUILD="https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/jobs/artifacts/main/download?job=core%20unix%20frozen%20debug%20build"
    # WARNING: this will download the emulator from the latest SUCCESSFULLY run pipeline from trezor-firmware. If the pipeline fails, it will download from the previous successful run.
    R_LATEST_BUILD="https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/jobs/artifacts/main/download?job=core%20unix%20frozen%20R%20debug%20build"
    # WARNING: this will download the emulator from the latest SUCCESSFULLY run pipeline from trezor-firmware. If the pipeline fails, it will download from the previous successful run.
    LEGACY_LATEST_BUILD="https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/jobs/artifacts/main/download?job=legacy%20emu%20regular%20debug%20build"
    CUT_DIRS=4

elif [[ $SYSTEM_ARCH == aarch64* ]]; then
    SITE="https://data.trezor.io/dev/firmware/releases/emulators/arm/"
    # WARNING: this will download the emulator from the latest SUCCESSFULLY run pipeline from trezor-firmware. If the pipeline fails, it will download from the previous successful run.
    CORE_LATEST_BUILD="https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/jobs/artifacts/main/download?job=core%20unix%20frozen%20debug%20build%20arm"
    # WARNING: this will download the emulator from the latest SUCCESSFULLY run pipeline from trezor-firmware. If the pipeline fails, it will download from the previous successful run.
    R_LATEST_BUILD="https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/jobs/artifacts/main/download?job=core%20unix%20frozen%20R%20debug%20build%20arm"
    # WARNING: this will download the emulator from the latest SUCCESSFULLY run pipeline from trezor-firmware. If the pipeline fails, it will download from the previous successful run.
    LEGACY_LATEST_BUILD="https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/jobs/artifacts/main/download?job=legacy%20emu%20regular%20debug%20build%20arm"
    CUT_DIRS=5

else
   echo "Not a supported arch - $SYSTEM_ARCH"
   exit 1
fi

cd "$(dirname "${BASH_SOURCE[0]}")"
BIN_DIR=$(pwd)

if ! wget --no-config -e robots=off --no-verbose --no-clobber --no-parent --cut-dirs=$CUT_DIRS --no-host-directories --recursive --reject "index.html*" "$SITE"; then
    echo "Unable to fetch released emulators from $SITE"
    echo "You will have only available latest builds from CI"
    echo
  fi

# download emulator from main
TMP_DIR="$BIN_DIR/tmp"
rm -rf "$TMP_DIR"
mkdir "$TMP_DIR"

cleanup() {
  rm -rf "$TMP_DIR"
}

trap cleanup EXIT

cd "$TMP_DIR"

# NOTE: when unziping, using -o to overwrite existing files,
# otherwise extracting TR into already existing TT will ask for confirmation

if [[ $SYSTEM_ARCH == x86_64* ]]; then
    wget --no-config -O trezor-emu-core-main.zip "$CORE_LATEST_BUILD"
    unzip -o -q trezor-emu-core-main.zip
    mv core/build/unix/trezor-emu-core ../trezor-emu-core-v2-main

    wget --no-config -O trezor-emu-core-R-main.zip "$R_LATEST_BUILD"
    unzip -o -q trezor-emu-core-R-main.zip
    mv core/build/unix/trezor-emu-core ../trezor-emu-core-R-v2-main

    wget --no-config -O trezor-emu-legacy-main.zip "$LEGACY_LATEST_BUILD"
    unzip -o -q trezor-emu-legacy-main.zip
    mv legacy/firmware/trezor.elf ../trezor-emu-legacy-v1-main

elif [[ $SYSTEM_ARCH == aarch64* ]]; then
    wget --no-config -O trezor-emu-core-arm-main.zip "$CORE_LATEST_BUILD"
    unzip -o -q trezor-emu-core-arm-main.zip -d arm/
    mv arm/core/build/unix/trezor-emu-core-arm ../trezor-emu-core-v2-main-arm

    wget --no-config -O trezor-emu-core-R-arm-main.zip "$R_LATEST_BUILD"
    unzip -o -q trezor-emu-core-R-arm-main.zip -d arm/
    mv arm/core/build/unix/trezor-emu-core-arm ../trezor-emu-core-R-v2-main-arm

    wget --no-config -O trezor-emu-legacy-arm-main.zip "$LEGACY_LATEST_BUILD"
    unzip -o -q trezor-emu-legacy-arm-main.zip -d arm/
    mv arm/legacy/firmware/trezor-arm.elf ../trezor-emu-legacy-v1-main-arm

fi

cd "$BIN_DIR"

# mark as executable
chmod u+x trezor-emu-*

# strip debug symbols to save space
strip trezor-emu-*

# no need for Mac builds
rm -rf macos
