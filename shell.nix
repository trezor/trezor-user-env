with import <nixpkgs> {};

# the last successful build of nixpkgs-unstable as of 2021-11-18
with import
  (builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/7fad01d9d5a3f82081c00fb57918d64145dc904c.tar.gz";
    sha256 = "0g0jn8cp1f3zgs7xk2xb2vwa44gb98qlp7k0dvigs0zh163c2kim";
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
    ps.websockets
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
      git
    ];
  # NIX_PATH needed for autoPatchelfHook nix-shells in download.sh scripts
  shellHook = ''
    export NIX_PATH="nixpkgs=https://github.com/NixOS/nixpkgs/archive/7fad01d9d5a3f82081c00fb57918d64145dc904c.tar.gz"
  '';
}
