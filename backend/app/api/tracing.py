"""
API 端点 - 提示词管理 + Token 统计 (Langfuse)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter()


# ============== 提示词管理 ==============

@router.get("/api/v1/prompts")
async def list_prompts() -> List[Dict[str, Any]]:
    """列出所有提示词"""
    from app.tracing.langfuse import langfuse_tracing
    
    if not langfuse_tracing.enabled:
        return []
    
    return langfuse_tracing.list_prompts()


@router.get("/api/v1/prompts/{name}")
async def get_prompt(name: str, version: int = None) -> Dict[str, Any]:
    """获取提示词"""
    from app.tracing.langfuse import langfuse_tracing
    
    prompt = langfuse_tracing.get_prompt(name, version)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    return prompt


@router.post("/api/v1/prompts")
async def create_prompt(
    name: str,
    prompt: str,
    version: int = None,
    config: Dict = None,
) -> Dict[str, Any]:
    """创建提示词"""
    from app.tracing.langfuse import langfuse_tracing
    
    result = langfuse_tracing.create_prompt(name, prompt, version, config)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create prompt")
    
    return result


@router.put("/api/v1/prompts/{name}")
async def update_prompt(
    name: str,
    prompt: str,
    config: Dict = None,
) -> Dict[str, Any]:
    """更新提示词 (自动版本管理)"""
    from app.tracing.langfuse import langfuse_tracing
    
    result = langfuse_tracing.update_prompt(name, prompt, config)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to update prompt")
    
    return result


@router.get("/api/v1/prompts/{name}/versions")
async def get_prompt_versions(name: str) -> List[Dict[str, Any]]:
    """获取提示词版本历史"""
    from app.tracing.langfuse import langfuse_tracing
    
    return langfuse_tracing.get_prompt_versions(name)


@router.post("/api/v1/prompts/{name}/render")
async def render_prompt(
    name: str,
    variables: Dict[str, str],
    version: int = None,
) -> Dict[str, str]:
    """渲染提示词"""
    from app.tracing.langfuse import langfuse_tracing
    
    rendered = langfuse_tracing.render_prompt(name, variables, version)
    if not rendered:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    return {"prompt": rendered}


@router.delete("/api/v1/prompts/{name}/versions/{version}")
async def delete_prompt_version(name: str, version: int) -> Dict[str, str]:
    """删除提示词版本"""
    from app.tracing.langfuse import langfuse_tracing
    
    success = langfuse_tracing.delete_prompt(name, version)
    if not success:
        raise HTTPException(status_code=500, detail="Cannot delete prompt (Langfuse API limitation)")
    
    return {"message": "deleted"}


# ============== Token & Cost 统计 ==============

@router.get("/api/v1/tracing/stats")
async def get_token_stats() -> Dict[str, Any]:
    """获取 Token 使用统计 (从 Langfuse)"""
    from app.tracing.langfuse import langfuse_tracing
    
    if not langfuse_tracing.enabled:
        return {
            "enabled": False,
            "message": "Langfuse not configured",
            "stats": {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "total_cost": 0,
                "by_model": {},
            }
        }
    
    stats = langfuse_tracing.get_token_stats()
    
    return {
        "enabled": True,
        "stats": stats,
    }


@router.get("/api/v1/tracing/generations")
async def get_generations(
    name: str = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """获取生成记录"""
    from app.tracing.langfuse import langfuse_tracing
    
    return langfuse_tracing.get_generations(name, limit)


@router.get("/api/v1/tracing/status")
async def get_tracing_status() -> Dict[str, Any]:
    """获取追踪状态"""
    from app.tracing.langfuse import langfuse_tracing
    
    return {
        "enabled": langfuse_tracing.enabled,
        "status": "healthy" if langfuse_tracing.enabled else "disabled",
    }


@router.post("/api/v1/tracing/clear")
async def clear_local_cache():
    """清除本地缓存 (仅本地追踪)"""
    # Langfuse 数据在云端
    return {"message": "Note: Langfuse data is managed in cloud"}
