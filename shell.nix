let
  # the last commit from master as of 2025-06-25
  nixpkgsCommit = "992f916556fcfaa94451ebc7fc6e396134bbf5b1";
  nixpkgsSha256 = "0wbqb6sy58q3mnrmx67ffdx8rq10jg4cvh4jx3rrbr1pqzpzsgxc";

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
    (poetry.withPlugins (ps: [ ps.poetry-plugin-shell ]))
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
