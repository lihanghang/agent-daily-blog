# AI 日报自动化系统

## 概述

这是一个自动化的 AI 日报采集和发布系统，包括：

1. **AI日报采集** (v4): 从多个数据源采集AI相关文章，自动过滤非AI内容
2. **AI数据源发现**: 每天自动全网搜索新的AI相关网站和文章
3. **定时任务**: 通过 cron 自动执行

## 脚本说明

### ai-daily-aggregator-v4.py

修复版的 AI 日报采集脚本，主要改进：

- 使用正则表达式按 item 块匹配 RSS，避免字段错位
- 改进 HTML 解析，过滤导航和非文章链接
- 加强 AI 关键词过滤和内容质量评分
- 自动分类：大模型、AI Agent、AI编程、开源工具、前沿探索、AI伦理、AI就业影响

**数据源**:
- Hacker News Frontpage/Best/AI (RSS)
- 宝玉的分享 (RSS)
- OpenAI Blog (HTML)
- The Gradient (HTML)

**输出**: `workspace/ai-daily-report-YYYY-MM-DD.md`

### discover-new-sources-v2.py

全网搜索新数据源脚本，使用 OpenClaw web_search 工具。

**搜索关键词**:
- AI research blog 2026
- machine learning news today
- artificial intelligence weekly
- LLM model updates
- AI agent tools 2026
- open source AI projects
- AI engineering blog
- deep learning research

**输出**:
- `memory/ai-daily-new-sources.json`: 发现的新数据源记录
- `memory/ai-daily-search-log.json`: 搜索日志
- `workspace/ai-daily-sources-report.md`: 数据源报告

## 使用方法

### 手动运行

```bash
# 采集 AI 日报
python3 skills/ai-daily-aggregator/scripts/ai-daily-aggregator-v4.py

# 发现新数据源
python3 skills/ai-daily-aggregator/scripts/discover-new-sources-v2.py
```

### 自动运行

已设置 cron 任务：

- **AI日报采集**: 每天凌晨2:00 (Asia/Shanghai)
- **AI数据源发现**: 每天凌晨3:00 (Asia/Shanghai)

## 扩展数据源

要添加新的数据源，编辑 `ai-daily-aggregator-v4.py` 中的 `SOURCES` 配置：

```python
SOURCES = {
    "Your Source Name": {
        "url": "https://example.com/feed.xml",
        "type": "rss",  # 或 "html"
        "priority": 10,
        # 如果是 HTML，可以指定选择器
        "article_selector": "article.post"
    },
}
```

## 扩展分类

要添加新的分类或调整关键词，编辑 `AI_KEYWORDS` 配置：

```python
AI_KEYWORDS = {
    "新分类名称": {
        "keywords": ["keyword1", "keyword2", ...],
        "weight": 1.5  # 权重，越高越容易匹配
    },
}
```

## 发布到社区

AI 日报生成后，可以考虑发布到：

1. **虾聊社区**: 使用 message tool 或直接调用 API
2. **虾饵论坛**: 使用 `publish_ai_daily.py` 脚本

## 查看历史

- **日报记录**: `workspace/ai-daily-report-*.md`
- **数据源记录**: `memory/ai-daily-new-sources.json`
- **搜索日志**: `memory/ai-daily-search-log.json`

## 故障排查

### RSS 解析失败

如果某个 RSS 源无法解析，可能是：
- RSS 格式不标准
- 需要添加 User-Agent
- 反爬限制

### HTML 解析获取0条

如果 HTML 源无法获取文章，可能是：
- 反爬限制（返回 403）
- 选择器不匹配
- 网站结构改变

建议：
- 优先使用 RSS 源
- 对于 HTML 源，添加 User-Agent 头
- 调整 article_selector

### 分类不准确

如果文章分类不准确：
- 调整 `AI_KEYWORDS` 中的关键词
- 调整权重
- 添加更多分类

## 维护建议

1. **每周审查新数据源**: 查看发现的网站，将高质量的添加到 SOURCES
2. **每月调整关键词**: 根据实际分类效果调整 AI_KEYWORDS
3. **监控数据源质量**: 如果某个源持续返回低质量内容，考虑降低优先级或移除
4. **备份历史数据**: 定期备份 memory/ 目录

## 性能优化

- 减少采集数量: 调整 count 参数
- 并行采集: 使用多线程/协程
- 缓存结果: 避免重复采集相同内容

## 未来改进

- 使用 LLM 生成更好的文章总结
- 自动将新数据源添加到 SOURCES
- 支持更多数据源格式 (Atom, JSON Feed)
- 添加文章去重（基于内容相似度）
- 支持多语言
