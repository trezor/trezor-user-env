#!/usr/bin/env bash

set -e

BRANCH=${1:-master}

cd repo
echo "Checking out branch $BRANCH"
git checkout "$BRANCH"
echo "Updating submodules"
git submodule update --init --recursive
echo "Running pipenv sync and build_unix_frozen"
nix-shell --run "pipenv sync && make -C core clean && PYOPT=0 pipenv run make -C core build_unix_frozen"
chmod u+x core/build/unix/micropython

COMMIT_SHA=$(git rev-parse --short HEAD)
VERSION=$(nix-shell --run "tools/version.sh core/embed/firmware/version.h")
mv core/build/unix/micropython "../bin/trezor-emu-regular-$VERSION-$COMMIT_SHA"
