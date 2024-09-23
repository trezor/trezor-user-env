let
  # the last commit from master as of 2024-04-02
  nixpkgsCommit = "0b1fa3a2a11c334cfe3c44bcf285599e34018799";
  nixpkgsSha256 = "12vjrwysfwyk7chplx57vq010f1vdz6sy94ai0kc90kkbvblgr6d";

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
    python311
    poetry
    SDL2
    SDL2_image
    xorg.xhost
    wget
    git
    curl
    nodejs # for node bridge
    procps
  ];
}
