import websockets
import asyncio
import redis
import json
from datetime import datetime

from common.messages import MessageRequest, OkResponse, ErrResponse
from common.redis_structures import Room, Message


redis_room = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
redis_room.set("123", '{"users":[], "name": "123"}')


async def client_login(socket, path):
    splitted_path = path.split('?')
    room_name = splitted_path.pop(0).replace('/', '')
    name = splitted_path.pop(0).split('=').pop(1)

    room = redis_room.get(room_name)
    if room is None:
        await socket.send(ErrResponse(error='такой пароль не существует').to_json(ensure_ascii=False))
        return None, None

    room = Room.from_json(room)

    if name in room.users:
        await socket.send(ErrResponse(error='пользователь уже в комнате').to_json(ensure_ascii=False))
        return None, None

    room.users.append(name)
    _ = redis_room.set(room_name, room.to_json())
    await socket.send(OkResponse().to_json())
    return name, room


async def new_client_connect(client_socket: websockets.WebSocketClientProtocol, path: str):
    name, room = await client_login(client_socket, path)

    if room:
        tasks = [
            listen_room(client_socket, room.name),
            listen_client(client_socket, room.name, name)
        ]

        errors = await asyncio.gather(*tasks, return_exceptions=True)

        print("лох + пидор", errors)

        room = redis_room.get(room.name)
        room = Room.from_json(room)
        room.users.remove(name)
        _ = redis_room.set(room.name, room.to_json())


async def listen_room(socket, room_name):
    subscriber = redis_room.pubsub()
    subscriber.subscribed(room_name)
    while True:
        message = subscriber.get_message()
        message = Message.from_json(message.get('data', '{}'))
        await socket.send(message.to_json())
    print('лох')


async def listen_client(socket, room_name, name):
    publisher = redis_room.pubsub()
    while True:
        raw_message = await socket.recv()
        json_message = json.loads(raw_message)
        match json_message.get('type', None):
            case 'message':
                message = MessageRequest.from_json(raw_message)
                redis_message = Message(user=name, text=message.text, time=datetime.now())
                _ = publisher.publish(room_name, redis_message.to_json())
            case _:
                await socket.send('неверный тип запроса')
    print('пидор')


async def start_server():
    await websockets.serve(new_client_connect, "localhost", 9090)


if __name__ == "__main__":
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    event_loop.run_until_complete(start_server())
    event_loop.run_forever()
