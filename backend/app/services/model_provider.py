"""
统一模型供应商抽象层
"""
from typing import List, Dict, Optional, AsyncGenerator, Union
from abc import ABC, abstractmethod
from loguru import logger
from enum import Enum


class ProviderType(str, Enum):
    """供应商类型"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    VLLM = "vllm"
    LOCAL = "local"  # 未来支持


class ModelCapability(str, Enum):
    """模型能力"""
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"


class BaseModelProvider(ABC):
    """模型供应商基类"""
    
    provider_type: ProviderType
    supported_models: List[str]
    capabilities: List[ModelCapability] = [ModelCapability.CHAT, ModelCapability.STREAMING]
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> str:
        """聊天完成"""
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """流式聊天"""
        pass
    
    @abstractmethod
    async def embed(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """生成嵌入"""
        pass
    
    @abstractmethod
    async def list_models(self) -> List[Dict]:
        """列出可用模型"""
        pass
    
    async def close(self):
        """关闭连接"""
        pass


class UnifiedModelClient:
    """统一模型客户端"""
    
    def __init__(self):
        self._providers: Dict[ProviderType, BaseModelProvider] = {}
        self._default_provider: ProviderType = ProviderType.OPENAI
        self._default_model: str = "gpt-4o"
    
    def register_provider(self, provider: BaseModelProvider):
        """注册供应商"""
        self._providers[provider.provider_type] = provider
        logger.info(f"Registered provider: {provider.provider_type}")
    
    def set_default(self, provider: ProviderType, model: str = None):
        """设置默认供应商"""
        self._default_provider = provider
        if model:
            self._default_model = model
        logger.info(f"Default provider set to: {provider}")
    
    def get_provider(self, provider: ProviderType = None) -> BaseModelProvider:
        """获取供应商"""
        p = provider or self._default_provider
        if p not in self._providers:
            raise ValueError(f"Provider {p} not registered")
        return self._providers[p]
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        provider: ProviderType = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """聊天完成"""
        
        prov = self.get_provider(provider)
        model = model or self._default_model
        
        if stream:
            return prov.chat_stream(messages, model, temperature, max_tokens)
        else:
            return await prov.chat(messages, model, temperature, max_tokens)
    
    async def embed(
        self,
        text: str,
        model: str = None,
        provider: ProviderType = None,
    ) -> List[float]:
        """生成嵌入"""
        
        prov = self.get_provider(provider)
        model = model or "text-embedding-3-small"
        
        return await prov.embed(text, model)
    
    async def list_models(
        self,
        provider: ProviderType = None,
    ) -> List[Dict]:
        """列出可用模型"""
        
        prov = self.get_provider(provider)
        return await prov.list_models()
    
    async def close(self, provider: ProviderType = None):
        """关闭连接"""
        if provider:
            await self.get_provider(provider).close()
        else:
            for prov in self._providers.values():
                await prov.close()


# 供应商工厂
class ProviderFactory:
    """供应商工厂"""
    
    @staticmethod
    def create_ollama(base_url: str = "http://localhost:11434") -> BaseModelProvider:
        """创建 Ollama 供应商"""
        from app.services.ollama import OllamaClient
        
        class OllamaProvider(BaseModelProvider):
            provider_type = ProviderType.OLLAMA
            supported_models = OllamaClient.SUPPORTED_MODELS
            
            def __init__(self):
                self.client = OllamaClient(base_url)
            
            async def chat(self, messages, model, temperature, max_tokens, **kwargs):
                return await self.client.chat(messages, model, temperature, max_tokens)
            
            async def chat_stream(self, messages, model, temperature, max_tokens, **kwargs):
                async for chunk in self.client.chat_stream(messages, model, temperature, max_tokens):
                    yield chunk
            
            async def embed(self, text, model="nomic-embed-text"):
                return await self.client.embed(text, model)
            
            async def list_models(self):
                return await self.client.list_models()
            
            async def close(self):
                await self.client.close()
        
        return OllamaProvider()
    
    @staticmethod
    def create_vllm(base_url: str = "http://localhost:8000/v1") -> BaseModelProvider:
        """创建 vLLM 供应商"""
        from app.services.vllm import VLLMClient
        
        class VLLMProvider(BaseModelProvider):
            provider_type = ProviderType.VLLM
            supported_models = VLLMClient.SUPPORTED_MODELS
            
            def __init__(self):
                self.client = VLLMClient(base_url)
            
            async def chat(self, messages, model, temperature, max_tokens, **kwargs):
                return await self.client.chat(messages, model, temperature, max_tokens)
            
            async def chat_stream(self, messages, model, temperature, max_tokens, **kwargs):
                async for chunk in self.client.chat_stream(messages, model, temperature, max_tokens):
                    yield chunk
            
            async def embed(self, text, model="BAAI/bge-multilingual-gemma2"):
                return await self.client.embed(text, model)
            
            async def list_models(self):
                return await self.client.list_models()
            
            async def close(self):
                await self.client.close()
        
        return VLLMProvider()


# 全局实例
model_client = UnifiedModelClient()


# 配置管理
class ModelConfig:
    """模型配置"""
    
    CONFIG = {
        ProviderType.OPENAI: {
            "model": "gpt-4o",
            "fallback": "gpt-4o-mini",
        },
        ProviderType.ANTHROPIC: {
            "model": "claude-3-5-sonnet-20241022",
            "fallback": "claude-3-haiku-20240307",
        },
        ProviderType.GOOGLE: {
            "model": "gemini-1.5-pro",
            "fallback": "gemini-1.5-flash",
        },
        ProviderType.OLLAMA: {
            "model": "qwen2.5:7b",
            "fallback": "llama3.2:3b",
        },
        ProviderType.VLLM: {
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "fallback": "meta-llama/Llama-3.2-3B-Instruct",
        },
    }
    
    @classmethod
    def get_model(cls, provider: ProviderType, use_fallback: bool = False) -> str:
        """获取模型名称"""
        config = cls.CONFIG.get(provider, {})
        if use_fallback:
            return config.get("fallback", "")
        return config.get("model", "")
    
    @classmethod
    def set_model(cls, provider: ProviderType, model: str):
        """设置模型"""
        if provider not in cls.CONFIG:
            cls.CONFIG[provider] = {}
        cls.CONFIG[provider]["model"] = model
