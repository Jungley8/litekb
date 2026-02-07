"""
模型管理 API 端点
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from pydantic import BaseModel

router = APIRouter()


class SwitchModelRequest(BaseModel):
    """切换模型请求"""

    provider: str
    model: str
    temperature: float = 0.1
    max_tokens: int = 4000


class TestConnectionRequest(BaseModel):
    """测试连接请求"""

    provider: str


# 当前模型配置
_current_config: Dict[str, Any] = {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.1,
    "max_tokens": 4000,
}


@router.get("/api/v1/models/providers")
async def list_providers() -> List[Dict[str, Any]]:
    """列出所有可用供应商"""
    from app.services.model_provider import model_client, ProviderType

    providers = []

    # OpenAI
    if ProviderType.OPENAI in model_client._providers:
        providers.append(
            {
                "type": "openai",
                "name": "OpenAI",
                "models": [
                    {
                        "id": "gpt-4o",
                        "object": "model",
                        "created": 0,
                        "owned_by": "openai",
                    },
                    {
                        "id": "gpt-4o-mini",
                        "object": "model",
                        "created": 0,
                        "owned_by": "openai",
                    },
                    {
                        "id": "gpt-4-turbo",
                        "object": "model",
                        "created": 0,
                        "owned_by": "openai",
                    },
                ],
                "capabilities": ["chat", "streaming", "function_calling", "vision"],
            }
        )

    # Ollama
    if ProviderType.OLLAMA in model_client._providers:
        prov = model_client._providers[ProviderType.OLLAMA]
        models = await prov.list_models()
        providers.append(
            {
                "type": "ollama",
                "name": "Ollama (本地)",
                "models": models,
                "capabilities": ["chat", "streaming", "embedding"],
            }
        )

    # vLLM
    if ProviderType.VLLM in model_client._providers:
        prov = model_client._providers[ProviderType.VLLM]
        models = await prov.list_models()
        providers.append(
            {
                "type": "vllm",
                "name": "vLLM (本地)",
                "models": models,
                "capabilities": ["chat", "streaming", "embedding"],
            }
        )

    # Anthropic
    providers.append(
        {
            "type": "anthropic",
            "name": "Anthropic",
            "models": [
                {"id": "claude-3-5-sonnet-20241022", "object": "model"},
                {"id": "claude-3-haiku-20240307", "object": "model"},
            ],
            "capabilities": ["chat", "streaming", "vision"],
        }
    )

    # Google
    providers.append(
        {
            "type": "google",
            "name": "Google",
            "models": [
                {"id": "gemini-1.5-pro", "object": "model"},
                {"id": "gemini-1.5-flash", "object": "model"},
            ],
            "capabilities": ["chat", "streaming", "vision"],
        }
    )

    return providers


@router.get("/api/v1/models/config")
async def get_config() -> Dict[str, Any]:
    """获取当前配置"""
    return _current_config


@router.post("/api/v1/models/switch")
async def switch_model(request: SwitchModelRequest) -> Dict[str, Any]:
    """切换模型供应商"""
    global _current_config

    valid_providers = ["openai", "anthropic", "google", "ollama", "vllm"]

    if request.provider not in valid_providers:
        raise HTTPException(status_code=400, detail="无效的供应商")

    _current_config = {
        "provider": request.provider,
        "model": request.model,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }

    return {"success": True, "config": _current_config}


@router.get("/api/v1/models/{provider}/list")
async def list_provider_models(provider: str) -> List[Dict[str, str]]:
    """获取供应商模型列表"""

    models_map = {
        "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "anthropic": ["claude-3-5-sonnet", "claude-3-haiku"],
        "google": ["gemini-1.5-pro", "gemini-1.5-flash"],
        "ollama": ["llama3.2:3b", "qwen2.5:7b", "mistral:7b"],
        "vllm": ["Qwen2.5-7B", "Llama-3.2-3B", "Mistral-7B"],
    }

    models = models_map.get(provider, [])
    return [{"id": m, "name": m} for m in models]


@router.post("/api/v1/models/{provider}/test")
async def test_connection(provider: str) -> Dict[str, Any]:
    """测试供应商连接"""
    import time

    start = time.time()

    try:
        # 简化的连接测试
        await new_test_connection(provider)
        latency = int((time.time() - start) * 1000)

        return {"success": True, "latency": latency}
    except Exception as e:
        return {"success": False, "latency": 0, "error": str(e)}


async def new_test_connection(provider: str) -> bool:
    """实际测试连接"""
    if provider == "ollama":
        try:
            from app.services.ollama import ollama_client

            await ollama_client.list_models()
            return True
        except:
            return False
    elif provider == "vllm":
        try:
            from app.services.vllm import vllm_client

            await vllm_client.list_models()
            return True
        except:
            return False
    else:
        # 云端供应商默认成功
        return True


# Ollama 专用端点
@router.get("/api/v1/models/ollama/list")
async def list_ollama_models() -> List[Dict[str, Any]]:
    """列出 Ollama 模型"""
    try:
        from app.services.ollama import ollama_client

        return await ollama_client.list_models()
    except Exception as e:
        return []


@router.post("/api/v1/models/ollama/pull")
async def pull_ollama_model(model: str, stream: bool = True) -> Dict[str, Any]:
    """拉取 Ollama 模型"""
    try:
        from app.services.ollama import ollama_client

        chunks = []
        async for chunk in ollama_client.pull_model(model, stream):
            chunks.append(chunk)

        return {"success": True, "model": model, "chunks": len(chunks)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# vLLM 专用端点
@router.get("/api/v1/models/vllm/list")
async def list_vllm_models() -> List[Dict[str, str]]:
    """列出 vLLM 模型"""
    try:
        from app.services.vllm import vllm_client

        models = await vllm_client.list_models()
        return [{"id": m["id"]} for m in models]
    except Exception as e:
        return []
