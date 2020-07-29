#!/usr/bin/env bash

set -e

BRANCH=${1:-develop}

cd repo
echo "Checking out branch $BRANCH"
git checkout "$BRANCH"
echo "Updating submodules"
git submodule update --init --recursive
echo "Running yarn && yarn suite:dev"
nix-shell --run "yarn && yarn suite:dev"
