#!/usr/bin/env bash
set -e -o pipefail

SYSTEM_ARCH=$(uname -m)
USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'

cd "$(dirname "${BASH_SOURCE[0]}")"
BIN_DIR=$(pwd)

# WARNING: this will download the emulators from the latest SUCCESSFULLY run pipeline from trezor-firmware.
# If the pipeline fails, it will download from the previous successful run.
GITLAB_URL="https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/jobs/artifacts/main/download"

if [[ $SYSTEM_ARCH == x86_64* ]]; then
    # All core emulators are downloaded from trezor.io
    SITE="https://data.trezor.io/dev/firmware/releases/emulators/"
    LEGACY_LATEST_BUILD="${GITLAB_URL}?job=legacy%20emu%20regular%20debug%20build"
    CUT_DIRS=4

elif [[ $SYSTEM_ARCH == aarch64* ]]; then
    SITE="https://data.trezor.io/dev/firmware/releases/emulators/arm/"
    CORE_LATEST_BUILD="${GITLAB_URL}?job=core%20unix%20frozen%20debug%20build%20arm"
    R_LATEST_BUILD="${GITLAB_URL}?job=core%20unix%20frozen%20R%20debug%20build%20arm"
    LEGACY_LATEST_BUILD="${GITLAB_URL}?job=legacy%20emu%20regular%20debug%20build%20arm"
    T3T1_LATEST_BUILD="${GITLAB_URL}?job=core%20unix%20frozen%20T3T1%20debug%20build%20arm"
    CUT_DIRS=5

else
   echo "Not a supported arch - $SYSTEM_ARCH"
   exit 1
fi

if ! wget --remote-encoding=utf-8 --user-agent="$USER_AGENT" --no-config -e robots=off --no-verbose --no-clobber --no-parent --cut-dirs=$CUT_DIRS --no-host-directories --recursive --reject "index.html*" "$SITE"; then
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
    wget --remote-encoding=utf-8 --user-agent="$USER_AGENT" --no-config -O trezor-emu-legacy-main.zip "$LEGACY_LATEST_BUILD"
    unzip -o -q trezor-emu-legacy-main.zip
    mv legacy/firmware/trezor.elf ../trezor-emu-legacy-v1-main

    wget --remote-encoding=utf-8 --user-agent="$USER_AGENT" https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-core-T2T1-universal
    mv trezor-emu-core-T2T1-universal ../trezor-emu-core-v2-main

    wget --remote-encoding=utf-8 --user-agent="$USER_AGENT" https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-core-T3T1-universal
    mv trezor-emu-core-T3T1-universal ../trezor-emu-core-T3T1-v2-main

    wget --remote-encoding=utf-8 --user-agent="$USER_AGENT" https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-core-T2B1-universal
    mv trezor-emu-core-T2B1-universal ../trezor-emu-core-R-v2-main

elif [[ $SYSTEM_ARCH == aarch64* ]]; then
    wget --remote-encoding=utf-8 --user-agent="$USER_AGENT" --no-config -O trezor-emu-core-arm-main.zip "$CORE_LATEST_BUILD"
    unzip -o -q trezor-emu-core-arm-main.zip -d arm/
    mv arm/core/build/unix/trezor-emu-core-arm ../trezor-emu-core-v2-main-arm

    wget --remote-encoding=utf-8 --user-agent="$USER_AGENT" --no-config -O trezor-emu-core-R-arm-main.zip "$R_LATEST_BUILD"
    unzip -o -q trezor-emu-core-R-arm-main.zip -d arm/
    mv arm/core/build/unix/trezor-emu-core-arm ../trezor-emu-core-R-v2-main-arm

    # TEMPORARILY replaced by baking the emulators into the image
    # wget --remote-encoding=utf-8 --user-agent="$USER_AGENT" --no-config -O trezor-emu-core-T3T1-arm-main.zip "$T3T1_LATEST_BUILD"
    # unzip -o -q trezor-emu-core-T3T1-arm-main.zip -d arm/
    # mv arm/core/build/unix/trezor-emu-core-arm ../trezor-emu-core-T3T1-v2-main-arm
    mv ../arm/trezor-emu-core-T3T1-v2-main-arm ../trezor-emu-core-T3T1-v2-main-arm

    wget --remote-encoding=utf-8 --user-agent="$USER_AGENT" --no-config -O trezor-emu-legacy-arm-main.zip "$LEGACY_LATEST_BUILD"
    unzip -o -q trezor-emu-legacy-arm-main.zip -d arm/
    mv arm/legacy/firmware/trezor-arm.elf ../trezor-emu-legacy-v1-main-arm

fi

cd "$BIN_DIR"

# patch the emulators to use correct interpreter
patchelf --set-interpreter /lib/ld-musl-aarch64.so.1 trezor-emu-*

# mark as executable
chmod u+x trezor-emu-*

# strip debug symbols to save space
strip trezor-emu-*

# no need for Mac builds
rm -rf macos
