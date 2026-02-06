# LiteKB 部署指南

## 环境要求

- Docker & Docker Compose
- Python 3.10+
- Node.js 18+ (前端开发)
- 4GB+ RAM

## 快速部署 (Docker)

### 1. 克隆项目
```bash
git clone https://github.com/yourname/litekb.git
cd litekb
```

### 2. 配置环境
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
vim .env
```

**.env 示例:**
```env
# 数据库
DATABASE_URL=sqlite:///./data/litekb.db

# Qdrant 向量库
QDRANT_URL=http://qdrant:6333

# JWT
JWT_SECRET_KEY=your-secret-key

# OpenAI (可选)
OPENAI_API_KEY=sk-...
```

### 3. 启动服务
```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 4. 访问应用
- **前端**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## 本地开发

### 后端
```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动
uvicorn app.main:app --reload
```

### 前端
```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build
```

### 独立启动 Qdrant
```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant:v1.9.0
```

## 生产部署

### Docker Compose (生产)
```bash
# 使用生产配置
docker-compose -f docker-compose.yml up -d

# 或使用 docker stack deploy (Swarm)
```

### Kubernetes

使用 helm 或 kubectl 部署:

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: litekb
spec:
  replicas: 2
  selector:
    matchLabels:
      app: litekb
  template:
    spec:
      containers:
      - name: backend
        image: litekb/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: postgresql://...
        - name: QDRANT_URL
          value: http://qdrant:6333
```

### 前端托管
- **Vercel**: `vercel --prod`
- **Railway**: 连接 GitHub 仓库

### 后端托管
- **Railway**: 部署后端服务
- **Render**: Web Service
- **Fly.io**: `fly deploy`

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| DATABASE_URL | 数据库连接 | sqlite:///./data/litekb.db |
| QDRANT_URL | Qdrant 地址 | http://localhost:6333 |
| QDRANT_API_KEY | Qdrant API Key | - |
| JWT_SECRET_KEY | JWT 密钥 | - |
| OPENAI_API_KEY | OpenAI API Key | - |
| LLM_PROVIDER | LLM 提供商 | openai |
| EMBEDDING_PROVIDER | Embedding 提供商 | openai |

### 可选组件

#### Neo4j (知识图谱)
```yaml
neo4j:
  image: neo4j:5.15-community
  environment:
    - NEO4J_AUTH=neo4j/password
  ports:
    - "7474:7474"
    - "7687:7687"
```

#### PostgreSQL (生产数据库)
```yaml
postgres:
  image: postgres:15-alpine
  environment:
    - POSTGRES_DB=litekb
    - POSTGRES_USER=litekb
    - POSTGRES_PASSWORD=password
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

## 性能优化

### 1. 向量索引
```python
# config.py
QDRANT_OPTIMIZE_CONFIG = OptimizeConfig(
    vec_index=HnswIndexConfig(
        m=16,
        ef_construct=100
    )
)
```

### 2. 缓存
```python
# 启用 Redis 缓存
REDIS_URL=redis://localhost:6379
```

### 3. 异步任务
```bash
# 使用 Celery 处理大文档
CELERY_BROKER_URL=redis://localhost:6379
```

## 监控

### 健康检查
```bash
curl http://localhost:8000/health
```

### 日志
```bash
# 查看实时日志
docker-compose logs -f backend
```

## 备份与恢复

### 数据库备份
```bash
# SQLite
cp data/litekb.db backup/litekb_$(date +%Y%m%d).db

# Qdrant
curl http://localhost:6333/collections/litekb_chunks/snapshot > backup/qdrant_snapshot.tar.gz
```

### 恢复
```bash
# SQLite
cp backup/litekb_20240101.db data/litekb.db

# Qdrant
curl -X POST http://localhost:6333/collections/litekb_chunks/snapshot \
  -H "Content-Type: application/json" \
  -d '{"location": "backup/qdrant_snapshot.tar.gz"}'
```

## 常见问题

### Q: Qdrant 启动失败?
A: 检查端口 6333 是否被占用，或查看日志 `docker-compose logs qdrant`

### Q: OpenAI API 调用失败?
A: 检查 API Key 是否正确，或网络连接

### Q: 前端无法连接后端?
A: 检查 `VITE_API_URL` 环境变量配置

## 更新升级

```bash
# 拉取最新镜像
docker-compose pull

# 重启服务
docker-compose up -d

# 数据库迁移 (如有)
alembic upgrade head
```
