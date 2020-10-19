# the last successful build of nixos-20.09 (stable) as of 2020-10-11
with import
  (builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/0b8799ecaaf0dc6b4c11583a3c96ca5b40fcfdfb.tar.gz";
    sha256 = "11m4aig6cv0zi3gbq2xn9by29cfvnsxgzf9qsvz67qr0yq29ryyz";
  })
{ };

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
