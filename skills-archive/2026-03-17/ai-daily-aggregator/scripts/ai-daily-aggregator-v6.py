#!/usr/bin/python3
"""
AI日报采集脚本 v6 - 实用技术版
专注于技术文章、Agent实现、开源工具、实际使用案例
"""

import requests
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
import sys
import os
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

# 配置 - 专注于实用技术内容
SOURCES = {
    # Hacker News Frontpage（最可靠）
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

    # 高质量技术博客
    "Anthropic Blog": {
        "url": "https://www.anthropic.com/blog",
        "type": "html",
        "priority": 3
    },
    "LangChain Blog": {
        "url": "https://blog.langchain.dev",
        "type": "html",
        "priority": 4
    },
    "Andrej Karpathy Blog": {
        "url": "https://karpathy.github.io",
        "type": "html",
        "priority": 5
    },
    "Lilian Weng Blog": {
        "url": "https://lilianweng.github.io",
        "type": "html",
        "priority": 6
    },

    # 国内技术分享
    "宝玉的分享": {
        "url": "https://baoyu.io/feed.xml",
        "type": "rss",
        "priority": 7
    },

    # The Gradient（高质量）
    "The Gradient": {
        "url": "https://thegradient.pub/",
        "type": "html",
        "priority": 8
    },
    "MIT Technology Review": {
        "url": "https://www.technologyreview.com/",
        "type": "html",
        "priority": 9
    },
}

# 优先关注的关键词（权重高）
PRIORITY_KEYWORDS = {
    "Agent实现与框架": {
        "keywords": ["agent", "autonomous", "workflow", "multi-agent", "AI agent",
                     "autonomous agent", "tool use", "function calling",
                     "LangChain", "AutoGPT", "BabyAGI", "CrewAI",
                     "agent framework", "agent implementation"],
        "weight": 3.0
    },
    "实际应用案例": {
        "keywords": ["example", "tutorial", "how to", "guide", "implementation",
                     "case study", "real-world", "practical", "production",
                     "build", "create", "deploy", "integrate"],
        "weight": 2.8
    },
    "开源工具": {
        "keywords": ["open source", "GitHub", "repository", "library", "toolkit",
                     "framework", "SDK", "Python package", "npm package",
                     "Hugging Face", "model zoo", "template", "starter"],
        "weight": 2.5
    },
    "技术文章": {
        "keywords": ["paper", "research", "technical", "architecture", "design",
                     "best practice", "pattern", "optimization", "technique"],
        "weight": 2.5
    },
    "API与集成": {
        "keywords": ["API", "integration", "SDK", "client", "library", "wrapper",
                     "connector", "plugin", "extension"],
        "weight": 2.3
    },
}

# 次要关键词
SECONDARY_KEYWORDS = {
    "大模型": ["GPT", "Claude", "LLM", "large language model", "language model"],
    "AI工程": ["engineering", "system design", "production", "scaling"],
}

# 非AI关键词（需要过滤）
NON_AI_KEYWORDS = [
    "music", "video game", "game review",
    "politics", "election", "government",
    "sports", "football", "basketball", "baseball",
    "entertainment", "movie", "film", "celebrity",
    "crypto", "cryptocurrency", "Bitcoin", "NFT",
    "stock market", "trading", "investment",
]

# 需要跳过的URL模式
SKIP_URL_PATTERNS = [
    '/course', '/app', '/live', '/events', '/following', '/pins',
    '/signup', '/login', '/contact', '/about',
    '/author/', '/category/', '/tag/', '/page/',
    '/comment', '/trackback',
]

OUTPUT_DIR = Path("/home/openclaw/.openclaw/workspace")
REPORT_FILE_TEMPLATE = "ai-daily-report-{date}.md"


def fetch_rss(url):
    """获取RSS内容"""
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            print(f"  ❌ RSS获取失败: {resp.status_code}")
            return []
        return parse_rss_xml(resp.text)
    except Exception as e:
        print(f"  ❌ RSS异常: {e}")
        return []


