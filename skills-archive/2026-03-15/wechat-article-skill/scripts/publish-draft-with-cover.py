#!/usr/bin/env python3
"""
上传封面图到素材库、获取 media_id、然后创建草稿并关联封面
"""
import argparse
import json
import os
import shutil
import subprocess
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


def upload_cover(token, image_path):
    """上传封面图到素材库，返回 media_id"""
    if not shutil.which("curl"):
        fail("curl not found. Please install curl first.")

    cmd = [
        "curl",
        "-sS",
        "-X",
        "POST",
        f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image",
        "-F",
        f"media=@{image_path}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        fail(f"upload cover failed: {result.stderr.strip() or result.stdout.strip()}")

    try:
        data = json.loads(result.stdout)
        print(f"[Cover] Media ID: {data.get('media_id', 'unknown')}")
    except Exception as e:
        fail(f"upload cover returned non-json: {result.stdout[:300]}")

    if "media_id" not in data:
        fail(f"upload cover failed: {data}")
    return data.get("media_id", "")


def create_draft(token, title, author, digest, content, need_open_comment, only_fans_can_comment, thumb_media_id=None):
    """创建公众号草稿（可选封面关联）"""
    payload = {
        "articles": [
            {
                "title": title,
                "author": author,
                "digest": digest,
                "content": content,
                "need_open_comment": int(need_open_comment),
                "only_fans_can_comment": int(only_fans_can_comment),
            }
        ]
    }

    # 只在 thumb_media_id 有效时才添加该字段
    if thumb_media_id and thumb_media_id.strip():
        payload["articles"][0]["thumb_media_id"] = thumb_media_id

    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    data = http_post_json(url, payload)

    # 打印调试信息
    print(f"[DEBUG] Draft API Response: {data}")

    # 检查响应：成功时应该有 media_id，失败时会有 errcode
    # 有 errcode 字段且不为 0 才是失败
    if "errcode" in data and data["errcode"] != 0:
        fail(f"create draft failed: {data}")

    if "media_id" not in data:
        fail(f"create draft failed: no media_id in response: {data}")

    return data


def ensure_file(path, name):
    if not path:
        fail(f"{name} path is empty")
    if not os.path.exists(path):
        fail(f"{name} not found: {path}")
    if not os.path.isfile(path):
        fail(f"{name} is not a file: {path}")


def validate_inputs(args, appid, appsecret):
    if not appid or not appsecret:
        fail("AppID/AppSecret required (--appid/--appsecret or WX_APPID/WX_APPSECRET)")

    ensure_file(args.content_file, "content file")

    if len(args.title.strip()) == 0:
        fail("title cannot be empty")

    if len(args.digest) > 120:
        print("Warn: digest length > 120 chars, WeChat display may truncate.", file=sys.stderr)

    if args.need_open_comment not in (0, 1):
        fail("--need-open-comment must be 0 or 1")

    if args.only_fans_can_comment not in (0, 1):
        fail("--only-fans-can-comment must be 0 or 1")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="创建公众号草稿（支持封面关联）")
    parser.add_argument("--title", required=True, help="文章标题")
    parser.add_argument("--author", default=None, help="作者（或设置 WX_AUTHOR 环境变量）")
    parser.add_argument("--digest", default="", help="文章摘要，建议 120 字以内")
    parser.add_argument("--content-file", required=True, help="HTML 内容文件路径")
    parser.add_argument("--cover", default=None, help="封面图路径（可选）")
    parser.add_argument("--appid", default=None, help="AppID（或设置 WX_APPID 环境变量）")
    parser.add_argument("--appsecret", default=None, help="AppSecret（或设置 WX_APPSECRET 环境变量）")
    parser.add_argument("--need-open-comment", type=int, default=1, help="是否开启评论：1 开启，0 关闭")
    parser.add_argument("--only-fans-can-comment", type=int, default=0, help="是否仅粉丝可评论：1 是，0 否")
    args = parser.parse_args()

    appid = args.appid or os.environ.get("WX_APPID")
    appsecret = args.appsecret or os.environ.get("WX_APPSECRET")
    author = args.author or os.environ.get("WX_AUTHOR", "")

    validate_inputs(args, appid, appsecret)

    with open(args.content_file, "r", encoding="utf-8") as f:
        content = f.read().strip()

    print("[1/3] Getting access token...")
    token = get_access_token(appid, appsecret)

    print("[2/3] Creating draft...")
    
    # 步骤 1：上传封面图（如果提供）
    thumb_media_id = None
    if args.cover:
        print(f"[2/3] Uploading cover image: {args.cover}")
        thumb_media_id = upload_cover(token, args.cover)
    else:
        print(f"[2/3] Skipping cover (not provided)")

    # 步骤 2：创建草稿
    result = create_draft(
        token=token,
        title=args.title,
        author=author,
        digest=args.digest,
        content=content,
        need_open_comment=args.need_open_comment,
        only_fans_can_comment=args.only_fans_can_comment,
        thumb_media_id=thumb_media_id,
    )

    if "data" in result:
        print("✅ Draft created successfully!")
        draft_id = result.get("media_id", "")
        print(f"   Draft ID: {draft_id}")
        print(f"   Thumb Media ID: {thumb_media_id or 'N/A'}")
        success = True
    else:
        # 检查是否实际上成功了（有 media_id 但没有 data 字段）
        if "media_id" in result:
            print("✅ Draft created successfully!")
            draft_id = result.get("media_id", "")
            print(f"   Draft ID: {draft_id}")
            print(f"   Thumb Media ID: {thumb_media_id or 'N/A'}")
            success = True
        else:
            print(f"❌ Create draft failed: {result}")
            success = False
    
    # 打印完整结果
    output = {
        "ok": success,
        "draft_id": result.get("media_id", ""),
        "thumb_media_id": thumb_media_id,
    }
    
    print(json.dumps(output, ensure_ascii=False))
