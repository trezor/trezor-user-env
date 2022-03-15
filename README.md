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
- **Bitcoin regtest**
  - Bitcoind with [blockbook](https://github.com/trezor/blockbook) running in regtest mode
  - Default credentials for bitcoin backend
    - user and password: `rpc/rpc` and that you can run
  - You can test the connection with `bitcoin-cli -rpcport=18021 -rpcuser=rpc -rpcpassword=rpc -getinfo`

## How to run

_You can also run trezor-user-env "natively" if you are on NixOS but we mainly support the Docker way as described here._

In case you have installed Trezor Bridge previously there will be a port conflict, please make sure it is not running. Either uninstall it completely or stop the service.

### Linux

#### Prerequisites

You need:
- Docker (to run NixOS in a container).
- xhost

On NixOS, simply enter the `nix-shell`, it is all there. All needed python libraries are then installed through `Poetry`, by `poetry install` and `poetry shell`.

#### Run it

1. Clone this repo `git clone git@github.com:trezor/trezor-user-env.git`. If you are new to Github, try `git clone https://github.com/trezor/trezor-user-env.git` instead.
2. Enter the directory using `cd trezor-user-env`.
3. Run the script `./run.sh` it will determine your platform and launch trezor-user-env
   3a. If you wish to launch only trezor-user-env use `--no-regtest` argument with `./run.sh --no-regtest`
4. Open http://localhost:9002.

[^1][^2]

[^1]: If you get an error with `trezor-user-env-regtest` starting up, you will need to clean container contents by pruning that container or all stopped containers with `docker container prune`
[^2]: `trezor-user-env-regtest` runs in emulation layer and is not ARM native image, you may experience some slowness or issues when using it on ARM Macs.

----

### MacOS

*Supported on Intel and Apple Silicon Mac devices*

#### Prerequisites

You need:
- [Docker](https://docs.docker.com/docker-for-mac/install/) (to run NixOS in a container)
- [XQuartz](https://www.xquartz.org/) (to share your screen with Docker)

Download these as you are used to. We recommend using `nix` or `brew`, but that's your fight.

#### Run it
1. Clone this repo `git clone git@github.com:trezor/trezor-user-env.git`. If you are new to Github, try `git clone https://github.com/trezor/trezor-user-env.git` instead.
2. Enter the directory using `cd trezor-user-env`.
3. Run the script `./run.sh` it will determine your platform and launch trezor-user-env
   3a. If you wish to launch only trezor-user-env use `--no-regtest` argument with `./run.sh --no-regtest`
4. Open http://localhost:9002.

[^1][^2]

[^1]: If you get an error with `trezor-user-env-regtest` starting up, you will need to clean container contents by pruning that container or all stopped containers with `docker container prune`
[^2]: `trezor-user-env-regtest` runs in emulation layer and is not ARM native image, you may experience some slowness or issues when using it on ARM Macs.
----

### Windows

Currently not supported, but should work using docker as well.

## How to develop

In case you need to modify something in trezor-user-env you have two options.

### Natively in NixOS

If you are using NixOS you can do the changes locally and then run the controller yourself. Run it via `nix-shell --run 'poetry run python src/main.py'` (or just `python src/main.py` in `Poetry` shell). Make sure you have run `src/binaries/{firmware,trezord-go}/bin/download.sh` beforehand otherwise you'll have old binaries.

This is suitable for smaller changes or things you can check via the HTML dashboard easily. However, if you are adding some functionality to trezor-user-env mainly because of Suite end-to-end tests, it is probably better to go the CI way (below). Otherwise you would need to run the whole Suite test suite locally.

### Let CI do it

The simpler but less flexible way is to let the GitHub Actions build it. You can create a branch, commit your changes and then push them. The GH Actions will build it for you and tag the appropriate docker image as `test`. You can then modify all scripts/commands and use `ghcr.io/trezor/trezor-user-env:test` instead of `ghcr.io/trezor/trezor-user-env` which defaults to the `latest` tag which equals trezor-user-env's master. Suite's docker-compose files in the `docker` subdirectory are the place where you want to change this.

## Local development against Suite end-to-end tests
_NOTE: The steps below are all dependant on Docker containers. It could be even better to be able to avoid the Docker completely - just running trezor-user-env on localhost and connecting Suite tests to it - but hard to say how to do it, all my experiments failed. Please feel free to improve the solution._

It may be helpful to run Suite e2e tests locally against the local trezor-user-env state, to avoid the need to involve the CI (Gitlab jobs) and the connected pain of merging changes into one branch just to test them.

#### Suite preparation steps:
- [this](https://github.com/trezor/trezor-suite/blob/develop/docs/tests/e2e-web.md) and [this](https://github.com/trezor/trezor-suite/#development) Suite guides should be followed for local Suite setup
- modifying trezor-user-env-unix image in `docker/docker-compose.suite-test.yml` - change it to `test-user-env` (or whatever the local image name will be)

#### Trezor-user-env steps:
- creating two new Dockerfiles, that are not a part of the repository
  - `Dockerfile_base` - exact copy of Dockerfile, but without CMD at the end (serves as a base image for the Dockerfile below, to avoid building it from scratch every time)
  - `Dockerfile_final` - starting from the base image and just copying all the files into it and running the server
- creating a base image - `docker build -f docker/Dockerfile_base -t test-user-env-base .`
- while not satisfied:
  - modify local user-env code
  - build a runnable image - `docker build -f docker/Dockerfile_final -t test-user-env .`
  - run the Suite test container application - `docker/docker-suite-test.sh` (with the appropriate image name in above-mentioned Suite .yml file, instead of the default one)
  - observing traffic in debugging.log file in the running `test-user-env` container - `docker exec $(docker ps | grep 'test-user-env' | awk {'print $1'}) tail -f logs/debugging.log`
  - choosing some test scenario from Cypress window
