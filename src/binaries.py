import glob
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from termcolor import colored

ROOT_DIR = Path(__file__).parent.parent.resolve()
FIRMWARES: Dict[str, List[str]] = {
    "T1": [],
    "TT": [],
}
BRIDGES: List[str] = []

IS_ARM = os.uname().machine.startswith("aarch64")
ARM_IDENTIFIER = "-arm"


def explore(args: Any) -> None:
    explore_firmwares(args)
    explore_bridges()


def explore_firmwares(args: Any) -> None:
    firmware_binary_files = str(ROOT_DIR / "src/binaries/firmware/bin/*")
    if args.verbosity > 0:
        print(f"Scanning {colored(firmware_binary_files, 'yellow')}")

    # Analyzing all potential emulator files and gathering their versions
    #   (version is located at the end, after emulator identifier and '-v')
    identifier_TT = "trezor-emu-core"
    identifier_T1 = "trezor-emu-legacy"
    for fw in glob.glob(firmware_binary_files):
        # Send only suitable emulators for ARM/non-ARM
        if IS_ARM and not fw.endswith(ARM_IDENTIFIER):
            print(f"On ARM, ignoring x86 emulator - {fw}")
            continue
        elif not IS_ARM and fw.endswith(ARM_IDENTIFIER):
            print(f"On x86, ignoring ARM emulator - {fw}")
            continue

        if identifier_TT in fw:
            version = fw.split(identifier_TT + "-v")[-1]
            FIRMWARES["TT"].append(version)
        elif identifier_T1 in fw:
            version = fw.split(identifier_T1 + "-v")[-1]
            FIRMWARES["T1"].append(version)
        else:
            if args.verbosity > 0:
                print(f"  skipping {colored(fw, 'yellow')}")
            continue

        if args.verbosity > 0:
            print(f"  found {colored(fw, 'yellow')} => {colored(version, 'magenta')}")

    for model in FIRMWARES.values():
        model.sort(key=sort_firmwares, reverse=True)


def sort_firmwares(version: str) -> Tuple[int, ...]:
    # Having master and url versions as the first one in the list
    if "master" in version or "url" in version:
        return 99, 99, 99

    # Removing the possible ARM-related suffix just for sorting, wont rename the file
    if version.endswith(ARM_IDENTIFIER):
        version = version[: -len(ARM_IDENTIFIER)]

    return tuple(int(n) for n in version.split("."))


def explore_bridges() -> None:
    # Send only suitable bridges for ARM/non-ARM
    if IS_ARM:
        BRIDGES.append(f"2.0.31{ARM_IDENTIFIER}")
        BRIDGES.append(f"2.0.30{ARM_IDENTIFIER}")
    else:
        BRIDGES.append("2.0.31")
        BRIDGES.append("2.0.27")
        BRIDGES.append("2.0.26")
        BRIDGES.append("2.0.19")
