#!/usr/bin/env bash
set -e -o pipefail

FILE_DIR="$(dirname "${0}")"

DIR_TO_PATCH="${1:-$FILE_DIR}"

echo "Patching ${DIR_TO_PATCH}"

nix-shell --run "autoPatchelf ${DIR_TO_PATCH}"
