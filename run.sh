#!/usr/bin/env bash
set -e -o pipefail
GREEN='\033[0;32m'
RED='\033[0;31m'
CLEAR='\033[0m'

TENV_REGTEST="trezor-user-env-regtest"
DASHBOARD_URL="http://localhost:9002"
SYSTEM=$(uname)
XHOST_ADDRESS=""
SERVICE_NAME=""
OPEN=""
PULL=1
PHYSICAL_TREZOR=0
BRANCH=$(git rev-parse --abbrev-ref HEAD)

function usage() {
  if [ -n "$1" ]; then
    echo -e "$1";
  fi
  echo "Usage: $0 [-r --no-regtest] [-p --no-pull]"
  echo "  -r, --no-regtest      Run tenv only, no regtest"
  echo "  -p, --no-pull         Do not pull changes, neither git nor docker. Automatically set to True when not on 'master'"
  echo "  -t, --trezor          Support for physical Trezor instead of an emulator. WARNING: only forks for Linux, not MacOS."
  echo ""
}

# parse params
while [[ "$#" > 0 ]]; do case $1 in
  -r|--no-regtest) TENV_REGTEST=""; shift;;
  -p|--no-pull) PULL=0; shift;;
  -t|--trezor) PHYSICAL_TREZOR=1; shift;;
  -h|--help) usage; exit 0; shift;;
  *) usage "${RED}Unknown parameter passed: $1${CLEAR}\n"; exit 1; shift;;
esac; done

if [[ $SYSTEM == Linux* ]]; then
    SERVICE_NAME="trezor-user-env-unix"
    OPEN="xdg-open"

elif [[ $SYSTEM == Darwin* ]]; then
    XHOST_ADDRESS="127.0.0.1"
    SERVICE_NAME="trezor-user-env-mac"
    OPEN="open"

else
    echo -e "${RED}Not a supported system: $SYSTEM${CLEAR}\n"
    exit 1
fi

echo -e "On system: $SYSTEM"

if [[ $PULL -eq 1 ]]; then
    if [[ $BRANCH != "master" ]]; then
        echo -e "${RED}Not on master, not pulling latest git changes${CLEAR}\n"
    else
        echo -e "Pulling git changes"
        git pull
    fi

    echo -e "Downloading latest images"
    docker-compose -f ./docker/compose.yml pull $SERVICE_NAME $TENV_REGTEST
fi

echo -e "Setup xhost for video device output"
xhost "+$XHOST_ADDRESS"

if [[ $TENV_REGTEST == "trezor-user-env-regtest" ]]; then
    echo -e "${GREEN}Starting trezor-user-env with Bitcoin regtest${CLEAR}\n"
else
    echo -e "${GREEN}Starting trezor-user-env${CLEAR}\n"
fi

# open localhost:9002 in web browser after the controller is launched
(while ! $(curl $DASHBOARD_URL -s -o /dev/null); do sleep 1; done; $OPEN $DASHBOARD_URL)&

if [[ $PHYSICAL_TREZOR -eq 1 ]]; then
    echo "Will support physical Trezor instead of emulator."
    # this env variable is being passed to the docker environment
    export PHYSICAL_TREZOR=1
fi

# launch trezor-user-env
docker-compose -f ./docker/compose.yml up --force-recreate $SERVICE_NAME $TENV_REGTEST
