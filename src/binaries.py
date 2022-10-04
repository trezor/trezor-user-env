import os
import subprocess
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Literal, Tuple

from termcolor import colored

ROOT_DIR = Path(__file__).resolve().parent.parent
FIRMWARE_BIN_DIR = ROOT_DIR / "src/binaries/firmware/bin"
USER_DOWNLOADED_DIR = FIRMWARE_BIN_DIR / "user_downloaded"
USER_DOWNLOADED_DIR.mkdir(exist_ok=True)

Model = Literal["1", "2", "R"]
FIRMWARES: Dict[Model, Dict[str, str]] = {
    "1": OrderedDict(),
    "2": OrderedDict(),
    "R": OrderedDict(),
}

BRIDGES: List[str] = []

IS_ARM = os.uname().machine.startswith("aarch64")
ARM_IDENTIFIER = "-arm"

IDENTIFIER_T1 = "trezor-emu-legacy-v"
IDENTIFIER_TT = "trezor-emu-core-v"
IDENTIFIER_TR = "trezor-emu-core-R-v"


def register_new_firmware(model: Model, version: str, location: str) -> None:
    FIRMWARES[model][version] = location


def get_firmware_location(model: Model, version: str) -> str:
    return FIRMWARES[model][version]


def get_all_firmware_versions() -> dict[Model, list[str]]:
    return {k: list(v.keys()) for k, v in FIRMWARES.items()}


def get_latest_release_version(model: Model) -> str:
    # Last index is the current master
    return list(FIRMWARES[model].keys())[1]


def get_master_version(model: Model) -> str:
    return list(FIRMWARES[model].keys())[0]


def check_model(model: str) -> None:
    supported_models = FIRMWARES.keys()
    if model not in supported_models:
        raise RuntimeError(f"Unknown model {model} - supported are {supported_models}")


def _print_in_verbose(text: str, args: Any) -> None:
    if args.verbosity > 0:
        print(text)


def explore(args: Any) -> None:
    explore_firmwares(args)
    explore_bridges()


def explore_firmwares(args: Any) -> None:
    _print_in_verbose(f"Scanning {colored(str(FIRMWARE_BIN_DIR), 'yellow')}", args)

    # Analyzing all potential emulator files and gathering their versions
    #   (version is located at the end, after emulator identifier)
    for fw_file in FIRMWARE_BIN_DIR.rglob("*"):
        fw = fw_file.name

        # Send only suitable emulators for ARM/non-ARM
        if IS_ARM and not fw.endswith(ARM_IDENTIFIER):
            _print_in_verbose(f"On ARM, ignoring x86 emulator - {fw}", args)
            continue
        elif not IS_ARM and fw.endswith(ARM_IDENTIFIER):
            _print_in_verbose(f"On x86, ignoring ARM emulator - {fw}", args)
            continue

        if IDENTIFIER_TR in fw:
            model: Model = "R"
            version = fw.split(IDENTIFIER_TR)[-1]
        elif IDENTIFIER_TT in fw:
            model = "2"
            version = fw.split(IDENTIFIER_TT)[-1]
        elif IDENTIFIER_T1 in fw:
            model = "1"
            version = fw.split(IDENTIFIER_T1)[-1]
        else:
            _print_in_verbose(f"  skipping {colored(fw, 'yellow')}", args)
            continue

        # Registering the found firmware and saving its absolute location
        register_new_firmware(model, version, fw_file.absolute().as_posix())

        _print_in_verbose(
            f"  found {colored(fw, 'yellow')} => {colored(version, 'magenta')}", args
        )

    # Sorting the model versions according to their numerical value
    for model_name, model_info in FIRMWARES.items():
        FIRMWARES[model_name] = OrderedDict(
            sorted(
                model_info.items(),
                key=lambda item: sort_firmwares(item[0]),
                reverse=True,
            )
        )


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
        BRIDGES.append(f"2.0.32{ARM_IDENTIFIER}")
        BRIDGES.append(f"2.0.31{ARM_IDENTIFIER}")
        BRIDGES.append(f"2.0.30{ARM_IDENTIFIER}")
    else:
        BRIDGES.append("2.0.32")
        BRIDGES.append("2.0.31")
        BRIDGES.append("2.0.27")
        BRIDGES.append("2.0.26")
        BRIDGES.append("2.0.19")


def patch_emulators_for_nix(dir_to_patch: str = "") -> None:
    """Make sure all the emulators can be run in Nix environment.

    When for some reason the script fails, it does not raise
    any python exception.
    That is on purpose, because it might be run in a non-Nix
    environment.
    """
    cmd = ["./patch_emulators.sh", dir_to_patch]
    subprocess.run(cmd, cwd=ROOT_DIR)
