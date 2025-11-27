import argparse
import atexit
import os

import binaries
import bridge
import controller
import dashboard
import emulator
import helpers
import tropic_model


def cleanup() -> None:
    emulator.stop()
    bridge.stop()
    tropic_model.stop()


atexit.register(cleanup)

LOG_COLOR = "cyan"


def log(text: str, color: str = LOG_COLOR) -> None:
    helpers.log(f"MAIN: {text}", color)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbosity", action="count", default=0)
    parser.add_argument("--work-dir")
    args = parser.parse_args()

    effective_work_dir = args.work_dir

    if effective_work_dir is None and "TREZOR_USER_ENV_WORK_DIR" in os.environ:
        effective_work_dir = os.environ["TREZOR_USER_ENV_WORK_DIR"]

    if effective_work_dir is None:
        effective_work_dir = "."

    effective_work_dir = os.path.abspath(os.path.expanduser(effective_work_dir))

    os.chdir(effective_work_dir)
    log(f"Working from {os.getcwd()}")

    binaries.explore(args)
    dashboard.start()

    if helpers.physical_trezor():
        log("Will support physical Trezor.")
    else:
        log(
            f"Will support emulator. Set {helpers.PHYSICAL_TREZOR_ENV}={helpers.TRUE_VAL} "
            "env var to enable physical Trezor support."
        )

    controller.start()
