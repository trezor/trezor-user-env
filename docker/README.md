# Docker

To support non-NixOS systems we provide a thin Docker layer (well
actually not that thin) that runs bare NixOS and enables this.

## Linux (not NixOS)

_Consider using NixOS!_

### Prerequisites

You need:
- Docker (to run NixOS in a container).
- SatoshiLabs VPN (to download emulators etc.).

### Run it

- Make sure your VPN is on.
- `xhost +`
- Run `docker-compose -f ./docker/compose.yml up --remove-orphans --build trezor-user-env-unix`.

- Open `controller/index.html`: `xdg-open controller/index.html`.

## MacOS

### Prerequisites

You need:
- Docker (to run NixOS in a container)
- xQuartz (to share your screen with Docker)
- SatoshiLabs VPN.

Download these as you are used to. We recommend using `nix` or `brew`, but that's your fight.

In Xquartz settings go to Preferences > Security and enable "Allow connections from network clients".

### Run it

- Run xQuartz and leave it running on the background. Wait till it is launched.
- Add yourself to the X access control list: `xhost +127.0.0.1`
- Make sure your VPN is on.
- Run `docker-compose -f ./docker/compose.yml up --remove-orphans --build trezor-user-env-mac`.
- Open `controller/index.html`: `open controller/index.html`.
