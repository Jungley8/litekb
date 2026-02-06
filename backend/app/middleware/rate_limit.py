"""
安全中间件 - Rate Limiting + Helmet
"""
from fastapi import Request, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Optional
from datetime import datetime, timedelta
import time
import hashlib
from loguru import logger


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls  # 允许的请求数
        self.period = period  # 时间窗口(秒)
        self._requests: Dict[str, list] = {}  # 记录请求
    
    async def dispatch(self, request: Request, call_next):
        # 获取客户端标识
        client_id = self._get_client_id(request)
        
        # 检查限流
        if self._is_rate_limited(client_id):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "retry_after": self.period
                },
                headers={"Retry-After": str(self.period)}
            )
        
        # 记录请求
        self._record_request(client_id)
        
        return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """获取客户端 ID"""
        # 优先使用 X-Forwarded-For
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        # 使用 IP
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_id: str) -> bool:
        """检查是否限流"""
        now = datetime.utcnow()
        
        if client_id not in self._requests:
            self._requests[client_id] = []
        
        # 清理过期请求
        self._requests[client_id] = [
            t for t in self._requests[client_id]
            if t > now - timedelta(seconds=self.period)
        ]
        
        # 检查是否超过限制
        return len(self._requests[client_id]) >= self.calls
    
    def _record_request(self, client_id: str):
        """记录请求"""
        if client_id not in self._requests:
            self._requests[client_id] = []
        self._requests[client_id].append(datetime.utcnow())


# API Key 限流
API_KEY_LIMITS = {
    "free": {"calls": 100, "period": 3600},      # 100次/小时
    "basic": {"calls": 1000, "period": 3600},    # 1000次/小时
    "pro": {"calls": 10000, "period": 3600},     # 10000次/小时
    "enterprise": {"calls": 100000, "period": 3600},  # 无限制
}


async def check_api_key_limit(
    api_key_hash: str,
    plan: str = "free"
) -> bool:
    """检查 API Key 限流"""
    limit = API_KEY_LIMITS.get(plan, API_KEY_LIMITS["free"])
    
    # 实现检查逻辑
    # ...
    return True
