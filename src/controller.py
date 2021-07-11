import asyncio
import http
import json
import traceback
from typing import Any, Dict

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


# Welcome new clients with info
async def welcome(websocket) -> None:
    intro = {
        "type": "client",
        "id": "TODO",
        "firmwares": binaries.FIRMWARES,
        "bridges": binaries.BRIDGES,
    }
    await websocket.send(json.dumps(intro))
    log(f"Welcome: {json.dumps(intro)}")


async def handler(websocket, path) -> None:
    await welcome(websocket)

    while True:
        response: Dict[str, Any] = {}

        try:
            request = await websocket.recv()
        except websockets.exceptions.ConnectionClosedOK:
            log("Client exiting OK. Goodbye")
            return
        except websockets.exceptions.ConnectionClosedError:
            log("Client exiting with a failure. Goodbye", "red")
            return

        try:
            request = json.loads(request)
            command = request["type"]
        except KeyError:
            error = f"Key 'type' must be present in JSON - {request}"
            log(error, "red")
            await websocket.send(json.dumps({"success": False, "error": error}))
            continue
        except json.decoder.JSONDecodeError:
            error = f"Invalid JSON message - {request}"
            log(error, "red")
            await websocket.send(json.dumps({"success": False, "error": error}))
            continue

        if command != "background-check":
            log(f"Request: {request}")

        # Saving the ID, if there, to match requests and responses for the client
        request_id = request.get("id", "unknown")

        try:
            if command == "ping":
                response = {"response": "pong"}
            elif command == "background-check":
                bridge_status = bridge.get_status()
                emulator_status = emulator.get_status()
                response = {
                    "response": "Background check done",
                    "bridge_status": bridge_status,
                    "emulator_status": emulator_status,
                    "background_check": True,
                }
            elif command == "emulator-start":
                version = request.get("version") or binaries.FIRMWARES["TT"][0]
                wipe = request.get("wipe") or False
                emulator.start(version, wipe)
                response = {"response": f"Emulator version {version} started"}
            elif command == "emulator-stop":
                emulator.stop()
                response = {"response": "Emulator stopped"}
            elif command == "emulator-setup":
                emulator.setup_device(
                    request["mnemonic"],
                    request["pin"],
                    request["passphrase_protection"],
                    request["label"],
                    request.get("needs_backup") or False,
                )
                response = {"response": f"Emulator set up - {request}"}
            elif command == "emulator-press-yes":
                emulator.press_yes()
                response = {"response": "Pressed YES"}
            elif command == "emulator-press-no":
                emulator.press_no()
                response = {"response": "Pressed NO"}
            elif command == "emulator-input":
                value = request["value"]
                emulator.input(value)
                response = {"response": f"Input into emulator: {value}"}
            elif command == "emulator-read-and-confirm-mnemonic":
                emulator.read_and_confirm_mnemonic()
                response = {"response": "Read and confirm mnemonic"}
            elif command == "emulator-allow-unsafe-paths":
                emulator.allow_unsafe()
                response = {"response": "Allowed unsafe path"}
            elif command == "select-num-of-words":
                num = request["num"]
                emulator.select_num_of_words(num)
                response = {"response": f"Selected {num} words"}
            elif command == "emulator-swipe":
                direction = request["direction"]
                emulator.swipe(direction)
                response = {"response": f"Swiped {direction}"}
            elif command == "emulator-wipe":
                emulator.wipe_device()
                response = {"response": "Device wiped"}
            elif command == "emulator-apply-settings":
                emulator.apply_settings(
                    request["passphrase_always_on_device"],
                )
                response = {"response": f"Applied setting on emulator {request}"}
            elif command == "emulator-reset-device":
                emulator.reset_device()
                response = {"response": "Device reset"}
            elif command == "bridge-start":
                version = request.get("version") or binaries.BRIDGES[0]
                bridge.start(version, proxy=BRIDGE_PROXY)
                response_text = f"Bridge version {version} started"
                if BRIDGE_PROXY:
                    response_text = response_text + " with bridge proxy"
                response = {"response": response_text}
            elif command == "bridge-stop":
                bridge.stop(proxy=BRIDGE_PROXY)
                response_text = "Stopping bridge"
                if BRIDGE_PROXY:
                    response_text = response_text + " + stopping bridge proxy"
                response = {"response": response_text}
            elif command == "exit":
                emulator.stop()
                bridge.stop()
                log("Exiting", "red")
                exit(1)
            else:
                response = {"success": False, "error": f"Unknown command - {command}"}

            if response:
                # Relaying the ID and filling success, if not there already
                response["id"] = request_id
                if "success" not in response:
                    response["success"] = True

                # Not logging in case of background checks, they would flood the screen
                if "background_check" not in response:
                    log(f"Response: {json.dumps(response)}")

                await websocket.send(json.dumps(response))

        # TODO: This is wrong and we should list all the trezorlib
        #   (or other) exceptions that we want to catch here.
        # But catching general \Exception is bad because it catches everything
        #   then including errors etc. A lot of kittens die when we are doing this.
        except Exception as e:
            traceback_string = traceback.format_exc()
            log(traceback_string, "red")
            error_msg = f"{type(e).__name__} - {e}"
            response = {
                "success": False,
                "id": request_id,
                "error": error_msg,
                "traceback": traceback_string,
            }
            log(f"ERROR response: {json.dumps(response)}", "red")
            await websocket.send(json.dumps(response))


async def health_check(path, request_headers):
    if path == "/health/":
        return http.HTTPStatus.OK, [], b"OK\n"


def start() -> None:
    log(f"Starting websocket server (controller.py) at {IP}:{PORT}")

    server = websockets.serve(handler, IP, PORT, process_request=health_check)

    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()
