import argparse
import atexit
import os

import binaries
import bridge
import dashboard
import emulator

import controller

import suite


def cleanup():
    emulator.stop()
    bridge.stop()


atexit.register(cleanup)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbosity", action="count", default=0)
    parser.add_argument("--work-dir")
    parser.add_argument("--disable-bridge-proxy", action="store_true")
    args = parser.parse_args()

    effective_work_dir = args.work_dir

    if effective_work_dir is None and "TREZOR_USER_ENV_WORK_DIR" in os.environ:
        effective_work_dir = os.environ["TREZOR_USER_ENV_WORK_DIR"]

    if effective_work_dir is None:
        effective_work_dir = "."

    effective_work_dir = os.path.abspath(os.path.expanduser(effective_work_dir))

    os.chdir(effective_work_dir)
    print(f"Working from {os.getcwd()}")

    binaries.explore(args)
    dashboard.start()

    if args.disable_bridge_proxy:
        print(
            "Bridge proxy disabled. "
            "Communication with Bridge needs to be done directly."
        )
    else:
        controller.BRIDGE_PROXY = True

    controller.start()
