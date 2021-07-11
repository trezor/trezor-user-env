import logging
from pathlib import Path

from termcolor import colored

ROOT_DIR = Path(__file__).parent.parent.resolve()

LOG_FILENAME = str(ROOT_DIR / "debugging.log")

logging.basicConfig(
    filename=LOG_FILENAME,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def log(text: str, color: str = "blue") -> None:
    logging.info(text)
    print(colored(text, color))
