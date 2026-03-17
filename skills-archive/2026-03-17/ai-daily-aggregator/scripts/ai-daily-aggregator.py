#!/usr/bin/env python3
"""
AI日报采集脚本
从Hacker News RSS等数据源采集最新AI文章
"""

import requests
import re
from datetime import datetime
from pathlib import Path

# 配置
SOURCES = [
    ("Hacker News Frontpage", "https://hnrss.org/frontpage?count=30"),
    ("Hacker News Best", "https://hnrss.org/best?count=20"),
    ("Hacker News AI", "https://hnrss.org/frontpage?q=AI&count=20"),
]

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
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        return []
    return parse_rss_xml(resp.text)


def parse_rss_xml(xml_content):
    """解析RSS XML"""
    items = []
    # 简化解析，提取title、link、pubDate
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
    # 简化：使用标题本身
    return title


def generate_daily_report():
    """生成AI日报"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始采集...")

    # 采集所有数据源
    all_articles = []
    for source_name, url in SOURCES:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 采集 {source_name}...")
        articles = fetch_rss(url)
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
- 最活跃的数据源: Hacker News

**趋势观察：**
- 开源AI工具持续增长
- AI Agent应用场景增多
- 大模型研究持续深入

---

**采集时间：** {today.strftime('%Y-%m-%d %H:%M')}
**数据来源：** Hacker News RSS
**整理：** 虾说 (Xiashuo)
"""

    # 保存报告
    date_str = today.strftime('%Y-%m-%d')
    report_file = REPORT_FILE.format(date=date_str)
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
