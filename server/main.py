import asyncio
from typing import Union
from datetime import datetime

import aioredis
from aioredis import Redis
from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect

from common.structures import Message
from server.manager import ConnectionManager


REDIS_URL = 'redis://localhost:6379'

app = FastAPI()
manager = ConnectionManager()


@app.websocket("/room/{room_id}")
async def room(
        websocket: WebSocket,
        room_id: str,
        name: Union[str, None] = None
) -> None:
    await manager.connect(websocket)

    try:
        logged_in = await client_login(websocket, room_id, name)
        if logged_in:
            client_finished, room_finished = await asyncio.gather(
                listen_client(websocket, room_id, name),
                listen_room(websocket, room_id)
            )
            print(client_finished, room_finished)

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        await manager.broadcast(f'Client disconnected {name}')


async def client_login(websocket: WebSocket, room_id: str, name: str) -> bool:
    print("login")
    pool: Redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
    if pool is None:
        return False

    users = await pool.smembers(room_id)

    if name in users:
        await manager.send_personal_message('Пользователь с таким именем уже находится в этой комнате.', websocket)
        return False

    await pool.sadd(room_id, name)
    await manager.send_personal_message('Вы вошли в чат!', websocket)
    return True


async def listen_room(websocket: WebSocket, room_id):
    print("room")
    pool: Redis = await aioredis.from_url(REDIS_URL, decode_responses=True)

    while pool:
        messages = await pool.xread(streams={room_id: '$'})
        message = messages.get_message()
        await websocket.send(message.get('data', '{}'))

    return 'Ok'


async def listen_client(websocket: WebSocket, room_id, name):
    print("client")
    pool: Redis = await aioredis.from_url(REDIS_URL, decode_responses=True)

    while pool:
        json_message = await websocket.receive_json()
        match json_message.get('type', None):
            case 'message':
                message = Message(user=name, text=json_message["text"], time=datetime.now())
                await pool.xadd(name=room_id, fields=message.to_json())
            case _:
                await websocket.send('Неверный тип запроса')

    return 'Ok'
