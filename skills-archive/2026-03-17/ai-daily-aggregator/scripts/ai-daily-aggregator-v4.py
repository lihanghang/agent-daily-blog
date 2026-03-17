#!/usr/bin/env python3
"""
AI日报采集脚本 v5 - 人类可读版
从Hacker News RSS和其他数据源采集最新AI文章，生成适合人类阅读的日报

改进点：
1. 抓取文章正文并生成摘要
2. 优化格式，增强可读性
3. 每篇文章包含：标题、摘要、原文链接、发布时间
4. 智能摘要生成（首段/关键句提取）
5. 集成微信推送
"""

import requests
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
import sys
import os
from dateutil import parser as date_parser
import time

# 添加 scripts 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', 'scripts'))

# 尝试导入微信推送模块
WX_PUSH_AVAILABLE = False
try:
    from wxpush import push_wechat
    WX_PUSH_AVAILABLE = True
    print("✅ 微信推送模块已加载")
except ImportError:
    print("⚠️  微信推送模块不可用")

# 配置
SOURCES = {
    # RSS数据源（高优先级）
    "Hacker News Frontpage": {
        "url": "https://hnrss.org/frontpage?count=50",
        "type": "rss",
        "priority": 1
    },
    "Hacker News Best": {
        "url": "https://hnrss.org/best?count=30",
        "type": "rss",
        "priority": 2
    },
    "Hacker News AI": {
        "url": "https://hnrss.org/frontpage?q=AI&count=30",
        "type": "rss",
        "priority": 3
    },

    # 个人博客（高质量）
    "宝玉的分享": {
        "url": "https://baoyu.io/feed.xml",
        "type": "rss",
        "priority": 4
    },

    # AI 官方博客
    "OpenAI Blog": {
        "url": "https://openai.com/blog",
        "type": "html",
        "priority": 5,
        "article_selector": "article.post"
    },
    "The Gradient": {
        "url": "https://thegradient.pub/",
        "type": "html",
        "priority": 6,
        "article_selector": "article"
    },
}

# AI 相关关键词（带权重）
AI_KEYWORDS = {
    "大模型 (LLM)": {
        "keywords": ["GPT", "Claude", "LLM", "large language model", "language model",
                     "fine-tuning", "training", "inference", "token", "transformer"],
        "weight": 2.0
    },
    "AI Agent": {
        "keywords": ["agent", "autonomous", "workflow", "multi-agent", "AI agent",
                     "autonomous agent", "tool use", "function calling"],
        "weight": 2.0
    },
    "AI编程与工程": {
        "keywords": ["Copilot", "Cursor", "AI code", "coding assistant", "program synthesis",
                     "code generation", "AI engineering", "LLM engineering"],
        "weight": 1.8
    },
    "开源工具": {
        "keywords": ["open source", "GitHub", "Hugging Face", "PyTorch", "TensorFlow",
                     "LangChain", "vector database", "embedding"],
        "weight": 1.5
    },
    "前沿探索": {
        "keywords": ["research", "paper", "breakthrough", "novel", "experimental",
                     "arXiv", "scientific", "study", "discovery"],
        "weight": 1.8
    },
    "AI伦理与隐私": {
        "keywords": ["privacy", "ethics", "bias", "safety", "alignment",
                     "surveillance", "regulation", "responsible AI"],
        "weight": 1.5
    },
    "AI就业影响": {
        "keywords": ["job", "career", "automation", "work", "hiring",
                     "employment", "future of work", "productivity"],
        "weight": 1.3
    },
}

# 非AI关键词（需要过滤）
NON_AI_KEYWORDS = [
    "YouTube as", "music", "video game", "game review",
    "politics", "election", "government",
    "sports", "football", "basketball", "baseball",
    "entertainment", "movie", "film", "celebrity",
    "crypto", "cryptocurrency", "Bitcoin", "NFT",
    "stock market", "trading", "investment",
    "cooking", "recipe", "food",
    "travel", "vacation", "hotel",
]

# 需要跳过的URL模式
SKIP_URL_PATTERNS = [
    '/course', '/app', '/live', '/events', '/following', '/pins',
    '/signup', '/login', '/contact', '/about',
    '/author/', '/category/', '/tag/', '/page/',
    '/comment', '/trackback',
]

