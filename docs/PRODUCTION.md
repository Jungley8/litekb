# 🚀 生产环境优化清单

## 1. 缺失的配置文件

### ❌ 缺失

| 文件 | 说明 | 优先级 |
|------|------|--------|
| `Dockerfile` | 后端 Docker 镜像 | 🔴 高 |
| `Dockerfile.prod` | 生产环境镜像 | 🔴 高 |
| `nginx.conf` | 反向代理 + SSL | 🔴 高 |
| `.env.example` | 环境变量模板 | 🟡 中 |
| `.dockerignore` | Docker 忽略文件 | 🟡 中 |
| `healthcheck.py` | 健康检查 | 🟡 中 |
| `prometheus.yml` | 监控配置 | 🟢 低 |
| `grafana/` | 监控面板 | 🟢 低 |

---

## 2. 安全性问题

### ⚠️ 需修复

| 问题 | 当前状态 | 修复方案 |
|------|----------|----------|
| JWT Key 硬编码 | ❌ | 使用环境变量 |
| 密码无强度验证 | ❌ | 添加密码策略 |
| 无 Rate Limiting | ❌ | 添加限流中间件 |
| 无输入验证 | ⚠️ 部分 | 增强 Pydantic 验证 |
| 无 HTTPS 强制 | ❌ | 添加 HTTPS 中间件 |
| 无安全 Headers | ❌ | 添加 Helmet |

---

## 3. 性能优化

### 📊 需优化

| 项目 | 当前 | 目标 |
|------|------|------|
| 数据库连接池 | ❌ 无 | 启用连接池 |
| Gzip 压缩 | ❌ 无 | 添加压缩 |
| Redis 缓存 | ⚠️ 部分 | 全面缓存 |
| 异步处理 | ⚠️ 部分 | Celery 异步 |
| 静态文件服务 | ❌ 无 | Nginx 托管 |
| 数据库索引 | ⚠️ 部分 | 完善索引 |

---

## 4. 监控与日志

### 📈 缺失

| 功能 | 状态 | 说明 |
|------|------|------|
| 应用监控 | ❌ | 添加 Prometheus |
| 错误追踪 | ❌ | 添加 Sentry |
| 日志集中 | ❌ | 结构化日志 |
| 健康检查 | ❌ | /health 端点 |
| 指标暴露 | ❌ | /metrics 端点 |

---

## 5. 高可用性

### 🔴 缺失

| 功能 | 状态 | 说明 |
|------|------|------|
| 多副本部署 | ❌ | K8s/Helm |
| 数据库备份 | ❌ | 自动备份 |
| 负载均衡 | ❌ | Nginx upstream |
| SSL 证书 | ❌ | Let's Encrypt |
| 域名配置 | ❌ | DNS 设置 |

---

## 6. 立即修复项

### 🔴 高优先级

```bash
# 1. 添加环境变量模板
cat > .env.example << 'EOF'
# 应用
SECRET_KEY=your-super-secret-key-change-this
DEBUG=false

# 数据库
DATABASE_URL=postgresql://user:pass@host:5432/litekb

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_URL=http://localhost:6333

# OpenAI
OPENAI_API_KEY=sk-xxx

# 可选
ANTHROPIC_API_KEY=sk-ant-xxx
GOOGLE_API_KEY=xxx
EOF

# 2. 创建 Dockerfile
cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

---

## 7. 生产环境部署命令

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 填写真实值

# 2. 构建并启动
docker-compose -f docker-compose.prod.yml up -d --build

# 3. 检查状态
docker-compose ps
docker-compose logs -f

# 4. 迁移数据库
docker-compose exec backend python -m alembic upgrade head
```

---

## 8. Docker Compose Prod 配置

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://litekb:password@postgres:5432/litekb
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_URL=http://qdrant:6333
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEBUG=false
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 2G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
      - backend

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=litekb
      - POSTGRES_USER= litekb
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  qdrant:
    image: qdrant/qdrant:v1.9.0
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
```

---

## 📋 优化优先级

### 立即执行 (1-2小时)

1. ✅ 创建 `.env.example`
2. ✅ 创建 `backend/Dockerfile`
3. ✅ 创建 `nginx.conf`
4. ✅ 添加健康检查端点
5. ✅ 启用 JWT Key 环境变量

### 一天内完成

6. 🔄 添加 Rate Limiting
7. 🔄 添加安全 Headers (Helmet)
8. 🔄 完善数据库连接池
9. 🔄 创建 `.dockerignore`
10. 🔄 添加 SSL 配置

### 一周内完成

11. 📅 监控 (Prometheus + Grafana)
12. 📅 日志集中
13. 📅 自动备份
14. 📅 CI/CD 完善
15. 📅 负载均衡配置

---

## ✅ 检查清单

### 安全性
- [ ] JWT Key 环境变量
- [ ] 密码强度验证
- [ ] Rate Limiting
- [ ] HTTPS 强制
- [ ] 安全 Headers
- [ ] CORS 限制

### 性能
- [ ] 数据库连接池
- [ ] Redis 缓存
- [ ] Gzip 压缩
- [ ] 异步 Celery
- [ ] 静态文件 Nginx

### 监控
- [ ] /health 端点
- [ ] /metrics 端点
- [ ] 错误追踪 (Sentry)
- [ ] 结构化日志

### 可用性
- [ ] 数据库备份
- [ ] SSL 证书
- [ ] 多副本部署
- [ ] 健康检查
- [ ] 自动重启
