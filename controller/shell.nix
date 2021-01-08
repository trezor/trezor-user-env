# the last successful build of nixos-20.09 (stable) as of 2020-10-11
with import
  (builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/0b8799ecaaf0dc6b4c11583a3c96ca5b40fcfdfb.tar.gz";
    sha256 = "11m4aig6cv0zi3gbq2xn9by29cfvnsxgzf9qsvz67qr0yq29ryyz";
  })
{ };

let
  trezorWithoutUdev = ps: ps.trezor.overrideAttrs (oldAttrs: {
    propagatedBuildInputs = with ps; [
      attrs
      click
      construct
      ecdsa
      hidapi
      libusb1
      mnemonic
      pillow
      protobuf
      pyblake2
      requests
      rlp
      shamir-mnemonic
      typing-extensions
    ];
  });
  MyPython = python3.withPackages(ps: [
    ps.termcolor
    # can be replaced with ps.trezor when https://github.com/NixOS/nixpkgs/pull/101847
    # makes it to nixpkgs imported above:
    (if stdenv.isLinux then ps.trezor else trezorWithoutUdev ps)
    ps.black
    ps.isort
    ps.websockets
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
