import json
import asyncio
from datetime import datetime

import aioconsole
import websockets
from common.structures import Message




WS_URL = 'ws://localhost:8000/room'


async def connect(url):
    while True:
        try:
            return await websockets.connect(url)
        except ConnectionRefusedError:
            print("Reconnecting...")


async def listen_room(ws):
    while True:
        raw_data = await ws.recv()
        json_data = json.loads(raw_data)
        await aioconsole.aprint(json_data)


async def listen_input(ws, user):
    while True:
        text = await aioconsole.ainput()

        message = Message(
            text=text,
            time=datetime.now(),
            user=user,
        ).to_json(ensure_ascii=False)

        await ws.send(message)


async def main():
    name = input('Введите имя: ')
    room_name = input('Введите комнату: ')

    websocket = await connect(f'{WS_URL}/{room_name}?name={name}')

    await asyncio.gather(
        listen_room(websocket),
        listen_input(websocket, name),
    )


if __name__ == '__main__':
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    asyncio.run(main())
