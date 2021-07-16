import logging
import os
from pathlib import Path

from termcolor import colored

ROOT_DIR = Path(__file__).parent.parent.resolve()
LOG_DIR = ROOT_DIR / "logs"

# Creating log dir here, so it does not need to be included in repository
if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)

LOG_FILENAME = str(LOG_DIR / "debugging.log")

logging.basicConfig(
    filename=LOG_FILENAME,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def log(text: str, color: str = "blue") -> None:
    logging.info(text)
    print(colored(text, color))
