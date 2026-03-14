#!/usr/bin/env python3
"""
创建公众号草稿（使用空字符串作为 thumb_media_id）
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request


def fail(msg, code=1):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)


def http_get_json(url, timeout=20):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        fail(f"HTTP GET failed: {e}")


def http_post_json(url, payload, timeout=20):
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        fail(f"HTTP POST failed: {e}")


def get_access_token(appid, appsecret):
    q = urllib.parse.urlencode(
        {
            "grant_type": "client_credential",
            "appid": appid,
            "secret": appsecret,
        }
    )
    url = f"https://api.weixin.qq.com/cgi-bin/token?{q}"
    data = http_get_json(url)
    if "access_token" not in data:
        fail(f"get token failed: {data}")
    return data["access_token"]


def create_draft_with_empty_cover(token, title, author, digest, content, need_open_comment, only_fans_can_comment):
    """创建公众号草稿（使用空字符串作为 thumb_media_id）"""
    payload = {
        "articles": [
            {
                "title": title,
                "author": author,
                "digest": digest,
                "content": content,
                "need_open_comment": int(need_open_comment),
                "only_fans_can_comment": int(only_fans_can_comment),
                "thumb_media_id": "",
            }
        ]
    }
    
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    data = http_post_json(url, payload)
    
    if "data" not in data:
        fail(f"create draft failed: {data}")
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="创建公众号草稿（使用空字符串作为 thumb_media_id）")
    parser.add_argument("--title", required=True, help="文章标题")
    parser.add_argument("--author", default="", help="作者")
    parser.add_argument("--digest", default="", help="文章摘要，建议 120 字以内")
    parser.add_argument("--content-file", required=True, help="HTML 内容文件路径")
    parser.add_argument("--appid", required=True, help="AppID")
    parser.add_argument("--appsecret", required=True, help="AppSecret")
    parser.add_argument("--need-open-comment", type=int, default=1, help="是否开启评论：1 开启，0 关闭")
    parser.add_argument("--only-fans-can-comment", type=int, default=0, help="是否仅粉丝可评论：1 是，0 否")
    args = parser.parse_args()

    # 读取内容文件
    if not os.path.exists(args.content_file):
        fail(f"Content file not found: {args.content_file}")
    
    with open(args.content_file, "r", encoding='utf-8') as f:
        content = f.read().strip()

    # 获取 access token
    print("[1/2] Getting access token...")
    token = get_access_token(args.appid, args.appsecret)

    # 创建草稿
    print("[2/2] Creating draft...")
    result = create_draft_with_empty_cover(
        token=token,
        title=args.title,
        author=args.author,
        digest=args.digest,
        content=content,
        need_open_comment=args.need_open_comment,
        only_fans_can_comment=args.only_fans_can_comment,
    )

    if "data" in result:
        print("✅ Draft created successfully!")
        draft_id = result.get("media_id", "")
        print(f"   Draft ID: {draft_id}")
    else:
        print(f"❌ Create draft failed: {result}")
