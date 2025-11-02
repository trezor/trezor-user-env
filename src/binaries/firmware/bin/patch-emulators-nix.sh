#!/bin/bash
#
# Patch emulator binaries for Nix environment
# This script fixes both the interpreter path and rpath for all emulator binaries
# to work with the current Nix environment's library paths.
#
# Usage: Run from trezor-user-env root directory, inside nix-shell
#   nix-shell --command 'src/binaries/firmware/bin/patch-emulators-nix.sh'
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$SCRIPT_DIR"

echo "========================================="
echo "Patching emulator binaries for Nix"
echo "========================================="
echo ""

# Check we're in nix-shell
if [ -z "$IN_NIX_SHELL" ]; then
    echo "ERROR: This script must be run inside nix-shell"
    echo "Please run: nix-shell --command '$0'"
    exit 1
fi

# Check patchelf is available
if ! command -v patchelf &> /dev/null; then
    echo "ERROR: patchelf not found in PATH"
    exit 1
fi

# Step 1: Find current library paths from nix environment
echo "Step 1: Finding library paths in current Nix environment..."

# Use ls instead of find for faster results
LIBJPEG_LIB=$(ls /nix/store/*libjpeg*/lib/libjpeg.so.62 2>/dev/null | head -1)
LIBJPEG=$(dirname "$LIBJPEG_LIB" 2>/dev/null || echo "")

SDL2_LIB=$(ls /nix/store/*SDL2-*/lib/libSDL2-2.0.so.0 2>/dev/null | head -1)
SDL2=$(dirname "$SDL2_LIB" 2>/dev/null || echo "")

SDL2_IMG_LIB=$(ls /nix/store/*SDL2*image*/lib/libSDL2_image-2.0.so.0 2>/dev/null | head -1)
SDL2_IMG=$(dirname "$SDL2_IMG_LIB" 2>/dev/null || echo "")

INTERPRETER=$(patchelf --print-interpreter $(which python) 2>/dev/null || echo "")
GLIBC=$(dirname "$INTERPRETER" 2>/dev/null || echo "")

if [ -z "$LIBJPEG" ] || [ -z "$SDL2" ] || [ -z "$SDL2_IMG" ] || [ -z "$GLIBC" ] || [ -z "$INTERPRETER" ]; then
    echo "ERROR: Could not find required libraries in Nix store"
    echo "LIBJPEG: $LIBJPEG"
    echo "SDL2: $SDL2"
    echo "SDL2_IMG: $SDL2_IMG"
    echo "GLIBC: $GLIBC"
    echo "INTERPRETER: $INTERPRETER"
    exit 1
fi

echo "  ✓ libjpeg:     $LIBJPEG"
echo "  ✓ SDL2:        $SDL2"
echo "  ✓ SDL2_image:  $SDL2_IMG"
echo "  ✓ glibc:       $GLIBC"
echo "  ✓ interpreter: $INTERPRETER"
echo ""

# Step 2: Build new rpath
NEW_RPATH="$LIBJPEG:$SDL2:$SDL2_IMG:$GLIBC"

# Step 3: Patch all emulator binaries
echo "Step 2: Patching emulator binaries..."
echo ""

COUNT=0
FAILED=0

for binary in "$BIN_DIR"/trezor-emu-*; do
    # Skip if not a file or not executable
    if [ ! -f "$binary" ] || [ ! -x "$binary" ]; then
        continue
    fi

    BINARY_NAME=$(basename "$binary")

    # Check if it's an ELF binary
    if ! readelf -h "$binary" &>/dev/null; then
        echo "  ⊗ Skipping $BINARY_NAME (not an ELF file)"
        continue
    fi

    # Patch interpreter
    if ! patchelf --set-interpreter "$INTERPRETER" "$binary" 2>/dev/null; then
        echo "  ✗ Failed to patch interpreter for $BINARY_NAME"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Patch rpath
    if ! patchelf --set-rpath "$NEW_RPATH" "$binary" 2>/dev/null; then
        echo "  ✗ Failed to patch rpath for $BINARY_NAME"
        FAILED=$((FAILED + 1))
        continue
    fi

    COUNT=$((COUNT + 1))

    # Print progress every 10 files
    if [ $((COUNT % 10)) -eq 0 ]; then
        echo "  Patched $COUNT binaries..."
    fi
done

echo ""
echo "========================================="
echo "Summary:"
echo "  ✓ Successfully patched: $COUNT binaries"
if [ $FAILED -gt 0 ]; then
    echo "  ✗ Failed: $FAILED binaries"
fi
echo "========================================="

# Verify one binary works
echo ""
echo "Verification: Checking a sample binary..."
SAMPLE_BINARY="$BIN_DIR/trezor-emu-core-T3T1-v2.9.0"
if [ -f "$SAMPLE_BINARY" ]; then
    echo ""
    echo "Libraries for $(basename $SAMPLE_BINARY):"
    ldd "$SAMPLE_BINARY" 2>&1 | grep -E "(libjpeg|SDL2)" || true
    echo ""
    echo "Testing if binary runs..."
    if "$SAMPLE_BINARY" --help &>/dev/null; then
        echo "  ✓ Binary runs successfully!"
    else
        echo "  ⚠ Binary may have issues (check manually)"
    fi
else
    echo "  (Sample binary not found, skipping verification)"
fi

echo ""
echo "Done! All emulator binaries have been patched."
