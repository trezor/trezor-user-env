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
2. Using Docker for all other platforms. The Docker image is based on NixOS and basically mimics (1).

### Nix OS

- Enter `nix-shell`.
- Download projects (you need SatoshiLabs VPN):
  - `firmware/bin/download.sh`
  - `trezord-go/bin/download.sh`
  - `suite/bin/download.sh`
- Run the controller `nix-shell controller/shell.nix --run 'python controller/main.py'`. Note that it has its own `shell.nix`!

### Docker

To support non-NixOS systems we provide a thin Docker layer (well
actually not that thin) that runs bare NixOS and enables this project.

----

#### Linux (not NixOS)

_Consider using NixOS!_

##### Prerequisites

You need:
- Docker (to run NixOS in a container).

##### Run it

1. Run in terminal: `xhost +`
2. Download the latest docker build: `docker-compose -f ./docker/compose.yml pull trezor-user-env-unix`
3. Run it: `docker-compose -f ./docker/compose.yml up trezor-user-env-unix`
4. Open `http://localhost:21326/`

For a future use you can omit the second step and run `up` (the third step) directly. However, you will not have the latest master builds then!

----

#### MacOS

##### Prerequisites

You need:
- [Docker](https://docs.docker.com/docker-for-mac/install/) (to run NixOS in a container)
- [XQuartz](https://www.xquartz.org/) (to share your screen with Docker)

Download these as you are used to. We recommend using `nix` or `brew`, but that's your fight.

##### Run it

1. Run XQuartz and leave it running on the background. Wait till it is launched.
2. In XQuartz settings go to Preferences > Security and enable "Allow connections from network clients".
3. Open a new terminal window (not in XQuartz) and add yourself to the X access control list: `xhost +127.0.0.1` (you will probably need to logout/login after XQuartz installation to have `xhost` command available)
4. Download the latest docker build: `docker-compose -f ./docker/compose.yml pull trezor-user-env-mac`
5. Run it: `docker-compose -f ./docker/compose.yml up trezor-user-env-mac`
6. Open `http://localhost:21326/`

For a future use you can omit the fourth step and run `up` (the fifth step) directly. However, you will not have the latest master builds then!

----

#### Windows

Currently not supported, but should work using docker as well.
