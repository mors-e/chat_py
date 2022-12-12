import websockets
import asyncio
import aioredis
import json
from datetime import datetime

from common.messages import MessageRequest, OkResponse, ErrResponse
from common.redis_structures import Room, Message

from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from aioredis.errors import ConnectionClosedError as ServerConnectionClosedError


async def get_redis_pool():
    try:
        pool = await aioredis.create_redis_pool(
            ('localhost', '6379'), encoding='utf-8')
        return pool
    except ConnectionRefusedError as e:
        print('cannot connect to redis on:', 'localhost', '6379')
        return None


async def client_login(socket, path):
    pool = await get_redis_pool()
    if pool is None:
        return

    splitted_path = path.split('?')
    room_name = splitted_path.pop(0).replace('/', '')
    name = splitted_path.pop(0).split('=').pop(1)

    users = await pool.smembers(room_name)

    if name in users:
        await socket.send(ErrResponse(error='пользователь уже в комнате').to_json(ensure_ascii=False))
        return None, None

    await pool.sadd(room_name, name)
    await socket.send(OkResponse().to_json())
    return name, room_name


async def new_client_connect(client_socket: websockets.WebSocketClientProtocol, path: str):
    name, room = await client_login(client_socket, path)

    if room:
        tasks = [
            await asyncio.create_task(listen_client(client_socket, room, name)),
            await asyncio.create_task(listen_room(client_socket, room))
        ]

        done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

        print("1 + 2")


async def listen_room(socket, room_name, name):
    pool = await get_redis_pool()
    connected = True

    while connected and pool:
        try:
            messages = await pool.xread(streams=[room_name], latest_ids=['$'])
            message = subscriber.get_message()
            message = Message.from_json(message.get('data', '{}'))
            await socket.send(message.to_json())
        except [ConnectionClosedError, ConnectionClosedOK]:
            fields = {
                'msg': '',
                'type': 'message',
                'room': room_name
            }
            await pool.xadd(stream=room_name, fields=fields, message_id=b'*', max_len=1000)
            ws_connected = False

        except ServerConnectionClosedError:
            print('redis server connection closed')
            return

        except ConnectionRefusedError:
            print('redis server connection closed')
            return


async def listen_client(socket, room_name, name):
    publisher = redis_room
    print('2')
    try:
        while True:
            raw_message = await socket.recv()
            json_message = json.loads(raw_message)
            match json_message.get('type', None):
                case 'message':
                    message = MessageRequest.from_json(raw_message)
                    redis_message = Message(user=name, text=message.text, time=datetime.now())
                    _ = publisher.publish(room_name, redis_message.to_json())
                    await socket.send(redis_message.to_json())
                case _:
                    await socket.send('неверный тип запроса')
    finally:
        room = redis_room.get(room_name)
        room = Room.from_json(room)
        room.users.remove(name)
        _ = redis_room.set(room.name, room.to_json())


async def start_server():
    await websockets.serve(new_client_connect, "localhost", 9090)


if __name__ == "__main__":
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    event_loop.run_until_complete(start_server())
    event_loop.run_forever()
