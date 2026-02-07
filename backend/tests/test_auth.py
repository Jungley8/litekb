"""
认证测试
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAuth:
    """认证测试"""

    def test_password_hashing(self):
        """密码哈希测试"""
        from app.auth import pwd_context

        password = "test_password_123"
        hashed = pwd_context.hash(password)

        assert pwd_context.verify(password, hashed)
        assert not pwd_context.verify("wrong_password", hashed)

    def test_password_not_plain(self):
        """密码不应是明文"""
        from app.auth import pwd_context

        password = "test_password"
        hashed = pwd_context.hash(password)

        assert hashed != password
        assert len(hashed) > len(password)

    def test_generate_api_key(self):
        """API Key 生成测试"""
        from app.auth import generate_api_key

        key_id, key, key_hash, prefix = generate_api_key()

        assert len(key_id) == 16  # 8 bytes hex
        assert key.startswith("lkb_")
        assert len(key) == 54  # "lkb_" + 48 hex chars
        assert prefix == key[:12]
        assert len(key_hash) == 64  # SHA256 hex

    def test_hash_api_key(self):
        """API Key 哈希测试"""
        from app.auth import hash_api_key

        key = "lkb_abc123"
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)

        assert hash1 == hash2  # 相同输入，相同输出
        assert len(hash1) == 64

    def test_generate_jwt_token(self):
        """JWT Token 生成测试"""
        from app.auth import generate_jwt_token

        token = generate_jwt_token("user_123")

        assert isinstance(token, str)
        assert len(token) > 50  # JWT 通常较长

    def test_permission_constants(self):
        """权限常量测试"""
        from app.auth import Permission

        assert hasattr(Permission, "KB_CREATE")
        assert hasattr(Permission, "KB_READ")
        assert hasattr(Permission, "KB_DELETE")
        assert hasattr(Permission, "DOC_CREATE")
        assert hasattr(Permission, "DOC_DELETE")

    def test_role_permissions(self):
        """角色权限测试"""
        from app.auth import ROLE_PERMISSIONS

        # Owner 应该拥有所有权限
        owner_perms = ROLE_PERMISSIONS["owner"]
        assert "kb:create" in owner_perms
        assert "kb:delete" in owner_perms
        assert "org:delete" in owner_perms

        # Member 只有基本权限
        member_perms = ROLE_PERMISSIONS["member"]
        assert "kb:create" in member_perms
        assert "kb:delete" not in member_perms
        assert "org:delete" not in member_perms

    def test_has_permission(self):
        """权限检查测试"""
        from app.auth import has_permission, AuthContext

        # 创建 AuthContext
        auth = AuthContext(
            user=Mock(id="user_1"), organization=Mock(id="org_1"), member_role="admin"
        )

        # Admin 应该有权
        assert has_permission(auth, "kb:create")
        assert has_permission(auth, "kb:delete")

        # Member 不应该有管理权限
        auth.member_role = "member"
        assert has_permission(auth, "kb:create")
        assert not has_permission(auth, "kb:delete")

    def test_auth_context_properties(self):
        """AuthContext 属性测试"""
        from app.auth import AuthContext

        user = Mock(id="user_123")
        org = Mock(id="org_456")

        auth = AuthContext(
            user=user,
            organization=org,
            member_role="admin",
            is_api_key=True,
            api_scopes=["read", "write"],
        )

        assert auth.user_id == "user_123"
        assert auth.org_id == "org_456"
        assert auth.member_role == "admin"
        assert auth.is_api_key is True
        assert "read" in auth.api_scopes


class TestCache:
    """缓存测试"""

    def test_cache_strategies(self):
        """缓存策略配置测试"""
        from app.cache import CACHE_STRATEGIES

        assert "kb_list" in CACHE_STRATEGIES
        assert "doc_list" in CACHE_STRATEGIES
        assert "rag_response" in CACHE_STRATEGIES
        assert "search_results" in CACHE_STRATEGIES

        # 检查 TTL 配置
        assert CACHE_STRATEGIES["kb_list"]["expire"] == 300  # 5分钟
        assert CACHE_STRATEGIES["rag_response"]["expire"] == 3600  # 1小时

    def test_make_key(self):
        """缓存 Key 生成测试"""
        from app.cache import Cache

        cache = Cache()
        key = cache.make_key("search", "test query", "kb_123")

        assert isinstance(key, str)
        assert len(key) == 32  # MD5 hex

    def test_make_key_consistency(self):
        """相同输入生成相同 Key"""
        from app.cache import Cache

        cache = Cache()
        key1 = cache.make_key("a", "b", "c")
        key2 = cache.make_key("a", "b", "c")

        assert key1 == key2


class TestModels:
    """数据模型测试"""

    def test_organization_model(self):
        """组织模型测试"""
        from app.models_v2 import Organization

        org = Organization(id="org_123", name="Test Org", slug="test-org", plan="pro")

        assert org.name == "Test Org"
        assert org.slug == "test-org"
        assert org.plan == "pro"

    def test_user_model(self):
        """用户模型测试"""
        from app.models_v2 import User

        user = User(
            id="user_123",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            organization_id="org_1",
            role="member",
        )

        assert user.username == "testuser"
        assert user.role == "member"

    def test_api_key_model(self):
        """API Key 模型测试"""
        from app.models_v2 import APIKey

        key = APIKey(
            id="key_123",
            organization_id="org_1",
            name="Test Key",
            key_hash="hash",
            key_prefix="lkb_abc",
            scopes=["read", "write"],
        )

        assert key.name == "Test Key"
        assert "read" in key.scopes


class TestDocumentService:
    """文档服务测试"""

    def test_chunk_size_default(self):
        """默认分块大小"""
        from app.services.document import DocumentProcessor

        processor = DocumentProcessor()

        assert processor.chunk_size == 1000
        assert processor.chunk_overlap == 200

    @pytest.mark.asyncio
    async def test_process_empty_document(self):
        """空文档处理"""
        from app.services.document import DocumentProcessor

        processor = DocumentProcessor()

        result = await processor.process_document(b"", "empty.txt")

        assert result["title"] == "empty"
        assert result["chunks"] == []

    @pytest.mark.asyncio
    async def test_extract_unsupported_format(self):
        """不支持格式测试"""
        from app.services.document import DocumentProcessor

        processor = DocumentProcessor()

        with pytest.raises(ValueError) as exc_info:
            await processor.extract_text(b"data", "test.exe")

        assert "不支持" in str(exc_info.value)


class TestSearchService:
    """搜索服务测试"""

    def test_search_result_dataclass(self):
        """搜索结果数据结构测试"""
        from app.services.search import SearchResult

        result = SearchResult(
            id="doc_1",
            content="test content",
            score=0.95,
            source_type="vector",
            metadata={"source": "pdf"},
        )

        assert result.id == "doc_1"
        assert result.score == 0.95
        assert result.source_type == "vector"

    def test_rrf_fusion_empty(self):
        """空结果融合测试"""
        from app.services.search import rrf_fuse

        results = rrf_fuse([], [], top_k=10)

        assert results == []


class TestRAGService:
    """RAG 服务测试"""

    def test_default_system_prompt(self):
        """默认系统提示测试"""
        from app.services.rag import RAGEngine

        engine = RAGEngine.__new__(RAGEngine)
        prompt = engine._default_system_prompt()

        assert "知识库助手" in prompt
        assert "上下文" in prompt
        assert len(prompt) > 50

    def test_build_context(self):
        """上下文构建测试"""
        from app.services.rag import RAGEngine
        from app.services.search import SearchResult

        engine = RAGEngine.__new__(RAGEngine)

        chunks = [
            SearchResult(
                id="1",
                content="First chunk with important info",
                score=0.9,
                source_type="vector",
                metadata={},
            ),
            SearchResult(
                id="2",
                content="Second chunk with more details",
                score=0.8,
                source_type="vector",
                metadata={},
            ),
        ]

        context = engine._build_context(chunks)

        assert "[1]" in context
        assert "[2]" in context
        assert "First chunk" in context
        assert "Second chunk" in context


class TestConfig:
    """配置测试"""

    def test_settings_defaults(self):
        """默认配置测试"""
        from app.config import Settings

        settings = Settings()

        assert settings.app_name == "LiteKB"
        assert settings.debug is True
        assert settings.chunk_size == 1000

    def test_permission_constants_complete(self):
        """权限常量完整性测试"""
        from app.auth import Permission

        required_perms = [
            "KB_CREATE",
            "KB_READ",
            "KB_UPDATE",
            "KB_DELETE",
            "KB_MANAGE",
            "DOC_CREATE",
            "DOC_READ",
            "DOC_DELETE",
            "MEMBER_INVITE",
            "MEMBER_REMOVE",
            "MEMBER_MANAGE",
            "ORG_SETTINGS",
            "ORG_DELETE",
            "API_KEY_CREATE",
            "API_KEY_DELETE",
        ]

        for perm in required_perms:
            assert hasattr(Permission, perm), f"Missing permission: {perm}"

    def test_role_permissions_completeness(self):
        """角色权限完整性测试"""
        from app.auth import ROLE_PERMISSIONS

        required_roles = ["owner", "admin", "member"]

        for role in required_roles:
            assert role in ROLE_PERMISSIONS, f"Missing role: {role}"

        # 检查 owner 有所有权限
        all_perms = set()
        for role_perms in ROLE_PERMISSIONS.values():
            all_perms.update(role_perms)

        owner_perms = set(ROLE_PERMISSIONS["owner"])
        assert owner_perms == all_perms, "Owner should have all permissions"
