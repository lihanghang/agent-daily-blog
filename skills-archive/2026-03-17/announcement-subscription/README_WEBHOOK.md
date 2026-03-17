# 公告推送 Webhook 服务

## 功能

接收公告订阅 API 的推送，并进行以下处理：

1. **保存到文件** - 按日期保存到 `memory/announcements/announcements-YYYY-MM-DD.jsonl`
2. **记录到内存日志** - 自动记录到当天的 `memory/YYYY-MM-DD.md`
3. **统计分析** - 可以查看今天收到了多少条公告

## 快速开始

### 步骤 1：启动 webhook 服务

```bash
cd ~/.openclaw/workspace/skills/announcement-subscription
python3 webhook_server.py
```

服务将在 `http://localhost:5000` 启动。

### 步骤 2：安装 tunnel 工具

选择以下任一工具：

```bash
# 方案 A: 使用 tunnel (简单快速)
npm install -g tunnel

# 方案 B: 使用 ngrok (需要注册)
# 下载: https://ngrok.com/download

# 方案 C: 使用 localtunnel (免费，无需注册)
npm install -g localtunnel
```

### 步骤 3：暴露到公网

```bash
# 方案 A: 使用 tunnel
tunnel --port 5000

# 方案 B: 使用 ngrok
ngrok http 5000

# 方案 C: 使用 localtunnel
lt --port 5000
```

你会得到一个公网 URL，例如：
- `https://random-id.tunnel.dev`
- `https://random-id.ngrok.io`
- `https://random-id.loca.lt`

### 步骤 4：配置订阅

使用你的公网 URL 配置订阅：

```bash
# 创建新的 webhook 订阅
curl -X POST "http://39.104.68.74:8452/api/v1/subscriptions" \
  -H "X-API-Key: mk_6b06aedefda608f513dd02599ff04c56" \
  -H "Content-Type: application/json" \
  -d '{
    "sub_type": "category",
    "notify_method": "webhook",
    "notify_target": "https://your-url.tunnel.dev/webhook/announcement",
    "category_code": "O_临时公告_股票交易风险提示",
    "category_name": "股票交易风险提示"
  }'
```

## API 端点

### POST /webhook/announcement

接收公告推送。

**响应示例：**
```json
{
  "status": "success",
  "message": "公告已接收并处理",
  "received_at": "2026-03-05T15:50:00.000000"
}
```

### GET /webhook/health

健康检查。

```bash
curl http://localhost:5000/webhook/health
```

### GET /webhook/stats

统计今天收到的公告数量。

```bash
curl http://localhost:5000/webhook/stats
```

## 后台运行

### 使用 systemd（推荐）

```bash
sudo tee /etc/systemd/system/announcement-webhook.service > /dev/null <<EOF
[Unit]
Description=Announcement Webhook Server
After=network.target

[Service]
Type=simple
User=openclaw
WorkingDirectory=/home/openclaw/.openclaw/workspace/skills/announcement-subscription
ExecStart=/usr/bin/python3 /home/openclaw/.openclaw/workspace/skills/announcement-subscription/webhook_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable announcement-webhook
sudo systemctl start announcement-webhook
```

### 使用 nohup

```bash
cd ~/.openclaw/workspace/skills/announcement-subscription
nohup python3 webhook_server.py > webhook.log 2>&1 &

# 查看日志
tail -f webhook.log

# 停止服务
pkill -f webhook_server.py
```

## 数据存储

### JSONL 文件

存储位置：`memory/announcements/announcements-YYYY-MM-DD.jsonl`

### 内存日志

自动记录到：`memory/YYYY-MM-DD.md`

## 扩展功能

### 添加飞书推送

在 `process_announcement` 函数中添加你的飞书推送逻辑。

### 添加数据分析

创建一个分析脚本来统计公告数据。

## 故障排查

### 服务启动失败

**问题：** `Address already in use`

**解决：**
```bash
lsof -i :5000
kill -9 <PID>
```

### 公告推送未接收

**检查：**
1. tunnel URL 是否正确
2. 订阅配置是否正确
3. 查看 webhook 日志

## 相关文件

- `webhook_server.py` - Webhook 服务主程序
- `api_wrapper.py` - 订阅管理 API 包装脚本
- `SKILL.md` - 主要文档
- `README_WEBHOOK.md` - 本文档
