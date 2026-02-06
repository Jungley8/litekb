# ==================== Secrets 配置 ====================

# 创建 secrets 目录
mkdir -p secrets ssl

# 生成安全密码
openssl rand -base64 32 > secrets/postgres_password.txt
openssl rand -base64 32 > secrets/jwt_secret.txt

# 生成 SSL 证书 (自签名，开发用)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem -out ssl/cert.pem \
  -subj "/CN=localhost"

# ==================== 部署步骤 ====================

# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 填写真实值

# 2. 创建 secrets
mkdir -p secrets ssl
# 生成或放置 SSL 证书到 ssl/ 目录

# 3. 构建并启动
docker-compose -f docker-compose.prod.yml up -d --build

# 4. 检查状态
docker-compose -f docker-compose.prod.yml ps

# 5. 运行数据库迁移
docker-compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head

# 6. 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# ==================== 监控访问 ====================

# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/密码在 .env 中)
