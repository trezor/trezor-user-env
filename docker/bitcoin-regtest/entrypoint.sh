#!/bin/bash
set -e

# start bitcoin backend
cd /opt/coins/nodes/bitcoin_regtest

echo "Starting bitcoin regtest backend service"
/opt/coins/nodes/bitcoin_regtest/bin/bitcoind -datadir=/opt/coins/data/bitcoin_regtest/backend -conf=/opt/coins/nodes/bitcoin_regtest/bitcoin_regtest.conf &

# start blockbook
cd /opt/coins/blockbook/bitcoin_regtest

echo "Starting blockbook service"
/opt/coins/blockbook/bitcoin_regtest/bin/blockbook -blockchaincfg=/opt/coins/blockbook/bitcoin_regtest/config/blockchaincfg.json -datadir=/opt/coins/data/bitcoin_regtest/blockbook/db -sync -internal=:19021 -public=:19121 -certfile=/opt/coins/blockbook/bitcoin_regtest/cert/blockbook -explorer= -log_dir=/opt/coins/blockbook/bitcoin_regtest/logs