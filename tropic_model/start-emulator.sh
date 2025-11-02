#!/bin/bash
#
# Start Tropic Square emulator via model_server
#

# Change to the directory where this script is located
cd "$(dirname "$0")" || exit 1

echo "========================================="
echo "Starting Tropic Square Emulator"
echo "========================================="
echo ""

# Run model_server with config from current directory
uv run model_server tcp -c config.yml
