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
    print("room")
    pool: Redis = await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    if pool is None:
        return

    await manager.connect(websocket)

    logged_in = False
    try:
        logged_in = await client_login(websocket, room_id, name)
        if logged_in:
            client_finished, room_finished = await asyncio.gather(
                listen_client(websocket, room_id, name),
                listen_room(websocket, room_id)
            )
            print(client_finished, room_finished)

    except WebSocketDisconnect:
        if logged_in:
            hash_key = f'{room_id}_hash'
            await pool.hdel(hash_key, name)
        await manager.disconnect(websocket)
        await manager.broadcast(f'Client disconnected {name}')


async def client_login(websocket: WebSocket, room_id: str, name: str) -> bool:
    print("login")
    pool: Redis = await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    if pool is None:
        return False

    hash_key = f'{room_id}_hash'
    users = await pool.smembers(hash_key)

    if name in users:
        await manager.send_personal_message('Пользователь с таким именем уже находится в этой комнате.', websocket)
        return False

    await pool.sadd(hash_key, name)
    await manager.send_personal_message('Вы вошли в чат!', websocket)
    return True


async def listen_room(websocket: WebSocket, room_id):
    print("room")
    pool: Redis = await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

    stream_key = f'{room_id}_stream'
    index = 0
    while pool:
        response = await pool.xread(streams={stream_key: index})
        for _stream_name, messages in response:
            for message_id, values in messages:
                index = message_id
                message = values.get('message', None)
                if message:
                    await websocket.send_text(message)

    return 'Ok'


async def listen_client(websocket: WebSocket, room_id, name):
    print("client")
    pool: Redis = await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

    stream_key = f'{room_id}_stream'
    while pool:
        json_message = await websocket.receive_json()
        match json_message.get('type', None):
            case 'message':
                message = Message(user=name, text=json_message["text"], time=datetime.now())
                await pool.xadd(name=stream_key, fields={'message': message.to_json()})
            case _:
                await websocket.send('Неверный тип запроса')

    return 'Ok'
