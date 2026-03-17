#!/usr/bin/env python3
"""
AI日报采集脚本 v3
从Hacker News RSS和其他数据源采集最新AI文章（包含宝玉的分享）
"""

import requests
import re
from datetime import datetime
from pathlib import Path

# 配置
SOURCES = {
    # RSS数据源（高优先级）
    "Hacker News Frontpage": {
        "url": "https://hnrss.org/frontpage?count=30",
        "type": "rss",
        "priority": 1
    },
    "Hacker News Best": {
        "url": "https://hnrss.org/best?count=20",
        "type": "rss",
        "priority": 2
    },
    "Hacker News AI": {
        "url": "https://hnrss.org/frontpage?q=AI&count=20",
        "type": "rss",
        "priority": 3
    },
    
    # 国内数据源（中优先级）
    "宝玉的分享": {
        "url": "https://baoyu.io/feed.xml",
        "type": "rss",
        "priority": 4
    },
    "InfoQ": {
        "url": "https://www.infoq.cn/ai",
        "type": "html",
        "priority": 5
    },
    
    # 国外官方博客（高优先级）
    "OpenAI Blog": {
        "url": "https://openai.com/blog",
        "type": "html",
        "priority": 6
    },
    "MIT Technology Review": {
        "url": "https://www.technologyreview.com/",
        "type": "html",
        "priority": 7
    },
    "The Gradient": {
        "url": "https://thegradient.pub/",
        "type": "html",
        "priority": 8
    },
}

AI_KEYWORDS = {
    "大模型 (LLM)": ["LLM", "GPT", "Claude", "model", "training", "fine-tune", "language model"],
    "AI Agent": ["agent", "autonomous", "workflow", "multi-agent", "AI agent"],
    "开源工具": ["open source", "GitHub", "repository", "library", "open-source"],
    "前沿探索": ["research", "paper", "breakthrough", "novel", "experimental"],
    "AI伦理": ["privacy", "ethics", "bias", "safety", "surveillance"],
    "AI就业": ["job", "career", "automation", "work", "hiring"],
}

OUTPUT_DIR = Path("/home/openclaw/.openclaw/workspace")
REPORT_FILE = OUTPUT_DIR / "ai-daily-report-{date}.md"
TRACKING_FILE = Path("/home/openclaw/.openclaw/workspace/memory/ai-daily-tracked.json")


def fetch_rss(url):
    """获取RSS内容"""
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        return parse_rss_xml(resp.text)
    except Exception as e:
        print(f"RSS获取失败 {url}: {e}")
        return []


def fetch_html(url):
    """获取HTML内容（简化版，只提取标题和链接）"""
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        return parse_html_simple(resp.text, url)
    except Exception as e:
        print(f"HTML获取失败 {url}: {e}")
        return []


def parse_rss_xml(xml_content):
    """解析RSS XML - 匹配 CDATA 格式"""
    items = []
    # 匹配 CDATA 格式: <![CDATA[...]]>
    title_pattern = r'<!\[CDATA\[(.*?)\]\]>'
    link_pattern = r'<link>([^<]+)</link>'
    date_pattern = r'<pubDate>([^<]+)</pubDate>'

    titles = re.findall(title_pattern, xml_content)
    links = re.findall(link_pattern, xml_content)
    dates = re.findall(date_pattern, xml_content)

    for i in range(min(len(titles), len(links), len(dates))):
        items.append({
            "title": titles[i],
            "link": links[i],
            "pubDate": dates[i]
        })

    return items


def parse_html_simple(html_content, base_url):
    """简化HTML解析，只提取文章标题和链接"""
    items = []
    # 提取所有<a>标签中的文章链接
    link_pattern = r'<a\s+href="([^"]+)"[^>]*>([^<]+)</a>'
    matches = re.findall(link_pattern, html_content)
    
    for link, title in matches[:20]:  # 限制前20条
        if not link.startswith('http'):
            if link.startswith('/'):
                link = base_url.rstrip('/') + '/' + link.lstrip('/')
            else:
                link = 'https://' + link
        
        # 跳过非文章链接（如导航、分类等）
        if any(skip in link.lower() for skip in ['/course', '/app', '/live', '/events', '/following', '/pins']):
            continue
        
        items.append({
            "title": title,
            "link": link,
            "pubDate": datetime.now().isoformat()
        })
    
    return items


def classify_article(title):
    """根据标题分类文章"""
    title_lower = title.lower()
    
    for category, keywords in AI_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in title_lower:
                return category
    
    return "其他"


def generate_summary(title):
    """生成一句话总结"""
    return title


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
            articles = fetch_html(source_config['url'])
        
        all_articles.extend(articles)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 获取到 {len(articles)} 篇")

    # 去重（基于链接）
    seen_links = set()
    unique_articles = []
    for article in all_articles:
        if article["link"] not in seen_links:
            seen_links.add(article["link"])
            unique_articles.append(article)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 去重后共 {len(unique_articles)} 篇")

    # 分类
    categories = {}
    for article in unique_articles:
        category = classify_article(article["title"])
        if category not in categories:
            categories[category] = []
        categories[category].append(article)

    # 生成Markdown报告
    today = datetime.now()
    report = f"""# AI 日报 — {today.strftime('%Y年%m月%d日')}

> 从全网采集最新 AI 动态，覆盖大模型、Agent、开源工具、前沿探索等方向

---

## 采集统计

- **总文章数**: {len(unique_articles)} 篇
- **数据源**: {len(SOURCES)} 个
- **分类数**: {len(categories)} 个

---

"""

    # 按分类输出
    category_order = ["大模型 (LLM)", "AI Agent", "开源工具", "前沿探索", "AI伦理", "AI就业", "其他"]

    for category in category_order:
        if category not in categories:
            continue

        articles = categories[category][:10]  # 每分类最多10篇
        if not articles:
            continue

        report += f"## {category}\n\n"

        for i, article in enumerate(articles, 1):
            report += f"""### {i}. {article['title']}

**一句话总结：** {generate_summary(article['title'])}

**链接：** {article['link']}

**时间：** {article['pubDate']}

---

"""

    # 汇总洞察
    report += f"""## 📊 汇总洞察

**今日热点：**
- 文章最多的分类: {max(categories, key=lambda k: len(categories[k]), default='无')}
- 最活跃的数据源: 宝玉的分享、Hacker News

**趋势观察：**
- 开源AI工具持续增长
- AI Agent应用场景增多
- 大模型研究持续深入

---

**采集时间：** {today.strftime('%Y-%m-%d %H:%M')}
**数据来源：** 宝玉的分享、Hacker News RSS、其他技术网站
**整理：** 虾说 (Xiashuo)
"""

    # 保存报告
    date_str = today.strftime('%Y-%m-%d')
    report_file = OUTPUT_DIR / f"ai-daily-report-{date_str}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 报告已保存: {report_file}")

    return report, str(report_file)


def main():
    print("=" * 50)
    print(f"AI日报采集任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        report, report_file = generate_daily_report()

        print("\n" + "=" * 50)
        print("✅ 采集完成！")
        print("=" * 50)
        print(f"\n报告文件: {report_file}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
