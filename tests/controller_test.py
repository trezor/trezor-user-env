import asyncio
import json
import os
import subprocess
import time
from pathlib import Path

import pytest
import websockets
from psutil import Popen

ROOT_DIR = Path(__file__).absolute().parent.parent.resolve()

PORT = 9001
HOST = "localhost"
URL = f"ws://{HOST}:{PORT}"

BRIDGE_TO_TEST = "2.0.31"
EMU_TO_TEST_TT = "2-master"
EMU_TO_TEST_T1 = "1-master"

# So that the async tests are understood by pytest
pytestmark = pytest.mark.asyncio

# The "vectors" here should/must be executed in this exact order
# We are spawning the bridge and emulator at the beginning to test `background-check`
# and then all possible emulator commands that would not work without
# running and setup emulator
commands_success = [
    {"type": "ping"},
    {"type": "log", "text": "abc"},
    {"type": "bridge-start", "version": BRIDGE_TO_TEST},
    {"type": "emulator-start", "version": EMU_TO_TEST_TT, "wipe": True},
    {"type": "background-check"},
    {
        "type": "emulator-setup",
        "mnemonic": " ".join(["all"] * 12),
        "pin": "1234",
        "passphrase_protection": False,
        "label": "My Trevor",
    },
    {"type": "emulator-apply-settings", "label": "label"},
    {"type": "emulator-press-yes"},
    {"type": "emulator-press-no"},
    {"type": "emulator-input", "value": "all all all..."},
    {"type": "emulator-click", "x": 123, "y": 121},
    {"type": "emulator-allow-unsafe-paths"},
    {"type": "emulator-select-num-of-words", "num": 12},
    {"type": "emulator-swipe", "direction": "down"},
    {"type": "emulator-wipe"},
    {"type": "emulator-reset-device"},
    {"type": "emulator-get-debug-state"},
    {"type": "emulator-stop"},
    {"type": "bridge-stop"},
]

# These could be run in any order, they are not dependent on each other
commands_failure = [
    {"type": "pong"},  # unexisting general command
    {"type": "bridge-explode"},  # unexisting bridge command
    {"type": "emulator-show-seed"},  # unexisting emulator command
    {"type": "log", "string": "key should be text not string"},  # bad key
    {
        "type": "emulator-start",
        "version": "2-notexisting",
        "wipe": True,
    },  # unexisting emulator
    {
        "type": "emulator-start",
        "version": "1-notexisting",
    },  # unexisting emulator
    {
        "type": "bridge-start",
        "version": "2.0.unexisting",
    },  # unexisting bridge
    {"type": "emulator-press-yes"},  # no running emulator
]


