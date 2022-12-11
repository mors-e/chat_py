import websockets
import asyncio
import json

WS_URL = 'ws://localhost:9090'


async def connect(url):
    connected = False
    while not connected:
        try:
            ws = await websockets.connect(url)
            connected = True
            return ws
        except ConnectionRefusedError:
            print("Reconnecting...")
            continue


async def main():
    socket = await connect(WS_URL)
    data = {
        'type': 'login',
        "name": "rb_client",
        "password": "123",
    }
    await socket.send(json.dumps(data))
    response = await socket.recv()
    print(response)

if __name__ == "__main__":
    event_loop = asyncio.new_event_loop()
    event_loop.run_until_complete(main())
    event_loop.run_forever()