def parse_rss_xml(xml_content):
    """解析RSS XML"""
    items = []
    title_pattern = r'<!\[CDATA\[(.*?)\]\]>'
    link_pattern = r'<link>([^<]+)</link>'
    date_pattern = r'<pubDate>([^<]+)</pubDate>'
    description_pattern = r'<description>([^<]+)</description>'

    titles = re.findall(title_pattern, xml_content)
    links = re.findall(link_pattern, xml_content)
    dates = re.findall(date_pattern, xml_content)
    descriptions = re.findall(description_pattern, xml_content)

    for i in range(min(len(titles), len(links), len(dates))):
        # 移除 CDATA 标记
        title = titles[i].strip()

        # 获取简短描述（如果有）
        desc = descriptions[i].strip() if i < len(descriptions) else ""
        # 清理 HTML 标签
        desc = re.sub(r'<[^>]+>', '', desc)[:200]

        items.append({
            "title": title,
            "link": links[i].strip(),
            "pubDate": dates[i].strip(),
            "description": desc
        })

    return items


def fetch_html(url, source_name):
    """获取HTML内容"""
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            print(f"  ❌ HTML获取失败: {resp.status_code}")
            return []
        return parse_html_smart(resp.text, url, source_name)
    except Exception as e:
        print(f"  ❌ HTML异常: {e}")
        return []


def parse_html_smart(html_content, base_url, source_name):
    """智能HTML解析，针对不同网站使用不同策略"""
    items = []

    # 根据数据源使用不同的选择器
    if "github.com" in base_url:
        # GitHub Trending - 提取仓库
        repo_pattern = r'<h2[^>]*><a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(repo_pattern, html_content)

        for repo_link, repo_name in matches[:15]:
            if not repo_link.startswith('http'):
                repo_link = 'https://github.com' + repo_link

            items.append({
                "title": f"⭐ {repo_name}",
                "link": repo_link,
                "pubDate": datetime.now().isoformat(),
                "description": "GitHub Trending Repository"
            })

    elif "huggingface.co" in base_url:
        # Hugging Face Papers
        paper_pattern = r'<a[^>]*class="[^"]*card-link[^"]*"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(paper_pattern, html_content)

        for paper_link, paper_title in matches[:15]:
            items.append({
                "title": paper_title.strip(),
                "link": urljoin(base_url, paper_link),
                "pubDate": datetime.now().isoformat(),
                "description": "Hugging Face Paper"
            })

    elif "anthropic.com" in base_url or "openai.com/blog" in base_url:
        # 官方博客 - 提取文章
        article_pattern = r'<a[^>]*class="[^"]*[^"]*"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(article_pattern, html_content)

        for article_link, article_title in matches[:15]:
            if article_link.startswith('/'):
                article_link = urljoin(base_url, article_link)

            # 跳过非文章链接
            if any(skip in article_link.lower() for skip in ['/about', '/careers', '/company', '/contact']):
                continue

            items.append({
                "title": article_title.strip(),
                "link": article_link,
                "pubDate": datetime.now().isoformat(),
                "description": "Official Blog Post"
            })

    elif "langchain.dev" in base_url:
        # LangChain Blog
        article_pattern = r'<a[^>]*href="(/blog/[^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(article_pattern, html_content)

        for article_link, article_title in matches[:15]:
            full_link = urljoin(base_url, article_link)

            items.append({
                "title": article_title.strip(),
                "link": full_link,
                "pubDate": datetime.now().isoformat(),
                "description": "LangChain Blog Post"
            })

    else:
        # 通用提取 - 找所有文章链接
        link_pattern = r'<a\s+href="([^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(link_pattern, html_content)

        for link, title in matches[:20]:
            if not link.startswith('http'):
                if link.startswith('/'):
                    link = base_url.rstrip('/') + '/' + link.lstrip('/')
                else:
                    link = 'https://' + link

            # 跳过非文章链接
            if any(skip in link.lower() for skip in SKIP_URL_PATTERNS):
                continue

            items.append({
                "title": title.strip(),
                "link": link,
                "pubDate": datetime.now().isoformat(),
                "description": ""
            })

    return items


