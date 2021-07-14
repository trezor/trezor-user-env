import asyncio
import json
import traceback
from copy import deepcopy

import websockets

import binaries
import bridge
import emulator
import helpers

IP = "0.0.0.0"
PORT = 9001
LOG_COLOR = "blue"
BRIDGE_PROXY = False  # is being set in main.py (when not disabled, will be True)


def log(text: str, color: str = LOG_COLOR) -> None:
    helpers.log(f"CONTROLLER: {text}", color)


class ResponseGetter:
    """Takes request from websocket, satisfies it and generates a response.

    Public API:
    get_response(request) -> dict
    """

    def __init__(self) -> None:
        pass

    def get_response(self, request: str) -> dict:
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

    def run_command_and_get_its_response(self) -> dict:
        """Performs wanted action and returns details of what happened."""
        if self.command == "ping":
            return {"response": "pong"}
        elif self.command == "background-check":
            bridge_status = bridge.get_status()
            emulator_status = emulator.get_status()
            return {
                "response": "Background check done",
                "bridge_status": bridge_status,
                "emulator_status": emulator_status,
                "background_check": True,
            }
        elif self.command == "emulator-start":
            version = self.request_dict.get("version") or binaries.FIRMWARES["TT"][0]
            wipe = self.request_dict.get("wipe") or False
            emulator.start(version, wipe)
            return {"response": f"Emulator version {version} started"}
        elif self.command == "emulator-stop":
            emulator.stop()
            return {"response": "Emulator stopped"}
        elif self.command == "emulator-setup":
            emulator.setup_device(
                self.request_dict["mnemonic"],
                self.request_dict["pin"],
                self.request_dict["passphrase_protection"],
                self.request_dict["label"],
                self.request_dict.get("needs_backup") or False,
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
        elif self.command == "emulator-read-and-confirm-mnemonic":
            emulator.read_and_confirm_mnemonic()
            return {"response": "Read and confirm mnemonic"}
        elif self.command == "emulator-allow-unsafe-paths":
            emulator.allow_unsafe()
            return {"response": "Allowed unsafe path"}
        elif self.command == "select-num-of-words":
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
            emulator.apply_settings(
                self.request_dict["passphrase_always_on_device"],
            )
            return {"response": f"Applied setting on emulator {self.request_dict}"}
        elif self.command == "emulator-reset-device":
            emulator.reset_device()
            return {"response": "Device reset"}
        elif self.command == "bridge-start":
            version = self.request_dict.get("version") or binaries.BRIDGES[0]
            bridge.start(version, proxy=BRIDGE_PROXY)
            response_text = f"Bridge version {version} started"
            if BRIDGE_PROXY:
                response_text = response_text + " with bridge proxy"
            return {"response": response_text}
        elif self.command == "bridge-stop":
            bridge.stop(proxy=BRIDGE_PROXY)
            response_text = "Stopping bridge"
            if BRIDGE_PROXY:
                response_text = response_text + " + stopping bridge proxy"
            return {"response": response_text}
        elif self.command == "exit":
            emulator.stop()
            bridge.stop()
            log("Exiting", "red")
            exit(1)
        else:
            return {"success": False, "error": f"Unknown command - {self.command}"}

    def generate_websocket_response(self, command_response: dict) -> dict:
        """Modifies the response before sending to websocket.

        Can conditionaly send more details according to each client's needs.
        """
        websocket_response = deepcopy(command_response)
        # Relaying request ID and filling success, if not there already
        websocket_response["id"] = self.request_id
        if "success" not in websocket_response:
            websocket_response["success"] = True

        return websocket_response

    def generate_exception_response(self, e: Exception) -> dict:
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
        return response


# Welcome new clients with info
async def welcome(websocket) -> None:
    intro = {
        "type": "client",
        "id": "TODO",
        "firmwares": binaries.FIRMWARES,
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
        except websockets.exceptions.ConnectionClosedOK:
            log("Client exiting OK. Goodbye")
            return
        except websockets.exceptions.ConnectionClosedError:
            log("Client exiting with a failure. Goodbye", "red")
            return


def start() -> None:
    log(f"Starting websocket server (controller.py) at {IP}:{PORT}")

    server = websockets.serve(handler, IP, PORT)

    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()
