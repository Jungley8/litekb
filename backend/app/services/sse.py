"""
SSE 流式响应服务
"""

from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime
from loguru import logger
import json
import asyncio


class SSEEvent:
    """SSE 事件"""

    CHUNK = "chunk"
    SOURCES = "sources"
    DONE = "done"
    ERROR = "error"
    PROGRESS = "progress"

    def __init__(self, event_type: str, data: Any = None):
        self.event_type = event_type
        self.data = data
        self.id = None
        self.retry = None

    def to_string(self) -> str:
        """转换为 SSE 格式"""
        lines = []

        if self.id:
            lines.append(f"id: {self.id}")

        if self.event_type:
            lines.append(f"event: {self.event_type}")

        if self.data is not None:
            if isinstance(self.data, (dict, list)):
                content = json.dumps(self.data, ensure_ascii=False)
            else:
                content = str(self.data)
            for line in content.split("\n"):
                lines.append(f"data: {line}")

        if self.retry:
            lines.append(f"retry: {self.retry}")

        return "\n".join(lines) + "\n\n"

    @classmethod
    def chunk(cls, content: str, chunk_id: int = None) -> "SSEEvent":
        """创建内容块事件"""
        event = cls(cls.CHUNK, content)
        event.id = str(chunk_id) if chunk_id else None
        return event

    @classmethod
    def sources(cls, sources: list) -> "SSEEvent":
        """创建来源事件"""
        return cls(cls.SOURCES, {"sources": sources})

    @classmethod
    def done(cls) -> "SSEEvent":
        """创建完成事件"""
        return cls(cls.DONE, {"status": "completed"})

    @classmethod
    def error(cls, message: str) -> "SSEEvent":
        """创建错误事件"""
        return cls(cls.ERROR, {"detail": message})

    @classmethod
    def progress(cls, progress: int, message: str = "") -> "SSEEvent":
        """创建进度事件"""
        return cls(cls.PROGRESS, {"progress": progress, "message": message})


class StreamBuffer:
    """流式缓冲区"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._chunks = []
        self._sources = []
        self._complete = False

    def add_chunk(self, chunk: str):
        """添加内容块"""
        self._chunks.append(chunk)
        # 限制缓冲区大小
        if len(self._chunks) > self.max_size:
            self._chunks.pop(0)

    def add_sources(self, sources: list):
        """添加来源"""
        self._sources.extend(sources)

    def complete(self):
        """标记完成"""
        self._complete = True

    @property
    def content(self) -> str:
        return "".join(self._chunks)

    @property
    def sources(self) -> list:
        return self._sources

    @property
    def is_complete(self) -> bool:
        return self._complete


class SSEStreamService:
    """SSE 流式服务"""

    def __init__(self):
        self._active_streams: Dict[str, StreamBuffer] = {}

    def create_stream(self, stream_id: str) -> StreamBuffer:
        """创建流"""
        buffer = StreamBuffer()
        self._active_streams[stream_id] = buffer
        return buffer

    def get_stream(self, stream_id: str) -> Optional[StreamBuffer]:
        """获取流"""
        return self._active_streams.get(stream_id)

    def close_stream(self, stream_id: str):
        """关闭流"""
        if stream_id in self._active_streams:
            del self._active_streams[stream_id]

    async def generate_stream(
        self,
        stream_id: str,
        chunks: AsyncGenerator[str, None],
        sources: list = None,
    ) -> AsyncGenerator[str, None]:
        """生成 SSE 流"""
        buffer = self.create_stream(stream_id)

        try:
            # 发送来源
            if sources:
                yield SSEEvent.sources(sources).to_string()

            # 发送内容块
            chunk_id = 0
            async for chunk in chunks:
                buffer.add_chunk(chunk)
                yield SSEEvent.chunk(chunk, chunk_id).to_string()
                chunk_id += 1

            # 标记完成
            buffer.complete()
            yield SSEEvent.done().to_string()

        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield SSEEvent.error(str(e)).to_string()
            self.close_stream(stream_id)

    async def rag_stream(
        self,
        stream_id: str,
        rag_engine,
        kb_id: str,
        message: str,
        mode: str = "naive",
    ) -> AsyncGenerator[str, None]:
        """RAG 流式响应"""

        buffer = self.create_stream(stream_id)
        sources = []

        try:
            # 1. 检索阶段
            yield SSEEvent.progress(10, "正在检索相关文档...").to_string()

            # 获取检索结果
            from app.services.search import search_service

            results = await search_service.hybrid_search(
                query=message,
                kb_id=kb_id,
                top_k=10,
            )

            sources = [
                {"id": r.id, "title": r.get("title", ""), "score": r.get("score", 0)}
                for r in results
            ]
            yield SSEEvent.sources(sources).to_string()
            yield SSEEvent.progress(30, f"找到 {len(results)} 篇相关文档").to_string()

            # 2. 生成阶段
            yield SSEEvent.progress(40, "正在生成回答...").to_string()

            # 使用流式 LLM 调用
            messages = [
                {
                    "role": "system",
                    "content": "基于以下上下文回答问题。\n\n"
                    + "\n\n".join([r.get("content", "") for r in results[:5]]),
                },
                {"role": "user", "content": message},
            ]

            # 获取流式响应
            from app.services.model_provider import model_client

            async for chunk in model_client.chat_stream(
                messages=messages,
                temperature=0.1,
                max_tokens=2000,
            ):
                if chunk:
                    buffer.add_chunk(chunk)
                    yield SSEEvent.chunk(chunk).to_string()

            # 3. 完成
            buffer.complete()
            yield SSEEvent.progress(100, "回答生成完成").to_string()
            yield SSEEvent.done().to_string()

        except Exception as e:
            logger.error(f"RAG stream error: {e}")
            yield SSEEvent.error(str(e)).to_string()
            self.close_stream(stream_id)


# 全局实例
sse_service = SSEStreamService()
