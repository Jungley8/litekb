"""
Redis 缓存层
"""

from typing import Optional, Any
from datetime import timedelta
import json
import hashlib

from app.config import settings

# 尝试导入 Redis
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class Cache:
    """Redis 缓存"""

    def __init__(self):
        self.client = None
        self.prefix = "litekb:"

    async def connect(self):
        """连接 Redis"""
        if not REDIS_AVAILABLE:
            return

        if settings.redis_url:
            self.client = redis.from_url(settings.redis_url)

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.client:
            return None

        value = await self.client.get(f"{self.prefix}{key}")
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, expire_seconds: int = 300):
        """设置缓存"""
        if not self.client:
            return

        await self.client.set(
            f"{self.prefix}{key}", json.dumps(value, default=str), ex=expire_seconds
        )

    async def delete(self, key: str):
        """删除缓存"""
        if not self.client:
            return

        await self.client.delete(f"{self.prefix}{key}")

    async def delete_pattern(self, pattern: str):
        """删除匹配的所有缓存"""
        if not self.client:
            return

        keys = await self.client.keys(f"{self.prefix}{pattern}")
        if keys:
            await self.client.delete(*keys)

    def make_key(self, *parts: str) -> str:
        """生成缓存 Key"""
        return hashlib.md5(":".join(parts).encode()).hexdigest()


# 全局缓存实例
cache = Cache()


class CacheMixin:
    """缓存 Mixin"""

    @property
    def cache(self) -> Cache:
        return cache

    async def get_cached(self, key: str):
        return await cache.get(key)

    async def set_cached(self, key: str, value: Any, ttl: int = 300):
        await cache.set(key, value, ttl)


# ==================== 缓存策略 ====================

CACHE_STRATEGIES = {
    # 知识库列表: 5分钟
    "kb_list": {"expire": 300, "versioned": True},
    # 文档列表: 2分钟
    "doc_list": {"expire": 120},
    # RAG 回答: 1小时 (相同问题相同回答)
    "rag_response": {"expire": 3600, "versioned": True},
    # 搜索结果: 10分钟
    "search_results": {"expire": 600},
    # 知识图谱: 30分钟
    "graph_data": {"expire": 1800},
    # 用户设置: 1小时
    "user_settings": {"expire": 3600},
    # 组织信息: 10分钟
    "org_info": {"expire": 600},
}


async def cached_search(
    query: str, kb_id: str, strategy: str = "hybrid", top_k: int = 10, ttl: int = 600
):
    """搜索结果缓存"""
    cache_key = cache.make_key("search", query, kb_id, strategy, str(top_k))

    cached = await cache.get(cache_key)
    if cached is not None:
        return cached

    # 实际搜索逻辑
    from app.services.search import hybrid_search

    results = await hybrid_search.search(query, kb_id, strategy, top_k)

    await cache.set(cache_key, results, ttl)
    return results


async def cached_rag(question: str, kb_id: str, mode: str = "naive", ttl: int = 3600):
    """RAG 回答缓存"""
    cache_key = cache.make_key("rag", question, kb_id, mode)

    cached = await cache.get(cache_key)
    if cached is not None:
        return cached

    # 实际 RAG 逻辑
    from app.services.rag import rag_engine

    response = await rag_engine.query(kb_id, question, mode)

    await cache.set(
        cache_key, {"answer": response.answer, "sources": response.sources}, ttl
    )

    return response


# ==================== 缓存失效 ====================


async def invalidate_kb(kb_id: str):
    """使知识库相关缓存失效"""
    await cache.delete_pattern(f"kb:{kb_id}:*")
    await cache.delete_pattern(f"search:*{kb_id}*")
    await cache.delete(f"graph:{kb_id}")


async def invalidate_doc(doc_id: str, kb_id: str):
    """使文档相关缓存失效"""
    await invalidate_kb(kb_id)


async def invalidate_user(user_id: str):
    """使用户缓存失效"""
    await cache.delete(f"settings:{user_id}")
    await cache.delete(f"orgs:{user_id}")
