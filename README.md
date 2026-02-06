# LiteKB - 项目状态

## ✅ 已完成

### 核心功能 (100%)
| 模块 | 状态 | 说明 |
|------|------|------|
| 用户认证 | ✅ | JWT + 注册/登录 |
| 知识库 CRUD | ✅ | 完整实现 |
| 文档管理 | ✅ | 上传/列表/删除 |
| RAG 对话 | ✅ | 3 种模式 |
| 混合检索 | ✅ | 向量 + BM25 + RRF |
| 知识图谱 | ✅ | 实体/关系抽取 |
| SSE 流式 | ✅ | 实时响应 |
| 数据持久化 | ✅ | JSON 文件存储 |
| Redis 缓存 | ✅ | 缓存中间件 |

### 高级功能
| 模块 | 状态 | 说明 |
|------|------|------|
| SSO 集成 | ✅ | Google/GitHub/Microsoft |
| 本地模型 | ✅ | Ollama + vLLM |
| 插件系统 | ✅ | 钩子系统 |
| 多模态 | ✅ | 图片/音频 |
| 分享功能 | ✅ | 链接 + 嵌入 |
| 统计仪表盘 | ✅ | 完整统计 |
| E2E 测试 | ✅ | Playwright |

---

## 📊 项目统计

| 项目 | 数量 |
|------|------|
| 提交次数 | 27 次 |
| API 端点 | 50+ |
| 后端服务 | 20+ |
| 前端页面 | 12+ |

---

## 🚀 快速启动

```bash
# 克隆
git clone https://github.com/Jungley8/litekb.git
cd litekb

# 启动 (开发)
docker-compose up -d

# 访问
# 前端: http://localhost:3000
# API: http://localhost:8000/docs
```

---

## ⚙️ 环境配置

```bash
# .env
JWT_SECRET_KEY=your-secure-key
TOKEN_EXPIRE_MINUTES=60
DB_BACKEND=json  # json / sqlite / postgresql
REDIS_ENABLED=false
OLLAMA_URL=http://localhost:11434
VLLM_URL=http://localhost:8000/v1
```

---

## 📁 项目结构

```
litekb/
├── backend/
│   ├── app/
│   │   ├── api/          # API 端点
│   │   │   ├── models.py # 模型管理
│   │   │   ├── stats.py  # 统计 API
│   │   │   └── share.py  # 分享 API
│   │   ├── db/           # 数据库
│   │   │   ├── json_store.py  # JSON 持久化
│   │   │   └── factory.py      # 数据库工厂
│   │   ├── services/     # 业务服务
│   │   │   ├── rag.py    # RAG 引擎
│   │   │   ├── search.py # 混合检索
│   │   │   ├── graph.py  # 知识图谱
│   │   │   ├── sse.py    # SSE 流式
│   │   │   ├── cache.py  # Redis 缓存
│   │   │   ├── ollama.py # Ollama 客户端
│   │   │   ├── vllm.py   # vLLM 客户端
│   │   │   └── model_provider.py # 多供应商
│   │   └── main.py       # 主入口
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── api/          # API 客户端
│   │   ├── views/        # 页面
│   │   ├── components/   # 组件
│   │   └── composables/  # Hooks
│   └── tests/           # E2E 测试
└── docs/               # 文档
    ├── MODEL_GUIDE.md   # 模型配置指南
    └── CHECKLIST.md     # 流程检查
```

---

## 🎯 供应商配置

| 场景 | 供应商 | 模型 | 成本 |
|------|--------|------|------|
| 高质量 | OpenAI | gpt-4o | $$ |
| 性价比 | OpenAI | gpt-4o-mini | $ |
| 免费本地 | Ollama | qwen2.5:7b | 免费 |
| 高并发 | vLLM | Qwen2.5-7B | 免费 |

---

## 📝 API 文档

访问 `http://localhost:8000/docs` 查看完整 API 文档。

主要端点：

```bash
# 认证
POST /api/v1/auth/register  # 注册
POST /api/v1/auth/login     # 登录

# 知识库
POST /api/v1/kb             # 创建
GET /api/v1/kb              # 列表
GET /api/v1/kb/{id}         # 详情
DELETE /api/v1/kb/{id}      # 删除

# 文档
POST /api/v1/kb/{id}/docs   # 创建
GET /api/v1/kb/{id}/docs    # 列表
DELETE /api/v1/kb/{id}/docs/{doc_id}  # 删除

# 搜索
POST /api/v1/kb/{id}/search  # 知识库内搜索
POST /api/v1/search          # 全局搜索

# RAG
POST /api/v1/kb/{id}/chat    # 对话
POST /api/v1/kb/{id}/chat/stream  # 流式对话

# 图谱
GET /api/v1/kb/{id}/graph    # 获取图谱
POST /api/v1/kb/{id}/graph/build  # 构建图谱
```

---

## 🧪 测试

```bash
# 后端测试
cd backend
pytest tests/ -v --cov

# 前端测试
cd frontend
npm run test:e2e

# API 测试
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'
```

---

## 📦 部署

### Docker 部署

```bash
# 开发环境
docker-compose up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d
```

### 环境变量

```bash
# 生产必填
JWT_SECRET_KEY=<生成随机字符串>
OPENAI_API_KEY=<你的 API Key>

# 可选
OLLAMA_URL=http://localhost:11434
VLLM_URL=http://localhost:8000/v1
REDIS_URL=redis://localhost:6379/0
```

---

## 🤝 贡献

1. Fork 本仓库
2. 创建分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -m "feat: xxx"`)
4. 推送分支 (`git push origin feature/xxx`)
5. 创建 PR

---

## 📄 许可证

MIT License

---

## 🙏 感谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [Vue 3](https://vuejs.org/)
- [Naive UI](https://www.naiveui.com/)
- [Qdrant](https://qdrant.tech/)
- [Ollama](https://ollama.com/)
