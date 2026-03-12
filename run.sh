#!/usr/bin/env bash
set -e -o pipefail
GREEN='\033[0;32m'
RED='\033[0;31m'
CLEAR='\033[0m'

TENV_REGTEST="trezor-user-env-regtest"
DASHBOARD_URL="http://localhost:9002"
NOVNC_URL="http://localhost:6080/vnc.html"
SYSTEM=$(uname)
SERVICE_NAME="trezor-user-env"
OPEN=""
PULL=1
PHYSICAL_TREZOR=0
BRANCH=$(git rev-parse --abbrev-ref HEAD)

function usage() {
  if [ -n "$1" ]; then
    echo -e "$1";
  fi
  echo "Usage: $0 [-r --no-regtest] [-p --no-pull] [-t --trezor]"
  echo "  -r, --no-regtest      Run tenv only, no regtest"
  echo "  -p, --no-pull         Do not pull changes, neither git nor docker. Automatically set to True when not on 'master'"
  echo "  -t, --trezor          Support for physical Trezor instead of an emulator."
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

# Platform detection: set OPEN, REGTEST_RPC_URL and MACOS flag
if [[ $SYSTEM == Linux* ]]; then
    OPEN="xdg-open"
    export REGTEST_RPC_URL="http://localhost:18021"
    export MACOS=0
    echo -e "On system: Linux"

elif [[ $SYSTEM == Darwin* ]]; then
    OPEN="open"
    export REGTEST_RPC_URL="http://host.docker.internal:18021"
    export MACOS=1
    echo -e "On system: macOS"

else
    echo -e "${RED}Not a supported system: $SYSTEM${CLEAR}\n"
    exit 1
fi

if [[ $PULL -eq 1 ]]; then
    if [[ $BRANCH != "master" ]]; then
        echo -e "${RED}Not on master, not pulling latest git changes${CLEAR}\n"
    else
        echo -e "Pulling git changes"
        git pull
    fi

    # Only pull if the image doesn't exist locally at all, or if we want to force updates
    if [[ "$(docker images -q ghcr.io/trezor/trezor-user-env:latest 2> /dev/null)" == "" ]]; then
        echo -e "Downloading latest images"
        docker compose -f ./docker/compose.yml pull $SERVICE_NAME $TENV_REGTEST
    else
        echo -e "Local image ghcr.io/trezor/trezor-user-env:latest found, skipping pull to preserve local changes."
        # Still pull regtest as it's less likely to be modified locally
        docker compose -f ./docker/compose.yml pull $TENV_REGTEST
    fi
fi

if [[ $TENV_REGTEST == "trezor-user-env-regtest" ]]; then
    echo -e "${GREEN}Starting trezor-user-env with Bitcoin regtest${CLEAR}\n"
else
    echo -e "${GREEN}Starting trezor-user-env${CLEAR}\n"
fi

echo -e "Emulator window will be available at: ${GREEN}${NOVNC_URL}${CLEAR}"

# Open dashboard in browser once the controller is up; also open the noVNC viewer
(while ! $(curl $DASHBOARD_URL -s -o /dev/null); do sleep 1; done; $OPEN $DASHBOARD_URL) &

if [[ $PHYSICAL_TREZOR -eq 1 ]]; then
    echo "Will support physical Trezor instead of emulator."
    export PHYSICAL_TREZOR=1
else
    export PHYSICAL_TREZOR=""
fi

# Launch trezor-user-env (Xvfb + noVNC are started inside the container by entrypoint.sh)
docker compose -f ./docker/compose.yml up --force-recreate $SERVICE_NAME $TENV_REGTEST
