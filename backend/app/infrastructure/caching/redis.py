import redis.asyncio as redis
from app.config.environment import environment
from typing import Optional

_redis_pool: Optional[redis.ConnectionPool] = None

def init_redis_pool():
    """Initialize Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool(
            host=environment.REDIS_HOST,
            port=environment.REDIS_PORT,
            db=environment.REDIS_DB,
            decode_responses=True
        )

def close_redis_pool():
    """Close Redis connection pool."""
    global _redis_pool
    if _redis_pool:
        _redis_pool = None
        print("Redis pool 'closed' (set to None).") # Log for confirmation

def get_redis_client() -> redis.Redis:
    """Get a Redis client from the pool."""
    if _redis_pool is None:
        raise RuntimeError("Redis pool is not initialized. Call init_redis_pool() first.")
    return redis.Redis(connection_pool=_redis_pool)
