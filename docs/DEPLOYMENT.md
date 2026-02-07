# 🚀 LiteKB 部署清单

## 环境要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 存储 | 20 GB | 50 GB+ |
| Docker | 20.10+ | 最新版 |
| Docker Compose | 2.0+ | 最新版 |

---

## 部署步骤

### 1. 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 重启 Docker
sudo systemctl restart docker
```

### 2. 获取代码

```bash
git clone https://github.com/Jungley8/litekb.git
cd litekb
```

### 3. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 生成强密钥
export SECRET_KEY=$(openssl rand -hex 64)
export POSTGRES_PASSWORD=$(openssl rand -hex 32)
export REDIS_PASSWORD=$(openssl rand -hex 32)

# 写入 .env
cat >> .env << EOF
SECRET_KEY=$SECRET_KEY
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD
EOF

# 编辑配置
nano .env
```

### 4. 必要配置 (.env)

```bash
# ========== 必须修改 ==========
SECRET_KEY=your-32-char-secret-key
POSTGRES_PASSWORD=your-postgres-password
REDIS_PASSWORD=your-redis-password
OPENAI_API_KEY=sk-your-openai-key

# ========== 可选配置 ==========
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-xxx
LANGFUSE_SECRET_KEY=sk-xxx
```

### 5. 创建必要目录

```bash
mkdir -p ssl secrets postgres/init grafana/provisioning
```

### 6. 配置 SSL (Let's Encrypt)

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot certonly --standalone -d your-domain.com

# 复制证书
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/
```

### 7. 启动服务

```bash
# 构建并启动
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 8. 验证部署

```bash
# 检查服务状态
docker-compose -f docker-compose.prod.yml ps

# 检查健康端点
curl http://localhost/health
curl http://localhost/ready
```

---

## 常用命令

| 命令 | 描述 |
|------|------|
| `docker-compose up -d` | 启动所有服务 |
| `docker-compose down` | 停止所有服务 |
| `docker-compose logs -f` | 查看日志 |
| `docker-compose restart` | 重启所有服务 |
| `docker-compose exec backend sh` | 进入后端容器 |

---

## 监控

| 服务 | 地址 | 默认账号 |
|------|------|---------|
| **Web UI** | http://localhost | - |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3001 | admin / `GRAFANA_PASSWORD` |

---

## 故障排查

### 数据库连接失败

```bash
# 检查 PostgreSQL 日志
docker-compose logs postgres

# 进入 PostgreSQL
docker-compose exec postgres psql -U litekb -d litekb
```

### Redis 连接失败

```bash
# 检查 Redis 日志
docker-compose logs redis

# 测试 Redis
docker-compose exec redis redis-cli -a $REDIS_PASSWORD ping
```

### Qdrant 问题

```bash
# 检查 Qdrant 状态
curl http://localhost:6333/dashboard
```

---

## 数据备份

```bash
# 备份 PostgreSQL
docker-compose exec postgres pg_dump -U litekb litekb > backup_$(date +%Y%m%d).sql

# 备份 Qdrant
docker-compose exec qdrant qdrant-cli backup --collection litekb_chunks ./backups
```

---

## 更新升级

```bash
# 拉取最新镜像
docker-compose -f docker-compose.prod.yml pull

# 重启服务
docker-compose -f docker-compose.prod.yml up -d

# 清理旧镜像
docker image prune -a
```
