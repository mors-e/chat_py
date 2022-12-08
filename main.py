import redis
import asyncio
import websockets


redis_client = redis.Redis(host="localhost", port=6379)


async def Send_Message(message: str):
    """определяем в какую комнату отрпавить сообщениие всем пользователям комнаты"""
    pass


async def New_Client_Connect():
    """
    клиент отправляет имя компьютера и слово redis
    тогда мы определяем, что это redis-client
    иначе ждём сообщения с паролем и подключаем к комнате

    recv data, check password in list, if ok, connect to room id, save to session(connect esteblished(ping), 
    in room to clients (rb_client, user_client)
    rb-send=>user_client
    user_client=>send=>rb_client
    """
    pass


async def Start_Server():
    await websockets.serve(New_Client_Connect, "localhost", 9090)


if __name__ == "__main__":
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(Start_Server())
    event_loop.run_forever()
