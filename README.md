# Trezor User Env

This environment is meant to support Trezor development - both Firmware and Suite and other related projects. Its main goals are:

- Provide an easy websocket server that is capable of:
  - Launching/stopping different versions of the firmware emulator.
  - Launching/stopping trezord-go (Bridge).
  - Send simple debug commands to the emulator.
- Enable full integration testing of Suite, firmware emulator and Bridge using the websocket server.
- Provide a HTML page that communicates with the server. This allows the developers to perform the actions above.
- To be Nix-native but also offer Docker image to allow non-NixOS developers to use it.

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

## How to run

_You can also run trezor-user-env "natively" if you are on NixOS but we mainly support the Docker way as described here._

In case you have installed Trezor Bridge previously there will be a port conflict, please make sure it is not running. Either uninstall it completely or stop the service.

### Linux

#### Prerequisites

You need:
- Docker (to run NixOS in a container). 
- xhost

On NixOS, simply enter the `nix-shell`, it is all there.

#### Run it

1. Clone this repo `git clone git@github.com:trezor/trezor-user-env.git`. If on NixOS, enter `nix-shell`.
2. Run in terminal: `xhost +`
3. Download the latest docker build: `docker-compose -f ./docker/compose.yml pull trezor-user-env-unix`
4. Run it: `docker-compose -f ./docker/compose.yml up trezor-user-env-unix`
5. Open http://localhost:9002.

For a future use you can omit the second step and run `up` (the third step) directly. **However, you will not have the latest master builds then!**

----

### MacOS

#### Prerequisites

You need:
- [Docker](https://docs.docker.com/docker-for-mac/install/) (to run NixOS in a container)
- [XQuartz](https://www.xquartz.org/) (to share your screen with Docker)

Download these as you are used to. We recommend using `nix` or `brew`, but that's your fight.

#### Run it

1. Run XQuartz and leave it running on the background. Wait till it is launched.
2. In XQuartz settings go to Preferences > Security and enable "Allow connections from network clients".
3. Open a new terminal window (not in XQuartz) and add yourself to the X access control list: `xhost +127.0.0.1` (you will probably need to logout/login after XQuartz installation to have `xhost` command available)
4. Clone this repo `git clone git@github.com:trezor/trezor-user-env.git`.
5. Download the latest docker build: `docker-compose -f ./docker/compose.yml pull trezor-user-env-mac`
6. Run it: `docker-compose -f ./docker/compose.yml up trezor-user-env-mac`
7. Open http://localhost:9002.

For a future use you can omit the second step and run `up` (the third step) directly. **However, you will not have the latest master builds then!**

----

### Windows

Currently not supported, but should work using docker as well.

## How to develop

In case you need to modify something in trezor-user-env you have two options.

### Natively in NixOS

If you are using NixOS you can do the changes locally and then run the controller yourself. Run it via `nix-shell --run 'python src/main.py'`. Make sure you have run `src/binaries/{firmware,trezord-go}/bin/download.sh` beforehand otherwise you'll have old binaries.

This is suitable for smaller changes or things you can check via the HTML dashboard easily. However, if you are adding some functionality to trezor-user-env mainly because of Suite end-to-end tests, it is probably better to go the CI way (below). Otherwise you would need to run the whole Suite test suite locally.

### Let CI do it

The simpler but less flexible way is to let the [CI](https://gitlab.com/satoshilabs/trezor/trezor-user-env/pipelines) build it. You can create a branch, commit your changes and then push them. The CI will build it for you and tag the appropriate docker image as `test`. You can then modify all scripts/commands and use `registry.gitlab.com/satoshilabs/trezor/trezor-user-env/trezor-user-env:test` instead of `registry.gitlab.com/satoshilabs/trezor/trezor-user-env/trezor-user-env` which defaults to the `latest` tag which equals trezor-user-env's master. Suite's docker-compose files in the `docker` subdirectory are the place where you want to change this.
