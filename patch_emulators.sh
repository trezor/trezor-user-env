#!/usr/bin/env bash

FILE_DIR="$(dirname "${0}")"
cd ${FILE_DIR}

DIR_TO_PATCH="${1:-src/binaries/firmware/bin}"

echo "Patching ${DIR_TO_PATCH}"

patchelf ${DIR_TO_PATCH}
