"""
安全中间件 - Helmet Headers
"""

try:
    from fastapi.middleware.base import BaseHTTPMiddleware
except ImportError:
    from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class HelmetMiddleware(BaseHTTPMiddleware):
    """安全 Headers 中间件"""

    # 默认安全 Headers
    DEFAULT_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }

    def __init__(self, app, csp: str = None):
        super().__init__(app)
        self.headers = self.DEFAULT_HEADERS.copy()
        if csp:
            self.headers["Content-Security-Policy"] = csp

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # 添加安全 Headers
        for key, value in self.headers.items():
            if key not in response.headers:
                response.headers[key] = value

        # 移除敏感 Headers
        response.headers.pop("X- Powered-By", None)

        return response


# HSTS 中间件 (生产环境使用)
class HSTSMiddleware(BaseHTTPMiddleware):
    """HTTP Strict Transport Security"""

    def __init__(self, app, max_age: int = 31536000, include_subdomains: bool = True):
        super().__init__(app)
        self.max_age = max_age
        self.include_subdomains = include_subdomains

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # 只有 HTTPS 请求才添加 HSTS
        if request.url.scheme == "https":
            value = f"max-age={self.max_age}"
            if self.include_subdomains:
                value += "; includeSubDomains"
            response.headers["Strict-Transport-Security"] = value

        return response


# CORS 安全配置
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI


def add_security_middleware(app: FastAPI, cors_origins: list = None):
    """添加所有安全中间件"""

    # Rate Limiting
    from app.middleware.rate_limit import RateLimitMiddleware

    app.add_middleware(RateLimitMiddleware, calls=100, period=60)

    # Helmet Headers
    app.add_middleware(
        HelmetMiddleware,
        csp="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
    )

    # HSTS (生产环境)
    if not app.debug:
        app.add_middleware(HSTSMiddleware, max_age=31536000)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins or ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
