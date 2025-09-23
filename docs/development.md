# Development

## How to develop

In case you need to modify something in trezor-user-env you have two options.

### Natively in NixOS

If you are using NixOS you can do the changes locally and then run the controller yourself. Run it via `nix-shell --run 'uv run python src/main.py'`. Make sure you have run `src/binaries/{firmware,trezord-go}/bin/download.sh` beforehand otherwise you'll have old binaries.

This is suitable for smaller changes or things you can check via the HTML dashboard easily. However, if you are adding some functionality to trezor-user-env mainly because of Suite end-to-end tests, it is probably better to go the CI way (below). Otherwise you would need to run the whole Suite test suite locally.

### Let CI do it

The simpler but less flexible way is to let the GitHub Actions build it. You can create a branch, commit your changes and then push them. The GH Actions will build it for you and tag the appropriate docker image as `test`. You can then modify all scripts/commands and use `ghcr.io/trezor/trezor-user-env:test` instead of `ghcr.io/trezor/trezor-user-env` which defaults to the `latest` tag which equals trezor-user-env's master. Suite's docker-compose files in the `docker` subdirectory are the place where you want to change this.

## Local development against Suite end-to-end tests

_NOTE: The steps below are all dependant on Docker containers. It could be even better to be able to avoid the Docker completely - just running trezor-user-env on localhost and connecting Suite tests to it - but hard to say how to do it, all my experiments failed. Please feel free to improve the solution._

It may be helpful to run Suite e2e tests locally against the local trezor-user-env state, to avoid the need to involve the CI (Gitlab jobs) and the connected pain of merging changes into one branch just to test them.

#### Suite preparation steps:
- [this](https://github.com/trezor/trezor-suite/blob/develop/docs/tests/e2e-web.md) and [this](https://github.com/trezor/trezor-suite/#development) Suite guides should be followed for local Suite setup
- modifying trezor-user-env-unix image in `docker/docker-compose.suite-test.yml` - change it to `test-user-env` (or whatever the local image name will be)

#### `trezor-user-env` steps:
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
