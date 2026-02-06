"""
Tracing API 端点
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter()


class PromptCreateRequest(BaseModel):
    """创建提示词请求"""
    name: str
    prompt: str
    version: Optional[int] = None
    description: Optional[str] = None


class PromptResponse(BaseModel):
    """提示词响应"""
    name: str
    version: int
    prompt: str
    metadata: Dict
    created_at: str


class PromptUpdateRequest(BaseModel):
    """更新提示词请求"""
    prompt: str
    description: Optional[str] = None


# ============== 提示词管理 ==============

@router.get("/api/v1/prompts")
async def list_prompts() -> List[Dict[str, Any]]:
    """列出所有提示词"""
    from app.tracing.prompts import prompt_manager
    
    prompts = []
    for file_path in Path("./data/prompts").glob("*_v*.json"):
        name = file_path.stem.rsplit("_v", 1)[0]
        prompt = prompt_manager.get_latest(name)
        if prompt:
            prompts.append({
                "name": prompt["name"],
                "version": prompt["version"],
                "description": prompt.get("metadata", {}).get("description", ""),
                "created_at": prompt["created_at"],
            })
    
    return prompts


@router.get("/api/v1/prompts/{name}")
async def get_prompt(name: str, version: int = None) -> PromptResponse:
    """获取提示词"""
    from app.tracing.prompts import prompt_manager
    
    prompt = prompt_manager.get_prompt(name, version)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    return PromptResponse(
        name=prompt["name"],
        version=prompt["version"],
        prompt=prompt["prompt"],
        metadata=prompt.get("metadata", {}),
        created_at=prompt["created_at"],
    )


@router.post("/api/v1/prompts", response_model=PromptResponse)
async def create_prompt(request: PromptCreateRequest) -> PromptResponse:
    """创建/更新提示词"""
    from app.tracing.prompts import prompt_manager
    
    result = prompt_manager.save_prompt(
        name=request.name,
        prompt=request.prompt,
        version=request.version,
        metadata={"description": request.description},
    )
    
    return PromptResponse(
        name=result["name"],
        version=result["version"],
        prompt=result["prompt"],
        metadata=result.get("metadata", {}),
        created_at=result["created_at"],
    )


@router.get("/api/v1/prompts/{name}/versions")
async def list_prompt_versions(name: str) -> List[Dict[str, Any]]:
    """列出提示词所有版本"""
    from app.tracing.prompts import prompt_manager
    
    return prompt_manager.list_versions(name)


@router.get("/api/v1/prompts/{name}/compare")
async def compare_prompt_versions(
    name: str,
    v1: int,
    v2: int,
) -> Dict[str, Any]:
    """比较版本"""
    from app.tracing.prompts import prompt_manager
    
    result = prompt_manager.compare_versions(name, v1, v2)
    if not result:
        raise HTTPException(status_code=404, detail="Versions not found")
    
    return result


@router.delete("/api/v1/prompts/{name}/versions/{version}")
async def delete_prompt_version(name: str, version: int):
    """删除版本"""
    from app.tracing.prompts import prompt_manager
    
    if not prompt_manager.delete_version(name, version):
        raise HTTPException(status_code=404, detail="Version not found")
    
    return {"message": "deleted"}


@router.post("/api/v1/prompts/{name}/render")
async def render_prompt(
    name: str,
    variables: Dict[str, str],
    version: int = None,
) -> Dict[str, str]:
    """渲染提示词"""
    from app.tracing.prompts import prompt_manager
    
    rendered = prompt_manager.render_prompt(name, variables, version)
    if not rendered:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    return {"prompt": rendered}


# ============== 追踪统计 ==============

@router.get("/api/v1/tracing/stats")
async def get_tracing_stats() -> Dict[str, Any]:
    """获取追踪统计"""
    from app.tracing.decorators import token_tracker
    
    return {
        "tokens": token_tracker.get_stats(),
        "enabled": True,
    }


@router.post("/api/v1/tracing/reset")
async def reset_tracing_stats():
    """重置追踪统计"""
    from app.tracing.decorators import token_tracker
    
    token_tracker.reset()
    return {"message": "reset"}


# ============== Langfuse 状态 ==============

@router.get("/api/v1/tracing/status")
async def get_tracing_status() -> Dict[str, Any]:
    """获取追踪状态"""
    from app.tracing.langfuse import langfuse
    
    return {
        "enabled": langfuse.enabled,
        "status": "healthy" if langfuse.enabled else "disabled",
    }


# ============== 默认提示词 ==============

@router.get("/api/v1/prompts/defaults")
async def get_default_prompts() -> Dict[str, Any]:
    """获取默认提示词模板"""
    from app.tracing.prompts import DEFAULT_PROMPTS
    
    return {
        name: {
            "description": config["description"],
            "prompt": config["prompt"][:500] + "...",
        }
        for name, config in DEFAULT_PROMPTS.items()
    }