OUTPUT_DIR = Path("/home/openclaw/.openclaw/workspace")
REPORT_FILE = OUTPUT_DIR / "ai-daily-report-{date}.md"


def fetch_article_content(url):
    """抓取文章内容并生成摘要"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; OpenClaw-AI-Aggregator/1.0)'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None

        html = resp.text

        # 移除 script、style 等标签
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<header[^>]*>.*?</header>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<aside[^>]*>.*?</aside>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # 尝试找到主要内容区域
        content = None

        # 尝试常见的文章容器
        patterns = [
            r'<article[^>]*>(.*?)</article>',
            r'<div[^>]*role="article"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*post-content[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*entry-content[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*article-content[^"]*"[^>]*>(.*?)</div>',
            r'<main[^>]*>(.*?)</main>',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, flags=re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1)
                break

        # 如果没找到，使用 body
        if not content:
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html, flags=re.DOTALL | re.IGNORECASE)
            if body_match:
                content = body_match.group(1)
            else:
                content = html

        # 移除所有HTML标签
        text = re.sub(r'<[^>]+>', ' ', content)

        # 清理文本
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        # 生成摘要（取前300字）
        if len(text) > 300:
            summary = text[:300] + "..."
        else:
            summary = text

        return summary

    except Exception as e:
        print(f"  ⚠️  抓取内容失败: {e}")
        return None


def generate_intelligent_summary(article):
    """智能生成文章摘要"""
    title = article.get('title', '')
    link = article.get('link', '')

    # 尝试抓取正文摘要
    print(f"    抓取摘要: {title[:50]}...")
    content = fetch_article_content(link)

    if content:
        article['summary'] = content
    else:
        # 如果抓取失败，使用标题作为摘要
        article['summary'] = title

    # 短暂延迟，避免请求过快
    time.sleep(0.5)

    return article


def fetch_rss(url):
    """获取并解析 RSS 内容"""
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            print(f"  HTTP {resp.status_code}")
            return []
        return parse_rss_xml(resp.text)
    except Exception as e:
        print(f"  错误: {e}")
        return []


def parse_rss_xml(xml_content):
    """使用正则表达式解析 RSS XML - 改进版，按 item 块匹配"""
    items = []

    try:
        # 先移除CDATA标记，方便解析
        xml_content = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', xml_content, flags=re.DOTALL)

        # 按 item 块分割
        item_pattern = r'<item>(.*?)</item>'
        item_blocks = re.findall(item_pattern, xml_content, re.DOTALL)

        for block in item_blocks:
            # 在每个 item 块中提取字段
            title_match = re.search(r'<title>(.*?)</title>', block, re.DOTALL)
            link_match = re.search(r'<link>(.*?)</link>', block, re.DOTALL)
            date_match = re.search(r'<pubDate>(.*?)</pubDate>', block, re.DOTALL)

            if title_match and link_match:
                title = title_match.group(1).strip()
                link = link_match.group(1).strip()
                pub_date = date_match.group(1).strip() if date_match else datetime.now().isoformat()

                # 清理HTML标签
                title = re.sub(r'<[^>]+>', '', title).strip()

                if title and link:
                    items.append({
                        "title": title,
                        "link": link,
                        "pubDate": pub_date
                    })

    except Exception as e:
        print(f"  RSS解析错误: {e}")

    return items


def fetch_html(url, article_selector="article"):
    """获取并解析 HTML 内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; OpenClaw-AI-Aggregator/1.0)'
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"  HTTP {resp.status_code}")
            return []
        return parse_html_articles(resp.text, url, article_selector)
    except Exception as e:
        print(f"  错误: {e}")
        return []


def parse_html_articles(html_content, base_url, article_selector):
    """解析 HTML 中的文章链接"""
    items = []
    seen_urls = set()

    # 提取所有链接
    link_pattern = r'<a\s+[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
    matches = re.findall(link_pattern, html_content, re.IGNORECASE)

    for link, title in matches[:50]:  # 限制前50条
        try:
            # 清理链接
            link = re.sub(r'&amp;', '&', link)

            # 跳过无效链接
            if not link or link.startswith('#') or link.startswith('javascript:'):
                continue

            # 跳过非文章链接
            skip = False
            for pattern in SKIP_URL_PATTERNS:
                if pattern in link.lower():
                    skip = True
                    break
            if skip:
                continue

            # 转换为绝对URL
            if not link.startswith('http'):
                if link.startswith('/'):
                    link = urljoin(base_url, link)
                else:
                    parsed = urlparse(base_url)
                    link = f"{parsed.scheme}://{parsed.netloc}/{link.lstrip('/')}"

            # 去重
            if link in seen_urls:
                continue
            seen_urls.add(link)

            # 清理标题
            title = re.sub(r'\s+', ' ', title).strip()

            if title and len(title) > 10:  # 过滤太短的标题
                items.append({
                    "title": title,
                    "link": link,
                    "pubDate": datetime.now().isoformat()
                })

        except Exception:
            continue

    return items


