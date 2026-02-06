# LiteKB API 文档

> 基于 FastAPI 自动生成的 API 文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API 版本**: v1
- **认证**: Bearer Token (JWT)

## 认证接口

### 注册用户
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "your_username",
  "email": "your@email.com",
  "password": "your_password"
}
```

**响应:**
```json
{
  "id": "uuid",
  "username": "your_username",
  "email": "your@email.com",
  "created_at": "2024-01-01T00:00:00"
}
```

### 登录
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**响应:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### 获取当前用户
```http
GET /api/v1/me
Authorization: Bearer <token>
```

## 知识库接口

### 创建知识库
```http
POST /api/v1/kb
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "我的知识库",
  "description": "这是一个测试知识库"
}
```

**响应:**
```json
{
  "id": "uuid",
  "name": "我的知识库",
  "description": "这是一个测试知识库",
  "doc_count": 0,
  "created_at": "2024-01-01T00:00:00"
}
```

### 列出知识库
```http
GET /api/v1/kb
Authorization: Bearer <token>
```

### 获取知识库详情
```http
GET /api/v1/kb/{kb_id}
Authorization: Bearer <token>
```

### 更新知识库
```http
PUT /api/v1/kb/{kb_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "新名称",
  "description": "新描述"
}
```

### 删除知识库
```http
DELETE /api/v1/kb/{kb_id}
Authorization: Bearer <token>
```

## 文档接口

### 创建文档
```http
POST /api/v1/kb/{kb_id}/docs
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "文档标题",
  "content": "文档内容...",
  "metadata": {"source": "url"}
}
```

### 上传文档文件
```http
POST /api/v1/kb/{kb_id}/docs/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: [文件]
```

**支持格式:** TXT, Markdown, DOCX, PDF

### 列出文档
```http
GET /api/v1/kb/{kb_id}/docs?skip=0&limit=100
Authorization: Bearer <token>
```

### 删除文档
```http
DELETE /api/v1/kb/{kb_id}/docs/{doc_id}
Authorization: Bearer <token>
```

## 搜索接口

### 混合检索
```http
POST /api/v1/kb/{kb_id}/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "搜索关键词",
  "strategy": "hybrid",  // hybrid, vector, keyword
  "top_k": 10,
  "filters": {"source": "pdf"}
}
```

**响应:**
```json
{
  "results": [
    {
      "id": "chunk_id",
      "title": "文档标题",
      "content": "...相关段落...",
      "score": 0.95,
      "type": "hybrid"
    }
  ],
  "strategy": "hybrid"
}
```

## RAG 对话接口

### 普通对话
```http
POST /api/v1/kb/{kb_id}/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "什么是 Transformer？",
  "history": [
    {"role": "user", "content": "之前的问题"},
    {"role": "assistant", "content": "之前的回答"}
  ],
  "mode": "naive"  // naive, contextual, graph-augmented
}
```

**响应:**
```json
{
  "answer": "Transformer 是一种...",
  "sources": [
    {
      "doc_id": "doc_id",
      "title": "相关文档标题",
      "chunk": "引用段落...",
      "score": 0.95
    }
  ],
  "conversation_id": "uuid"
}
```

### 流式对话 (SSE)
```http
GET /api/v1/kb/{kb_id}/chat/stream?message=问题&mode=naive
Authorization: Bearer <token>
```

**SSE 事件:**

| 事件 | 数据 |
|------|------|
| sources | 检索来源 |
| message | 回答内容片段 |
| done | 完成信号 |
| error | 错误信息 |

## 知识图谱接口

### 获取图谱
```http
GET /api/v1/kb/{kb_id}/graph
Authorization: Bearer <token>
```

**响应:**
```json
{
  "nodes": [
    {"id": "entity_id", "label": "实体名", "type": "类型"}
  ],
  "links": [
    {"source": "source_id", "target": "target_id", "type": "关系"}
  ]
}
```

### 构建图谱
```http
POST /api/v1/kb/{kb_id}/graph/build?rebuild=false
Authorization: Bearer <token>
```

### 搜索实体
```http
GET /api/v1/kb/{kb_id}/graph/search?q=关键词
Authorization: Bearer <token>
```

### 获取实体详情
```http
GET /api/v1/kb/{kb_id}/graph/entity/{entity_id}
Authorization: Bearer <token>
```

## 错误处理

### 错误响应格式
```json
{
  "detail": "错误描述"
}
```

### 常见错误码

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未认证或 token 无效 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
