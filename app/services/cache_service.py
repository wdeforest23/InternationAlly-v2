from redis import asyncio as aioredis
import json
from typing import Optional, Any, Dict
from datetime import timedelta
import os

class CacheService:
    def __init__(self):
        redis_url = os.getenv('REDIS_URL', 'redis://localhost')
        self.redis = aioredis.from_url(redis_url)
        self.default_ttl = timedelta(hours=1)
    
    async def get_housing_data(self, params: Dict[str, Any]) -> Optional[list]:
        """Get cached housing data"""
        cache_key = f"housing:{self._hash_params(params)}"
        data = await self.redis.get(cache_key)
        return json.loads(data) if data else None
    
    async def set_housing_data(self, params: Dict[str, Any], data: list):
        """Cache housing data"""
        cache_key = f"housing:{self._hash_params(params)}"
        await self.redis.set(
            cache_key,
            json.dumps(data),
            ex=self.default_ttl
        )
    
    async def get_places_data(self, params: Dict[str, Any]) -> Optional[list]:
        """Get cached places data"""
        cache_key = f"places:{self._hash_params(params)}"
        data = await self.redis.get(cache_key)
        return json.loads(data) if data else None
    
    async def set_places_data(self, params: Dict[str, Any], data: list):
        """Cache places data"""
        cache_key = f"places:{self._hash_params(params)}"
        await self.redis.set(
            cache_key,
            json.dumps(data),
            ex=self.default_ttl
        )
    
    def _hash_params(self, params: Dict[str, Any]) -> str:
        """Create a consistent hash for parameters"""
        sorted_params = dict(sorted(params.items()))
        return json.dumps(sorted_params, sort_keys=True) 