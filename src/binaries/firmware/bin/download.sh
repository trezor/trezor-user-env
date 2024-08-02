#!/usr/bin/env bash
set -e -o pipefail

SYSTEM_ARCH=$(uname -m)

cd "$(dirname "${BASH_SOURCE[0]}")"
BIN_DIR=$(pwd)

if [[ $SYSTEM_ARCH == x86_64* ]]; then
    SITE="https://data.trezor.io/dev/firmware/releases/emulators/"
    CUT_DIRS=4

elif [[ $SYSTEM_ARCH == aarch64* ]]; then
    SITE="https://data.trezor.io/dev/firmware/releases/emulators/arm/"
    CUT_DIRS=5

else
   echo "Not a supported arch - $SYSTEM_ARCH"
   exit 1
fi

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
    wget https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-legacy-T1B1-universal
    mv trezor-emu-legacy-T1B1-universal ../trezor-emu-legacy-v1-main

    wget https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-core-T2T1-universal
    mv trezor-emu-core-T2T1-universal ../trezor-emu-core-v2-main

    wget https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-core-T2B1-universal
    mv trezor-emu-core-T2B1-universal ../trezor-emu-core-R-v2-main

    wget https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-core-T3T1-universal
    mv trezor-emu-core-T3T1-universal ../trezor-emu-core-T3T1-v2-main

elif [[ $SYSTEM_ARCH == aarch64* ]]; then

    wget https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-arm-legacy-T1B1-universal
    mv trezor-emu-arm-legacy-T1B1-universal ../trezor-emu-legacy-v1-main-arm

    wget https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-arm-core-T2T1-universal
    mv trezor-emu-arm-core-T2T1-universal ../trezor-emu-core-v2-main-arm

    wget https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-arm-core-T2B1-universal
    mv trezor-emu-arm-core-T2B1-universal ../trezor-emu-core-R-v2-main-arm

    wget https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-arm-core-T3T1-universal
    mv trezor-emu-arm-core-T3T1-universal ../trezor-emu-core-T3T1-v2-main-arm
fi

cd "$BIN_DIR"

# mark as executable
chmod u+x trezor-emu-*

# strip debug symbols to save space
strip trezor-emu-*

# no need for Mac builds
rm -rf macos
