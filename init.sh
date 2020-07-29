#!/usr/bin/env bash

set -e
mkdir -p firmware/repo suite/repo



if [ -f firmware/repo/README.md ]; then
  echo "Firmware repo seems to be already present"
else
  echo "Cloning Firmware"
  cd firmware
  git clone git@github.com:trezor/trezor-firmware.git repo
  cd repo
  git submodule update --init --recursive
  cd ../..
fi

if [ -f suite/repo/README.md ]; then
  echo "Suite repo seems to be already present"
else
  echo "Cloning Suite"
  cd suite
  git clone git@github.com:trezor/trezor-suite.git repo
  cd ..
fi

echo "Init done!"
