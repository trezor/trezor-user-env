# Trezor User Env

This environment is meant to support Trezor development - both Firmware
and Suite and other related projects. Its main goals are:

- Provide an easy websocket server that is capable of:
  - Launching/stopping different versions of the firmware emulator.
  - Launching/stopping trezord-go (Bridge).
  - Launching Suite.
  - Send simple debug commands to the emulator.
- Enable full integration testing of Suite, firmware emulator and Bridge using the websocket server.
- Provide a HTML page that communicates with the server. This allows the developers to perform the actions above.
- To be Nix-native but also offer Docker image to allow non-NixOS 
developers to use it.

## How to

There are two ways to run this project:

1. Natively if you are using NixOS.
2. Using Docker for all other platforms. The Docker image is based on NixOS and basically copies (1).

### Nix OS

- Enter `nix-shell`.
- Download projects (you need SatoshiLabs VPN):
  - `firmware/bin/download.sh`
  - `trezord-go/bin/download.sh`
  - `suite/bin/download.sh`
- Run the controller `nix-shell controller/shell.nix --run 'python controller/main.py'`. Note that it has its own `shell.nix`!

### Other Linux distributions

See [docker/README.md](docker/README.md).

### MacOS

See [docker/README.md](docker/README.md).

### Windows

Currently not supported, but should work using docker as well.
