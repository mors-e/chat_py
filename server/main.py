import asyncio
from typing import Union
from datetime import datetime

from redis.asyncio.client import Redis
from fastapi import FastAPI, WebSocket, WebSocketException

from common.structures import Message
from server.redis import get_pool
from server.manager import ConnectionManager
from server.messages import connected_message, disconnected_message


app = FastAPI()
manager = ConnectionManager()


@app.websocket("/room/{room_id}")
async def room(
        websocket: WebSocket,
        room_id: str,
        name: Union[str, None] = None
) -> None:
    print('room')
    await manager.connect(websocket)

    appended = False
    try:
        appended = await append_user_to_room(room_id, name)
        await manager.broadcast(connected_message(name))
        await asyncio.gather(
            listen_client(websocket, room_id, name),
            listen_room(websocket, room_id)
        )
    finally:
        print('finally')
        await manager.disconnect(websocket)
        if appended:
            await remove_user_from_room(room_id, name)


async def append_user_to_room(room_id: str, name: str):
    print('append')
    pool: Redis = await get_pool()

    hash_key = f'{room_id}_hash'
    users = await pool.smembers(hash_key)
    if name in users:
        raise WebSocketException(code=1010, reason='Пользователь с таким именем уже находится в комнате')
    await pool.sadd(hash_key, name)
    return True


async def remove_user_from_room(room_id: str, name: str):
    print('remove')
    pool: Redis = await get_pool()

    hash_key = f'{room_id}_hash'
    await pool.srem(hash_key, name)
    await manager.broadcast(disconnected_message(name))


async def listen_room(websocket: WebSocket, room_id):
    print('listen_room')
    pool: Redis = await get_pool()

    stream_key = f'{room_id}_stream'
    index = '0-0'
    while pool:
        response = await pool.xread(streams={stream_key: index})
        for _stream_name, messages in response:
            for message_id, values in messages:
                index = message_id
                message = values.get('message', None)
                if message:
                    await websocket.send_text(message)


async def listen_client(websocket: WebSocket, room_id, name):
    print('listen_client')
    pool: Redis = await get_pool()

    stream_key = f'{room_id}_stream'
    while pool:
        json_message = await websocket.receive_json()
        if json_message.get('text', None):
            message = Message(user=name, text=json_message['text'], time=datetime.now())
            await pool.xadd(name=stream_key, fields={'message': message.to_json(ensure_ascii=False)})
        else:
            await websocket.send_text('Неверный тип запроса')
