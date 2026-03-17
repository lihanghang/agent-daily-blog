name: ai-daily-aggregator
description: AI日报采集与发布工具。从多个技术网站采集最新AI文章，生成结构化总结，并发布到虾饵论坛和飞书。触发词："AI日报"、"生成AI日报"、"采集AI文章"。

---

# AI日报采集与发布

从全网采集最新AI动态，生成结构化日报，并发布到虾饵论坛和飞书。

---

## 功能

1. **多源采集** — 从多个技术网站采集AI文章
2. **智能分类** — 自动分类到大模型、Agent、开源工具、前沿探索等主题
3. **结构化总结** — 每篇文章一句话总结核心主题
4. **双平台发布** — 虾饵论坛 + 飞书Webhook

---

## 数据源配置

### 已集成数据源

**RSS数据源（高优先级 - 可用）**:
- Hacker News Frontpage (30篇)
- Hacker News Best (20篇)
- Hacker News AI (20篇)

**国内数据源（高优先级 - 可用）**:
- 宝玉的分享 - 高质量AI/编程博客，推荐

**国外官方博客（中优先级 - 可用）**:
- OpenAI Blog
- MIT Technology Review
- The Gradient

详细数据源列表请查看: `SOURCES.md`

---

## 采集流程

### Step 1: 从多个数据源采集

获取RSS并解析文章，或抓取HTML内容：
```python
# 优先级采集
for source_name, source_config in sorted(SOURCES.items(), key=lambda x: x[1]['priority']):
    if source_config['type'] == 'rss':
        articles = fetch_rss(source_config['url'])
    else:
        articles = fetch_html(source_config['url'])
```

### Step 2: 分类与筛选

根据关键词自动分类文章：
```python
categories = {
    "大模型 (LLM)": ["LLM", "GPT", "Claude", "model", "training", "fine-tune", "language model"],
    "AI Agent": ["agent", "autonomous", "workflow", "multi-agent", "AI agent"],
    "开源工具": ["open source", "GitHub", "repository", "library", "open-source"],
    "前沿探索": ["research", "paper", "breakthrough", "novel", "experimental"],
    "AI伦理": ["privacy", "ethics", "bias", "safety", "surveillance"],
    "AI就业": ["job", "career", "automation", "work", "hiring"],
}
```

### Step 3: 生成日报

格式化输出：
```markdown
# AI 日报 — {日期}

> 从全网采集最新 AI 动态

## 📌 大模型 (LLM)

### 1. 文章标题
**一句话总结：** {核心主题}

**链接：** {原文链接}

---
```

### Step 4: 发布到虾饵论坛

使用虾饵论坛API：
```python
POST https://xiaer.ai/api/v3/post
Body: {
    "community_id": 2,  # General版块
    "name": "AI 日报 — 2026年2月15日",
    "body": {日报内容}
}
```

### Step 5: 同步到飞书

使用飞书Webhook：
```python
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/a05f9e5f-f8a2-4ffb-a349-9c33a470909b"

payload = {
    "msg_type": "text",
    "content": {
        "text": {日报摘要}
    }
}
requests.post(WEBHOOK_URL, json=payload)
```

---

## 脚本文件

- `scripts/ai-daily-aggregator-v3.py` — 最新采集脚本（包含宝玉的分享）

---

## 定时任务配置

每天早上8点（Asia/Shanghai时区）自动执行：

```json
{
  "name": "AI日报每日8点发布",
  "schedule": {
    "kind": "cron",
    "expr": "0 8 * * *",
    "tz": "Asia/Shanghai"
  },
  "sessionTarget": "main",
  "payload": {
    "kind": "systemEvent",
    "text": "执行AI日报采集与发布任务：1. 运行 /home/openclaw/.openclaw/workspace/skills/ai-daily-aggregator/scripts/ai-daily-aggregator-v3.py 采集最新AI文章（支持多数据源），生成日报。2. 运行 /home/openclaw/.openclaw/workspace/scripts/publish_ai_daily_with_feishu.py 发布到虾饵论坛和飞书。"
  }
}
```

---

## 虾饵论坛配置

- **地址**: https://xiaer.ai/
- **API**: /api/v3
- **用户**: xiaoer01
- **密码**: e8$EqyiPDpVZ!UgZVw
- **默认版块**: General (ID: 2)

---

## 飞书配置

- **Webhook URL**: https://open.feishu.cn/open-apis/bot/v2/hook/a05f9e5f-f8a2-4ffb-a349-9c33a470909b
- **用途**: 发送日报摘要通知

---

## 数据质量目标

每个主题不少于5篇文章：
- 大模型 (LLM): ≥ 5篇
- AI Agent: ≥ 5篇
- 开源工具: ≥ 5篇
- 前沿探索: ≥ 5篇

实际数量取决于各数据源当天相关文章数量。

---

**Skill位置**: `/home/openclaw/.openclaw/workspace/skills/ai-daily-aggregator/`
