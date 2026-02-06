"""
SSE 流式响应服务
"""
from typing import AsyncGenerator
from loguru import logger
from sse_starlette.sse import EventSourceResponse


async def stream_rag_response(
    rag_engine,
    kb_id: str,
    question: str,
    mode: str = "naive",
    history: list = None
) -> AsyncGenerator[dict, None]:
    """流式 RAG 响应"""
    
    # 先进行检索，获取来源
    try:
        from app.services.search import hybrid_search
        chunks = await hybrid_search.search(
            query=question,
            kb_id=kb_id,
            strategy="hybrid",
            top_k=5
        )
        
        # 发送来源信息
        yield {
            "event": "sources",
            "data": {
                "sources": [
                    {
                        "doc_id": c.id,
                        "title": c.metadata.get("source", "Unknown"),
                        "score": c.score
                    }
                    for c in chunks
                ]
            }
        }
        
        # 构建上下文
        context_parts = []
        for i, chunk in enumerate(chunks):
            context_parts.append(f"[{i+1}] {chunk.content}")
        context = "\n\n".join(context_parts)
        
        # 流式调用 LLM
        from app.config import settings
        if settings.llm_provider == "openai":
            async for chunk in stream_openai(
                question=question,
                context=context,
                system_prompt=_get_system_prompt()
            ):
                yield chunk
        
        elif settings.llm_provider == "ollama":
            async for chunk in stream_ollama(
                question=question,
                context=context,
                system_prompt=_get_system_prompt()
            ):
                yield chunk
        
        # 发送完成信号
        yield {"event": "done", "data": ""}
    
    except Exception as e:
        logger.error(f"流式响应错误: {e}")
        yield {"event": "error", "data": str(e)}


async def stream_openai(
    question: str,
    context: str,
    system_prompt: str
) -> AsyncGenerator[dict, None]:
    """OpenAI 流式响应"""
    from openai import AsyncOpenAI
    from app.config import settings
    
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
    ]
    
    try:
        stream = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=0.7,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield {
                    "event": "message",
                    "data": chunk.choices[0].delta.content
                }
    
    except Exception as e:
        logger.error(f"OpenAI 流式错误: {e}")


async def stream_ollama(
    question: str,
    context: str,
    system_prompt: str
) -> AsyncGenerator[dict, None]:
    """Ollama 流式响应"""
    import httpx
    from openai import AsyncOpenAI
    from app.config import settings
    
    client = AsyncOpenAI(
        api_key="ollama",
        base_url=settings.ollama_url + "/v1"
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
    ]
    
    try:
        stream = await client.chat.completions.create(
            model=settings.ollama_model,
            messages=messages,
            temperature=0.7,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield {
                    "event": "message",
                    "data": chunk.choices[0].delta.content
                }
    
    except Exception as e:
        logger.error(f"Ollama 流式错误: {e}")


def _get_system_prompt() -> str:
    """获取系统提示"""
    return """你是一个知识库助手。请根据提供的上下文回答用户的问题。

要求：
1. 只基于上下文回答，不要编造信息
2. 如果上下文没有相关信息，请明确说明
3. 回答要简洁、有条理"""


# ==================== FastAPI SSE 端点 ====================

from fastapi import APIRouter, Depends
from sse_starlette import EventSourceResponse
from app.main import get_current_user

router = APIRouter()


@router.get("/kb/{kb_id}/chat/stream")
async def stream_chat(
    kb_id: str,
    message: str,
    mode: str = "naive",
    current_user = Depends(get_current_user)
):
    """流式 RAG 对话端点"""
    
    # 模拟 history，实际从数据库获取
    history = []
    
    return EventSourceResponse(
        stream_rag_response(
            rag_engine=None,  # TODO: 传入实际 rag_engine
            kb_id=kb_id,
            question=message,
            mode=mode,
            history=history
        )
    )