def start_controller() -> None:
    """Running the controller on the background.

    Luckily, we do not have to care about killing the
    thread/process/whatever-spawned-it, as the controller
    can be killed from any client with `{"type": "exit"}` message
    """
    # WARNING: yes, it is ugly, but I tried some things with multithreading
    # and multiprocessing and they either did not work or had some disadvantages
    # The closest attempt `multiprocessing.Process(target=controller.start).start()`
    # was spamming the console with controller logs, which we probably do not want

    controller = Popen(
        f"python {ROOT_DIR}/src/main.py",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    print(f"Controller spawned: {controller}. CMD: {controller.cmdline()}")

    time.sleep(2)

    # Verifying if the controller is really running
    if not controller.is_running():
        raise RuntimeError(f"Controller {controller} is unable to run!")


def shutdown_controller() -> None:
    """Making sure the controller will stop."""

    async def _shutdown_controller() -> None:
        async with websockets.connect(URL) as websocket:  # type: ignore [attr-defined]
            payload = {"type": "exit"}
            await websocket.send(json.dumps(payload))

    asyncio.get_event_loop().run_until_complete(_shutdown_controller())


async def _test_start_stop(websocket, component: str, version: str) -> None:
    """Making sure emulator/bridge can be successfully started and stopped."""
    background_check_payload = {"type": "background-check"}
    if component == "bridge":
        status_key = "bridge_status"
        start_payload = {"type": "bridge-start", "version": version}
        stop_payload = {"type": "bridge-stop"}
    elif component == "emulator":
        status_key = "emulator_status"
        start_payload = {"type": "emulator-start", "version": version}
        stop_payload = {"type": "emulator-stop"}
    else:
        raise RuntimeError(f"Only emulator and bridge are supported, not {component}")

    # Not running at the beginning
    await websocket.send(json.dumps(background_check_payload))
    response = json.loads(await websocket.recv())
    print(response)
    assert response["success"]
    assert not response[status_key]["is_running"]

    # Spawning it
    await websocket.send(json.dumps(start_payload))
    response = json.loads(await websocket.recv())
    print(response)
    assert response["success"]

    # Is running after starting it
    await websocket.send(json.dumps(background_check_payload))
    response = json.loads(await websocket.recv())
    print(response)
    assert response["success"]
    assert response[status_key]["is_running"]
    assert response[status_key]["version"] == version

    # Stopping it
    await websocket.send(json.dumps(stop_payload))
    response = json.loads(await websocket.recv())
    print(response)
    assert response["success"]

    # Not running after stopping it
    await websocket.send(json.dumps(background_check_payload))
    response = json.loads(await websocket.recv())
    print(response)
    assert response["success"]
    assert not response[status_key]["is_running"]


async def _test(websocket, payload: dict, success: bool = True) -> None:
    await websocket.send(json.dumps(payload))
    response = json.loads(await websocket.recv())
    print(response)
    assert response["success"] == success


async def test_bridge_start_stop(websocket) -> None:
    await _test_start_stop(websocket, component="bridge", version=BRIDGE_TO_TEST)


async def test_emulator_tt_start_stop(websocket) -> None:
    await _test_start_stop(websocket, component="emulator", version=EMU_TO_TEST_TT)


async def test_emulator_t1_start_stop(websocket) -> None:
    await _test_start_stop(websocket, component="emulator", version=EMU_TO_TEST_T1)


@pytest.mark.parametrize("payload", commands_success)
async def test_successful(websocket, payload: dict) -> None:
    await _test(websocket, payload, success=True)


@pytest.mark.parametrize("payload", commands_failure)
async def test_failure(websocket, payload: dict) -> None:
    await _test(websocket, payload, success=False)


@pytest.mark.skip("Emulator is frozen after device backup")
async def test_read_and_confirm_mnemonic(websocket) -> None:
    # Setting up emulator with a new seed
    payload = {
        "type": "emulator-start",
        "id": 444,
        "version": EMU_TO_TEST_TT,
        "wipe": True,
    }
    await websocket.send(json.dumps(payload))
    response = json.loads(await websocket.recv())
    print("response", response)
    assert response["success"]

    payload = {"type": "emulator-reset-device", "id": 555}
    await websocket.send(json.dumps(payload))
    response = json.loads(await websocket.recv())
    print(response)
    assert response["success"]

    # WARNING: this is not very nice, we should do it via trezorlib somehow
    # We need to set trezor into backup mode without clicking anything else
    # (the Debuglink would be actually clicking the OKs)
    os.system("trezorctl device backup &")
    time.sleep(1)

    # Triggering the confirming walkthrough
    payload = {"type": "emulator-read-and-confirm-mnemonic", "id": 666}
    await websocket.send(json.dumps(payload))
    response = json.loads(await websocket.recv())
    print(response)
    assert response["success"]
    assert response["id"] == 666


@pytest.mark.skip("Emulator is frozen after device backup")
async def test_read_and_confirm_mnemonic_shamir(websocket) -> None:
    # Setting up emulator with a new seed
    payload = {
        "type": "emulator-start",
        "id": 444,
        "version": EMU_TO_TEST_TT,
        "wipe": True,
    }
    await websocket.send(json.dumps(payload))
    response = json.loads(await websocket.recv())
    print("response", response)
    assert response["success"]

    payload = {"type": "emulator-reset-device", "use_shamir": True, "id": 555}
    await websocket.send(json.dumps(payload))
    response = json.loads(await websocket.recv())
    print(response)
    assert response["success"]

    # WARNING: this is not very nice, we should do it via trezorlib somehow
    # We need to set trezor into backup mode without clicking anything else
    # (the Debuglink would be actually clicking the OKs)
    os.system("trezorctl device backup &")
    time.sleep(1)

    # Triggering the confirming walkthrough
    payload = {
        "type": "emulator-read-and-confirm-shamir-mnemonic",
        "shares": 3,
        "threshold": 2,
        "id": 666,
    }
    await websocket.send(json.dumps(payload))
    response = json.loads(await websocket.recv())
    print(response)
    assert response["success"]
    assert response["id"] == 666
