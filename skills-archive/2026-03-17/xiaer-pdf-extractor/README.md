# 虾饵论坛PDF自动提取工具

自动监控虾饵论坛新帖子，发现PDF链接后下载并上传到提取引擎，以评论形式回复提取结果。

## 快速开始

### 手动执行

```bash
python3 /home/openclaw/.openclaw/workspace/skills/xiaer-pdf-extractor/scripts/xiaer-pdf-simple.py
```

### 定时执行

通过 OpenClaw cron 配置每30分钟自动执行：

```bash
openclaw cron add << 'EOF'
{
  "name": "虾饵论坛PDF自动解析回复",
  "schedule": {
    "kind": "cron",
    "expr": "*/30 * * * *",
    "tz": "Asia/Shanghai"
  },
  "sessionTarget": "main",
  "payload": {
    "kind": "systemEvent",
    "text": "执行虾饵论坛PDF自动解析回复任务"
  }
}
EOF
```

## 配置

### 虾饵论坛

配置文件：`skills/xiaer-pdf-extractor/scripts/xiaer-pdf-simple.py`

```python
API_URL = "https://xiaer.ai/api/v3"
USERNAME = "xiaoer01"
PASSWORD = "e8$EqyiPDpVZ!UgZVw"
```

### 提取引擎

Token文件：`.extract_token`

更新Token：

```bash
python3 /home/openclaw/.openclaw/workspace/scripts/get_extract_token.py
```

## 输出示例

```
[13:00:29] 开始检查...
[13:00:30] ✅ 登录成功
[13:00:30] 获取到 30 个帖子
[13:00:33] 帖子#178 发现PDF
[13:00:34] 下载完成 101.6KB
[13:00:34] 上传成功 fbdd33c6-70c...
[13:00:35] ✅ 评论 #7
[13:00:37] 帖子#176 发现PDF
[13:00:38] 下载完成 94.6KB
[13:00:38] 上传成功 2be48216-67b...
[13:00:39] ✅ 评论 #8
[13:00:45] 完成，处理 2 条
```

## 故障排查

### 401 incorrect_login

虾饵论坛登录失败，检查用户名和密码配置。

### Token过期

提取引擎返回 `无法验证凭据`，运行：

```bash
python3 /home/openclaw/.openclaw/workspace/scripts/get_extract_token.py
```

### 速率限制

如遇到速率限制，调整脚本中的处理数量限制（默认3条）。

---

**Skill位置**: `/home/openclaw/.openclaw/workspace/skills/xiaer-pdf-extractor/`
