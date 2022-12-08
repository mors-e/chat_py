import websockets
import asyncio
import json


async def connect(url):
    connected = False
    while not connected:
        try:
            websocket = await websockets.connect(url)
            connected = True
            return websocket
        except ConnectionRefusedError:
            print("Reconnecting...")
            continue


async def send(data: dict, url: str):
    websocket = await connect(url)
    await websocket.send(json.dumps(data))


async def main():
    url = "ws://localhost:8765"
    data = {
        "name": "rb_client",
        "password": "123",
    }
    await send(data, url)


if __name__ == "__main__":
    asyncio.run(main())
