"""
Token 黑名单服务
"""
from typing import Optional, List
from datetime import datetime, timedelta
from loguru import logger

# Redis 黑名单
_blacklist = set()


async def add_to_blacklist(token: str, expires_in: int = 86400) -> None:
    """将 Token 加入黑名单"""
    from app.config import settings
    
    if hasattr(settings, 'redis_url') and settings.redis_url:
        try:
            import redis.asyncio as redis
            client = redis.from_url(settings.redis_url)
            await client.setex(
                f"blacklist:{token[:32]}",
                expires_in,
                "revoked"
            )
            logger.info(f"Token added to Redis blacklist")
        except Exception as e:
            logger.error(f"Redis blacklist failed: {e}")
            _blacklist.add(token[:32])
    else:
        _blacklist.add(token[:32])


async def is_blacklisted(token: str) -> bool:
    """检查 Token 是否在黑名单"""
    from app.config import settings
    
    token_hash = token[:32]
    
    if hasattr(settings, 'redis_url') and settings.redis_url:
        try:
            import redis.asyncio as redis
            client = redis.from_url(settings.redis_url)
            result = await client.get(f"blacklist:{token_hash}")
            return result is not None
        except Exception as e:
            logger.error(f"Redis blacklist check failed: {e}")
            return token_hash in _blacklist
    else:
        return token_hash in _blacklist


async def remove_from_blacklist(token: str) -> bool:
    """从黑名单移除"""
    from app.config import settings
    
    token_hash = token[:32]
    
    if hasattr(settings, 'redis_url') and settings.redis_url:
        try:
            import redis.asyncio as redis
            client = redis.from_url(settings.redis_url)
            await client.delete(f"blacklist:{token_hash}")
            return True
        except Exception as e:
            logger.error(f"Redis blacklist remove failed: {e}")
            _blacklist.discard(token_hash)
            return True
    else:
        _blacklist.discard(token_hash)
        return True


def cleanup_blacklist() -> int:
    """清理过期 Token (内存模式)"""
    # Redis 模式自动清理
    # 内存模式需要手动清理
    removed = 0
    # 实际实现时应该跟踪过期时间
    logger.info(f"Blacklist cleanup: {len(_blacklist)} tokens")
    return removed
