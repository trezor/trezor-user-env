import atexit
import json
import os
import binaries

from termcolor import colored

import bridge
import emulator
import suite
import proxy
from websocket_server import WebsocketServer


def cleanup():
    emulator.stop()
    bridge.stop()


atexit.register(cleanup)

PORT = 9001

print("starting websocket server on port: " + str(PORT))


# Called for every client connecting (after handshake)
def new_client(client, server):
    intro = {
        "type": "client",
        "id": client["id"],
        "firmwares": binaries.FIRMWARES,
        "suites": binaries.SUITES,
        "bridges": binaries.BRIDGES,
    }
    welcome = json.dumps(intro)
    server.send_message_to_all(welcome)


# Called for every client disconnecting
def client_left(client, server):
    print(colored("Client(%d) disconnected" % client["id"], "blue"))


# Called when a client sends a message
def message_received(client, server, message):
    print("Client(%d) request: %s" % (client["id"], message))
    try:
        cmd = json.loads(message)
        cmdId = cmd["id"]
        cmdType = cmd["type"]
    except:
        server.send_message(
            client, json.dumps({"success": False, "error": "Invalid json message"})
        )
        return

    response = None
    try:
        if cmdType == "ping":
            server.send_message(client, "pong")
        elif cmdType == "suite-start":
            version = cmd.get("version")
            suite.start(version)
            response = {"success": True}
        elif cmdType == "emulator-start":
            version = cmd.get("version") or binaries.FIRMWARES["TT"][0]
            wipe = cmd.get("wipe") or False
            emulator.start(version, wipe)
            response = {"success": True}
        elif cmdType == "emulator-stop":
            emulator.stop()
            response = {"success": True}
        elif cmdType == "emulator-setup":
            emulator.setup_device(
                cmd["mnemonic"],
                cmd["pin"],
                cmd["passphrase_protection"],
                cmd["label"],
                cmd.get("needs_backup"),
            )
            response = {"success": True}
        elif cmdType == "emulator-decision":
            emulator.decision()
            response = {"success": True}
        elif cmdType == "emulator-input":
            emulator.input(cmd["value"])
            response = {"success": True}
        elif cmdType == "emulator-read-and-confirm-mnemonic":
            emulator.read_and_confirm_mnemonic()
            response = {"success": True}
        elif cmdType == "emulator-allow-unsafe-paths":
            emulator.allow_unsafe()
            response = {"success": True}
        elif cmdType == "select-num-of-words":
            emulator.select_num_of_words(cmd["num"])
            response = {"success": True}
        elif cmdType == "emulator-swipe":
            emulator.swipe(cmd["direction"])
            response = {"success": True}
        elif cmdType == "emulator-wipe":
            emulator.wipe_device()
            response = {"success": True}
        elif cmdType == "emulator-apply-settings":
            emulator.apply_settings(cmd["passphrase_always_on_device"],)
            response = {"success": True}
        elif cmdType == "emulator-reset-device":
            resp = emulator.reset_device()
            print(resp)
            response = {"success": True}
        elif cmdType == "bridge-start":
            version = cmd.get("version") or binaries.BRIDGES[0]
            bridge.start(version)
            response = {"success": True}
        elif cmdType == "bridge-stop":
            bridge.stop()
            response = {"success": True}
        elif cmdType == "exit":
            emulator.stop()
            bridge.stop()
            os._exit(1)
        else:
            response = {"success": False, "error": "unknown command"}
            server.send_message(client, json.dumps(response))
            print("Client(%d) response: %s" % (client["id"], str(response)))
            return
        print("Client(%d) response: %s" % (client["id"], str(response)))
        if response is not None:
            server.send_message(
                client, json.dumps(dict(response, id=cmdId, success=True))
            )
    except RuntimeError as e:
        print("Client(%d) response: %s" % (client["id"], str(e)))
        server.send_message(
            client, json.dumps({"id": cmdId, "success": False, "error": str(e)})
        )


proxy.start()
binaries.explore()
server = WebsocketServer(PORT)
server.set_fn_new_client(new_client)
server.set_fn_client_left(client_left)
server.set_fn_message_received(message_received)
print("websocket server running ")
server.run_forever()
