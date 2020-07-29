# the last successful build of nixos-unstable - 2020-07-01
with import (builtins.fetchTarball https://github.com/NixOS/nixpkgs/archive/55668eb671b915b49bcaaeec4518cc49d8de0a99.tar.gz) {};

let
  MyPython = python3.withPackages(ps: [
    ps.termcolor
    ps.trezor
    ps.black
    ps.isort
  ]);
in
  stdenv.mkDerivation {
    name = "trezor-user-env-controller";
    buildInputs = [
      MyPython
    ];
  }
