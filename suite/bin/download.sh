#!/usr/bin/env bash
set -e

SITE="https://suite.corp.sldev.cz/suite-desktop/releases/"
cd "$(dirname "$0")"

# download all emulators without index files, without directories and only if not present
wget -e robots=off --no-verbose  --no-parent --cut-dirs=2 --no-host-directories --recursive --reject "*.exe" --reject "*.zip" $SITE