def parse_pub_date(pub_date_str):
    """解析发布日期字符串，返回datetime对象（无时区）"""
    try:
        # 使用 dateutil 解析日期
        dt = date_parser.parse(pub_date_str)

        # 如果有时区，转换为无时区的时间
        if dt.tzinfo:
            # 转换为当前时区
            dt = dt.astimezone().replace(tzinfo=None)

        return dt
    except Exception as e:
        # 尝试手动解析常见的日期格式
        try:
            # 尝试 RFC 2822 格式 (如: Tue, 17 Feb 2026 17:48:52 +0000)
            dt = datetime.strptime(pub_date_str[:25], '%a, %d %b %Y %H:%M:%S')
            return dt
        except:
            pass

        return None


def is_today_article(pub_date_str):
    """检查文章是否是今天发布的（UTC+8时区）"""
    pub_dt = parse_pub_date(pub_date_str)
    if not pub_dt:
        return False

    # 获取今天的日期（UTC+8）
    now = datetime.now()
    today = now.date()

    # 检查日期是否相同
    return pub_dt.date() == today


def calculate_ai_score(title, content=""):
    """计算文章的 AI 相关性得分"""
    text = (title + " " + content).lower()
    score = 0.0
    matched_categories = []

    # 检查非AI关键词
    for keyword in NON_AI_KEYWORDS:
        if keyword.lower() in text:
            return 0, matched_categories

    # 检查AI关键词
    for category, config in AI_KEYWORDS.items():
        for keyword in config["keywords"]:
            if keyword.lower() in text:
                score += config["weight"]
                if category not in matched_categories:
                    matched_categories.append(category)

    return score, matched_categories


def classify_article(title, content=""):
    """根据标题和内容分类文章"""
    score, categories = calculate_ai_score(title, content)

    # 过滤非AI文章
    if score < 0.5:
        return None

    # 返回得分最高的分类
    if categories:
        return categories[0]

    return "其他"


def format_article_block(article):
    """格式化文章为易读的块"""
    title = article.get('title', '')
    link = article.get('link', '')
    summary = article.get('summary', '')
    pub_date = article.get('pubDate', '')

    # 解析日期为更友好的格式
    try:
        dt = parse_pub_date(pub_date)
        if dt:
            date_str = dt.strftime('%Y-%m-%d %H:%M')
        else:
            date_str = pub_date
    except:
        date_str = pub_date

    # 检查摘要是否有效
    if not summary or summary == title:
        summary = "*摘要抓取失败，请点击原文链接查看完整内容*"

    block = f"""**{title}**

{summary}

📅 发布时间：{date_str}
🔗 [原文链接]({link})

---

"""

    return block


