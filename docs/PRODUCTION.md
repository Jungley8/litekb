# 🚀 LiteKB 生产环境优化清单

## ⚠️ 立即修复

### 1. Langfuse 环境变量

```yaml
# docker-compose.prod.yml
environment:
  # ... 现有配置
  - LANGFUSE_ENABLED=${LANGFUSE_ENABLED}
  - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
  - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}
  - LANGFUSE_HOST=${LANGFUSE_HOST:-https://cloud.langfuse.com}
```

添加 `.env`:
```bash
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-xxx
LANGFUSE_SECRET_KEY=sk-xxx
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

### 2. Celery Broker 配置

```yaml
celery-worker:
  environment:
    - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    - CELERY_RESULT_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
```

---

### 3. 后端健康检查

```yaml
backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    # 改为检查 /ready
    test: ["CMD-SHELL", "curl -f http://localhost:8000/health && curl -f http://localhost:8000/ready"]
```

---

## 🔒 安全加固

### 4. Redis 认证

```yaml
redis:
  command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
  environment:
    - REDIS_PASSWORD=${REDIS_PASSWORD}
```

更新所有依赖 Redis 的服务：
```yaml
environment:
  - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
```

---

### 5. JWT Secret 强度

```bash
# 生成强密钥
openssl rand -hex 64

# .env
SECRET_KEY=your-super-secret-key-min-32-chars
JWT_ALGORITHM=HS256
TOKEN_EXPIRE_MINUTES=60
```

---

### 6. HTTPS 强制重定向

```nginx
# nginx.conf
server {
    listen 80;
    server_name _;
    
    # 强制 HTTPS
    return 301 https://$server_name$request_uri;
}
```

---

## 🚀 性能优化

### 7. Nginx Rate Limiting

```nginx
http {
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
    
    server {
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
        }
        
        location /api/auth/login {
            limit_req zone=login_limit burst=5 nodelay;
        }
    }
}
```

---

### 8. 数据库连接池调优

```bash
# .env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
```

---

### 9. Qdrant 性能

```yaml
qdrant:
  environment:
    - QDRANT__STORAGE__PERFORMANCE__MAX_OPTIMIZERS_THREADS=4
    - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=4
    - QDRANT__STORAGE__PERFORMANCE__UPDATE_CUDA=1  # 如果有 GPU
```

---

### 10. PostgreSQL 优化

```sql
-- postgres/init/performance.sql
ALTER SYSTEM SET shared_buffers = '1GB';
ALTER SYSTEM SET effective_cache_size = '3GB';
ALTER SYSTEM SET work_mem = '64MB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '64MB';
ALTER SYSTEM SET max_connections = 200;
```

---

## 📊 监控告警

### 11. 健康检查端点

后端需实现 `/ready` 端点：

```python
# app/main.py
@app.get("/ready")
async def readiness_check():
    """就绪检查"""
    checks = {
        "database": False,
        "redis": False,
        "qdrant": False,
    }
    
    try:
        # DB
        from app.db.factory import db
        db.session.execute("SELECT 1")
        checks["database"] = True
    except:
        pass
    
    # ... 其他检查
    
    if all(checks.values()):
        return {"status": "ready", "checks": checks}
    else:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "checks": checks}
        )
```

---

### 12. 日志轮转

```bash
# /etc/logrotate.d/litekb
/var/log/litekb/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 root root
    postrotate
        docker-compose restart backend nginx
    endscript
}
```

---

## 💾 备份策略

### 13. 自动备份脚本

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 数据库备份
docker exec litekb_postgres_1 pg_dump -U litekb litekb > "$BACKUP_DIR/db_$DATE.sql"

# Qdrant 备份
docker exec litekb_qdrant_1 qdrant-cli backup --collection litekb_chunks "$BACKUP_DIR/qdrant_$DATE"

# 清理旧备份 (保留 7 天)
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "qdrant_*" -mtime +7 -rf

# 上传到 S3 (可选)
# aws s3 cp "$BACKUP_DIR/" s3://litekb-backups/
```

定时任务:
```bash
# crontab
0 3 * * * /opt/litekb/scripts/backup.sh
```

---

## 📋 部署清单

### 部署前检查

```bash
# 1. 生成密钥
openssl rand -hex 64 > .env.secret
echo "SECRET_KEY=$(cat .env.secret)" >> .env

# 2. 更新环境变量
cp .env.example .env
# 编辑 .env 填入所有密钥

# 3. 创建目录
mkdir -p ssl secrets backups

# 4. 生成 SSL 证书
# Let's Encrypt
certbot certonly --standalone -d your-domain.com

# 5. 构建
docker-compose -f docker-compose.prod.yml build

# 6. 测试
docker-compose -f docker-compose.prod.yml up -d
docker-compose logs -f
```

---

## ✅ 最终检查清单

| 项目 | 状态 | 优先级 |
|------|------|--------|
| Langfuse 环境变量 | ⬜ | P0 |
| Redis 认证 | ⬜ | P0 |
| JWT Secret 强密钥 | ⬜ | P0 |
| HTTPS 强制重定向 | ⬜ | P1 |
| Rate Limiting | ⬜ | P1 |
| 数据库连接池调优 | ⬜ | P2 |
| /ready 健康检查 | ⬜ | P2 |
| 日志轮转 | ⬜ | P2 |
| 自动备份 | ⬜ | P2 |
| PostgreSQL 优化 | ⬜ | P3 |
| 监控告警 | ⬜ | P3 |

---

## 🎯 最小可行生产配置 (P0)

只需修改 `docker-compose.prod.yml` 和 `.env`：

```bash
# .env
SECRET_KEY=<openssl rand -hex 64>
POSTGRES_PASSWORD=<openssl rand -hex 32>
REDIS_PASSWORD=<openssl rand -hex 32>
JWT_SECRET_KEY=<openssl rand -hex 32>

LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-xxx
LANGFUSE_SECRET_KEY=sk-xxx

OPENAI_API_KEY=sk-xxx
```

```yaml
# docker-compose.prod.yml
backend:
  environment:
    - SECRET_KEY=${SECRET_KEY}
    - LANGFUSE_ENABLED=${LANGFUSE_ENABLED}
    - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
    - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}

redis:
  command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
```

这样就可以部署了！
