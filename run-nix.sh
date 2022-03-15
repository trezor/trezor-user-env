#!/usr/bin/env sh

DIR=$(dirname "$0")
cd "${DIR}"

version_file="docker/version.txt"
if [ -f "${version_file}" ]
then
    cat "${version_file}"
else
    echo "Version file is missing - ${version_file}"
fi
# Patch trezord after the container starts to prevent flaky behavior with arm version.
nix-shell -p bash --run "cd ./src/binaries/trezord-go/bin/ && ./download.sh"

echo -n "Python version: "
nix-shell --run "poetry run python --version"
echo -n "Trezorctl version: "
nix-shell --run "poetry run trezorctl version"

echo "Starting trezor-user-env server"
nix-shell --run "poetry run python src/main.py"
