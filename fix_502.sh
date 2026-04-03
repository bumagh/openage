#!/bin/bash
# 修复 502 错误 - 更新 main.py 并重启服务

set -e

DEPLOY_DIR=/opt/openage

echo "=== 1. 备份当前文件 ==="
cp $DEPLOY_DIR/app/main.py $DEPLOY_DIR/app/main.py.backup.$(date +%Y%m%d_%H%M%S)

echo "=== 2. 上传修复后的文件 ==="
# 这一步需要你先把本地的 app/main.py 上传到服务器
# 使用 scp 或 rsync 命令

echo "=== 3. 重启服务 ==="
systemctl restart openage

echo "=== 4. 等待服务启动 ==="
sleep 3

echo "=== 5. 检查服务状态 ==="
systemctl status openage --no-pager || true

echo ""
echo "=== 6. 检查服务日志 ==="
journalctl -u openage -n 20 --no-pager

echo ""
echo "=== 7. 测试端口 ==="
curl -s http://127.0.0.1:8000/ > /dev/null && echo "✓ 服务正常运行" || echo "✗ 服务仍有问题"

echo ""
echo "=== 修复完成 ==="
