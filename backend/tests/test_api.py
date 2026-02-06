"""
API 测试
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAPIEndpoints:
    """API 端点测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from app.main import app
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """根端点测试"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "LiteKB API"
        assert "version" in data
    
    def test_health_check(self, client):
        """健康检查测试"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAuthEndpoints:
    """认证端点测试"""
    
    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)
    
    def test_register_validation(self, client):
        """注册验证测试"""
        # 缺少必填字段
        response = client.post("/api/v1/auth/register", json={})
        
        assert response.status_code == 422  # Validation error
    
    def test_login_validation(self, client):
        """登录验证测试"""
        # 缺少必填字段
        response = client.post("/api/v1/auth/login", json={})
        
        assert response.status_code == 422
    
    def test_register_success(self, client):
        """注册成功测试"""
        import uuid
        
        username = f"test_user_{uuid.uuid4().hex[:8]}"
        
        response = client.post("/api/v1/auth/register", json={
            "username": username,
            "email": f"{username}@test.com",
            "password": "test_password_123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == username
        assert "id" in data
        assert "created_at" in data
    
    def test_login_success(self, client):
        """登录成功测试"""
        import uuid
        
        username = f"login_test_{uuid.uuid4().hex[:8]}"
        password = "test_password_123"
        
        # 先注册
        client.post("/api/v1/auth/register", json={
            "username": username,
            "password": password
        })
        
        # 再登录
        response = client.post("/api/v1/auth/login", json={
            "username": username,
            "password": password
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client):
        """错误密码测试"""
        import uuid
        
        username = f"wrong_pass_{uuid.uuid4().hex[:8]}"
        password = "correct_password"
        
        # 注册
        client.post("/api/v1/auth/register", json={
            "username": username,
            "password": password
        })
        
        # 错误密码登录
        response = client.post("/api/v1/auth/login", json={
            "username": username,
            "password": "wrong_password"
        })
        
        assert response.status_code == 400
    
    def test_get_me_unauthorized(self, client):
        """未授权访问测试"""
        response = client.get("/api/v1/me")
        
        assert response.status_code == 401


class TestKBEndpoints:
    """知识库端点测试"""
    
    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, client):
        """获取认证头"""
        import uuid
        username = f"kb_test_{uuid.uuid4().hex[:8]}"
        
        client.post("/api/v1/auth/register", json={
            "username": username,
            "password": "test123"
        })
        
        login_resp = client.post("/api/v1/auth/login", json={
            "username": username,
            "password": "test123"
        })
        
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_kb_unauthorized(self, client):
        """未授权创建知识库"""
        response = client.post("/api/v1/kb", json={
            "name": "Test KB"
        })
        
        assert response.status_code == 401
    
    def test_create_kb_success(self, client, auth_headers):
        """创建知识库成功"""
        response = client.post(
            "/api/v1/kb",
            json={"name": "My Test Knowledge Base"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "My Test Knowledge Base"
        assert "id" in data
        assert data["doc_count"] == 0
    
    def test_list_kbs_empty(self, client, auth_headers):
        """空知识库列表"""
        response = client.get("/api/v1/kb", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_and_list_kb(self, client, auth_headers):
        """创建并列出知识库"""
        # 创建
        create_resp = client.post(
            "/api/v1/kb",
            json={"name": "Test KB 2", "description": "A test"},
            headers=auth_headers
        )
        kb_id = create_resp.json()["id"]
        
        # 列出
        list_resp = client.get("/api/v1/kb", headers=auth_headers)
        
        assert list_resp.status_code == 200
        kbs = list_resp.json()
        
        kb_ids = [kb["id"] for kb in kbs]
        assert kb_id in kb_ids
    
    def test_get_kb_not_found(self, client, auth_headers):
        """获取不存在的知识库"""
        response = client.get(
            "/api/v1/kb/nonexistent_id",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_update_kb(self, client, auth_headers):
        """更新知识库"""
        # 创建
        create_resp = client.post(
            "/api/v1/kb",
            json={"name": "Original Name"},
            headers=auth_headers
        )
        kb_id = create_resp.json()["id"]
        
        # 更新
        update_resp = client.put(
            f"/api/v1/kb/{kb_id}",
            json={"name": "Updated Name", "description": "New desc"},
            headers=auth_headers
        )
        
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "Updated Name"
    
    def test_delete_kb(self, client, auth_headers):
        """删除知识库"""
        # 创建
        create_resp = client.post(
            "/api/v1/kb",
            json={"name": "To Delete"},
            headers=auth_headers
        )
        kb_id = create_resp.json()["id"]
        
        # 删除
        del_resp = client.delete(
            f"/api/v1/kb/{kb_id}",
            headers=auth_headers
        )
        
        assert del_resp.status_code == 200
        
        # 确认删除
        get_resp = client.get(
            f"/api/v1/kb/{kb_id}",
            headers=auth_headers
        )
        assert get_resp.status_code == 404


class TestDocEndpoints:
    """文档端点测试"""
    
    @pytest.fixture
    def setup(self):
        """创建测试环境"""
        from app.main import app
        client = TestClient(app)
        
        import uuid
        username = f"doc_test_{uuid.uuid4().hex[:8]}"
        
        client.post("/api/v1/auth/register", json={
            "username": username,
            "password": "test123"
        })
        
        login_resp = client.post("/api/v1/auth/login", json={
            "username": username,
            "password": "test123"
        })
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建知识库
        kb_resp = client.post(
            "/api/v1/kb",
            json={"name": "Doc Test KB"},
            headers=headers
        )
        kb_id = kb_resp.json()["id"]
        
        return client, headers, kb_id
    
    def test_create_doc(self, setup):
        """创建文档测试"""
        client, headers, kb_id = setup
        
        response = client.post(
            f"/api/v1/kb/{kb_id}/docs",
            json={
                "title": "Test Document",
                "content": "This is test content"
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Document"
        assert data["status"] == "indexed"
    
    def test_list_docs_empty(self, setup):
        """空文档列表"""
        client, headers, kb_id = setup
        
        response = client.get(
            f"/api/v1/kb/{kb_id}/docs",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_and_list_docs(self, setup):
        """创建并列出文档"""
        client, headers, kb_id = setup
        
        # 创建多个文档
        for i in range(3):
            client.post(
                f"/api/v1/kb/{kb_id}/docs",
                json={
                    "title": f"Document {i}",
                    "content": f"Content {i}"
                },
                headers=headers
            )
        
        # 列出
        response = client.get(
            f"/api/v1/kb/{kb_id}/docs",
            headers=headers
        )
        
        assert response.status_code == 200
        docs = response.json()
        assert len(docs) == 3


class TestChatEndpoints:
    """对话端点测试"""
    
    @pytest.fixture
    def setup(self):
        from app.main import app
        client = TestClient(app)
        
        import uuid
        username = f"chat_test_{uuid.uuid4().hex[:8]}"
        
        client.post("/api/v1/auth/register", json={
            "username": username,
            "password": "test123"
        })
        
        login_resp = client.post("/api/v1/auth/login", json={
            "username": username,
            "password": "test123"
        })
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 创建知识库和文档
        kb_resp = client.post(
            "/api/v1/kb",
            json={"name": "Chat Test KB"},
            headers=headers
        )
        kb_id = kb_resp.json()["id"]
        
        # 添加文档
        client.post(
            f"/api/v1/kb/{kb_id}/docs",
            json={"title": "AI Guide", "content": "AI stands for Artificial Intelligence."},
            headers=headers
        )
        
        return client, headers, kb_id
    
    def test_chat_without_kb(self, setup):
        """不存在的知识库对话"""
        client, headers, _ = setup
        
        response = client.post(
            "/api/v1/kb/nonexistent/chat",
            json={"message": "Hello"},
            headers=headers
        )
        
        assert response.status_code == 404
    
    def test_chat_request_validation(self, setup):
        """对话请求验证"""
        client, headers, kb_id = setup
        
        # 空消息
        response = client.post(
            f"/api/v1/kb/{kb_id}/chat",
            json={"message": ""},
            headers=headers
        )
        
        # 应该成功(空消息也允许)
        assert response.status_code == 200
