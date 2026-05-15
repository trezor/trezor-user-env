let
  # the last commit from master as of 2026-03-15
  nixpkgsCommit = "a07d4ce6bee67d7c838a8a5796e75dff9caa21ef";
  nixpkgsSha256 = "0f6zni3jn6ji5icwbidbpmcgxdal2qnjszp7ragdcy0857hvq3c5";

  nixpkgsUrl = "https://github.com/NixOS/nixpkgs/archive/${nixpkgsCommit}.tar.gz";

  pkgs = import
    (builtins.fetchTarball {
      url = nixpkgsUrl;
      sha256 = nixpkgsSha256;
    }) { };

  novnc = pkgs.fetchFromGitHub {
    owner = "novnc";
    repo = "noVNC";
    rev = "v1.5.0";
    sha256 = "sha256-3Q87bYsC824/8A85Kxdqlm+InuuR/D/HjVrYTJZfE9Y=";
  };
in
with pkgs;
stdenv.mkDerivation {
  name = "trezor-user-env-controller";
  buildInputs = [
    autoPatchelfHook
    python312
    uv
    sdl3
    sdl3-image
    SDL2
    SDL2_image
    xhost
    xorg-server # Xvfb
    x11vnc
    xdotool
    python312Packages.websockify
    wget
    git
    curl
    nodejs # for node bridge
    procps
  ];
  shellHook = ''
    # Build a writable noVNC web root with our custom viewer
    NOVNC_LOCAL="$PWD/.novnc"
    if [ ! -d "$NOVNC_LOCAL/core" ]; then
      mkdir -p "$NOVNC_LOCAL"
      ln -sf ${novnc}/core "$NOVNC_LOCAL/core"
      ln -sf ${novnc}/vendor "$NOVNC_LOCAL/vendor"
      cp "$PWD/src/vnc_embed.html" "$NOVNC_LOCAL/vnc_embed.html"
    fi
    export NOVNC_WEB="$NOVNC_LOCAL"
  '';
}
