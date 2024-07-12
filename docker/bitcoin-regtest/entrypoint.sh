#!/bin/bash
set -e

# start bitcoin backend
cd /opt/coins/nodes/bitcoin_regtest

echo "Starting bitcoin regtest backend service"
bin/bitcoind -blockfilterindex -mempoolfullrbf=1 -datadir=/opt/coins/data/bitcoin_regtest/backend -conf=/opt/coins/nodes/bitcoin_regtest/bitcoin_regtest.conf &

sleep 5

# generate test wallet and blocks
bin/bitcoin-cli -rpcport=18021 -rpcuser=rpc -rpcpassword=rpc createwallet "tenv-wallet"
bin/bitcoin-cli -rpcport=18021 -rpcuser=rpc -rpcpassword=rpc -generate 150
bin/bitcoin-cli -rpcport=18021 -rpcuser=rpc -rpcpassword=rpc settxfee 0.00001

# start blockbook
cd /opt/coins/blockbook/bitcoin_regtest

echo "Starting blockbook service"
bin/blockbook \
    -blockchaincfg=/opt/coins/blockbook/bitcoin_regtest/config/blockchaincfg.json \
    -datadir=/opt/coins/data/bitcoin_regtest/blockbook/db \
    -sync \
    -internal=:19021 \
    -public=:19121 \
    -explorer= \
    -log_dir=/opt/coins/blockbook/bitcoin_regtest/logs \
    -dbcache=0
