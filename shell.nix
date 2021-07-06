with import <nixpkgs> {};

# the last successful build of nixos-21.05 (stable) as of 2021-07-02
with import
  (builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/e9148dc1c30e02aae80cc52f68ceb37b772066f3.tar.gz";
    sha256 = "1xs5all93r3fg4ld13s9lmzri0bgq25d9dydb08caqa7pc10f5ki";
  })
{ };

let
  MyPython = python3.withPackages(ps: [
    ps.termcolor
    ps.trezor
    ps.black
    ps.isort
    ps.mypy
    ps.flake8
  ]);
in
  stdenv.mkDerivation {
    name = "trezor-user-env-controller";
    buildInputs = [
      MyPython
      SDL2
      SDL2_image
      docker
      docker-compose
      xorg.xhost
      wget
    ];
  }
