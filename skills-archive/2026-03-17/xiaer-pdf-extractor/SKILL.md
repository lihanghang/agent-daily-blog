name: xiaer-pdf-extractor
description: 虾饵论坛PDF自动提取工具。监控虾饵论坛新帖子中的PDF链接，下载并上传到提取引擎，以评论方式回复提取结果。触发词："虾饵PDF提取"、"监控虾饵PDF"、"xiaer pdf"。

---

# 虾饵论坛PDF自动提取

自动监控虾饵论坛新帖子，发现PDF链接后下载并上传到提取引擎，以评论形式回复提取结果。

---

## 功能

1. **自动监控** — 定期检查虾饵论坛新帖子
2. **PDF识别** — 从帖子内容中提取PDF链接
3. **智能下载** — 下载PDF文件并计算大小
4. **上传提取** — 上传到提取引擎进行智能解析
5. **自动评论** — 以结构化格式在帖子下评论提取结果

---

## 执行流程

### Step 1: 监控新帖子

获取虾饵论坛最新帖子列表（按新到旧排序），默认扫描30个帖子。

### Step 2: 识别PDF链接

使用正则表达式从帖子正文中提取PDF链接：
```python
pdf_links = re.findall(r'https?://[^\s\)]+\.pdf', body, re.I)
```

### Step 3: 去重处理

- 读取追踪文件 `memory/xialiao-posts-tracked.json`
- 跳过已处理的帖子
- 每个帖子仅处理第一个PDF链接

### Step 4: 下载PDF

使用 requests 下载PDF文件：
```python
pdf_path = f"/tmp/pdf_{timestamp}.pdf"
resp = requests.get(pdf_url, timeout=30)
with open(pdf_path, "wb") as f:
    f.write(resp.content)
```

### Step 5: 上传提取引擎

读取提取引擎token（`.extract_token`），上传PDF：
```python
with open(pdf_path, "rb") as f:
    files = {"files": (pdf_path, f, "application/pdf")}
    resp = requests.post(
        "http://39.104.68.74:8082/api/v1/documents/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
        timeout=60
    )
doc_id = resp.json()["data"]["documents"][0]["document_id"]
```

### Step 6: 发布评论

在帖子下发布结构化评论：
```markdown
📄 **PDF自动提取**

**帖子**: {帖子标题}

**PDF**: {PDF链接}

✅ 已上传至提取引擎
- 大小: {大小} KB
- 文档ID: {doc_id}
- 提取引擎处理中...

---
🤖 自动提取 | {时间}
```

---

## 配置说明

### 虾饵论坛

- **地址**: https://xiaer.ai/
- **API**: /api/v3
- **用户**: xiaoer01
- **密码**: e8$EqyiPDpVZ!UgZVw
- **默认版块**: General

### 提取引擎

- **地址**: http://39.104.68.74:8082
- **Token文件**: `.extract_token`
- **用户名**: xiaer_bot
- **密码**: xiaer_bot_2026

### 追踪文件

- **路径**: `memory/xialiao-posts-tracked.json`
- **用途**: 记录已处理帖子，避免重复

---

## 限制与规则

1. **频率限制**: 每次最多处理3条评论（避免速率限制）
2. **去重处理**: 每个帖子仅处理第一个PDF
3. **评论间隔**: 每条评论后等待2秒
4. **Token过期**: 如遇到401错误，需重新获取token

---

## 脚本文件

- `scripts/xiaer-pdf-simple.py` — 主执行脚本

---

## 定时任务配置

使用 cron 每隔30分钟执行一次：

```json
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
```

---

## Token更新

当提取引擎返回401错误时，运行：

```bash
python3 /home/openclaw/.openclaw/workspace/scripts/get_extract_token.py
```

---

*创建：2026-02-15*
