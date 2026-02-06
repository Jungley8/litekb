"""
vLLM 本地模型客户端
"""
from typing import List, Dict, Optional, AsyncGenerator
from loguru import logger
from openai import AsyncOpenAI


class VLLMClient:
    """vLLM 客户端 (OpenAI 兼容 API)"""
    
    SUPPORTED_MODELS = [
        "llama-3.2-1b",
        "llama-3.2-3b",
        "llama-3.1-8b",
        "llama-3.1-70b",
        "llama-3-8b",
        "llama-3-70b",
        "qwen-2.5-7b",
        "qwen-2.5-14b",
        "qwen-2.5-32b",
        "mistral-7b",
        "mixtral-8x7b",
        "deepseek-7b",
        "yi-9b",
        "aya-23b",
    ]
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        api_key: str = "sk-no-key",
        timeout: int = 120,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self._client = None
    
    @property
    def client(self) -> AsyncOpenAI:
        """客户端"""
        if self._client is None:
            self._client = AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.timeout,
            )
        return self._client
    
    async def list_models(self) -> List[Dict]:
        """列出可用模型"""
        try:
            models = await self.client.models.list()
            return [
                {
                    "id": m.id,
                    "object": m.object,
                    "created": m.created,
                    "owned_by": m.owned_by,
                }
                for m in models.data
            ]
        except Exception as e:
            logger.error(f"List vLLM models failed: {e}")
            return []
    
    async def generate(
        self,
        prompt: str,
        model: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> str:
        """生成文本 (非流式)"""
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        return await self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )
    
    async def generate_stream(
        self,
        prompt: str,
        model: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """生成文本 (流式)"""
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        async for chunk in self.chat_stream(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield chunk
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> str:
        """聊天完成 (非流式)"""
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"vLLM chat failed: {e}")
            raise
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """聊天完成 (流式)"""
        
        try:
            async with self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            ) as stream_response:
                async for chunk in stream_response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"vLLM chat stream failed: {e}")
            raise
    
    async def embed(
        self,
        text: str,
        model: str = "BAAI/bge-multilingual-gemma2",
    ) -> List[float]:
        """生成嵌入"""
        
        try:
            response = await self.client.embeddings.create(
                model=model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"vLLM embed failed: {e}")
            raise
    
    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()


# 全局实例
vllm_client = VLLMClient()
