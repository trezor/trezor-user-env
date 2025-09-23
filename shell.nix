let
  # the last commit from master as of 2025-09-23
  nixpkgsCommit = "7ea43b194fff615fe75741cf258988d6571623e0";
  nixpkgsSha256 = "09nbk2q4w3v8x3v4r2y2s7v3nk8n4wqzxgykkp7na9bhijry2zla";

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
    uv
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
