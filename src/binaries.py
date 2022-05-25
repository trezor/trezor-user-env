import glob
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from termcolor import colored

ROOT_DIR = Path(__file__).resolve().parent.parent
FIRMWARES: Dict[str, List[str]] = {
    "T1": [],
    "TT": [],
    "TR": [],
}
BRIDGES: List[str] = []

IS_ARM = os.uname().machine.startswith("aarch64")
ARM_IDENTIFIER = "-arm"

IDENTIFIER_T1 = "trezor-emu-legacy-v"
IDENTIFIER_TT = "trezor-emu-core-v"
IDENTIFIER_TR = "trezor-emu-core-R-v"


def _print_in_verbose(text: str, args: Any) -> None:
    if args.verbosity > 0:
        print(text)


def explore(args: Any) -> None:
    explore_firmwares(args)
    explore_bridges()


def explore_firmwares(args: Any) -> None:
    firmware_binary_files = str(ROOT_DIR / "src/binaries/firmware/bin/*")
    _print_in_verbose(f"Scanning {colored(firmware_binary_files, 'yellow')}", args)

    # Analyzing all potential emulator files and gathering their versions
    #   (version is located at the end, after emulator identifier)
    for fw in glob.glob(firmware_binary_files):
        # Send only suitable emulators for ARM/non-ARM
        if IS_ARM and not fw.endswith(ARM_IDENTIFIER):
            _print_in_verbose(f"On ARM, ignoring x86 emulator - {fw}", args)
            continue
        elif not IS_ARM and fw.endswith(ARM_IDENTIFIER):
            _print_in_verbose(f"On x86, ignoring ARM emulator - {fw}", args)
            continue

        if IDENTIFIER_TR in fw:
            version = fw.split(IDENTIFIER_TR)[-1]
            FIRMWARES["TR"].append(version)
        elif IDENTIFIER_TT in fw:
            version = fw.split(IDENTIFIER_TT)[-1]
            FIRMWARES["TT"].append(version)
        elif IDENTIFIER_T1 in fw:
            version = fw.split(IDENTIFIER_T1)[-1]
            FIRMWARES["T1"].append(version)
        else:
            _print_in_verbose(f"  skipping {colored(fw, 'yellow')}", args)
            continue

        _print_in_verbose(
            f"  found {colored(fw, 'yellow')} => {colored(version, 'magenta')}", args
        )

    for model in FIRMWARES.values():
        model.sort(key=sort_firmwares, reverse=True)


def sort_firmwares(version: str) -> Tuple[int, ...]:
    # Having master and url versions as the first one in the list
    if "master" in version:
        return 99, 99, 99
    elif "url" in version:
        return 88, 88, 88

    # Removing the possible ARM-related suffix just for sorting, wont rename the file
    if version.endswith(ARM_IDENTIFIER):
        version = version[: -len(ARM_IDENTIFIER)]

    # When the version is not \d+.\d+.\d+, make it be just below master and URL versions,
    # so that it is well visible in the dashboard (is a custom user version)
    try:
        return tuple(int(n) for n in version.split("."))
    except ValueError:
        return 77, 77, 77


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
