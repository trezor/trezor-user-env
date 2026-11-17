FROM debian:bookworm-slim

RUN useradd -rG sudo bitcoin \
  && apt-get update -y \
  && apt-get install -y curl wget gnupg gosu logrotate procps \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Fetching the binaries from foked blockbook repo unti we introduce building of packages directly in blockbook repo
# https://github.com/satoshilabs/devops/issues/45
ARG TARGETPLATFORM
ARG BACKEND_VERSION=31.1-satoshilabs-1
ARG BLOCKBOOK_VERSION=0.6.0
# apt-get installs the packages' library dependencies, which dpkg -i does not
RUN if [ "$TARGETPLATFORM" = "linux/amd64" ]; then ARCHITECTURE=amd64; elif [ "$TARGETPLATFORM" = "linux/arm64" ]; then ARCHITECTURE=arm64; else ARCHITECTURE=amd64; fi \
  && wget https://data.trezor.io/dev/blockbook/builds/backend-bitcoin-regtest_${BACKEND_VERSION}_${ARCHITECTURE}.deb \
  && wget https://data.trezor.io/dev/blockbook/builds/blockbook-bitcoin-regtest_${BLOCKBOOK_VERSION}_${ARCHITECTURE}.deb \
  && apt-get update -y \
  && apt-get install -y --no-install-recommends \
    ./backend-bitcoin-regtest_${BACKEND_VERSION}_${ARCHITECTURE}.deb \
    ./blockbook-bitcoin-regtest_${BLOCKBOOK_VERSION}_${ARCHITECTURE}.deb \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && rm blockbook-bitcoin-regtest_${BLOCKBOOK_VERSION}_${ARCHITECTURE}.deb \
  && rm backend-bitcoin-regtest_${BACKEND_VERSION}_${ARCHITECTURE}.deb

# replace default bitcoind config, which binds RPC to localhost only, so the RPC port published from the container is reachable.
COPY ./docker/bitcoin-regtest/bitcoin_regtest.conf /opt/coins/nodes/bitcoin_regtest/bitcoin_regtest.conf
# replace default blockbook config with custom config with changed coin_shortcut to "REGTEST", to be compatibile with trezor-common shorcut.
COPY ./docker/bitcoin-regtest/blockchaincfg.json /opt/coins/blockbook/bitcoin_regtest/config/blockchaincfg.json
COPY ./docker/bitcoin-regtest/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

ENTRYPOINT [ "./entrypoint.sh" ]
