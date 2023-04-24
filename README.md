# Trezor User Env

This environment is meant to support Trezor development - both Firmware and Suite and other related projects. Its main goals are:

- Provide an easy websocket server that is capable of:
  - Launching/stopping different versions of the firmware emulator.
  - Launching/stopping trezord-go (Bridge).
  - Send simple debug commands to the emulator.
- Enable full integration testing of Suite, firmware emulator and Bridge using the websocket server.
- Provide a HTML page that communicates with the server. This allows the developers to perform the actions above.
- To be Nix-native but also offer Docker image to allow non-NixOS developers to use it.

## How to run

_You can also run trezor-user-env "natively" if you are on NixOS but we mainly support the Docker way as described here._

In case you have installed Trezor Bridge previously there will be a port conflict, please make sure it is not running. Either uninstall it completely or stop the service.

Supported platforms are Linux and macOS (both Intel and Silicon).

### Prerequisites

- Docker
- xhost on Linux
- [XQuartz](https://www.xquartz.org/) on macOS. Configure > Preferences > Security > Allow connections from network clients
- Reboot (sign out/sign in might work)

### Steps

1. Clone this repo and enter the directory
2. Run `./run.sh` it will determine your platform and launch trezor-user-env. See `./run.sh --help` for some additional arguments.
3. Open http://localhost:9002.

## Basic terminology

- **Controller**
  - Websocket server running on *localhost:9001*
  - Has the functionality to control trezor components (run emulators, bridges, etc.)
  - Used by Dashboard (below) or by automated end-to-end tests in Trezor Suite
- **Dashboard**
  - HTML page being accessible on *localhost:9002*
  - Instructs the websocket server what to do by predefined functionality
  - Used by developers testing their firmware/suite applications manually
- **Bridge**
  - Service running on *localhost:21325*
  - Connection between the trezor device (or running emulator) and the host
  - Used by applications needing to communicate with trezor device (for example Suite)
- **Bridge proxy**
  - Proxies requests to the bridge
- **Bitcoin regtest**
  - Bitcoind with [blockbook](https://github.com/trezor/blockbook) running in regtest mode
  - Default credentials for bitcoin backend
    - user and password: `rpc/rpc` and that you can run
  - You can test the connection with `bitcoin-cli -rpcport=18021 -rpcuser=rpc -rpcpassword=rpc -getinfo`

## Development

See [docs/development.md](docs/development.md).

## Troubleshooting

- On Apple Silicon Macs, `trezor-user-env-regtest` runs in an emulation layer as there is no arm native image. You may experience some slowness or issues when using it on arm Macs.
