#!/bin/bash
set -e

# stop bitcoind
cd /opt/coins/nodes/bitcoin_regtest
echo "Stoping bitcoin regtest backend service"
bin/bitcoin-cli -rpcport=18021 -rpcuser=rpc -rpcpassword=rpc stop

sleep 5

# delete regtest data
cd /opt/coins/data/bitcoin_regtest/backend
rm -r regtest/

# start bitcoin backend
echo "Starting bitcoin regtest backend service"
bin/bitcoind -blockfilterindex -datadir=/opt/coins/data/bitcoin_regtest/backend -conf=/opt/coins/nodes/bitcoin_regtest/bitcoin_regtest.conf

# generate test wallet and blocks
cd /opt/coins/nodes/bitcoin_regtest
bin/bitcoin-cli -rpcport=18021 -rpcuser=rpc -rpcpassword=rpc createwallet "tenv-wallet"
bin/bitcoin-cli -rpcport=18021 -rpcuser=rpc -rpcpassword=rpc -generate 150
bin/bitcoin-cli -rpcport=18021 -rpcuser=rpc -rpcpassword=rpc settxfee 0.00001
