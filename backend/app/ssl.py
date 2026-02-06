"""
Let's Encrypt SSL 自动配置
"""
import os
import subprocess
import time
from pathlib import Path


class SSLCertificateManager:
    """SSL 证书管理"""
    
    def __init__(self, domain: str, email: str, webroot: str = "/var/www/letsencrypt"):
        self.domain = domain
        self.email = email
        self.webroot = webroot
        self.cert_path = Path(f"/etc/letsencrypt/live/{domain}")
        self.nginx_template = """
server {{
    listen 80;
    server_name {domain};
    
    location /.well-known/acme-challenge/ {{
        root {webroot};
    }}
    
    location / {{
        return 301 https://$server_name$request_uri;
    }}
}}

server {{
    listen 443 ssl http2;
    server_name {domain};
    
    ssl_certificate {cert_path}/fullchain.pem;
    ssl_certificate_key {cert_path}/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    # ... 其他配置
}}
"""
    
    def request_certificate(self) -> bool:
        """请求 SSL 证书"""
        # 创建 webroot
        Path(self.webroot).mkdir(parents=True, exist_ok=True)
        
        cmd = [
            "certbot", "certonly",
            "--webroot",
            "--webroot-path", self.webroot,
            "--domain", self.domain,
            "--email", self.email,
            "--agree-tos",
            "--non-interactive",
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            print(f"Certificate obtained for {self.domain}")
            return True
        else:
            print(f"Failed: {result.stderr.decode()}")
            return False
    
    def renew_certificate(self) -> bool:
        """续期证书"""
        cmd = ["certbot", "renew", "--quiet"]
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            print(f"Certificate renewed for {self.domain}")
            return True
        return False
    
    def generate_nginx_config(self) -> str:
        """生成 Nginx 配置"""
        return self.nginx_template.format(
            domain=self.domain,
            webroot=self.webroot,
            cert_path=self.cert_path
        )
    
    def setup_renewal_hook(self):
        """设置自动续期"""
        renewal_hook = "/etc/letsencrypt/renewal-hooks/post/renewal-nginx.sh"
        
        Path(renewal_hook).write_text("""#!/bin/bash
systemctl reload nginx
""")
        os.chmod(renewal_hook, 0o755)


# Certbot Docker 命令
DOCKER_CERTBOT_CMD = """
docker run -it --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/www/letsencrypt:/var/www/letsencrypt \
  certbot/certbot \
  certonly --webroot --domain YOUR_DOMAIN --email YOUR_EMAIL --agree-tos --non-interactive
"""

# 添加到 crontab
CRON_JOB = "0 0,12 * * * docker exec nginx certbot renew --quiet"
