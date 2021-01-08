import json
import binaries

from termcolor import colored

import bridge
import bridge_proxy
import emulator
import suite
import websockets
import asyncio

IP = "0.0.0.0"
PORT = 9001
LOG_COLOR = "blue"
BRIDGE_PROXY = False


# Welcome new clients with info
async def welcome(websocket):
    intro = {
        "type": "client",
        "id": "TODO",
        "firmwares": binaries.FIRMWARES,
        "suites": binaries.SUITES,
        "bridges": binaries.BRIDGES,
    }
    await websocket.send(json.dumps(intro))
    log("Welcome: " + json.dumps(intro))


async def handler(websocket, path):
    await welcome(websocket)

    while True:
        response = None

        try:
            request = await websocket.recv()
        except websockets.exceptions.ConnectionClosedOK:
            log("Client exiting OK. Goodbye")
            return
        except websockets.exceptions.ConnectionClosedError:
            log("Client exiting with a failure. Goodbye")
            return
        log("Request: " + request)

        try:
            request = json.loads(request)
            command = request["type"]
        except KeyError:
            error = "Command 'type' missing"
            await websocket.send(json.dumps({"success": False, "error": error}))
            continue
        except json.decoder.JSONDecodeError:
            error = "Invalid json message"
            await websocket.send(json.dumps({"success": False, "error": error}))
            continue

        try:
            if command == "ping":
                await websocket.send("pong")
            elif command == "suite-start":
                version = request.get("version")
                suite.start(version)
                response = {"success": True}
            elif command == "emulator-start":
                version = request.get("version") or binaries.FIRMWARES["TT"][0]
                wipe = request.get("wipe") or False
                emulator.start(version, wipe)
                response = {"success": True}
            elif command == "emulator-stop":
                emulator.stop()
                response = {"success": True}
            elif command == "emulator-setup":
                emulator.setup_device(
                    request["mnemonic"],
                    request["pin"],
                    request["passphrase_protection"],
                    request["label"],
                    request.get("needs_backup"),
                )
                response = {"success": True}
            elif command == "emulator-press-yes":
                emulator.press_yes()
                response = {"success": True}
            elif command == "emulator-press-no":
                emulator.press_no()
                response = {"success": True}
            elif command == "emulator-input":
                emulator.input(request["value"])
                response = {"success": True}
            elif command == "emulator-read-and-confirm-mnemonic":
                emulator.read_and_confirm_mnemonic()
                response = {"success": True}
            elif command == "emulator-allow-unsafe-paths":
                emulator.allow_unsafe()
                response = {"success": True}
            elif command == "select-num-of-words":
                emulator.select_num_of_words(request["num"])
                response = {"success": True}
            elif command == "emulator-swipe":
                emulator.swipe(request["direction"])
                response = {"success": True}
            elif command == "emulator-wipe":
                emulator.wipe_device()
                response = {"success": True}
            elif command == "emulator-apply-settings":
                emulator.apply_settings(request["passphrase_always_on_device"],)
                response = {"success": True}
            elif command == "emulator-reset-device":
                emulator.reset_device()
                response = {"success": True}
            elif command == "bridge-start":
                version = request.get("version") or binaries.BRIDGES[0]
                bridge.start(version)
                if BRIDGE_PROXY:
                    bridge_proxy.start()
                response = {"success": True}
            elif command == "bridge-stop":
                bridge.stop()
                if BRIDGE_PROXY:
                    bridge_proxy.stop()
                response = {"success": True}
            elif command == "exit":
                emulator.stop()
                bridge.stop()
                log("Exiting")
                exit(1)
            else:
                response = {"success": False, "error": "unknown command"}
                await websocket.send(json.dumps(response))
                log("Response: " + json.dumps(response))
                continue

            if response is not None:
                log("Response: " + json.dumps(response))
                await websocket.send(json.dumps(response))

        # TODO: This is wrong and we should list all the trezorlib (or other) exceptions that
        # we want to catch here. But catching general \Exception is bad because it catches
        # everything then including errors etc. A lot of kittens die when we are doing this.
        except Exception as e:
            response = {"success": False, "error": str(e)}
            log("Response: " + json.dumps(response))
            await websocket.send(json.dumps(response))


# TODO: use logging
def log(content):
    print(colored("CONTROLLER: " + content, LOG_COLOR))


def start():
    log("Starting at {}:{}".format(IP, PORT))

    server = websockets.serve(handler, IP, PORT)

    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()
