# Docker

To support non-NixOS systems we provide a thin Docker layer (well
actually not that thin) that runs bare NixOS and enables you to run 
this. 

## Non-NixOS Linux

_Consider using NixOS!_

### Prerequisites

You need:
- Docker (to run NixOS in a container)
- SatoshiLabs VPN.

### Run it

- Make sure your VPN is on.
- `xhost +`  TODO: is this needed?
- Run `docker-compose -f ./docker/docker-compose-mac.yml up --build`.
- Open `controller/index.html`: `xdg-open controller/index.html`.

## MacOS

### Prerequisites

You need:
- Docker (to run NixOS in a container)
- xQuartz (to share your screen with Docker)
- SatoshiLabs VPN.

Download these as you are used to. We recommend using nix or brew, but that's your fight.

TODO: Xquartz setting

### Run it

- Run xQuartz and leave it running on the background. Wait till it is launched.
- Add yourself to the X access control list: `xhost +127.0.0.1`
- Make sure your VPN is on.
- Run `docker-compose -f ./docker/docker-compose-mac.yml up --build`.
- Open `controller/index.html`: `open controller/index.html`.
