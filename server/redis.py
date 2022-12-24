import aioredis


REDIS_HOST = 'localhost'
REDIS_PORT = '6379'


async def get_redis_pool():
    try:
        pool = await aioredis.create_redis_pool((REDIS_HOST, REDIS_PORT), encoding='utf-8')
        return pool
    except ConnectionRefusedError as e:
        print('cannot connect to redis on:', 'localhost', '6379')
        return None
