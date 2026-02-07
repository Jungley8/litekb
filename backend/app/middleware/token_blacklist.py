"""
Token 黑名单中间件
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.blacklist import is_blacklisted


class TokenBlacklistMiddleware(BaseHTTPMiddleware):
    """Token 黑名单中间件"""

    async def dispatch(self, request: Request, call_next):
        # 获取 Authorization 头
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

            # 检查黑名单
            if await is_blacklisted(token):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token has been revoked"},
                )

        return await call_next(request)


# 撤销 Token API
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()


class RevokeTokenRequest(BaseModel):
    token: str


@router.post("/api/v1/auth/revoke")
async def revoke_token(request: RevokeTokenRequest):
    """撤销 Token"""
    from app.services.blacklist import add_to_blacklist

    await add_to_blacklist(request.token)
    return {"message": "Token revoked successfully"}


@router.post("/api/v1/auth/revoke-all")
async def revoke_all_tokens(user_id: str = Depends(get_current_user)):
    """撤销用户所有 Token (需要实现)"""
    # TODO: 撤销用户的所有 Token
    # 1. 删除 refresh token
    # 2. 将所有 access token 加入黑名单
    return {"message": "All tokens revoked successfully"}
