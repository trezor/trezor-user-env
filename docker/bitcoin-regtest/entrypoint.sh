#!/usr/bin/env bash
set -e

# start bitcoin backend
cd /opt/coins/nodes/bitcoin_regtest

echo "Starting bitcoin regtest backend service"
# Fee floors match Bitcoin Core 29.1+ defaults. The bundled 25.0 defaults to 1 sat/vB, which rejects
# sub-1 sat/vB transactions and replacements with a smaller fee increase, such as Suite's RBF cancel.
bin/bitcoind -blockfilterindex -mempoolfullrbf=1 \
    -minrelaytxfee=0.000001 \
    -incrementalrelayfee=0.000001 \
    -blockmintxfee=0.00000001 \
    -datadir=/opt/coins/data/bitcoin_regtest/backend \
    -conf=/opt/coins/nodes/bitcoin_regtest/bitcoin_regtest.conf &

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
