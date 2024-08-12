#!/usr/bin/env bash
set -e -o pipefail

SYSTEM_ARCH=$(uname -m)

cd "$(dirname "${BASH_SOURCE[0]}")"
BIN_DIR=$(pwd)
BASE_EMU_URL="https://data.trezor.io/dev/firmware/releases/emulators-new"

if [[ $SYSTEM_ARCH == x86_64* ]]; then
    suffix=""

elif [[ $SYSTEM_ARCH == aarch64* ]]; then
    suffix="-arm"

else
   echo "Not a supported arch - $SYSTEM_ARCH"
   exit 1
fi

# Define the emulators to download latest 10 versions
files=(
 # T1B1
  "T1B1/trezor-emu-legacy-T1B1-v1.10.0${suffix}"
  "T1B1/trezor-emu-legacy-T1B1-v1.10.1${suffix}"
  "T1B1/trezor-emu-legacy-T1B1-v1.10.2${suffix}"
  "T1B1/trezor-emu-legacy-T1B1-v1.10.3${suffix}"
  "T1B1/trezor-emu-legacy-T1B1-v1.10.4${suffix}"
  "T1B1/trezor-emu-legacy-T1B1-v1.10.5${suffix}"
  "T1B1/trezor-emu-legacy-T1B1-v1.11.1${suffix}"
  "T1B1/trezor-emu-legacy-T1B1-v1.11.2${suffix}"
  "T1B1/trezor-emu-legacy-T1B1-v1.12.0${suffix}"
  "T1B1/trezor-emu-legacy-T1B1-v1.12.1${suffix}"
  # T2T1
  "T2T1/trezor-emu-core-T2T1-v2.5.1${suffix}"
  "T2T1/trezor-emu-core-T2T1-v2.5.2${suffix}"
  "T2T1/trezor-emu-core-T2T1-v2.5.3${suffix}"
  "T2T1/trezor-emu-core-T2T1-v2.6.0${suffix}"
  "T2T1/trezor-emu-core-T2T1-v2.6.3${suffix}"
  "T2T1/trezor-emu-core-T2T1-v2.6.4${suffix}"
  "T2T1/trezor-emu-core-T2T1-v2.7.0${suffix}"
  "T2T1/trezor-emu-core-T2T1-v2.7.2${suffix}"
  "T2T1/trezor-emu-core-T2T1-v2.8.1${suffix}"
  # T2B1
  "T2B1/trezor-emu-core-T2B1-v2.6.3${suffix}"
  "T2B1/trezor-emu-core-T2B1-v2.6.4${suffix}"
  "T2B1/trezor-emu-core-T2B1-v2.7.0${suffix}"
  "T2B1/trezor-emu-core-T2B1-v2.7.2${suffix}"
  "T2B1/trezor-emu-core-T2B1-v2.8.0${suffix}"
  # T3T1
  "T3T1/trezor-emu-core-T3T1-v2.7.2${suffix}"
  "T3T1/trezor-emu-core-T3T1-v2.8.0${suffix}"
  "T3T1/trezor-emu-core-T3T1-v2.8.1${suffix}"
)

for file in "${files[@]}"; do
  wget "${BASE_EMU_URL}/${file}" || true
done

# download emulator from main
TMP_DIR="$BIN_DIR/tmp"
rm -rf "$TMP_DIR"
mkdir "$TMP_DIR"

cleanup() {
  rm -rf "$TMP_DIR"
}

trap cleanup EXIT

cd "$TMP_DIR"

if [[ $SYSTEM_ARCH == x86_64* ]]; then
    wget https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-legacy-T1B1-universal
    mv trezor-emu-legacy-T1B1-universal ../trezor-emu-legacy-T1B1-v1-main

    wget https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-core-T2T1-universal
    mv trezor-emu-core-T2T1-universal ../trezor-emu-core-T2T1-v2-main

    wget https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-core-T2B1-universal
    mv trezor-emu-core-T2B1-universal ../trezor-emu-core-T2B1-v2-main

    wget https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-core-T3T1-universal
    mv trezor-emu-core-T3T1-universal ../trezor-emu-core-T3T1-v2-main

elif [[ $SYSTEM_ARCH == aarch64* ]]; then

    wget https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-arm-legacy-T1B1-universal
    mv trezor-emu-arm-legacy-T1B1-universal ../trezor-emu-legacy-T1B1-v1-main-arm

    wget https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-arm-core-T2T1-universal
    mv trezor-emu-arm-core-T2T1-universal ../trezor-emu-core-T2T1-v2-main-arm

    wget https://data.trezor.io/dev/firmware/emu-nightly/trezor-emu-arm-core-T2B1-universal
    mv trezor-emu-arm-core-T2B1-universal ../trezor-emu-core-T2B1-v2-main-arm

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
