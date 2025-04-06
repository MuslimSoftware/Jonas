import functools
import json
import hashlib
import inspect
from typing import Callable, Any, Optional
from starlette.requests import Request
from redis.asyncio import Redis # Import the type hint

def manual_cache(expiry_seconds: int) -> Callable:
    """
    Manual caching decorator.

    Assumes the decorated function receives a 'starlette.requests.Request' object
    as one of its arguments, and that the Redis client instance is available
    via 'request.state.redis'.

    Caches the JSON-serializable result of the function based on its name
    and the hash of its arguments (excluding the Request object).
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request_obj: Optional[Request] = None
            redis_client: Optional[Redis] = None
            args_for_key = []
            kwargs_for_key = {}

            # 1. Find Request object and Redis client
            for arg in args:
                if isinstance(arg, Request):
                    request_obj = arg
                    try:
                        redis_client = request_obj.state.redis
                    except AttributeError:
                        raise RuntimeError("Redis client not found in request.state.redis. Ensure it's set by middleware or dependency.")
                    # Don't include request in cache key args
                else:
                    args_for_key.append(arg)

            if not request_obj:
                 for key, value in kwargs.items():
                    if isinstance(value, Request):
                        request_obj = value
                        try:
                            redis_client = request_obj.state.redis
                        except AttributeError:
                             raise RuntimeError("Redis client not found in request.state.redis. Ensure it's set by middleware or dependency.")
                         # Don't include request in cache key kwargs
                    else:
                        kwargs_for_key[key] = value

            if not request_obj or not redis_client:
                raise TypeError(f"Function '{func.__name__}' must be called with a 'starlette.requests.Request' argument containing 'request.state.redis' for caching.")

            # 2. Generate Cache Key
            # Simple key: function name + hash of args/kwargs representation
            # Convert args/kwargs to a stable string representation for hashing
            # Using inspect might be needed for complex defaults, but repr is simpler start
            try:
                 key_payload = f"{func.__name__}:{repr(tuple(args_for_key))}:{repr(sorted(kwargs_for_key.items()))}"
                 key_hash = hashlib.md5(key_payload.encode()).hexdigest()
                 cache_key = f"manual_cache:{key_hash}"
            except Exception as e:
                 # Handle cases where args/kwargs are not easily representable
                 print(f"Warning: Could not generate cache key for {func.__name__}: {e}")
                 # Fallback: Execute function without caching for this call
                 return await func(*args, **kwargs)


            # 3. Check Cache
            try:
                cached_result_json = await redis_client.get(cache_key)
                if cached_result_json:
                    print(f"Cache HIT for {func.__name__} with key {cache_key}")
                    try:
                        return json.loads(cached_result_json)
                    except json.JSONDecodeError:
                         print(f"Warning: Could not decode cached JSON for {func.__name__}. Refetching.")
                         # Treat as miss if decoding fails
            except Exception as e:
                 print(f"Warning: Redis GET failed for {func.__name__}: {e}. Proceeding without cache.")
                 # Fallback on Redis error


            # 4. Cache Miss: Execute function, store result
            print(f"Cache MISS for {func.__name__} with key {cache_key}")
            result = await func(*args, **kwargs)

            # TODO: SERIALIZATION - Ensure the 'result' is JSON serializable.
            # If 'result' is a Pydantic model, consider returning result.model_dump() from the decorated function.
            try:
                result_json = json.dumps(result) # Assumes result is JSON serializable
            except TypeError:
                 print(f"Warning: Result of {func.__name__} is not JSON serializable. Cannot cache.")
                 return result # Return original non-serializable result

            try:
                 await redis_client.set(cache_key, result_json, ex=expiry_seconds)
            except Exception as e:
                 print(f"Warning: Redis SET failed for {func.__name__}: {e}. Result not cached.")
                 # Still return the computed result even if caching fails

            return result

        return wrapper
    return decorator

# TODO: CACHE INVALIDATION - Implement a strategy to delete relevant cache keys
# when underlying data is modified (e.g., in PUT/POST/DELETE handlers or service/repo layers).
# Example: await request.state.redis.delete(cache_key_to_invalidate) 