def calculate_relevance_score(article):
    """计算文章相关性得分"""
    title = article["title"].lower()
    score = 0.0

    # 优先关键词（权重高）
    for category, info in PRIORITY_KEYWORDS.items():
        for keyword in info["keywords"]:
            if keyword.lower() in title:
                score += info["weight"]
                # 如果标题包含多个相关词，额外加分
                if title.count(keyword.lower()) > 0:
                    score += 0.5

    # 次要关键词
    for keyword in SECONDARY_KEYWORDS["大模型"]:
        if keyword.lower() in title:
            score += 1.0

    for keyword in SECONDARY_KEYWORDS["AI工程"]:
        if keyword.lower() in title:
            score += 1.0

    # 非AI关键词扣分
    for keyword in NON_AI_KEYWORDS:
        if keyword.lower() in title:
            score -= 5.0

    # 鼓励技术性标题（包含技术术语）
    tech_terms = ["python", "api", "sdk", "library", "tool", "framework",
                  "implementation", "example", "tutorial", "guide", "code"]
    for term in tech_terms:
        if term in title:
            score += 0.5

    return score


def classify_article(title):
    """根据标题分类文章"""
    title_lower = title.lower()
    scores = {}

    for category, info in PRIORITY_KEYWORDS.items():
        score = 0
        for keyword in info["keywords"]:
            if keyword.lower() in title_lower:
                score += info["weight"]
        scores[category] = score

    # 返回得分最高的分类
    if not scores:
        return "其他"

    max_category = max(scores, key=scores.get)
    return max_category if scores[max_category] > 0 else "其他"


def generate_summary(article):
    """生成智能摘要"""
    title = article["title"]
    desc = article.get("description", "")

    # 如果已有描述，返回它
    if desc and len(desc) > 50:
        return desc[:200]

    # 否则，基于标题生成
    # 移除特殊字符
    clean_title = re.sub(r'[^\w\s\-\.]', ' ', title)
    words = clean_title.split()

    # 返回前 20 个字
    summary = ' '.join(words[:15])
    if len(summary) < len(clean_title):
        summary += '...'

    return summary


def fetch_article_content(url, timeout=30):
    """抓取文章正文内容（简化版）"""
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code != 200:
            return None

        html = resp.text

        # 简化：提取所有段落
        paragraphs = re.findall(r'<p[^>]*>([^<]+)</p>', html)
        if not paragraphs:
            return None

        # 前几段内容
        content = ' '.join(paragraphs[:3])
        # 清理 HTML
        content = re.sub(r'<[^>]+>', ' ', content)
        # 移除多余空格
        content = ' '.join(content.split())

        return content[:500]

    except Exception as e:
        return None


def generate_smart_summary(article):
    """生成智能摘要（基于正文内容）"""
    title = article["title"]
    url = article["link"]

    # 优先使用描述
    desc = article.get("description", "")
    if desc and len(desc) > 30:
        return desc[:200]

    # 尝试抓取正文（选择性，只对高分文章）
    score = calculate_relevance_score(article)
    if score < 2.0:
        # 低分文章，只返回标题摘要
        words = re.sub(r'[^\w\s\-\.]', ' ', title).split()
        return ' '.join(words[:12]) + '...'

    # 高分文章，尝试抓取正文
    content = fetch_article_content(url)
    if content:
        return content[:200]

    # 回退到标题摘要
    words = re.sub(r'[^\w\s\-\.]', ' ', title).split()
    return ' '.join(words[:12]) + '...'


