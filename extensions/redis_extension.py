"""
Redis extension.

Creates a Redis client using the REDIS_URL environment variable.
"""

import os
from redis import Redis

def get_redis_client() -> Redis:
    """Return a Redis client instance.
    
    Returns:
        Redis client connected to the specified REDIS_URL.
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(redis_url, decode_responses=True)
