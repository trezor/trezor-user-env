with import <nixpkgs> {};

stdenv.mkDerivation {
  name = "trezor-user-env";
  buildInputs = [
    docker
    docker-compose
    xorg.xhost
    SDL2
    SDL2_image
    wget
  ];
}
