# TODO pin for 2020-09 stable when relased
with import <nixpkgs> {};

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
      SDL2
      SDL2_image
    ];
  }
