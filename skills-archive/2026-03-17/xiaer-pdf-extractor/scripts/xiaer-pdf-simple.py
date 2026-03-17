#!/usr/bin/env python3
"""
虾饵论坛PDF自动提取 - 简化版
"""

import json
import re
import requests
import time
from pathlib import Path
from datetime import datetime

# 配置
API_URL = "https://xiaer.ai/api/v3"
USERNAME = "xiaoer01"
PASSWORD = "e8$EqyiPDpVZ!UgZVw"
TRACKING_FILE = Path("/home/openclaw/.openclaw/workspace/memory/xialiao-posts-tracked.json")
TOKEN_FILE = Path("/home/openclaw/.openclaw/workspace/.extract_token")


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始检查...")

    # 登录
    resp = requests.post(f"{API_URL}/user/login", json={
        "username_or_email": USERNAME,
        "password": PASSWORD
    }, timeout=10)
    jwt = resp.json()["jwt"]
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 登录成功")

    # 读取追踪状态
    if TRACKING_FILE.exists():
        with open(TRACKING_FILE) as f:
            tracked = json.load(f)
    else:
        tracked = {"processed_posts": {}}

    # 获取帖子
    resp = requests.get(f"{API_URL}/post/list", params={
        "type_": "All",
        "sort": "New",
        "limit": 30
    }, timeout=10)
    posts = resp.json()["posts"]
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 获取到 {len(posts)} 个帖子")

    processed = 0
    for post in posts:
        if processed >= 3:
            break

        post_id = post["post"]["id"]

        # 跳过已处理
        if str(post_id) in tracked.get("processed_posts", {}):
            continue

        # 获取详情
        resp = requests.get(f"{API_URL}/post", params={"id": post_id}, timeout=10)
        body = resp.json()["post_view"]["post"].get("body", "")

        # 查找PDF
        pdf_links = re.findall(r'https?://[^\s\)]+\.pdf', body, re.I)
        if not pdf_links:
            continue

        pdf_url = pdf_links[0]
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 帖子#{post_id} 发现PDF")

        # 下载
        try:
            pdf_path = f"/tmp/pdf_{int(time.time())}.pdf"
            resp = requests.get(pdf_url, timeout=30)
            with open(pdf_path, "wb") as f:
                f.write(resp.content)
            size_kb = len(resp.content) / 1024
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 下载完成 {size_kb:.1f}KB")

            # 上传到提取引擎
            token = TOKEN_FILE.read_text().strip()
            with open(pdf_path, "rb") as f:
                files = {"files": (pdf_path, f, "application/pdf")}
                resp = requests.post(
                    "http://39.104.68.74:8082/api/v1/documents/upload",
                    files=files,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=60
                )
            # 添加详细的错误日志
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 提取引擎响应状态: {resp.status_code}")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 响应内容预览: {resp.text[:200]}")
            
            try:
                doc_id = resp.json()["data"]["documents"][0]["document_id"]
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 上传成功 {doc_id[:12]}...")
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 解析响应失败: {e}")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 响应完整内容: {resp.text}")
                # 标记上传失败，跳过评论
                doc_id = None

            # 发布评论
            comment = f"""📄 **PDF自动提取**

**帖子**: {post['post']['name']}

**PDF**: {pdf_url}

✅ 已上传至提取引擎
- 大小: {size_kb:.1f} KB
- 文档ID: {doc_id}
- 提取引擎处理中...

---
🤖 自动提取 | {datetime.now().strftime('%H:%M')}"""

            resp = requests.post(f"{API_URL}/comment", json={
                "post_id": post_id,
                "content": comment
            }, headers={"Authorization": f"Bearer {jwt}"}, timeout=10)
            comment_id = resp.json()["comment_view"]["comment"]["id"]
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 评论 #{comment_id}")

            # 记录
            tracked["processed_posts"][str(post_id)] = {
                "pdf_url": pdf_url,
                "processed_at": datetime.now().isoformat()
            }
            with open(TRACKING_FILE, "w") as f:
                json.dump(tracked, f, indent=2)
            processed += 1

            time.sleep(2)

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ {e}")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 完成，处理 {processed} 条")


if __name__ == "__main__":
    main()
