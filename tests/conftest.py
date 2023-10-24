"""
Pytest configuration file defining some useful functionality.
"""

from typing import TYPE_CHECKING

import pytest
import websockets

from . import controller_test

if TYPE_CHECKING:
    from _pytest.config.argparsing import Parser


def pytest_addoption(parser: "Parser"):
    """Adding CLI options."""
    parser.addoption(
        "--controller-already-runs",
        action="store_true",
        default=False,
        help="Chosen when the controller is already running and we should not spawn it again.",
    )


def pytest_sessionstart(session: pytest.Session):
    """What should run before all the tests start."""
    # When the controller is not running, spawning it
    if session.config.getoption("controller_already_runs"):
        print("\nController already runs, not touching it")
    else:
        print("\nStarting controller before tests")
        controller_test.start_controller()


def pytest_sessionfinish(session: pytest.Session, exitstatus: pytest.ExitCode):
    """What should run after all the tests are finished."""
    # When the controller was spawned by us, killing it
    if session.config.getoption("controller_already_runs"):
        print("\nController was already running, not touching it")
    else:
        print("\nKilling the controller after all tests")
        controller_test.shutdown_controller()


@pytest.fixture(scope="function")
async def websocket():
    """Injecting a websocket connection to test functions."""
    # TODO: ws connection could be somehow cached, but I tried it through a
    # global variable and it was not successful
    async with websockets.connect(controller_test.URL) as ws:
        # Catching the welcome message, so that it can be immediately used
        await ws.recv()
        yield ws
