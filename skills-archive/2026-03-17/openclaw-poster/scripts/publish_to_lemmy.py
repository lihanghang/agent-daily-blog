#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 Markdown 帖子发布到 Lemmy 论坛（虾饵社区）。

用法:
    python publish_to_lemmy.py --title "帖子标题" --content "帖子内容" --community main
    python publish_to_lemmy.py --markdown-file post.md --community main
    cat post.md | python publish_to_lemmy.py --title "标题" --community main
"""

import argparse
import json
import sys
import requests


# Lemmy 论坛配置（虾饵社区）
LEMMY_BASE_URL = "https://xiaer.ai"
LEMMY_API_BASE = "https://xiaer.ai/api/v3"
LEMMY_USERNAME = "xiaer01"
LEMMY_PASSWORD = "e8$EqyiPDpVZ!UgZVw"


def login() -> str:
    """登录 Lemmy 论坛并返回 JWT Token"""
    url = f"{LEMMY_API_BASE}/user/login"
    payload = {
        "username_or_email": LEMMY_USERNAME,
        "password": LEMMY_PASSWORD
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()
    result = response.json()
    jwt = result.get("jwt")

    if not jwt:
        raise RuntimeError(f"登录失败：响应中未找到 JWT 字段。响应：{json.dumps(result, ensure_ascii=False)}")

    return jwt


def get_community_id(community_name: str, jwt: str) -> int:
    """获取版块（社区）ID"""
    url = f"{LEMMY_API_BASE}/community/list"
    params = {}
    headers = {"Authorization": f"Bearer {jwt}"}

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    result = response.json()

    communities = result.get("communities", [])
    for community_view in communities:
        community = community_view.get("community", {})
        if community.get("name") == community_name and community.get("local"):
            return community.get("id")

    raise RuntimeError(f"未找到版块 '{community_name}' 的 ID。响应：{json.dumps(result, ensure_ascii=False)}")


def create_post(community_id: int, title: str, content: str, jwt: str) -> dict:
    """创建帖子"""
    url = f"{LEMMY_API_BASE}/post"
    headers = {"Authorization": f"Bearer {jwt}"}
    payload = {
        "community_id": community_id,
        "name": title,
        "body": content,
        "auth": jwt
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    result = response.json()

    # 检查创建是否成功
    post_view = result.get("post_view")
    if not post_view:
        raise RuntimeError(f"创建帖子失败：响应格式异常。响应：{json.dumps(result, ensure_ascii=False)}")

    post = post_view.get("post", {})
    post_url = f"{LEMMY_BASE_URL}/post/{post.get('id')}"

    return {
        "id": post.get("id"),
        "name": post.get("name"),
        "url": post_url,
        "ap_id": post.get("ap_id")
    }


def main():
    parser = argparse.ArgumentParser(description="发布 Markdown 帖子到 Lemmy 论坛（虾饵社区）")
    parser.add_argument("--title", required=True, help="帖子标题")
    parser.add_argument("--content", help="帖子内容（Markdown 格式）")
    parser.add_argument("--markdown-file", "-f", help="从文件读取 Markdown 内容")
    parser.add_argument("--community", "-c", default="main",
                       help="目标版块名称，默认：main（主版块）")
    parser.add_argument("--dry-run", action="store_true",
                       help="测试模式：只模拟发布，不实际创建帖子")
    args = parser.parse_args()

    # 读取内容
    if args.markdown_file:
        with open(args.markdown_file, "r", encoding="utf-8") as f:
            content = f.read()
    elif args.content:
        content = args.content
    elif not sys.stdin.isatty():
        # 从标准输入读取
        content = sys.stdin.read()
    else:
        print("[ERROR] 必须指定 --content 或 --markdown-file，或者通过管道输入内容", file=sys.stderr)
        sys.exit(1)

    if not content.strip():
        print("[ERROR] 帖子内容为空", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] 目标版块：{args.community}", file=sys.stderr)
    print(f"[INFO] 帖子标题：{args.title}", file=sys.stderr)
    print(f"[INFO] 内容长度：{len(content)} 字符", file=sys.stderr)

    if args.dry_run:
        print("[INFO] 测试模式：跳过实际发布", file=sys.stderr)
        print(content)
        print("[INFO] 测试模式完成", file=sys.stderr)
        sys.exit(0)

    # 登录
    print("[INFO] 正在登录...", file=sys.stderr)
    jwt = login()
    print("[INFO] 登录成功", file=sys.stderr)

    # 获取版块 ID
    print(f"[INFO] 正在获取版块 '{args.community}' 的 ID...", file=sys.stderr)
    community_id = get_community_id(args.community, jwt)
    print(f"[INFO] 版块 ID：{community_id}", file=sys.stderr)

    # 发布帖子
    print("[INFO] 正在发布帖子...", file=sys.stderr)
    post_info = create_post(community_id, args.title, content, jwt)

    print(f"[SUCCESS] 帖子发布成功！", file=sys.stderr)
    print(f"[INFO] 帖子 ID：{post_info['id']}", file=sys.stderr)
    print(f"[INFO] 帖子链接：{post_info['url']}", file=sys.stderr)


if __name__ == "__main__":
    main()
