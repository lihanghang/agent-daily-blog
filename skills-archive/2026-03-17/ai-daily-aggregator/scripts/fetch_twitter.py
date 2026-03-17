#!/usr/bin/env python3
"""
从 Twitter API 搜索 AI 相关推文
"""

import requests
import json
from pathlib import Path

# Load credentials
CREDS_FILE = Path("/home/openclaw/.xialiao/credentials/twitter.json")
with open(CREDS_FILE) as f:
    creds = json.load(f)

BEARER_TOKEN = creds["twitter"]["bearer_token"]

# Optional: Configure proxy if needed
# proxies = {
#     'http': 'http://proxy-server:port',
#     'https': 'http://proxy-server:port',
# }

# Search parameters
KEYWORDS = [
    "AI", "LLM", "ArtificialIntelligence",
    "Agent", "MachineLearning", "OpenAI",
    "LangChain", "AutoGen", "CrewAI"
]

def fetch_tweets(query, max_results=10):
    """Fetch recent tweets for a query"""
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }

    url = f"https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": query,
        "max_results": max_results,
        "tweet.fields": "created_at,author_id,public_metrics,entities"
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)  # , proxies=proxies
        if resp.status_code == 200:
            return resp.json().get("data", [])
        else:
            print(f"Error: {resp.status_code} - {resp.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return []

def main():
    print("=" * 60)
    print("Twitter AI 搜索")
    print("=" * 60)

    all_tweets = []

    for keyword in KEYWORDS[:3]:  # Limit to 3 keywords for testing
        print(f"\n搜索: {keyword}")
        tweets = fetch_tweets(keyword, max_results=5)
        print(f"  获取到 {len(tweets)} 条推文")

        for tweet in tweets:
            all_tweets.append({
                "text": tweet.get("text", ""),
                "created_at": tweet.get("created_at", ""),
                "metrics": tweet.get("public_metrics", {}),
                "keyword": keyword
            })

    print(f"\n总计: {len(all_tweets)} 条推文")

    # Save to file
    output_file = Path("/home/openclaw/.openclaw/workspace/ai-twitter-tweets.json")
    with open(output_file, "w") as f:
        json.dump(all_tweets, f, indent=2, ensure_ascii=False)
    print(f"✅ 已保存到: {output_file}")

if __name__ == "__main__":
    main()
