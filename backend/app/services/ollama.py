"""
Ollama 本地模型客户端
"""

from typing import List, Dict, Optional, AsyncGenerator
from loguru import logger
import httpx


class OllamaClient:
    """Ollama 客户端"""

    SUPPORTED_MODELS = [
        "llama3.2",
        "llama3.1",
        "llama3",
        "qwen2.5",
        "qwen2",
        "deepseek-r1",
        "deepseek-v2",
        "mistral",
        "codellama",
        "gemma2",
        "phi3",
    ]

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self._client = None
        self._async_client = None

    @property
    def client(self):
        """同步客户端"""
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    @property
    async def async_client(self):
        """异步客户端"""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(timeout=self.timeout)
        return self._async_client

    async def list_models(self) -> List[Dict]:
        """列出可用模型"""
        try:
            async with self.async_client as client:
                response = await client.get(f"{self.base_url}/api/tags")
                models = response.json().get("models", [])

                return [
                    {
                        "name": m["name"],
                        "size": m.get("size", 0),
                        "digest": m.get("digest", ""),
                    }
                    for m in models
                ]
        except Exception as e:
            logger.error(f"List Ollama models failed: {e}")
            return []

    async def pull_model(
        self, model: str, stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """拉取模型"""
        async with self.async_client as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/pull",
                json={"name": model, "stream": stream},
            ) as response:
                async for chunk in response.aiter_lines():
                    yield chunk

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

        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": False,
        }

        if system:
            payload["system"] = system

        try:
            async with self.async_client as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                data = response.json()
                return data.get("response", "")
        except Exception as e:
            logger.error(f"Ollama generate failed: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        model: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """生成文本 (流式)"""

        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": True,
        }

        if system:
            payload["system"] = system

        try:
            async with self.async_client as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload,
                ) as response:
                    async for line in response.aiter_lines():
                        import json

                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
        except Exception as e:
            logger.error(f"Ollama stream failed: {e}")
            raise

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> str:
        """聊天完成 (非流式)"""

        payload = {
            "model": model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": False,
        }

        try:
            async with self.async_client as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                data = response.json()
                return data.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            raise

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """聊天完成 (流式)"""

        payload = {
            "model": model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": True,
        }

        try:
            async with self.async_client as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                ) as response:
                    async for line in response.aiter_lines():
                        import json

                        data = json.loads(line)
                        if "message" in data:
                            yield data["message"].get("content", "")
        except Exception as e:
            logger.error(f"Ollama chat stream failed: {e}")
            raise

    async def embed(self, text: str, model: str = "nomic-embed-text") -> List[float]:
        """生成嵌入"""

        payload = {
            "model": model,
            "prompt": text,
        }

        try:
            async with self.async_client as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json=payload,
                )
                data = response.json()
                return data.get("embedding", [])
        except Exception as e:
            logger.error(f"Ollama embed failed: {e}")
            raise

    async def close(self):
        """关闭客户端"""
        if self._client:
            self._client.close()
        if self._async_client:
            await self._async_client.aclose()


# 全局实例
ollama_client = OllamaClient()
