from __future__ import annotations

import asyncio
import json
import os
import traceback
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Union

from trezorlib import messages
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from websockets.server import serve

import binaries
import bridge
import emulator
import helpers
from bitcoin_regtest.rpc import BTCJsonRPC

if TYPE_CHECKING:
    from typing_extensions import TypedDict

    class NormalResponse(TypedDict, total=False):
        success: bool
        response: str | dict[str, Any]
        id: str
        error: str
        traceback: str

    class BackgroundCheckResponse(TypedDict):
        response: str
        bridge_status: bool | Any
        emulator_status: bool | Any
        regtest_status: bool | Any
        background_check: bool

    ResponseType = Union[NormalResponse, BackgroundCheckResponse]


IP = "0.0.0.0"
PORT = 9001
LOG_COLOR = "blue"
BRIDGE_PROXY = False  # is being set in main.py (when not disabled, will be True)
REGTEST_RPC = BTCJsonRPC(
    url=os.getenv("REGTEST_RPC_URL") or "http://0.0.0.0:18021",
    user="rpc",
    passwd="rpc",
)
PREV_RUNNING_MODEL: binaries.Model | None = None


def is_regtest_active() -> bool:
    """Finds out whether the regtest backend is running."""
    try:
        REGTEST_RPC.getblockchaininfo()
        return True
    except Exception:
        return False


def log(text: str, color: str = LOG_COLOR) -> None:
    helpers.log(f"CONTROLLER: {text}", color)


