import redis.asyncio as redis
from app.config.env import settings

_redis_pool = None

async def init_redis_pool():
    """Initialize Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

async def close_redis_pool():
    """Close Redis connection pool."""
    global _redis_pool
    if _redis_pool:
        # redis-py doesn't have an explicit async close for the pool itself,
        # connections are managed individually. We just need to reset our variable.
        # For individual client connections, use client.close() and client.wait_closed()
        # but the pool manages this. Setting to None signifies it's closed for our app logic.
        _redis_pool = None
        print("Redis pool 'closed' (set to None).") # Log for confirmation

async def get_redis_client() -> redis.Redis:
    """Get a Redis client from the pool."""
    if _redis_pool is None:
        raise RuntimeError("Redis pool is not initialized. Call init_redis_pool() first.")
    return redis.Redis(connection_pool=_redis_pool)
