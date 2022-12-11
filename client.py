import websockets
import asyncio
import json

URL = "ws://localhost:8765"


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
        "type": "rb_client",
        "password": "123",
    }
    await send(data, url)

async def sendInput():
    message = ''
    while message != "e":
        message = input("Enter message(e - end): ")
        data = {
            "type": "message",
            "message": message,
        }
        await send(data, URL)


if __name__ == "__main__":
    asyncio.run(sendInput())
