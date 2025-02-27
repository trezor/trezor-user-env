#!/bin/bash

SYSTEM_ARCH=$(uname -m)
echo "System architecture: $SYSTEM_ARCH"

# Use the first argument as BINARY_DIR if provided; otherwise, default to './'
BINARY_DIR="${1:-./}"

# ./src/binaries/firmware/bin/patch-bin.sh ./src/binaries/firmware/bin/
if [ -n "$IN_NIX_SHELL" ]; then
    nix-shell --run "autoPatchelf ${BINARY_DIR}trezor-emu-*"
    exit
fi

if [[ "$SYSTEM_ARCH" == "x86_64" ]]; then
    INTERPRETER_DEFAULT="/lib64/ld-linux-x86-64.so.2"
elif [[ "$SYSTEM_ARCH" == "aarch64" || "$SYSTEM_ARCH" == "arm64" ]]; then
    INTERPRETER_DEFAULT="/lib/ld-linux-aarch64.so.1"
else
    echo "Unknown system architecture: $SYSTEM_ARCH"
    exit 1
fi

get_interpreter() {
    local arch="$1"
    case "$arch" in
        "Advanced Micro Devices X86-64"|"x86-64")
            echo "/lib64/ld-linux-x86-64.so.2"
            ;;
        "AArch64")
            echo "/lib/ld-linux-aarch64.so.1"
            ;;
        *)
            echo "Unknown architecture: $arch"
            return 1
            ;;
    esac
}

change_interpreter() {
    local binary="$1"
    local arch current_interpreter new_interpreter

    if ! readelf -h "$binary" &>/dev/null; then
        echo "Skipping $binary: Not an ELF file."
        return
    fi

    arch=$(readelf -h "$binary" | awk -F: '/Machine:/ {print $2}' | xargs)
    echo "Detected architecture for $binary: $arch"

    new_interpreter=$(get_interpreter "$arch")

    if [[ $? -ne 0 || -z "$new_interpreter" ]]; then
        echo "Skipping $binary: Unsupported or unknown architecture."
        return
    fi

    current_interpreter=$(patchelf --print-interpreter "$binary" 2>/dev/null)
    echo "Current interpreter for $binary: $current_interpreter"

    if [[ $? -eq 0 && "$current_interpreter" != "$new_interpreter" ]]; then
        echo "Patching $binary (arch: $arch, old: $current_interpreter, new: $new_interpreter)"
        patchelf --set-interpreter "$new_interpreter" "$binary"
    else
        echo "No need to patch $binary."
    fi
}

export -f change_interpreter
export -f get_interpreter
export INTERPRETER_DEFAULT

find "$BINARY_DIR" -type f -executable -exec bash -c 'change_interpreter "$0"' {} \;

echo "All binaries patched."
