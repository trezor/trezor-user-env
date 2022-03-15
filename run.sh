#!/usr/bin/env bash
set -e -o pipefail

if [ -z "$1" ]
  then
    TENV_REGTEST="trezor-user-env-regtest"
elif [[ $1 == --no-regtest ]]; then
    TENV_REGTEST=""
fi

SYSTEM=$(uname)

if [[ $SYSTEM == Linux* ]]; then

    echo -e "Setup xhost for video device output"
    xhost +
    echo -e "Downloading latest images"
    docker-compose -f ./docker/compose.yml pull trezor-user-env-unix $TENV_REGTEST
    echo -e "Starting trezor-user-env"
    docker-compose -f ./docker/compose.yml up trezor-user-env-unix $TENV_REGTEST

elif [[ $SYSTEM == Darwin* ]]; then

    echo -e "Setup xhost for video device output"
    xhost +127.0.0.1
    echo -e "Downloading latest images"
    docker-compose -f ./docker/compose.yml pull trezor-user-env-mac $TENV_REGTEST
    echo -e "Starting trezor-user-env"
    docker-compose -f ./docker/compose.yml up trezor-user-env-mac $TENV_REGTEST

else
    echo -e "Not a supported system - $SYSTEM"
    exit 1
fi