def generate_daily_report():
    """生成AI日报"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始采集...")

    # 按优先级采集数据源
    all_articles = []
    for source_name, source_config in sorted(SOURCES.items(), key=lambda x: x[1]['priority']):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 采集 {source_name} (优先级 {source_config['priority']})...")

        if source_config['type'] == 'rss':
            articles = fetch_rss(source_config['url'])
        else:
            articles = fetch_html(source_config['url'], source_name)

        all_articles.extend(articles)
        print(f"  获取到 {len(articles)} 篇")

    # 去重（基于链接）
    seen_links = set()
    unique_articles = []
    for article in all_articles:
        if article["link"] not in seen_links:
            seen_links.add(article["link"])
            unique_articles.append(article)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 去重后共 {len(unique_articles)} 篇")

    # 计算相关性得分并排序
    for article in unique_articles:
        article["relevance_score"] = calculate_relevance_score(article)

    # 只保留得分大于 1.0 的文章
    relevant_articles = [a for a in unique_articles if a["relevance_score"] > 1.0]
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 相关性筛选后 {len(relevant_articles)} 篇")

    # 按得分排序
    relevant_articles.sort(key=lambda x: x["relevance_score"], reverse=True)

    # 限制文章数量
    MAX_ARTICLES = 15
    top_articles = relevant_articles[:MAX_ARTICLES]
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 选取前 {len(top_articles)} 篇")

    # 分类
    categories = {}
    for article in top_articles:
        category = classify_article(article["title"])
        if category not in categories:
            categories[category] = []
        categories[category].append(article)

    # 开始抓取摘要
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始抓取文章摘要...")
    article_index = 0
    for category, articles in categories.items():
        article_index += 1
        print(f"  [{category}] {article_index}/{len(top_articles)}")
        for article in articles:
            article["summary"] = generate_smart_summary(article)
            time.sleep(0.5)  # 避免请求过快

    # 生成报告
    lines = []
    lines.append(f"# AI 实用技术日报 — {datetime.now().strftime('%Y年%m月%d日')}")
    lines.append("")
    lines.append(f"> 专注于 **Agent实现、开源工具、技术文章、实际案例**，帮助快速掌握 AI 实用技能")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 统计信息
    lines.append("## 采集统计")
    lines.append("")
    lines.append(f"- **总文章数**: {len(top_articles)} 篇")
    lines.append(f"- **数据源**: {len(SOURCES)} 个")
    lines.append(f"- **分类数**: {len(categories)} 个")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 按分类展示文章
    for category, articles in categories.items():
        lines.append(f"## {category}")
        lines.append("")

        for article in articles:
            title = article["title"]
            summary = article.get("summary", "")
            link = article["link"]
            pub_date = article.get("pubDate", "")

            lines.append(f"**{title}**")
            lines.append("")
            lines.append(f"{summary}")
            lines.append("")
            lines.append(f"📅 发布时间：{pub_date[:25]}")
            lines.append(f"🔗 [原文链接]({link})")
            lines.append("")
            lines.append("---")
            lines.append("")

    # 今日要点
    lines.append("## 📊 今日要点")
    lines.append("")
    lines.append(f"**最高相关度文章**: {top_articles[0]['title'][:60]}...")
    lines.append("")
    lines.append(f"**文章最多的分类**: {max(categories, key=lambda k: len(categories[k]))}")
    lines.append("")
    lines.append(f"**采集范围**: 今日发布的实用技术内容（相关性得分 > 1.0）")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 结尾
    lines.append(f"**采集时间**：{datetime.now().strftime('%H:%M')}")
    lines.append(f"**数据来源**：{', '.join(SOURCES.keys())}")
    lines.append(f"**整理**：虾说 (Xiashuo)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("> 💡 **提示**：本日报专注于实用技术内容。点击\"原文链接\"可阅读完整文章。")
    lines.append("")
    lines.append("> 🎯 **适用场景**：Agent开发者、AI工程师、开源爱好者")

    # 保存报告
    report_content = '\n'.join(lines)
    report_file = OUTPUT_DIR / REPORT_FILE_TEMPLATE.format(date=datetime.now().strftime('%Y-%m-%d'))

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 报告已保存: {report_file}")

    # 微信推送
    if WX_PUSH_AVAILABLE:
        try:
            summary_lines = [
                f"AI 实用技术日报 - {datetime.now().strftime('%m月%d日')}",
                "",
                f"📊 文章数: {len(top_articles)} 篇",
                f"🔥 最高相关: {top_articles[0]['title'][:50]}...",
                "",
                "📖 查看: ai-daily-report-*.md",
                "",
                f"📅 采集时间: {datetime.now().strftime('%H:%M')}"
            ]
            push_wechat("AI 实用技术日报", '\n'.join(summary_lines))
            print("✅ 微信推送成功")
        except Exception as e:
            print(f"⚠️  微信推送失败: {e}")

    return report_file


if __name__ == "__main__":
    try:
        generate_daily_report()
        print("\n" + "=" * 50)
        print("✅ 采集完成！")
        print("=" * 50)
        print(f"\n报告文件: {OUTPUT_DIR / REPORT_FILE_TEMPLATE.format(date=datetime.now().strftime('%Y-%m-%d'))}")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
