"""
自动追踪中间件
"""

from typing import Callable, Dict, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from loguru import logger

try:
    from app.tracing.langfuse import langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    langfuse = None


class TracingMiddleware(BaseHTTPMiddleware):
    """自动追踪中间件"""

    # 不追踪的路径
    EXCLUDE_PATHS = {
        "/health",
        "/ready",
        "/metrics",
        "/favicon.ico",
        "/static",
    }

    def __init__(self, app, trace_all: bool = False):
        super().__init__(app)
        self.trace_all = trace_all

    async def dispatch(self, request: Request, call_next: Callable):
        # 排除不需要追踪的路径
        if request.url.path in self.EXCLUDE_PATHS:
            return await call_next(request)

        # 只追踪 API 请求
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        start_time = time.time()
        trace = None

        try:
            # 创建追踪
            if LANGFUSE_AVAILABLE and langfuse.enabled:
                trace = langfuse.create_trace(
                    name=f"{request.method} {request.url.path}",
                    metadata={
                        "method": request.method,
                        "path": request.url.path,
                        "query_params": dict(request.query_params),
                        "user_agent": request.headers.get("user-agent"),
                        "ip": request.client.host if request.client else None,
                    },
                )

                # 记录请求
                trace.event(
                    "request_received",
                    {
                        "body_size": request.headers.get("content-length", 0),
                    },
                )

            # 执行请求
            response = await call_next(request)

            duration = (time.time() - start_time) * 1000

            # 记录响应
            if LANGFUSE_AVAILABLE and langfuse.enabled:
                trace.event(
                    "response_sent",
                    {
                        "status_code": response.status_code,
                        "duration_ms": duration,
                    },
                )

                # 结束追踪
                trace.end(
                    {
                        "status_code": response.status_code,
                        "duration_ms": duration,
                    }
                )

            # 记录慢请求
            if duration > 5000:  # > 5s
                logger.warning(
                    f"[Slow Request] {request.method} {request.url.path}: "
                    f"{duration:.2f}ms"
                )

            return response

        except Exception as e:
            duration = (time.time() - start_time) * 1000

            if LANGFUSE_AVAILABLE and langfuse.enabled and trace:
                trace.event(
                    "error",
                    {
                        "error": str(e),
                        "duration_ms": duration,
                    },
                )
                trace.end({"error": True})

            logger.error(f"[Request Error] {request.method} {request.url.path}: {e}")

            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )


# RAG 追踪集成
class RAGTracing:
    """RAG 流程追踪"""

    def __init__(self):
        self.langfuse = langfuse
        self.enabled = LANGFUSE_AVAILABLE

    async def trace_rag_query(
        self,
        kb_id: str,
        query: str,
        mode: str,
        func,
    ):
        """追踪 RAG 查询"""
        if not self.enabled:
            return await func()

        start_time = time.time()
        trace = None
        retrieval_span = None
        generation_span = None

        try:
            # 创建追踪
            with self.langfuse.trace_context(
                name=f"rag.query.{mode}",
                metadata={
                    "kb_id": kb_id,
                    "query": query[:500],
                    "mode": mode,
                },
            ) as trace:
                # 检索阶段
                retrieval_span = trace.span(
                    name="retrieval",
                    metadata={"strategy": "hybrid"},
                )

                # 执行检索
                results = await func()

                # 结束检索
                retrieval_span.end(
                    {
                        "results_count": len(results),
                        "duration_ms": (time.time() - start_time) * 1000,
                    }
                )

                # 生成阶段
                generation_span = trace.span(
                    name="generation",
                    metadata={"model": "unknown"},
                )

                return results, trace, generation_span

        except Exception as e:
            logger.error(f"RAG tracing failed: {e}")
            return None, None, None

    def end_generation(
        self,
        generation_span,
        completion: str,
        model: str,
        usage: Optional[Dict] = None,
    ):
        """结束生成"""
        if generation_span:
            generation_span.end(
                {
                    "completion_length": len(completion) if completion else 0,
                    "model": model,
                    "input_tokens": usage.get("input_tokens", 0) if usage else 0,
                    "output_tokens": usage.get("output_tokens", 0) if usage else 0,
                }
            )


# 全局 RAG 追踪器
rag_tracing = RAGTracing()
