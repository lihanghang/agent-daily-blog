# Content Collector - 社交内容收藏助手

自动收集社交媒体精彩内容，AI 整理后存入飞书文档。

## 特性

- 🚀 **支持多平台**：X/Twitter、微信公众号、即刻、Reddit、知乎、Bilibili、Hacker News
- 🎯 **微信公众号完美抓取**：基于 Scrapling，绕过微信反爬
- 🤖 **AI 整理**：自动摘要、关键词提取、分类
- 📝 **飞书集成**：自动存入飞书文档或多维表格
- 🔄 **去重机制**：避免重复收藏

## 平台支持

| 平台 | 抓取方式 | 状态 |
|------|---------|------|
| X/Twitter | x-tweet-fetcher | ✅ 完美支持 |
| 微信公众号 | Scrapling | ✅ 完美支持（绕过反爬）|
| 即刻 | defuddle | ✅ 支持 |
| Reddit | defuddle | ✅ 支持 |
| 知乎 | defuddle | ✅ 支持 |
| Bilibili | defuddle | ✅ 支持（标题/描述）|
| Hacker News | defuddle | ✅ 支持 |

## 使用方式

### 作为 OpenClaw Skill 使用

1. 将整个目录复制到 OpenClaw skills 目录：
   ```bash
   cp -r content-collector-skill ~/.openclaw/workspace/skills/content-collector
   ```

2. 重启 OpenClaw，skill 自动生效

### 命令行使用

```bash
# 平台检测
python3 scripts/extract_content.py "https://mp.weixin.qq.com/s/xxx"

# 微信公众号抓取（Scrapling）
python3 ~/.openclaw/workspace/skills/web-content-fetcher/scripts/fetch.py "https://mp.weixin.qq.com/s/xxx" 50000
```

## 依赖

### 必需

- Python 3.10+
- scrapling + html2text（微信公众号抓取）
- x-tweet-fetcher skill（Twitter 抓取）

### 安装

```bash
pip install scrapling html2text
scrapling install  # 安装浏览器依赖
```

## 配置

在飞书创建多维表格，字段配置：

| 字段名 | 类型 |
|--------|------|
| 标题 | 文本 |
| 分类 | 单选 |
| 来源 | 文本 |
| 原文链接 | 超链接 |
| 原文内容 | 文本 |
| 记录时间 | 创建时间 |

## 工作流程

```
用户发送链接
    ↓
平台检测 (extract_content.py)
    ↓
内容抓取 (Scrapling/x-tweet-fetcher)
    ↓
AI 整理（摘要、关键词、分类）
    ↓
存入飞书多维表格
```

## 更新日志

### v1.3.0 (2026-03-17)
- 🎉 **微信公众号抓取能力升级**：改用 Scrapling 方案，完美绕过微信反爬
- 🔧 更新平台映射：微信公众号首选 web-content-fetcher skill

### v1.2.0 (2026-03-14)
- 🔧 移除所有硬编码路径，适配多环境部署
- 🔧 重写 extract_content.py 为平台检测 + skill 路由模式

### v1.1.0 (2026-03-14)
- ✅ 添加去重机制（本地缓存 + 文档检查）
- ✅ 支持更多平台

### v1.0.0 (2026-03-14)
- 初始版本

## 作者

vigor - [懂点儿AI](https://mp.weixin.qq.com/s/hw4uKk-9ezaJlDpL1nEUuA)

## License

MIT