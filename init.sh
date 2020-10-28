#!/usr/bin/env bash

set -e -o pipefail
mkdir -p firmware/repo suite/repo

if [[ -f firmware/repo/README.md ]]; then
  echo "Firmware repo seems to be already present"
else
  echo "Cloning Firmware"
  cd firmware
  git clone --recurse-submodules git@github.com:trezor/trezor-firmware.git repo
  cd ..
fi

if [[ -f suite/repo/README.md ]]; then
  echo "Suite repo seems to be already present"
else
  echo "Cloning Suite"
  cd suite
  git clone --recurse-submodules git@github.com:trezor/trezor-suite.git repo
  cd ..
fi

echo "Init done!"