def generate_daily_report():
    """生成AI日报"""
    print("=" * 60)
    print(f"AI日报采集任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 按优先级采集数据源
    all_articles = []
    for source_name, source_config in sorted(SOURCES.items(), key=lambda x: x[1]['priority']):
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 采集 {source_name} (优先级 {source_config['priority']})...")

        if source_config['type'] == 'rss':
            articles = fetch_rss(source_config['url'])
        else:
            selector = source_config.get('article_selector', 'article')
            articles = fetch_html(source_config['url'], selector)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] 获取到 {len(articles)} 篇")

        # 过滤非AI内容 + 只保留当天发布的文章
        filtered = []
        for article in articles:
            # 检查是否是今天发布的
            if not is_today_article(article.get('pubDate', '')):
                continue

            category = classify_article(article['title'])
            if category:
                article['category'] = category
                filtered.append(article)

        if len(filtered) < len(articles):
            print(f"  过滤后（当天AI文章）: {len(filtered)} 篇")

        all_articles.extend(filtered)

    # 去重（基于链接）
    seen_links = set()
    unique_articles = []
    for article in all_articles:
        if article["link"] not in seen_links:
            seen_links.add(article["link"])
            unique_articles.append(article)

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 去重后共 {len(unique_articles)} 篇")

    # 分类
    categories = {}
    for article in unique_articles:
        cat = article.get('category', '其他')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(article)

    # 抓取文章摘要
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 开始抓取文章摘要...")
    for cat in categories:
        for i, article in enumerate(categories[cat]):
            print(f"  [{cat}] {i+1}/{len(categories[cat])}")
            generate_intelligent_summary(article)

    # 生成Markdown报告
    today = datetime.now()
    report = f"""# AI 日报 — {today.strftime('%Y年%m月%d日')}

> 从全网采集今日最新 AI 动态，为每篇文章提供摘要，方便快速阅读

---

## 采集统计

- **总文章数**: {len(unique_articles)} 篇
- **数据源**: {len(SOURCES)} 个
- **分类数**: {len(categories)} 个

---

"""

    # 按分类输出
    category_order = [
        "大模型 (LLM)", "AI Agent", "AI编程与工程", "开源工具",
        "前沿探索", "AI伦理与隐私", "AI就业影响", "其他"
    ]

    for category in category_order:
        if category not in categories:
            continue

        articles = categories[category][:10]  # 每分类最多10篇
        if not articles:
            continue

        report += f"## {category}\n\n"

        for i, article in enumerate(articles, 1):
            report += format_article_block(article)

    # 汇总洞察
    report += f"""## 📊 今日要点

**采集范围：** 仅包含今日（{today.strftime('%Y年%m月%d日')}）发布的AI相关文章

**热门分类：**
- 文章最多的分类: {max(categories, key=lambda k: len(categories[k]), default='无')}
- 最活跃的数据源: Hacker News

**核心动态：**
"""

    # 添加每分类最热门的文章（第一篇）
    priority_categories = ["大模型 (LLM)", "AI Agent", "开源工具", "前沿探索", "AI编程与工程"]
    for category in priority_categories:
        if category in categories and categories[category]:
            article = categories[category][0]
            report += f"- **{category}**：{article['title'][:60]}...\n"

    report += f"""

---

**采集时间：** {today.strftime('%Y-%m-%d %H:%M')}
**数据来源：** Hacker News RSS、宝玉的分享、OpenAI Blog、The Gradient
**整理：** 虾说 (Xiashuo)

---

> 💡 **提示**：点击"原文链接"可阅读完整文章。本日报由 AI 自动采集并生成摘要，如有偏差请以原文为准。
"""

    # 保存报告
    date_str = today.strftime('%Y-%m-%d')
    report_file = OUTPUT_DIR / f"ai-daily-report-{date_str}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ✅ 报告已保存: {report_file}")
    print(f"\n{'=' * 60}")
    print("✅ 采集完成！")
    print(f"{'=' * 60}")
    print(f"\n报告文件: {report_file}")

    # 推送到微信
    if WX_PUSH_AVAILABLE:
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📱 正在推送到微信...")
            # 推送摘要
            content = f"""📊 AI日报 - {today.strftime('%Y-%m-%d')}

采集统计：
- 总文章数：{len(unique_articles)} 篇
- 数据源：{len(SOURCES)} 个
- 分类数：{len(categories)} 个

"""
            # 添加各分类的首篇（最热门）
            priority_categories = ["大模型 (LLM)", "AI Agent", "开源工具", "前沿探索", "AI编程与工程", "AI就业影响"]
            for category in priority_categories:
                if category not in categories:
                    continue

                articles = categories[category][:1]  # 只取第一篇
                if not articles:
                    continue

                article = articles[0]
                content += f"\n## {category}\n\n"
                content += f"**{article['title']}**\n\n"
                content += f"{article.get('summary', '')[:150]}...\n\n"
                content += f"🔗 {article['link']}\n"

            content += f"\n---\n\n完整报告：{report_file}\n采集时间：{today.strftime('%Y-%m-%d %H:%M')}"

            if push_wechat("AI日报", content):
                print(f"✅ 微信推送成功")
            else:
                print(f"❌ 微信推送失败")
        except Exception as e:
            print(f"❌ 微信推送异常: {e}")

    return report, str(report_file)


if __name__ == "__main__":
    try:
        generate_daily_report()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
