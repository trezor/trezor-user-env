#!/usr/bin/env bash
set -e -o pipefail

SYSTEM_ARCH=$(uname -m)

if [[ $SYSTEM_ARCH == x86_64* ]]; then
    SITE="https://data.trezor.io/dev/firmware/releases/emulators/"
    CORE_LATEST_BUILD="https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/jobs/artifacts/master/download?job=core%20unix%20frozen%20debug%20build"
    # WARNING: just temporary
    # It should get the build from master branch, but it does not
    # have all the needed functionality. Using custom branch for now.
    R_LATEST_BUILD="https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/jobs/2727705686/artifacts/raw/core/build/unix/trezor-emu-core"
    LEGACY_LATEST_BUILD="https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/jobs/artifacts/master/download?job=legacy%20emu%20regular%20debug%20build"
    CUT_DIRS=4

elif [[ $SYSTEM_ARCH == aarch64* ]]; then
    SITE="https://data.trezor.io/dev/firmware/releases/emulators/arm/"
    CORE_LATEST_BUILD="https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/jobs/artifacts/master/download?job=core%20unix%20frozen%20debug%20build%20arm"
    # WARNING: just temporary
    # It should get the build from master branch, but it does not
    # have all the needed functionality. Using custom branch for now.
    R_LATEST_BUILD="https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/jobs/2727705693/artifacts/raw/core/build/unix/trezor-emu-core-arm"
    LEGACY_LATEST_BUILD="https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/jobs/artifacts/master/download?job=legacy%20emu%20regular%20debug%20build%20arm"
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

# download emulator from master
TMP_DIR="$BIN_DIR/tmp"
rm -rf "$TMP_DIR"
mkdir "$TMP_DIR"

cleanup() {
  rm -rf "$TMP_DIR"
}

trap cleanup EXIT

cd "$TMP_DIR"

if [[ $SYSTEM_ARCH == x86_64* ]]; then
    wget --no-config -O trezor-emu-core-master.zip "$CORE_LATEST_BUILD"
    unzip -q trezor-emu-core-master.zip
    mv core/build/unix/trezor-emu-core ../trezor-emu-core-v2-master

    wget --no-config -O trezor-emu-legacy-master.zip "$LEGACY_LATEST_BUILD"
    unzip -q trezor-emu-legacy-master.zip
    mv legacy/firmware/trezor.elf ../trezor-emu-legacy-v1-master

    wget --no-config -O trezor_r_master_emu "$R_LATEST_BUILD"
    mv trezor_r_master_emu ../trezor-emu-core-R-v2-master

elif [[ $SYSTEM_ARCH == aarch64* ]]; then
    wget --no-config -O trezor-emu-core-arm-master.zip "$CORE_LATEST_BUILD"
    unzip -q trezor-emu-core-arm-master.zip -d arm/
    mv arm/core/build/unix/trezor-emu-core-arm ../trezor-emu-core-v2-master-arm

    wget --no-config -O trezor-emu-legacy-arm-master.zip "$LEGACY_LATEST_BUILD"
    unzip -q trezor-emu-legacy-arm-master.zip -d arm/
    mv arm/legacy/firmware/trezor-arm.elf ../trezor-emu-legacy-v1-master-arm

    wget --no-config -O trezor_r_master_emu_arm "$R_LATEST_BUILD"
    mv trezor_r_master_emu_arm ../trezor-emu-core-R-v2-master-arm
fi

cd "$BIN_DIR"

# mark as executable
chmod u+x trezor-emu-*

# no need for Mac builds
rm -rf macos
