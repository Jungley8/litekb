"""
Sentry 错误追踪集成
"""

import os
from loguru import logger
from functools import wraps


class SentryClient:
    """Sentry 客户端"""

    def __init__(self, dsn: str = None):
        self.dsn = dsn or os.getenv("SENTRY_DSN")
        self._client = None

    def init(self):
        """初始化 Sentry"""
        if not self.dsn:
            logger.warning("Sentry DSN not configured")
            return

        try:
            import sentry_sdk

            sentry_sdk.init(
                dsn=self.dsn,
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1,
                environment=os.getenv("ENVIRONMENT", "development"),
                release=os.getenv("VERSION", "1.0.0"),
            )
            self._client = sentry_sdk
            logger.info("Sentry initialized")
        except ImportError:
            logger.warning("sentry-sdk not installed")

    def capture_exception(self, exc: Exception):
        """捕获异常"""
        if self._client:
            self._client.capture_exception(exc)

    def capture_message(self, message: str, level: str = "info"):
        """捕获消息"""
        if self._client:
            self._client.capture_message(message, level=level)


# 全局实例
sentry = SentryClient()


def setup_sentry():
    """设置 Sentry"""
    sentry.init()


class ErrorTracker:
    """错误追踪器"""

    def __init__(self):
        self.errors = []

    async def track_error(self, error: Exception, context: dict = None) -> str:
        """追踪错误"""
        error_id = f"err_{int(time.time())}"

        error_info = {
            "id": error_id,
            "type": type(error).__name__,
            "message": str(error),
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.errors.append(error_info)

        # 发送到 Sentry
        sentry.capture_exception(error)

        # 保留最近 100 个错误
        if len(self.errors) > 100:
            self.errors = self.errors[-100:]

        return error_id

    def get_recent_errors(self, limit: int = 10) -> list:
        """获取最近错误"""
        return self.errors[-limit:]

    def clear_errors(self):
        """清除错误记录"""
        self.errors = []


# 全局错误追踪器
error_tracker = ErrorTracker()


def track_errors(func):
    """错误追踪装饰器"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            await error_tracker.track_error(
                e,
                {
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs),
                },
            )
            raise

    return wrapper
