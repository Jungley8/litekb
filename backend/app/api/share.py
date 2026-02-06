"""
分享 API 端点
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter()


class CreateShareRequest(BaseModel):
    """创建分享请求"""
    resource_type: str  # "kb" | "doc" | "chat"
    resource_id: str
    title: str
    password: Optional[str] = None
    expires_in_days: int = 7


class ShareResponse(BaseModel):
    """分享响应"""
    id: str
    token: str
    url: str
    title: str
    expires_at: Optional[datetime]
    created_at: datetime


# 演示数据
_demo_shares = []


@router.post("/api/v1/share", response_model=ShareResponse)
async def create_share(request: CreateShareRequest):
    """创建分享链接"""
    import secrets
    
    token = secrets.token_urlsafe(16)
    expires_at = datetime.utcnow() + datetime.timedelta(days=request.expires_in_days)
    
    share = {
        "id": secrets.uuid4().hex[:8],
        "token": token,
        "url": f"/share/{token}",
        "resource_type": request.resource_type,
        "resource_id": request.resource_id,
        "title": request.title,
        "password": request.password,
        "expires_at": expires_at,
        "created_at": datetime.utcnow(),
        "view_count": 0,
        "is_active": True,
    }
    
    _demo_shares.append(share)
    
    return {
        "id": share["id"],
        "token": token,
        "url": share["url"],
        "title": share["title"],
        "expires_at": expires_at,
        "created_at": share["created_at"],
    }


@router.get("/api/v1/share/{token}")
async def get_share(token: str):
    """获取分享信息"""
    share = next((s for s in _demo_shares if s["token"] == token and s["is_active"]), None)
    
    if not share:
        raise HTTPException(status_code=404, detail="分享链接不存在")
    
    return {
        "title": share["title"],
        "resource_type": share["resource_type"],
        "created_at": share["created_at"].isoformat(),
        "expires_at": share["expires_at"].isoformat() if share["expires_at"] else None,
    }


@router.get("/api/v1/share/{token}/content")
async def get_share_content(token: str, password: str = None):
    """获取分享内容"""
    share = next((s for s in _demo_shares if s["token"] == token and s["is_active"]), None)
    
    if not share:
        raise HTTPException(status_code=404, detail="分享链接不存在")
    
    # 检查密码
    if share.get("password") and share["password"] != password:
        raise HTTPException(status_code=401, detail="密码错误")
    
    # TODO: 从数据库获取实际内容
    return {
        "title": share["title"],
        "type": share["resource_type"],
        "content": f"这是分享的内容 (ID: {share['resource_id']})",
    }


@router.delete("/api/v1/share/{token}")
async def revoke_share(token: str):
    """撤销分享"""
    share = next((s for s in _demo_shares if s["token"] == token), None)
    
    if share:
        share["is_active"] = False
        return {"message": "分享已撤销"}
    
    raise HTTPException(status_code=404, detail="分享链接不存在")


@router.get("/api/v1/share/{token}/stats")
async def get_share_stats(token: str):
    """获取分享统计"""
    share = next((s for s in _demo_shares if s["token"] == token), None)
    
    if not share:
        raise HTTPException(status_code=404, detail="分享链接不存在")
    
    return {
        "view_count": share["view_count"],
        "created_at": share["created_at"].isoformat(),
        "expires_at": share["expires_at"].isoformat() if share["expires_at"] else None,
    }


@router.get("/api/v1/share/{token}/embed")
async def get_embed_code(token: str):
    """获取嵌入代码"""
    share = next((s for s in _demo_shares if s["token"] == token and s["is_active"]), None)
    
    if not share:
        raise HTTPException(status_code=404, detail="分享链接不存在")
    
    return {
        "code": f'<iframe src="/embed/{token}" width="100%" height="600"></iframe>',
    }


@router.get("/api/v1/shares")
async def list_shares():
    """列出所有分享"""
    return [
        {
            "id": s["id"],
            "token": s["token"][:8] + "...",
            "title": s["title"],
            "type": s["resource_type"],
            "is_active": s["is_active"],
        }
        for s in _demo_shares
    ]
