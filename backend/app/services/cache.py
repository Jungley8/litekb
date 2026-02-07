"""
Redis 缓存服务
"""

import json
import os
from typing import Optional, Any, Dict, List
from datetime import timedelta
from loguru import logger


class CacheService:
    """缓存服务"""

    def __init__(self):
        self._enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"
        self._redis = None
        self._local_cache: Dict[str, Any] = {}
        self._local_ttl: Dict[str, float] = {}

    async def get_redis(self):
        """获取 Redis 连接"""
        if self._redis is None and self._enabled:
            try:
                import redis.asyncio as redis

                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                self._redis = redis.from_url(redis_url)
                logger.info("Redis 连接成功")
            except Exception as e:
                logger.warning(f"Redis 连接失败，使用本地缓存: {e}")
                self._enabled = False
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        # 尝试 Redis
        redis_client = await self.get_redis()
        if redis_client:
            try:
                value = await redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get failed: {e}")

        # 回退到本地缓存
        if key in self._local_cache:
            if self._local_ttl.get(key, 0) > datetime.utcnow().timestamp():
                return self._local_cache[key]
            else:
                del self._local_cache[key]
                del self._local_ttl[key]

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
    ) -> bool:
        """设置缓存"""

        serialized = json.dumps(value, ensure_ascii=False, default=str)

        # 尝试 Redis
        redis_client = await self.get_redis()
        if redis_client:
            try:
                await redis_client.setex(key, ttl_seconds, serialized)
                return True
            except Exception as e:
                logger.error(f"Redis set failed: {e}")

        # 回退到本地缓存
        self._local_cache[key] = value
        self._local_ttl[key] = datetime.utcnow().timestamp() + ttl_seconds
        return True

    async def delete(self, key: str) -> bool:
        """删除缓存"""

        redis_client = await self.get_redis()
        if redis_client:
            try:
                await redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete failed: {e}")

        self._local_cache.pop(key, None)
        self._local_ttl.pop(key, None)
        return True

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""

        redis_client = await self.get_redis()
        if redis_client:
            try:
                return await redis_client.exists(key) > 0
            except Exception as e:
                logger.error(f"Redis exists failed: {e}")

        return key in self._local_cache

    async def clear_pattern(self, pattern: str):
        """清除匹配模式的键"""

        redis_client = await self.get_redis()
        if redis_client:
            try:
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"Redis clear pattern failed: {e}")

        # 清除本地缓存
        import fnmatch

        for key in list(self._local_cache.keys()):
            if fnmatch.fnmatch(key, pattern):
                del self._local_cache[key]
                del self._local_ttl[key]

    async def close(self):
        """关闭连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None


# 便捷方法
from datetime import datetime


class CachedProperty:
    """缓存属性装饰器"""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Any] = {}
        self._ttl: Dict[str, float] = {}

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{args}:{kwargs}"
            now = datetime.utcnow().timestamp()

            if key in self._cache and self._ttl.get(key, 0) > now:
                return self._cache[key]

            result = func(*args, **kwargs)
            self._cache[key] = result
            self._ttl[key] = now + self.ttl_seconds
            return result

        return wrapper


# 全局缓存实例
cache = CacheService()


# RAG 缓存优化
async def get_cached_rag_response(
    query: str,
    kb_id: str,
    cache: CacheService = None,
) -> Optional[Dict]:
    """获取缓存的 RAG 响应"""
    cache = cache or cache
    cache_key = f"rag:{kb_id}:{hash(query)}"
    return await cache.get(cache_key)


async def set_cached_rag_response(
    query: str,
    kb_id: str,
    response: Dict,
    ttl_seconds: int = 3600,
    cache: CacheService = None,
) -> bool:
    """缓存 RAG 响应"""
    cache = cache or cache
    cache_key = f"rag:{kb_id}:{hash(query)}"
    return await cache.set(cache_key, response, ttl_seconds)


# 检索结果缓存
async def get_cached_search_results(
    query: str,
    kb_id: str,
    strategy: str,
    cache: CacheService = None,
) -> Optional[List[Dict]]:
    """获取缓存的检索结果"""
    cache = cache or cache
    cache_key = f"search:{kb_id}:{strategy}:{hash(query)}"
    return await cache.get(cache_key)


async def set_cached_search_results(
    query: str,
    kb_id: str,
    strategy: str,
    results: List[Dict],
    ttl_seconds: int = 600,  # 检索结果缓存 10 分钟
    cache: CacheService = None,
) -> bool:
    """缓存检索结果"""
    cache = cache or cache
    cache_key = f"search:{kb_id}:{strategy}:{hash(query)}"
    return await cache.set(cache_key, results, ttl_seconds)
