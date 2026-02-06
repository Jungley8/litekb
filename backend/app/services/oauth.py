"""
OAuth2 企业登录服务
"""
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from fastapi import HTTPException, status
from loguru import logger
import httpx
import secrets


class OAuthProvider(str, Enum):
    """OAuth 提供商"""
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    OKTA = "okta"
    SAML = "saml"


@dataclass
class OAuthConfig:
    """OAuth 配置"""
    client_id: str
    client_secret: str
    redirect_uri: str
    auth_url: str
    token_url: str
    userinfo_url: str
    scopes: list


class OAuthService:
    """OAuth 服务"""
    
    PROVIDERS = {
        OAuthProvider.GOOGLE: OAuthConfig(
            client_id="",
            client_secret="",
            redirect_uri="",
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
            scopes=["openid", "email", "profile"]
        ),
        OAuthProvider.GITHUB: OAuthConfig(
            client_id="",
            client_secret="",
            redirect_uri="",
            auth_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            userinfo_url="https://api.github.com/user",
            scopes=["read:user", "user:email"]
        ),
        OAuthProvider.MICROSOFT: OAuthConfig(
            client_id="",
            client_secret="",
            redirect_uri="",
            auth_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            userinfo_url="https://graph.microsoft.com/v1.0/me",
            scopes=["openid", "email", "profile", "User.Read"]
        ),
    }
    
    def __init__(self):
        self.configs: Dict[OAuthProvider, OAuthConfig] = {}
    
    def configure_provider(
        self,
        provider: OAuthProvider,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ):
        """配置 OAuth 提供商"""
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}")
        
        config = self.PROVIDERS[provider]
        config.client_id = client_id
        config.client_secret = client_secret
        config.redirect_uri = redirect_uri
        
        self.configs[provider] = config
        logger.info(f"Configured OAuth provider: {provider.value}")
    
    def get_authorization_url(
        self,
        provider: OAuthProvider,
        state: str = None
    ) -> str:
        """获取授权 URL"""
        config = self._get_config(provider)
        
        state = state or secrets.token_urlsafe(16)
        
        params = {
            "client_id": config.client_id,
            "redirect_uri": config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(config.scopes),
            "state": state
        }
        
        # 提供商特定参数
        if provider == OAuthProvider.GOOGLE:
            params["access_type"] = "offline"
            params["prompt"] = "consent"
        
        elif provider == OAuthProvider.MICROSOFT:
            params["response_mode"] = "query"
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{config.auth_url}?{query_string}"
    
    def _get_config(self, provider: OAuthProvider) -> OAuthConfig:
        """获取配置"""
        if provider not in self.configs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider {provider} not configured"
            )
        return self.configs[provider]
    
    async def exchange_code_for_token(
        self,
        provider: OAuthProvider,
        code: str
    ) -> Dict[str, Any]:
        """用授权码交换 Token"""
        config = self._get_config(provider)
        
        async with httpx.AsyncClient() as client:
            if provider == OAuthProvider.GOOGLE:
                response = await client.post(config.token_url, data={
                    "client_id": config.client_id,
                    "client_secret": config.client_secret,
                    "code": code,
                    "redirect_uri": config.redirect_uri,
                    "grant_type": "authorization_code"
                })
            
            elif provider == OAuthProvider.GITHUB:
                headers = {"Accept": "application/json"}
                response = await client.post(
                    config.token_url,
                    headers=headers,
                    data={
                        "client_id": config.client_id,
                        "client_secret": config.client_secret,
                        "code": code,
                        "redirect_uri": config.redirect_uri
                    }
                )
            
            else:
                response = await client.post(config.token_url, data={
                    "client_id": config.client_id,
                    "client_secret": config.client_secret,
                    "code": code,
                    "redirect_uri": config.redirect_uri,
                    "grant_type": "authorization_code"
                })
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token"
                )
            
            return response.json()
    
    async def get_user_info(
        self,
        provider: OAuthProvider,
        access_token: str
    ) -> Dict[str, Any]:
        """获取用户信息"""
        config = self._get_config(provider)
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            if provider == OAuthProvider.GITHUB:
                headers["Accept"] = "application/vnd.github.v3+json"
            
            response = await client.get(config.userinfo_url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"User info failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info"
                )
            
            return self._normalize_user_info(provider, response.json())
    
    def _normalize_user_info(
        self,
        provider: OAuthProvider,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """标准化用户信息"""
        normalizers = {
            OAuthProvider.GOOGLE: lambda d: {
                "email": d.get("email"),
                "name": d.get("name"),
                "avatar": d.get("picture"),
                "provider_id": d.get("id"),
                "provider": "google"
            },
            OAuthProvider.GITHUB: lambda d: {
                "email": d.get("email"),
                "name": d.get("name"),
                "avatar": d.get("avatar_url"),
                "provider_id": str(d.get("id")),
                "provider": "github"
            },
            OAuthProvider.MICROSOFT: lambda d: {
                "email": d.get("mail") or d.get("userPrincipalName"),
                "name": d.get("displayName"),
                "avatar": None,
                "provider_id": d.get("id"),
                "provider": "microsoft"
            }
        }
        
        normalizer = normalizers.get(provider, lambda d: d)
        return normalizer(data)
    
    def link_account(
        self,
        user_id: str,
        provider: OAuthProvider,
        provider_id: str
    ) -> bool:
        """绑定第三方账号"""
        # TODO: 保存到数据库
        logger.info(f"Linked account: user={user_id}, provider={provider.value}, id={provider_id}")
        return True


# 全局实例
oauth_service = OAuthService()


# ==================== SSO 企业登录 ====================

class SSOService:
    """SSO 服务"""
    
    def __init__(self):
        self.oauth = oauth_service
    
    def get_sso_providers(self) -> list:
        """获取可用的 SSO 提供商"""
        return [
            {
                "id": p.value,
                "name": p.value.title(),
                "configured": p in self.oauth.configs
            }
            for p in OAuthProvider
        ]
    
    async def handle_sso_callback(
        self,
        provider: OAuthProvider,
        code: str,
        state: str
    ) -> Dict[str, Any]:
        """处理 SSO 回调"""
        # 1. 交换 Token
        tokens = await self.oauth.exchange_code_for_token(provider, code)
        
        # 2. 获取用户信息
        user_info = await self.oauth.get_user_info(
            provider,
            tokens.get("access_token")
        )
        
        # TODO: 查找或创建用户
        # 返回用户信息 + Token
        
        return {
            "user": user_info,
            "tokens": {
                "access_token": tokens.get("access_token"),
                "provider": provider.value
            }
        }


# 全局实例
sso_service = SSOService()


# ==================== SAML 支持 ====================

class SAMLAuth:
    """SAML 认证"""
    
    def __init__(self):
        self.enabled = False
    
    def configure(
        self,
        idp_metadata_url: str,
        entity_id: str,
        acs_url: str
    ):
        """配置 SAML"""
        try:
            import onelogin.saml2.auth
            from onelogin.saml2.utils import OneLogin_Saml2_Utils
            
            self.enabled = True
            logger.info("SAML configured")
        
        except ImportError:
            logger.warning("python3-saml not installed")
    
    def get_login_url(self) -> str:
        """获取登录 URL"""
        # TODO: 实现 SAML 登录 URL
        return ""
    
    def handle_response(self, saml_response: str) -> Dict[str, Any]:
        """处理 SAML 响应"""
        # TODO: 实现 SAML 响应处理
        return {}


# 全局实例
saml_auth = SAMLAuth()
