import logging
import os
from pathlib import Path

from termcolor import colored  # type: ignore

ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT_DIR / "logs"

PHYSICAL_TREZOR_ENV = "PHYSICAL_TREZOR"
TRUE_VAL = "1"

# Creating log dir here, so it does not need to be included in repository
if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)

LOG_FILENAME = str(LOG_DIR / "debugging.log")
EMU_BRIDGE_LOG = str(LOG_DIR / "emulator_bridge.log")


logging.basicConfig(
    filename=LOG_FILENAME,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def log(text: str, color: str = "blue") -> None:
    logging.info(text)
    print(colored(text, color))


def physical_trezor() -> bool:
    """Whether we should support physical Trezor."""
    return os.environ.get(PHYSICAL_TREZOR_ENV, "") == TRUE_VAL
