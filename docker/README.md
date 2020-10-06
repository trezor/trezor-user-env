# Docker

To support non-NixOS systems we provide a thin Docker layer (well
actually not that thin) that runs bare NixOS and enables this.

## Linux (not NixOS)

_Consider using NixOS!_

### Prerequisites

You need:
- Docker (to run NixOS in a container).

### Run it

1. Run in terminal: `xhost +`
2. Download the latest docker build: `docker-compose -f ./docker/compose.yml pull trezor-user-env-unix`
3. Run it: `docker-compose -f ./docker/compose.yml up trezor-user-env-unix`.
4. Open `controller/index.html`: `xdg-open controller/index.html`.

For a future use you can omit the second step and run `up` (the third step) directly. However, you will not have the latest master builds then!

## MacOS

### Prerequisites

You need:
- Docker (to run NixOS in a container)
- xQuartz (to share your screen with Docker)

Download these as you are used to. We recommend using `nix` or `brew`, but that's your fight.

### Run it

1. Run xQuartz and leave it running on the background. Wait till it is launched.
2. In Xquartz settings go to Preferences > Security and enable "Allow connections from network clients".
3. Open a new terminal window and add yourself to the X access control list: `xhost +127.0.0.1`
4. Download the latest docker build: `docker-compose -f ./docker/compose.yml pull trezor-user-env-mac`
5. Run it: `docker-compose -f ./docker/compose.yml up trezor-user-env-mac`.
6. Open `controller/index.html`: `open controller/index.html`.

For a future use you can omit the fourth step and run `up` (the fifth step) directly. However, you will not have the latest master builds then!
