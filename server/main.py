import websockets
import asyncio
import redis
import json

from server.messages import LoginRequest, MessageRequest, OkResponse, ErrResponse
from redis_structures import Room


redis_room = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
redis_room.set("123", '{"users":[]}')

redis_online_users = redis.Redis(host="localhost", port=6379, db=1, decode_responses=True)


async def new_client_connect(client_socket: websockets.WebSocketClientProtocol, path: str):
    new_message = await client_socket.recv()
    data = json.loads(new_message)
    match data['type']:
        case 'login':
            data = LoginRequest.from_json(new_message)
            is_online = redis_online_users.get(data.name)
            if is_online == '1':
                await client_socket.send(ErrResponse(error='пользователь уже онлайн').to_json(ensure_ascii=False))
            _ = redis_online_users.set(data.name, '1')

            password = redis_room.get(data.password)
            if password is None:
                await client_socket.send(ErrResponse(error='такой пароль не существует').to_json(ensure_ascii=False))

            room = Room.from_json(password)
            room.users.append(data.name)
            _ = redis_room.set(data.password, room.to_json())
            await client_socket.send(OkResponse().to_json())
        case 'message':
            data = MessageRequest.from_json(new_message)
        case _:
            await client_socket.send(ErrResponse(error='некорректный тип сообщения').to_json(ensure_ascii=False))


async def start_server():
    await websockets.serve(new_client_connect, "localhost", 9090)


if __name__ == "__main__":
    event_loop = asyncio.new_event_loop()
    event_loop.run_until_complete(start_server())
    event_loop.run_forever()
