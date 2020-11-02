FROM nixos/nix

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

RUN nix-shell "controller/shell.nix" --run "python --version"
RUN nix-shell "controller/shell.nix" --run "trezorctl --version"

# TODO: entrypoint for nix-shell?

RUN nix-shell --run "./firmware/bin/download.sh"
RUN nix-shell --run "./trezord-go/bin/download.sh"
RUN nix-shell --run "./suite/bin/download.sh"

RUN rm -rf /var/tmp/trezor.flash

CMD nix-shell controller/shell.nix --run 'python controller/main.py'
