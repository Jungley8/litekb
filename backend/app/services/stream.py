"""
流式对话服务
"""

from typing import AsyncGenerator, Optional
from loguru import logger


class StreamService:
    """流式服务"""

    def __init__(self):
        self.active_streams = {}

    async def stream_chat(
        self,
        kb_id: str,
        message: str,
        mode: str = "naive",
        rag_engine=None,
    ) -> AsyncGenerator[str, None]:
        """流式对话"""

        # 模拟流式输出
        chunks = [
            f"收到问题: {message}\n\n",
            "正在检索知识库...\n",
            f"找到相关内容，使用 {mode} 模式处理...\n\n",
            "这是基于知识库的智能回答。\n",
            "回答生成完成。",
        ]

        for chunk in chunks:
            yield f"data: {chunk}\n\n"
            import asyncio

            await asyncio.sleep(0.3)

    async def stream_search(
        self,
        query: str,
        kb_id: str = None,
    ) -> AsyncGenerator[str, None]:
        """流式搜索"""

        steps = [
            "正在分析查询...",
            "向量检索中...",
            "关键词匹配...",
            "融合结果...",
        ]

        for step in steps:
            yield f"data: {step}\n\n"
            import asyncio

            await asyncio.sleep(0.2)

        # 模拟结果
        results = [
            {"title": "相关文档1", "score": 0.95},
            {"title": "相关文档2", "score": 0.87},
        ]

        yield f"data: {results}\n\n"

    def cancel_stream(self, stream_id: str):
        """取消流式"""
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]


stream_service = StreamService()
