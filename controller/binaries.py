import glob
from pathlib import Path
from termcolor import colored

ROOT_DIR = Path(__file__).parent.parent.resolve()
FIRMWARES = {
    "T1": [],
    "TT": [],
}
SUITES = []
BRIDGES = []


def explore(args):
    explore_firmwares(args)
    explore_suites()
    explore_bridges()


def explore_firmwares(args):
    scan_glob = "firmware/bin/*"
    if args.verbosity > 0:
        print("Scanning {}".format(colored(scan_glob, "yellow")))
    for fw in glob.glob(scan_glob):
        if "trezor-emu-core" in fw:
            version = fw.replace("firmware/bin/trezor-emu-core-v", "")
            FIRMWARES["TT"].append(version)
            if args.verbosity > 0:
                print(
                    "  found {} => {}".format(
                        colored(fw, "yellow"), colored(version, "magenta")
                    )
                )
        elif "trezor-emu-legacy" in fw:
            version = fw.replace("firmware/bin/trezor-emu-legacy-v", "")
            FIRMWARES["T1"].append(version)
            if args.verbosity > 0:
                print(
                    "  found {} => {}".format(
                        colored(fw, "yellow"), colored(version, "magenta")
                    )
                )
        else:
            if args.verbosity > 0:
                print("  skipping {}".format(colored(fw, "yellow")))

    for model in FIRMWARES.values():
        model.sort(key=sort_firmwares, reverse=True)


def sort_firmwares(version):
    if "master" in version:
        return 0, 0, 0
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
