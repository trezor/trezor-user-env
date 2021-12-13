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

echo -n "Python version: "
nix-shell --run "poetry run python --version"
echo -n "Trezorctl version: "
nix-shell --run "poetry run trezorctl version"

echo "Starting trezor-user-env server"
nix-shell --run "poetry run python src/main.py"
