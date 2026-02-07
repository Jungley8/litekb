"""
RAG 引擎 - 支持多供应商切换 + Langfuse 提示词
"""

from typing import List, Dict, Optional, AsyncGenerator
from datetime import datetime
from loguru import logger
from dataclasses import dataclass

from app.config import settings
from app.services.search import search_service
from app.services.vector import vector_store
from app.services.graph import graph_service
from app.services.model_provider import (
    model_client,
    ProviderType,
    ModelConfig,
)
from app.services.prompt import rag_prompt


@dataclass
class RAGConfig:
    """RAG 配置"""

    provider: ProviderType = ProviderType.OPENAI
    model: str = None
    temperature: float = 0.1
    max_tokens: int = 4000
    top_k: int = 10
    chunk_size: int = 512
    mode: str = "naive"  # naive / contextual / graph-augmented
    stream: bool = True


class RAGEngine:
    """RAG 引擎"""

    def __init__(self, config: RAGConfig = None):
        self.config = config or RAGConfig()
        self._init_providers()

    def _init_providers(self):
        """初始化供应商"""
        # 注册 Ollama (如果配置了)
        if settings.ollama_url:
            try:
                from app.services.ollama import OllamaClient

                model_client.register_provider(
                    ProviderFactory.create_ollama(settings.ollama_url)
                )
                logger.info("Ollama provider registered")
            except Exception as e:
                logger.warning(f"Failed to register Ollama: {e}")

        # 注册 vLLM (如果配置了)
        if settings.vllm_url:
            try:
                from app.services.vllm import VLLMClient

                model_client.register_provider(
                    ProviderFactory.create_vllm(settings.vllm_url)
                )
                logger.info("vLLM provider registered")
            except Exception as e:
                logger.warning(f"Failed to register vLLM: {e}")

        # 默认 OpenAI
        if not model_client._providers:
            model_client.set_default(ProviderType.OPENAI)

    async def chat(
        self,
        kb_id: str,
        message: str,
        history: List[Dict] = None,
        stream: bool = None,
    ) -> AsyncGenerator[str, None]:
        """对话"""

        config = self.config
        stream = stream if stream is not None else config.stream

        # 1. 检索
        search_results = await search_service.hybrid_search(
            query=message,
            kb_id=kb_id,
            top_k=config.top_k,
        )

        # 2. 构建上下文
        context = self._build_context(search_results)

        # 3. 构建消息
        messages = self._build_messages(message, context, history)

        # 4. 生成回答
        if stream:
            async for chunk in model_client.chat_stream(
                messages=messages,
                model=config.model,
                provider=config.provider,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            ):
                yield chunk
        else:
            response = await model_client.chat(
                messages=messages,
                model=config.model,
                provider=config.provider,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
            yield response

    def _build_context(self, results: List[Dict]) -> str:
        """构建上下文"""
        context_parts = []

        for i, r in enumerate(results, 1):
            context_parts.append(f"[{i}] {r.get('content', '')}")

        return "\n\n".join(context_parts)

    def _build_messages(
        self,
        message: str,
        context: str,
        history: List[Dict] = None,
    ) -> List[Dict]:
        """构建消息 - 使用 Langfuse 提示词"""

        # 获取历史文本
        history_text = ""
        if history:
            for h in history[-5:]:  # 只取最近5轮
                role = h.get("role", "user")
                content = h.get("content", "")
                history_text += f"{role}: {content}\n"

        # 使用 Langfuse 提示词
        system_prompt = rag_prompt(
            mode=self.config.mode,
            question=message,
            context=context,
            history=history_text,
        )

        messages = [{"role": "system", "content": system_prompt}]

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": message})

        return messages

    async def get_embedding(self, text: str) -> List[float]:
        """获取嵌入"""
        return await model_client.embed(
            text=text,
            provider=self.config.provider,
        )


# 便捷函数
async def get_available_providers() -> List[Dict]:
    """获取可用供应商"""
    providers = []

    for ptype, prov in model_client._providers.items():
        models = await prov.list_models()
        providers.append(
            {
                "type": ptype.value,
                "name": ptype.value.upper(),
                "models": models,
                "capabilities": [c.value for c in prov.capabilities],
            }
        )

    return providers


async def switch_provider(
    provider: str,
    model: str = None,
) -> bool:
    """切换供应商"""

    try:
        ptype = ProviderType(provider)
        model_client.set_default(ptype, model)
        return True
    except Exception as e:
        logger.error(f"Switch provider failed: {e}")
        return False


def get_current_config() -> Dict:
    """获取当前配置"""
    return {
        "provider": model_client._default_provider.value,
        "model": model_client._default_model,
    }
