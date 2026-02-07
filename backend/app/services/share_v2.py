"""
分享服务
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from pydantic import BaseModel
import secrets


class ShareLink(BaseModel):
    """分享链接"""

    id: str
    token: str
    resource_type: str  # "kb" | "doc" | "chat"
    resource_id: str
    title: str
    password: Optional[str] = None
    view_count: int = 0
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True


class ShareService:
    """分享服务"""

    # 模拟数据库
    _shares: Dict[str, ShareLink] = {}

    def __init__(self):
        self._init_demo_shares()

    def _init_demo_shares(self):
        """初始化演示数据"""
        demo_token = secrets.token_urlsafe(16)
        self._shares[demo_token] = ShareLink(
            id="demo-1",
            token=demo_token,
            resource_type="doc",
            resource_id="doc-1",
            title="示例文档分享",
            view_count=42,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=7),
            is_active=True,
        )

    async def create_share(
        self,
        resource_type: str,
        resource_id: str,
        title: str,
        password: Optional[str] = None,
        expires_in_days: int = 7,
    ) -> ShareLink:
        """创建分享链接"""

        token = secrets.token_urlsafe(16)
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        share = ShareLink(
            id=secrets.uuid4().hex[:8],
            token=token,
            resource_type=resource_type,
            resource_id=resource_id,
            title=title,
            password=password,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
        )

        self._shares[token] = share
        logger.info(f"Created share link: {token}")

        return share

    async def get_share(self, token: str) -> Optional[ShareLink]:
        """获取分享链接"""
        share = self._shares.get(token)

        if share and share.is_active:
            # 检查过期
            if share.expires_at and share.expires_at < datetime.utcnow():
                return None

            # 增加浏览量
            share.view_count += 1
            return share

        return None

    async def get_share_content(self, token: str) -> Dict[str, Any]:
        """获取分享内容"""
        share = await self.get_share(token)

        if not share:
            raise ValueError("分享链接不存在或已过期")

        # TODO: 从数据库获取实际内容
        # 这里根据 resource_type 和 resource_id 获取

        content_map = {
            "doc": {
                "title": share.title,
                "content": f"这是分享的文档内容 (ID: {share.resource_id})",
                "type": "document",
            },
            "kb": {
                "title": share.title,
                "content": f"这是知识库 {share.resource_id} 的分享",
                "type": "knowledge_base",
                "docs": [
                    {"title": "文档1", "id": "1"},
                    {"title": "文档2", "id": "2"},
                ],
            },
            "chat": {
                "title": share.title,
                "content": "对话分享内容",
                "type": "conversation",
                "messages": [
                    {"role": "user", "content": "你好！"},
                    {"role": "assistant", "content": "你好！有什么可以帮助的？"},
                ],
            },
        }

        # TODO: 返回实际内容
        return content_map.get(
            share.resource_type,
            {
                "title": share.title,
                "content": "分享内容",
            },
        )

    async def revoke_share(self, token: str) -> bool:
        """撤销分享"""
        if token in self._shares:
            self._shares[token].is_active = False
            return True
        return False

    async def list_shares(
        self,
        resource_type: Optional[str] = None,
        active_only: bool = True,
    ) -> List[ShareLink]:
        """列出分享链接"""
        shares = list(self._shares.values())

        if resource_type:
            shares = [s for s in shares if s.resource_type == resource_type]

        if active_only:
            shares = [
                s
                for s in shares
                if s.is_active
                and (not s.expires_at or s.expires_at > datetime.utcnow())
            ]

        return sorted(shares, key=lambda s: s.created_at, reverse=True)

    async def get_share_stats(self, token: str) -> Dict[str, Any]:
        """获取分享统计"""
        share = self._shares.get(token)

        if not share:
            raise ValueError("分享链接不存在")

        return {
            "token": token,
            "title": share.title,
            "view_count": share.view_count,
            "created_at": share.created_at.isoformat(),
            "expires_at": share.expires_at.isoformat() if share.expires_at else None,
            "is_active": share.is_active,
        }

    async def generate_embed_code(self, token: str) -> str:
        """生成嵌入代码"""
        share = await self.get_share(token)

        if not share:
            raise ValueError("分享链接不存在")

        return f'<iframe src="/embed/{token}" width="100%" height="600"></iframe>'


# 全局实例
share_service = ShareService()
