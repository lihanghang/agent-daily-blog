#!/bin/bash
# 公告推送 Webhook 服务快速启动脚本

cd ~/.openclaw/workspace/skills/announcement-subscription

echo "🚀 启动公告推送 Webhook 服务..."
echo ""

# 检查端口是否被占用
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口 5000 已被占用，尝试停止现有进程..."
    pkill -f webhook_server_simple.py
    sleep 1
fi

# 启动服务
python3 webhook_server_simple.py
