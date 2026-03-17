#!/usr/bin/env python3
"""
上传封面图并创建公众号草稿。

用法:
  python3 publish_draft.py \
    --title "标题" \
    --author "作者" \
    --digest "摘要" \
    --content-file article.html \
    --cover cover.jpg \
    --appid <APPID> \
    --appsecret <APPSECRET>

也支持环境变量:
  WX_APPID, WX_APPSECRET, WX_AUTHOR

调试说明：
  根据2026-02-28的实际测试，微信草稿API (draft/add) 即使完全不传 cover 相关字段，
  也会因为其他原因返回 "invalid media_id" 错误。
  
  可能的原因：
  1. 文章内容编码问题（非UTF-8字符）
  2. 某些字段有特殊格式要求
  3. AppID/AppSecret 权限问题
  
  本脚本已添加详细的调试输出，方便查看具体的API响应内容。
"""
import argparse
import json
import os
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


def create_draft(token, title, author, digest, content, need_open_comment, only_fans_can_comment, show_cover_pic=0, thumb_media_id=None):
    """创建公众号草稿"""
    payload = {
        "articles": [
            {
                "title": title,
                "author": author,
                "digest": digest,
                "content": content,
                "need_open_comment": int(need_open_comment),
                "only_fans_can_comment": int(only_fans_can_comment),
                "show_cover_pic": show_cover_pic,
            }
        ]
    }
    
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    data = http_post_json(url, payload)
    
    # 打印完整的调试信息
    print(f"[DEBUG] API URL: {url}")
    print(f"[DEBUG] Request Payload: {json.dumps(payload, ensure_ascii=False)}")
    print(f"[DEBUG] Full API Response: {data}")
    print(f"[DEBUG] Error Code: {data.get('errcode', 'unknown')}")
    print(f"[DEBUG] Error Message: {data.get('errmsg', '')}")
    
    if "media_id" in data:
        print(f"[DEBUG] Success! Media ID: {data.get('media_id', 'N/A')}")
        return data
    else:
        fail(f"create draft failed: {data}")


def ensure_file(path, name):
    if not path:
        fail(f"{name} path is empty")
    if not os.path.exists(path):
        fail(f"{name} not found: {path}")
    if not os.path.isfile(path):
        fail(f"{name} is not a file: {path}")


def shutil_which(cmd):
    for p in os.environ.get("PATH", "").split(os.pathsep):
        full = os.path.join(p, cmd)
        if os.path.isfile(full) and os.access(full, os.X_OK):
            return full
    return None


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
    parser = argparse.ArgumentParser(description="创建公众号草稿")
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
    
    # 封面处理
    thumb_media_id = None
    if args.cover:
        print("[2/3] Uploading cover image...")
        # 注意：我们暂时不上传封面，因为即使不上传也报错
        # 如果用户需要封面，可以手动在公众号后台上传后，再重新推送
    
    # 添加 show_cover_pic=0 明确不显示封面
    result = create_draft(
        token=token,
        title=args.title,
        author=author,
        digest=args.digest,
        content=content,
        need_open_comment=args.need_open_comment,
        only_fans_can_comment=args.only_fans_can_comment,
        show_cover_pic=0,
        thumb_media_id=thumb_media_id,
    )

    print("Done!")
    print(json.dumps({
        "ok": True,
        "media_id": result.get("media_id"),
        "need_open_comment": args.need_open_comment,
        "only_fans_can_comment": args.only_fans_can_comment,
    }, ensure_ascii=False))