class ResponseGetter:
    """Takes request from websocket, satisfies it and generates a response.

    Public API:
    get_response(request) -> dict
    """

    def __init__(self) -> None:
        pass

    def get_response(self, request: str) -> "ResponseType":
        """Handles the whole process of translating request into response."""
        try:
            self.request_dict = json.loads(request)
        except json.decoder.JSONDecodeError:
            error = f"Invalid JSON message - {request}"
            log(error, "red")
            return {"success": False, "error": error}

        try:
            self.command = self.request_dict["type"]
        except KeyError:
            error = f"Key 'type' must be present in JSON - {self.request_dict}"
            log(error, "red")
            return {"success": False, "error": error}

        # Saving the ID, if there, to match requests and responses for the client
        self.request_id = self.request_dict.get("id", "unknown")

        if self.command != "background-check":
            log(f"Request: {self.request_dict}")

        try:
            command_response = self.run_command_and_get_its_response()
            websocket_response = self.generate_websocket_response(command_response)
            if "background_check" not in websocket_response:
                log(f"Response: {websocket_response}")
            return websocket_response
        except Exception as e:
            return self.generate_exception_response(e)

    def run_command_and_get_its_response(self) -> "ResponseType":
        """Performs wanted action and returns details of what happened."""
        if self.command == "ping":
            return {"response": "pong"}
        elif self.command == "log":
            text = self.request_dict["text"]
            log(text)
            return {"response": "Text logged"}
        elif self.command == "background-check":
            bridge_status = bridge.get_status()
            emulator_status = emulator.get_status()
            regtest_status = is_regtest_active()
            return {
                "response": "Background check done",
                "bridge_status": bridge_status,
                "emulator_status": emulator_status,
                "regtest_status": regtest_status,
                "background_check": True,
            }
        elif self.command == "exit":
            emulator.stop()
            bridge.stop()
            log("Exiting", "red")
            exit(1)
        elif self.command.startswith("bridge"):
            return self.run_bridge_command()
        elif self.command.startswith("emulator"):
            return self.run_emulator_command()
        elif self.command.startswith("regtest"):
            return self.run_regtest_command()
        else:
            return {"success": False, "error": f"Unknown command - {self.command}"}

    def run_bridge_command(self) -> "ResponseType":
        if self.command == "bridge-start":
            version = self.request_dict.get("version", binaries.DEFAULT_BRIDGE)
            output_to_logfile = self.request_dict.get("output_to_logfile", True)
            bridge.start(
                version, proxy=BRIDGE_PROXY, output_to_logfile=output_to_logfile
            )
            response_text = f"Bridge version {version} started"
            if BRIDGE_PROXY:
                response_text += " with bridge proxy"
            return {"response": response_text}
        elif self.command == "bridge-stop":
            bridge.stop(proxy=BRIDGE_PROXY)
            response_text = "Stopping bridge"
            if BRIDGE_PROXY:
                response_text += " + stopping bridge proxy"
            return {"response": response_text}
        else:
            return {
                "success": False,
                "error": f"Unknown bridge command - {self.command}",
            }

    def run_emulator_command(self) -> "ResponseType":
        global PREV_RUNNING_MODEL

        if self.command == "emulator-start":
            model: binaries.Model | None = self.request_dict.get("model")
            if not model:
                return {
                    "success": False,
                    "error": "Model must be supplied for the emulator to start",
                }
            binaries.check_model(model)

            # Not supplying any version will result in "-main",
            # "-latest" will get the latest release of X.
            if "version" in self.request_dict:
                requested_version = self.request_dict["version"]
                if requested_version.endswith("-latest"):
                    version = binaries.get_latest_release_version(model)
                else:
                    version = requested_version
            else:
                version = binaries.get_main_version(model)

            wipe = self.request_dict.get("wipe", False)
            output_to_logfile = self.request_dict.get("output_to_logfile", True)
            save_screenshots = self.request_dict.get("save_screenshots", False)
            if model != PREV_RUNNING_MODEL:
                wipe = True
            PREV_RUNNING_MODEL = model
            emulator.start(
                version=version,
                model=model,
                wipe=wipe,
                output_to_logfile=output_to_logfile,
                save_screenshots=save_screenshots,
            )
            response_text = f"Emulator version {version} ({model}) started"
            if wipe:
                response_text += " and wiped to be empty"
            return {"response": response_text}
        elif self.command == "emulator-start-from-url":
            url = self.request_dict["url"]
            model = self.request_dict["model"]
            if not model:
                return {
                    "success": False,
                    "error": "Model must be supplied for the emulator to start",
                }
            binaries.check_model(model)
            wipe = self.request_dict.get("wipe", False)
            output_to_logfile = self.request_dict.get("output_to_logfile", True)
            save_screenshots = self.request_dict.get("save_screenshots", False)
            if model != PREV_RUNNING_MODEL:
                wipe = True
            PREV_RUNNING_MODEL = model
            emulator.start_from_url(
                url=url,
                model=model,
                wipe=wipe,
                output_to_logfile=output_to_logfile,
                save_screenshots=save_screenshots,
            )
            response_text = f"Emulator downloaded from {url} and started"
            if wipe:
                response_text += " and wiped to be empty"
            return {"response": response_text}
        elif self.command == "emulator-stop":
            emulator.stop()
            return {"response": "Emulator stopped"}
        elif self.command == "emulator-setup":
            emulator.setup_device(
                self.request_dict["mnemonic"],
                self.request_dict["pin"],
                self.request_dict["passphrase_protection"],
                self.request_dict["label"],
                self.request_dict.get("needs_backup", False),
            )
            return {"response": f"Emulator set up - {self.request_dict}"}
        elif self.command == "emulator-press-yes":
            emulator.press_yes()
            return {"response": "Pressed YES"}
        elif self.command == "emulator-press-no":
            emulator.press_no()
            return {"response": "Pressed NO"}
        elif self.command == "emulator-input":
            value = self.request_dict["value"]
            emulator.input(value)
            return {"response": f"Input into emulator: {value}"}
        elif self.command == "emulator-click":
            x = self.request_dict["x"]
            y = self.request_dict["y"]
            emulator.click(x=x, y=y)
            return {"response": f"Clicked in emulator: x: {x}, y: {y}"}
        elif self.command == "emulator-read-and-confirm-mnemonic":
            emulator.read_and_confirm_mnemonic()
            return {"response": "Read and confirm mnemonic"}
        elif self.command == "emulator-read-and-confirm-shamir-mnemonic":
            shares = self.request_dict.get("shares", 1)
            threshold = self.request_dict.get("threshold", 1)
            emulator.read_and_confirm_shamir_mnemonic(
                shares=shares, threshold=threshold
            )
            return {
                "response": f"Read and confirm Shamir mnemonic for {shares} shares and threshold {threshold}."
            }
        elif self.command == "emulator-allow-unsafe-paths":
            emulator.allow_unsafe()
            return {"response": "Allowed unsafe path"}
        elif self.command == "emulator-select-num-of-words":
            num = self.request_dict["num"]
            emulator.select_num_of_words(num)
            return {"response": f"Selected {num} words"}
        elif self.command == "emulator-swipe":
            direction = self.request_dict["direction"]
            emulator.swipe(direction)
            return {"response": f"Swiped {direction}"}
        elif self.command == "emulator-wipe":
            emulator.wipe_device()
            return {"response": "Device wiped"}
        elif self.command == "emulator-apply-settings":
            # Relaying all the relevant fields from the request, to make sure
            #   the client is notified when it sends an unknown field
            #   and the function will throw an Exception
            settings_fields = deepcopy(self.request_dict)
            settings_fields.pop("type", None)
            settings_fields.pop("id", None)
            emulator.apply_settings(**settings_fields)
            return {"response": f"Applied settings on emulator {settings_fields}"}
        elif self.command == "emulator-reset-device":
            emulator.reset_device(
                self.request_dict.get("backup_type", messages.BackupType.Bip39),
                self.request_dict.get("strength", 128),
                use_shamir=self.request_dict.get("use_shamir", False),
            )
            return {"response": "Device reset"}
        elif self.command == "emulator-get-screenshot":
            screen_base_64 = emulator.get_current_screen()
            return {"response": screen_base_64}
        elif self.command == "emulator-get-debug-state":
            debug_state = emulator.get_debug_state()
            return {"response": debug_state}
        elif self.command == "emulator-get-screen-content":
            content = emulator.get_screen_content()
            return {"response": content}  # type: ignore
        else:
            return {
                "success": False,
                "error": f"Unknown emulator command - {self.command}",
            }

    def run_regtest_command(self) -> "ResponseType":
        if self.command == "regtest-mine-blocks":
            block_amount = self.request_dict["block_amount"]
            address: str = (
                self.request_dict.get("address") or REGTEST_RPC.getnewaddress()
            )
            REGTEST_RPC.generatetoaddress(block_amount, address)
            return {"response": f"Mined {block_amount} blocks by address {address}"}
        elif self.command == "regtest-send-to-address":
            btc_amount = self.request_dict["btc_amount"]
            address = self.request_dict["address"]
            # Sending the amount and mining a block to confirm it
            REGTEST_RPC.sendtoaddress(address, btc_amount)
            REGTEST_RPC.generatetoaddress(1, REGTEST_RPC.getnewaddress())
            return {"response": f"{btc_amount} BTC sent to {address}."}
        elif self.command == "regtest-generateblock":
            address = self.request_dict["address"]
            txids = self.request_dict["txids"]
            REGTEST_RPC.generateblock(address, txids)
            return {"response": f"block to {address} mined."}
        else:
            return {
                "success": False,
                "error": f"Unknown regtest command - {self.command}",
            }

    def generate_websocket_response(
        self, command_response: "ResponseType"
    ) -> "ResponseType":
        """Modifies the response before sending to websocket.

        Can conditionaly send more details according to each client's needs.
        """
        websocket_response = deepcopy(command_response)
        # Relaying request ID and filling success, if not there already
        websocket_response["id"] = self.request_id  # type: ignore
        if "success" not in websocket_response:
            websocket_response["success"] = True  # type: ignore

        return websocket_response

    def generate_exception_response(self, e: Exception) -> "ResponseType":
        """Creates response for exception case."""
        traceback_string = traceback.format_exc()
        log(traceback_string, "red")
        error_msg = f"{type(e).__name__} - {e}"
        response = {
            "success": False,
            "id": self.request_id,
            "error": error_msg,
            "traceback": traceback_string,
        }
        log(f"ERROR response: {response}", "red")
        return response  # type: ignore


# Welcome new clients with info
async def welcome(websocket) -> None:
    intro = {
        "type": "client",
        "id": "TODO",
        "firmwares": binaries.get_all_firmware_versions(),
        "bridges": binaries.BRIDGES,
    }
    await websocket.send(json.dumps(intro))
    log(f"Welcome: {intro}")


async def handler(websocket, path) -> None:
    await welcome(websocket)
    RESPONSE_GETTER = ResponseGetter()

    while True:
        try:
            request = await websocket.recv()
            response = RESPONSE_GETTER.get_response(request)
            await websocket.send(json.dumps(response))
        except ConnectionClosedOK:
            log("Client exiting OK. Goodbye")
            return
        except ConnectionClosedError:
            log("Client exiting with a failure. Goodbye", "red")
            return


def start() -> None:
    log(f"Starting websocket server (controller.py) at {IP}:{PORT}")

    server = serve(handler, IP, PORT)

    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()
