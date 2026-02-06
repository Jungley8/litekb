"""
认证与权限中间件
"""
from typing import Optional, List
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
import secrets
import hashlib

from app.config import settings
from app.models_v2 import (
    get_session, User, Organization, OrganizationMember, APIKey
)


# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================== 权限定义 ====================

class Permission:
    """权限常量"""
    # 知识库权限
    KB_CREATE = "kb:create"
    KB_READ = "kb:read"
    KB_UPDATE = "kb:update"
    KB_DELETE = "kb:delete"
    KB_MANAGE = "kb:manage"
    
    # 文档权限
    DOC_CREATE = "doc:create"
    DOC_READ = "doc:read"
    DOC_DELETE = "doc:delete"
    
    # 成员权限
    MEMBER_INVITE = "member:invite"
    MEMBER_REMOVE = "member:remove"
    MEMBER_MANAGE = "member:manage"
    
    # 组织权限
    ORG_SETTINGS = "org:settings"
    ORG_DELETE = "org:delete"
    
    # API Key 权限
    API_KEY_CREATE = "api_key:create"
    API_KEY_DELETE = "api_key:delete"


# 角色权限映射
ROLE_PERMISSIONS = {
    "owner": [
        Permission.KB_CREATE, Permission.KB_READ, Permission.KB_UPDATE,
        Permission.KB_DELETE, Permission.KB_MANAGE,
        Permission.DOC_CREATE, Permission.DOC_READ, Permission.DOC_DELETE,
        Permission.MEMBER_INVITE, Permission.MEMBER_REMOVE, Permission.MEMBER_MANAGE,
        Permission.ORG_SETTINGS, Permission.ORG_DELETE,
        Permission.API_KEY_CREATE, Permission.API_KEY_DELETE,
    ],
    "admin": [
        Permission.KB_CREATE, Permission.KB_READ, Permission.KB_UPDATE,
        Permission.KB_DELETE, Permission.KB_MANAGE,
        Permission.DOC_CREATE, Permission.DOC_READ, Permission.DOC_DELETE,
        Permission.MEMBER_INVITE, Permission.MEMBER_REMOVE, Permission.MEMBER_MANAGE,
        Permission.ORG_SETTINGS,
        Permission.API_KEY_CREATE, Permission.API_KEY_DELETE,
    ],
    "member": [
        Permission.KB_CREATE, Permission.KB_READ,
        Permission.DOC_CREATE, Permission.DOC_READ,
    ],
    "viewer": [
        Permission.KB_READ,
        Permission.DOC_READ,
    ],
}


# ==================== 依赖注入 ====================

class AuthContext:
    """认证上下文"""
    
    def __init__(
        self,
        user: Optional[User] = None,
        organization: Optional[Organization] = None,
        member_role: str = None,
        is_api_key: bool = False,
        api_scopes: List[str] = None
    ):
        self.user = user
        self.organization = organization
        self.member_role = member_role
        self.is_api_key = is_api_key
        self.api_scopes = api_scopes or []
    
    @property
    def user_id(self) -> Optional[str]:
        return self.user.id if self.user else None
    
    @property
    def org_id(self) -> Optional[str]:
        return self.organization.id if self.organization else None


async def get_current_user(
    x_organization_id: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    x_api_key_id: Optional[str] = Header(None)
) -> AuthContext:
    """
    获取当前认证上下文
    优先级: API Key > JWT Token
    """
    
    # 1. 尝试 API Key 认证
    if x_api_key and x_api_key_id:
        return await authenticate_api_key(x_api_key, x_api_key_id, x_organization_id)
    
    # 2. JWT 认证
    if authorization and authorization.startswith("Bearer "):
        return await authenticate_jwt(authorization, x_organization_id)
    
    # 3. 未认证
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def authenticate_api_key(
    key: str,
    key_id: str,
    org_id: Optional[str]
) -> AuthContext:
    """API Key 认证"""
    session = get_session()
    try:
        # 查找 API Key
        api_key = session.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.key_hash == hash_api_key(key),
            APIKey.is_active == True
        ).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key"
            )
        
        # 检查过期
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key expired"
            )
        
        # 更新最后使用时间
        api_key.last_used_at = datetime.utcnow()
        session.commit()
        
        # 获取组织
        organization = None
        if org_id or api_key.organization_id:
            org_id = org_id or api_key.organization_id
            organization = session.query(Organization).get(org_id)
        
        return AuthContext(
            organization=organization,
            is_api_key=True,
            api_scopes=api_key.scopes or []
        )
    
    finally:
        session.close()


async def authenticate_jwt(
    token: str,
    org_id: Optional[str]
) -> AuthContext:
    """JWT 认证"""
    try:
        payload = jwt.decode(
            token.replace("Bearer ", ""),
            settings.jwt_secret_key,
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        session = get_session()
        try:
            user = session.query(User).get(user_id)
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # 获取组织
            organization = None
            member_role = None
            
            target_org_id = org_id or user.organization_id
            
            if target_org_id:
                organization = session.query(Organization).get(target_org_id)
                
                if organization:
                    # 检查成员关系
                    member = session.query(OrganizationMember).filter(
                        OrganizationMember.organization_id == target_org_id,
                        OrganizationMember.user_id == user_id
                    ).first()
                    
                    if member:
                        member_role = member.role
            
            # 更新最后登录
            user.last_login_at = datetime.utcnow()
            session.commit()
            
            return AuthContext(
                user=user,
                organization=organization,
                member_role=member_role
            )
        
        finally:
            session.close()
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_permission(permission: str):
    """权限检查依赖"""
    async def check(auth: AuthContext = Depends(get_current_user)):
        if auth.is_api_key:
            # API Key 检查 scopes
            if permission not in auth.api_scopes and "admin" not in auth.api_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"API Key missing scope: {permission}"
                )
        else:
            # 用户检查角色权限
            if not has_permission(auth, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission}"
                )
        return auth
    
    return check


def has_permission(auth: AuthContext, permission: str) -> bool:
    """检查是否有权限"""
    if not auth.user or not auth.member_role:
        return False
    
    user_permissions = ROLE_PERMISSIONS.get(auth.member_role, [])
    return permission in user_permissions


def require_organization(auth: AuthContext = Depends(get_current_user)) -> AuthContext:
    """检查是否属于组织"""
    if not auth.organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization required"
        )
    return auth


# ==================== Token 生成 ====================

def generate_jwt_token(user_id: str, additional_claims: dict = None) -> str:
    """生成 JWT Token"""
    payload = {"sub": user_id, "type": "access"}
    if additional_claims:
        payload.update(additional_claims)
    
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm="HS256"
    )


def generate_refresh_token(user_id: str) -> str:
    """生成刷新 Token"""
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def generate_api_key() -> tuple:
    """生成 API Key"""
    key_id = secrets.token_hex(8)
    key = f"lkb_{secrets.token_hex(24)}"
    key_hash = hash_api_key(key)
    key_prefix = key[:12]  # lkb_xxxx...
    
    return key_id, key, key_hash, key_prefix


def hash_api_key(key: str) -> str:
    """Hash API Key"""
    return hashlib.sha256(key.encode()).hexdigest()


# ==================== 组织切换 ====================

async def switch_organization(
    user_id: str,
    organization_id: str
) -> AuthContext:
    """切换组织"""
    session = get_session()
    try:
        # 检查成员关系
        member = session.query(OrganizationMember).filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id
        ).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not a member of this organization"
            )
        
        organization = session.query(Organization).get(organization_id)
        
        return AuthContext(
            user=session.query(User).get(user_id),
            organization=organization,
            member_role=member.role
        )
    
    finally:
        session.close()
