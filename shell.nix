let
  # the last commit from master as of 2025-09-23
  nixpkgsCommit = "7ea43b194fff615fe75741cf258988d6571623e0";
  nixpkgsSha256 = "09nbk2q4w3v8x3v4r2y2s7v3nk8n4wqzxgykkp7na9bhijry2zla";

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
    python311
    uv
    sdl3
    sdl3-image
    SDL2
    SDL2_image
    xorg.xhost
    xorg.xorgserver # Xvfb
    x11vnc
    xdotool
    python311Packages.websockify
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
