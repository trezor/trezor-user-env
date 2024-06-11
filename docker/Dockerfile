# install the latest Alpine linux from scratch

FROM scratch
ARG ALPINE_VERSION=3.15.0
ARG ALPINE_ARCH=x86_64
ADD docker/alpine-minirootfs-${ALPINE_VERSION}-${ALPINE_ARCH}.tar.gz /
# http://dl-cdn.alpinelinux.org/alpine/edge/releases/x86_64/alpine-minirootfs-3.15.0-x86_64.tar.gz

# the following is adapted from https://github.com/NixOS/docker/blob/master/Dockerfile

# Enable HTTPS support in wget and set nsswitch.conf to make resolution work within containers
RUN apk add --no-cache --update openssl \
  && echo hosts: files dns > /etc/nsswitch.conf
# Add basic packages
RUN apk update && apk add bash git python3

# Download Nix and install it into the system.
# https://nixos.org/releases/nix/nix-2.4/nix-2.4-x86_64-linux.tar.xz
ARG NIX_VERSION=2.4
RUN wget https://nixos.org/releases/nix/nix-${NIX_VERSION}/nix-${NIX_VERSION}-${ALPINE_ARCH}-linux.tar.xz \
  && tar xf nix-${NIX_VERSION}-${ALPINE_ARCH}-linux.tar.xz \
  && addgroup -g 30000 -S nixbld \
  && for i in $(seq 1 30); do adduser -S -D -h /var/empty -g "Nix build user $i" -u $((30000 + i)) -G nixbld nixbld$i ; done \
  && mkdir -m 0755 /etc/nix \
  && echo 'sandbox = false' > /etc/nix/nix.conf \
  && mkdir -m 0755 /nix && USER=root sh nix-${NIX_VERSION}-${ALPINE_ARCH}-linux/install \
  && ln -s /nix/var/nix/profiles/default/etc/profile.d/nix.sh /etc/profile.d/ \
  && rm -r /nix-${NIX_VERSION}-${ALPINE_ARCH}-linux* \
  && rm -rf /var/cache/apk/* \
  && /nix/var/nix/profiles/default/bin/nix-collect-garbage --delete-old \
  && /nix/var/nix/profiles/default/bin/nix-store --optimise \
  && /nix/var/nix/profiles/default/bin/nix-store --verify --check-contents

ENV \
    USER=root \
    PATH=/nix/var/nix/profiles/default/bin:/nix/var/nix/profiles/default/sbin:/bin:/sbin:/usr/bin:/usr/sbin \
    GIT_SSL_CAINFO=/etc/ssl/certs/ca-certificates.crt \
    NIX_SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    NIX_PATH=/nix/var/nix/profiles/per-user/root/channels

# ####################################
# Trezor specific stuff starts here
# ####################################

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

RUN nix-shell --run "poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR" \
  && nix-shell --run "./src/binaries/firmware/bin/download.sh" \
  && nix-shell --run "./patch_emulators.sh src/binaries/firmware/bin" \
  && nix-shell --run "./src/binaries/trezord-go/bin/download.sh"

CMD nix-shell --run "./run-nix.sh"
