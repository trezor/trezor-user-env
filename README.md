# Trezor User Env

This environment is meant to support Trezor development - both Firmware
and Suite and other related projects. Its main goals are:

- Provide an easy websocket server that is capable of:
 - Launching/stopping different versions of the firmware emulator.
 - Launching/stopping trezord-go (Bridge).
 - Send simple debug commands to the emulator.
- Provide a HTML page that communicates with the server. This allows 
developers to easy perform the actions above.
- To be Nix-native but also offer Docker image to allow non-NixOS 
developers to use this tool.

## How to

### Nix OS

TODO

### Other Linux distributions

See [docker/README.md](docker/README.md).

### MacOS

See [docker/README.md](docker/README.md).

### Windows

Currently not supported, but should work using docker as well.
