"""
分享服务
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid
import hashlib

from app.config import settings
from app.models_v2 import get_session, Document, KnowledgeBase


class ShareType(str, Enum):
    """分享类型"""

    DOCUMENT = "document"
    KNOWLEDGE_BASE = "knowledge_base"
    CONVERSATION = "conversation"
    SEARCH_RESULT = "search_result"


class SharePermission(str, Enum):
    """分享权限"""

    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"


@dataclass
class ShareLink:
    """分享链接"""

    id: str
    share_type: ShareType
    resource_id: str
    permission: SharePermission
    token: str
    short_url: str
    expires_at: Optional[datetime]
    view_count: int
    max_views: Optional[int]
    password: Optional[str]
    created_by: str
    created_at: datetime


class ShareService:
    """分享服务"""

    def __init__(self):
        self.base_url = settings.app_url or "http://localhost:3000"

    def create_share_link(
        self,
        share_type: ShareType,
        resource_id: str,
        permission: SharePermission = SharePermission.VIEW,
        expires_in_days: Optional[int] = None,
        max_views: Optional[int] = None,
        password: Optional[str] = None,
        created_by: str = "anonymous",
    ) -> ShareLink:
        """创建分享链接"""
        share_id = str(uuid.uuid4())[:8]
        token = self._generate_token()

        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # 保存到数据库
        share_link = ShareLink(
            id=share_id,
            share_type=share_type,
            resource_id=resource_id,
            permission=permission,
            token=token,
            short_url=f"{self.base_url}/s/{share_id}",
            expires_at=expires_at,
            view_count=0,
            max_views=max_views,
            password=password,
            created_by=created_by,
            created_at=datetime.utcnow(),
        )

        return share_link

    def _generate_token(self) -> str:
        """生成短 token"""
        return uuid.uuid4().hex[:16]

    def get_share_link(self, share_id: str) -> Optional[ShareLink]:
        """获取分享链接"""
        # 从数据库查询
        return None

    def validate_share_link(
        self, share_id: str, token: str, password: Optional[str] = None
    ) -> Optional[ShareLink]:
        """验证分享链接"""
        share = self.get_share_link(share_id)

        if not share:
            return None

        # 验证 token
        if share.token != token:
            return None

        # 验证过期
        if share.expires_at and share.expires_at < datetime.utcnow():
            return None

        # 验证最大查看次数
        if share.max_views and share.view_count >= share.max_views:
            return None

        # 验证密码
        if share.password and share.password != password:
            return None

        return share

    def record_view(self, share_id: str):
        """记录查看"""
        # 更新数据库
        pass

    def revoke_share_link(self, share_id: str, created_by: str) -> bool:
        """撤销分享链接"""
        # 从数据库删除
        return True

    def get_share_stats(self, share_id: str) -> Dict[str, Any]:
        """获取分享统计"""
        return {
            "share_id": share_id,
            "view_count": 0,
            "unique_visitors": 0,
            "created_at": datetime.utcnow().isoformat(),
        }


# ==================== 公开访问页面 ====================

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


class CreateShareRequest(BaseModel):
    type: ShareType
    resource_id: str
    permission: SharePermission = SharePermission.VIEW
    expires_in_days: Optional[int] = 7
    max_views: Optional[int] = None
    password: Optional[str] = None


class ShareResponse(BaseModel):
    share_id: str
    short_url: str
    token: str
    expires_at: Optional[str]


@router.post("/api/v1/share", response_model=ShareResponse)
async def create_share_link(request: CreateShareRequest, created_by: str = "anonymous"):
    """创建分享链接"""
    service = ShareService()

    link = service.create_share_link(
        share_type=request.type,
        resource_id=request.resource_id,
        permission=request.permission,
        expires_in_days=request.expires_in_days,
        max_views=request.max_views,
        password=request.password,
        created_by=created_by,
    )

    # 保存到数据库

    return ShareResponse(
        share_id=link.id,
        short_url=link.short_url,
        token=link.token,
        expires_at=link.expires_at.isoformat() if link.expires_at else None,
    )


@router.get("/api/v1/share/{share_id}")
async def get_share_info(
    share_id: str, token: str = Query(...), password: Optional[str] = Query(None)
):
    """获取分享信息（无需认证）"""
    service = ShareService()

    link = service.validate_share_link(share_id, token, password)

    if not link:
        raise HTTPException(status_code=404, detail="分享链接不存在或已过期")

    # 获取资源内容
    if link.share_type == ShareType.DOCUMENT:
        # 获取文档内容
        pass
    elif link.share_type == ShareType.KNOWLEDGE_BASE:
        # 获取知识库信息
        pass

    return {
        "type": link.share_type,
        "permission": link.permission,
        "title": "Resource Title",  # 获取实际标题
    }


@router.get("/s/{share_id}")
async def public_share_page(
    share_id: str, token: str = Query(...), password: Optional[str] = Query(None)
):
    """公开分享页面"""
    service = ShareService()

    link = service.validate_share_link(share_id, token, password)

    if not link:
        return {"error": "分享链接不存在或已过期"}

    # 记录查看
    service.record_view(share_id)

    # 返回资源内容
    # 返回实际内容
    return {
        "message": "Access granted",
        "share_type": link.share_type,
        "resource_id": link.resource_id,
    }


# 全局实例
share_service = ShareService()
