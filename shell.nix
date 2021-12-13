let
  # the last successful build of nixpkgs-unstable as of 2021-11-18
  nixpkgsCommit = "7fad01d9d5a3f82081c00fb57918d64145dc904c";
  nixpkgsSha256 = "0g0jn8cp1f3zgs7xk2xb2vwa44gb98qlp7k0dvigs0zh163c2kim";

  nixpkgsUrl = "https://github.com/NixOS/nixpkgs/archive/${nixpkgsCommit}.tar.gz";
in
with import
  (builtins.fetchTarball {
    url = nixpkgsUrl;
    sha256 = nixpkgsSha256;
  }) { };
stdenv.mkDerivation {
  name = "trezor-user-env-controller";
  buildInputs = [
    python39
    poetry
    SDL2
    SDL2_image
    docker
    docker-compose
    xorg.xhost
    wget
    git
  ];
  # NIX_PATH needed for autoPatchelfHook nix-shells in download.sh scripts
  NIX_PATH = "nixpkgs=${nixpkgsUrl}";
}
