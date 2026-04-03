#!/bin/bash
# OpenAge VPS 部署脚本（Debian 12，已有 Nginx）
# 用法：bash deploy.sh your_anthropic_api_key

set -e
API_KEY=${1:?"用法: bash deploy.sh <ANTHROPIC_API_KEY>"}
DEPLOY_DIR=/opt/openage

echo "=== 1. 安装系统依赖 ==="
apt-get update -q
apt-get install -y python3 python3-venv python3-pip git

echo "=== 2. 复制项目文件 ==="
mkdir -p $DEPLOY_DIR
rsync -av --exclude='.git' --exclude='nhanes_data' --exclude='__pycache__' \
  --exclude='*.pyc' --exclude='.venv' \
  ./ $DEPLOY_DIR/

echo "=== 3. 创建虚拟环境并安装依赖 ==="
cd $DEPLOY_DIR
python3 -m venv venv
venv/bin/pip install --upgrade pip -q
venv/bin/pip install fastapi uvicorn python-multipart anthropic -q
venv/bin/pip install -e . -q

echo "=== 4. 配置 systemd 服务 ==="
sed "s|your_key_here|$API_KEY|g" deploy/openage.service > /etc/systemd/system/openage.service
systemctl daemon-reload
systemctl enable openage
systemctl restart openage
sleep 2
systemctl status openage --no-pager

echo "=== 5. 配置 Nginx ==="
cp deploy/nginx.conf /etc/nginx/sites-available/openage
ln -sf /etc/nginx/sites-available/openage /etc/nginx/sites-enabled/openage
# 移除默认站点（如果存在）
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo ""
echo "=== 部署完成 ==="
echo "访问地址：http://$(curl -s ifconfig.me)"
