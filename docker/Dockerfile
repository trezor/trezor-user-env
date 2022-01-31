FROM vdovhanych/nixos

# "fake" dbus address to prevent errors
# https://github.com/SeleniumHQ/docker-selenium/issues/87
#ENV DBUS_SESSION_BUS_ADDRESS=/dev/null

# good colors for most applications
ENV TERM xterm

# trezor emu
ENV XDG_RUNTIME_DIR "/var/tmp"

# trezorctl https://click.palletsprojects.com/en/7.x/python3/
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

# copy python websocket server and all binaries
COPY ./ ./trezor-user-env

WORKDIR ./trezor-user-env

RUN ls /
RUN ls /trezor-user-env

# updates the nix-channel to have latest changes
RUN nix-channel --update
RUN nix-shell --run "./src/binaries/firmware/bin/download.sh"
RUN nix-shell --run "./src/binaries/trezord-go/bin/download.sh"

RUN nix-shell --run "./docker/create_version_file.sh"

RUN rm -rf /var/tmp/trezor.flash

RUN nix-shell --run "echo deps pre-installed"

RUN nix-shell --run "poetry install"

CMD nix-shell --run './run.sh'
