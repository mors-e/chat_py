import json
import asyncio
import websockets


WS_URL = 'ws://localhost:8000/room'


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
    room_name = '123'
    name = 'rb_client1234'
    socket = await connect(f'{WS_URL}/{room_name}?name={name}')

    ok = await socket.recv()
    print(ok)

    while True:
        message = input()
        data = {
            "type": "message",
            "text": message,
        }
        await socket.send(json.dumps(data))
        raw_response = await socket.recv()
        response = json.loads(raw_response)
        print(response)


if __name__ == "__main__":
    event_loop = asyncio.new_event_loop()
    event_loop.run_until_complete(main())
    event_loop.run_forever()
