let
  # the last successful build of nixpkgs-unstable as of 2022-06-20
  nixpkgsCommit = "e0a42267f73ea52adc061a64650fddc59906fc99";
  nixpkgsSha256 = "0r1dsj51x2rm016xwvdnkm94v517jb1rpn4rk63k6krc4d0n3kh9";

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
    autoPatchelfHook
    python39
    poetry
    SDL2
    SDL2_image
    xorg.xhost
    wget
    git
    unzip
    curl
    procps
  ];
}
