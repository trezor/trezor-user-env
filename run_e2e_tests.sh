#!/usr/bin/env bash

set -e

# launch controller
cd controller
nix-shell --run "python main.py &"

# launch Suite
cd ../suite/repo
nix-shell --run "yarn && yarn suite:dev &"

sleep 60  # wait for Suite to build TODO

# launch cypress tests
CYPRESS_BIN=$(nix-shell --run "which Cypress")
nix-shell --run "CYPRESS_RUN_BINARY=$CYPRESS_BIN CYPRESS_baseUrl=http://localhost:3000 CYPRESS_defaultCommandTimeout=60000 cypress open --project packages/integration-tests/projects/suite-web"

nix-shell --run "kill yarn && kill python"
