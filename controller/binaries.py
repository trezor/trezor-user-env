import glob
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
FIRMWARES = {
    "T1": [],
    "TT": [],
}
SUITES = []
BRIDGES = []


def explore():
    explore_firmwares()
    explore_suites()
    explore_bridges()


def explore_firmwares():
    for fw in glob.glob("firmware/bin/*"):
        if "trezor-emu-core" in fw:
            version = fw.replace("firmware/bin/trezor-emu-core-v", "")
            FIRMWARES["TT"].append(version)
        elif "trezor-emu-legacy" in fw:
            version = fw.replace("firmware/bin/trezor-emu-legacy-v", "")
            FIRMWARES["T1"].append(version)
    for model in FIRMWARES.values():
        model.sort(key=sort_firmwares, reverse=True)


def sort_firmwares(version):
    if "master" in version:
        return 9, 9, 9
    return tuple(int(n) for n in version.split("."))


def explore_suites():
    # TODO automate
    SUITES.append("20.8.1")
    SUITES.append("20.7.1")


def explore_bridges():
    # TODO automate
    BRIDGES.append("2.0.27")
    BRIDGES.append("2.0.26")
    BRIDGES.append("2.0.19")
