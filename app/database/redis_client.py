"""Redis client for configuration storage."""

import json
import logging
from typing import Any, Optional
import redis
from app.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client for storing configuration and cache data."""
    
    def __init__(self) -> None:
        """Initialize Redis client."""
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True,
        )
    
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        try:
            self.client.ping()
            return True
        except redis.ConnectionError:
            return False
    
    def set_config(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set configuration value in Redis."""
        try:
            serialized_value = json.dumps(value)
            self.client.set(key, serialized_value, ex=expire)
            logger.info(f"Config set: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to set config {key}: {e}")
            return False
    
    def get_config(self, key: str) -> Optional[Any]:
        """Get configuration value from Redis."""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get config {key}: {e}")
            return None
    
    def delete_config(self, key: str) -> bool:
        """Delete configuration value from Redis."""
        try:
            result = self.client.delete(key)
            logger.info(f"Config deleted: {key}")
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete config {key}: {e}")
            return False
    
    def set_cache(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set cache value in Redis."""
        return self.set_config(f"cache:{key}", value, expire)
    
    def get_cache(self, key: str) -> Optional[Any]:
        """Get cache value from Redis."""
        return self.get_config(f"cache:{key}")


redis_client = RedisClient()
