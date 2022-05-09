"""
Connects to the controller websocket and sends it the payload.
"""

import asyncio
import json

import websockets

WS_ADDRESS = "ws://localhost:9001"
PAYLOAD = {
    "type": "emulator-start",
    "version": "2-latest",
}


async def send_cmd():
    async with websockets.connect(WS_ADDRESS) as ws:
        await ws.recv()  # Catch the welcome message
        await ws.send(json.dumps(PAYLOAD))
        response = await ws.recv()
        print(response)


if __name__ == "__main__":
    asyncio.run(send_cmd())
