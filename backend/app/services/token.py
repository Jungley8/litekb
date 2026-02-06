"""
Token 刷新服务
"""
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from jose import jwt, JWTError
from fastapi import HTTPException, status
from loguru import logger

from app.config import settings
from app.models_v2 import get_session, User


@dataclass
class TokenPair:
    """Token 对"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 1 hour


class TokenService:
    """Token 服务"""
    
    # Token 过期时间
    ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days
    
    # Token 类型
    TYPE_ACCESS = "access"
    TYPE_REFRESH = "refresh"
    
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = "HS256"
    
    def create_access_token(
        self,
        user_id: str,
        additional_claims: dict = None
    ) -> str:
        """创建访问 Token"""
        expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": user_id,
            "type": self.TYPE_ACCESS,
            "exp": expire,
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """创建刷新 Token"""
        expire = datetime.utcnow() + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "sub": user_id,
            "type": self.TYPE_REFRESH,
            "exp": expire,
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_token_pair(self, user_id: str, additional_claims: dict = None) -> TokenPair:
        """创建 Token 对"""
        return TokenPair(
            access_token=self.create_access_token(user_id, additional_claims),
            refresh_token=self.create_refresh_token(user_id),
            token_type="bearer",
            expires_in=self.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    def verify_token(self, token: str, expected_type: str = TYPE_ACCESS) -> dict:
        """验证 Token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # 检查 Token 类型
            token_type = payload.get("type")
            if token_type != expected_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type: expected {expected_type}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # 检查过期
            exp = payload.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return payload
            
        except JWTError as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def decode_token(self, token: str) -> dict:
        """解码 Token (不验证过期)"""
        try:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
        except JWTError as e:
            logger.error(f"Token decode failed: {e}")
            return None
    
    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """从 Token 获取用户 ID"""
        payload = self.decode_token(token)
        return payload.get("sub") if payload else None
    
    def refresh_access_token(self, refresh_token: str) -> TokenPair:
        """使用刷新 Token 获取新的访问 Token"""
        # 验证刷新 Token
        payload = self.verify_token(refresh_token, self.TYPE_REFRESH)
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # 检查用户是否存在
        session = get_session()
        try:
            user = session.query(User).get(user_id)
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # 创建新的 Token 对
            return self.create_token_pair(user_id, {
                "username": user.username,
                "email": user.email
            })
        
        finally:
            session.close()
    
    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """撤销刷新 Token"""
        # TODO: 将 Token 加入黑名单
        # 可以使用 Redis 存储已撤销的 Token
        logger.info(f"Revoking refresh token: {refresh_token[:20]}...")
        return True
    
    def is_token_revoked(self, token: str) -> bool:
        """检查 Token 是否已被撤销"""
        # TODO: 检查 Token 是否在黑名单中
        return False


# 全局实例
token_service = TokenService()


# ==================== API 端点 ====================

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求"""
    refresh_token: str


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


@router.post("/api/v1/auth/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """刷新访问 Token"""
    token_pair = token_service.refresh_access_token(request.refresh_token)
    
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in
    )


@router.post("/api/v1/auth/revoke")
async def revoke_token(request: RefreshTokenRequest):
    """撤销 Token"""
    token_service.revoke_refresh_token(request.refresh_token)
    return {"message": "Token revoked successfully"}


@router.get("/api/v1/auth/me")
async def get_current_user_info(
    authorization: str = Header(None)
):
    """获取当前用户信息"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    token = authorization.split(" ")[1]
    payload = token_service.verify_token(token)
    user_id = payload.get("sub")
    
    session = get_session()
    try:
        user = session.query(User).get(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "organization_id": user.organization_id,
            "role": user.role,
            "is_active": user.is_active,
        }
    
    finally:
        session.close()
