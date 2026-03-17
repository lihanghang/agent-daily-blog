#!/usr/bin/env python3
"""
全网搜索新数据源脚本
每天半夜自动搜索，发现新的AI相关网站和文章
"""

import json
import re
from datetime import datetime
from pathlib import Path
import requests

# 配置
SEARCH_QUERIES = [
    "AI research blog 2026",
    "machine learning news today",
    "artificial intelligence weekly",
    "deep learning papers arXiv",
    "LLM model updates",
    "AI agent tools",
    "open source AI projects",
    "AI ethics research",
]

# 已知数据源（用于去重）
KNOWN_SOURCES = {
    "hnrss.org",
    "baoyu.io",
    "openai.com",
    "thegradient.pub",
    "technologyreview.com",
    "distill.pub",
    "arxiv.org",
    "huggingface.co",
    "pytorch.org",
    "tensorflow.org",
    "langchain.com",
}

# 输出路径
OUTPUT_DIR = Path("/home/openclaw/.openclaw/workspace")
NEW_SOURCES_FILE = OUTPUT_DIR / "memory/ai-daily-new-sources.json"
SEARCH_LOG_FILE = OUTPUT_DIR / "memory/ai-daily-search-log.json"


def search_brave(query, count=10):
    """使用 Brave Search API 搜索"""
    # 注意：这里需要配置 Brave Search API
    # 如果没有 API key，可以跳过
    try:
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
        }
        params = {
            "q": query,
            "count": count,
        }
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("web", {}).get("results", [])
    except Exception as e:
        print(f"  搜索错误: {e}")
    return []


def extract_domain(url):
    """提取域名"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except:
        return ""


def classify_relevance(url, title, snippet):
    """分类相关性"""
    text = (title + " " + snippet + " " + url).lower()

    # AI 相关关键词
    ai_keywords = [
        "ai", "artificial intelligence", "machine learning", "deep learning",
        "neural network", "gpt", "llm", "language model", "transformer",
        "reinforcement learning", "computer vision", "nlp", "natural language",
        "chatbot", "agent", "autonomous", "openai", "anthropic", "google ai",
        "meta ai", "microsoft ai", "research paper", "arxiv",
    ]

    score = sum(1 for keyword in ai_keywords if keyword in text)
    return score


def discover_new_sources():
    """发现新数据源"""
    print("=" * 60)
    print(f"全网搜索新数据源 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    new_sources = []

    # 加载已知的来源
    known_domains = KNOWN_SOURCES.copy()
    if NEW_SOURCES_FILE.exists():
        with open(NEW_SOURCES_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
            for entry in history:
                known_domains.add(entry.get('domain', ''))

    # 执行搜索
    for query in SEARCH_QUERIES:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 搜索: {query}")

        results = search_brave(query, count=20)

        print(f"  找到 {len(results)} 个结果")

        for result in results:
            url = result.get('url', '')
            title = result.get('title', '')
            snippet = result.get('description', '')

            if not url:
                continue

            # 提取域名
            domain = extract_domain(url)

            # 跳过已知来源
            if domain in known_domains:
                continue

            # 评估相关性
            relevance = classify_relevance(url, title, snippet)

            if relevance >= 2:  # 至少2个关键词匹配
                new_sources.append({
                    "domain": domain,
                    "url": url,
                    "title": title,
                    "snippet": snippet,
                    "relevance": relevance,
                    "discovered_at": datetime.now().isoformat(),
                })
                known_domains.add(domain)

    # 按相关性排序
    new_sources.sort(key=lambda x: x['relevance'], reverse=True)

    # 保存结果
    if new_sources:
        # 更新历史记录
        history = []
        if NEW_SOURCES_FILE.exists():
            with open(NEW_SOURCES_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)

        history.extend(new_sources)

        # 只保留最近100条
        history = history[-100:]

        with open(NEW_SOURCES_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        # 记录日志
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "count": len(new_sources),
            "sources": new_sources,
        }

        logs = []
        if SEARCH_LOG_FILE.exists():
            with open(SEARCH_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)

        logs.append(log_entry)
        logs = logs[-30:]  # 保留最近30次搜索

        with open(SEARCH_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

        print(f"\n{'=' * 60}")
        print(f"✅ 发现 {len(new_sources)} 个新数据源！")
        print(f"{'=' * 60}")
        print(f"\nTop 10 新数据源:\n")

        for i, source in enumerate(new_sources[:10], 1):
            print(f"{i}. {source['domain']} (相关性: {source['relevance']})")
            print(f"   {source['title']}")
            print(f"   {source['url']}")
            print()

        return new_sources
    else:
        print(f"\n{'=' * 60}")
        print("❌ 未发现新数据源")
        print(f"{'=' * 60}")
        return []


def generate_summary():
    """生成数据源总结报告"""
    if not NEW_SOURCES_FILE.exists():
        return None

    with open(NEW_SOURCES_FILE, 'r', encoding='utf-8') as f:
        history = json.load(f)

    if not history:
        return None

    # 统计
    from collections import Counter
    domain_counter = Counter([s['domain'] for s in history])

    report = f"""# AI 数据源发现报告

> 自动全网搜索发现的 AI 相关网站和文章

---

## 统计信息

- **总发现数**: {len(history)} 个
- **独立域名**: {len(domain_counter)} 个
- **最近更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 高质量数据源（Top 20）

"""

    # 按域名的最高相关性排序
    domain_scores = {}
    for entry in history:
        domain = entry['domain']
        relevance = entry['relevance']
        if domain not in domain_scores:
            domain_scores[domain] = relevance
        else:
            domain_scores[domain] = max(domain_scores[domain], relevance)

    top_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[:20]

    for i, (domain, score) in enumerate(top_domains, 1):
        # 找到该域名的代表条目
        rep = next((s for s in history if s['domain'] == domain), None)
        if rep:
            report += f"""### {i}. {domain} (相关性: {score})

**标题**: {rep['title']}
**链接**: {rep['url']}
**发现时间**: {rep['discovered_at'][:10]}

---

"""

    return report


if __name__ == "__main__":
    try:
        new_sources = discover_new_sources()

        # 生成总结报告
        summary = generate_summary()
        if summary:
            report_file = OUTPUT_DIR / "ai-daily-sources-report.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"\n总结报告已保存: {report_file}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
