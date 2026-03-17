#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章技能入口
支持：文章创作、排版、草稿推送（不包含封面生成，因系统无 Pillow）
"""
import os
import sys
import json
import subprocess

# 配置文件路径
CONFIG_FILE = "/home/openclaw/.openclaw/workspace/skills/wechat-article-skill/wechat-article.config.json"
SCRIPTS_DIR = "/home/openclaw/.openclaw/workspace/skills/wechat-article-skill/scripts"
ASSETS_DIR = "/home/openclaw/.openclaw/workspace/skills/wechat-article-skill/assets"

def load_config():
    """加载配置"""
    if not os.path.exists(CONFIG_FILE):
        return None

    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"✅ 配置已保存到 {CONFIG_FILE}")

def init_config():
    """首次初始化配置"""
    print("🔧 首次使用，需要配置公众号信息")
    print("请提供以下信息：")
    print()
    print("1. 公众号 AppID: ", end="")
    appid = input().strip()
    print()
    print("2. 公众号 AppSecret: ", end="")
    appsecret = input().strip()
    print()
    print("3. 默认作者名: ", end="")
    author = input().strip() or "虾说"
    print()
    print("4. 写作风格视角: ", end="")
    print("   - 第一人称")
    print("   - 第三人称")
    perspective = input().strip() or "第一人称"
    print()
    print("5. 写作语气: ", end="")
    print("   - 口语化")
    print("   - 正式")
    print("   - 幽默")
    tone = input().strip() or "口语化"
    print()
    print("6. 文章长度: ", end="")
    print("   - 短篇（800-1200字）")
    print("   - 中篇（1500-2500字）")
    print("   - 长篇（2500+字）")
    length = input().strip() or "1500-2500字"
    print()
    print("7. 是否开放评论（1=开放，0=关闭）: ", end="")
    need_open_comment = input().strip() or "1"
    print()

    # 默认封面策略（暂时用内置预览图）
    preview_path = os.path.join(ASSETS_DIR, "cover-style-palette-preview-grid.jpg")

    config = {
        "appid": appid,
        "appsecret": appsecret,
        "author": author,
        "writing": {
            "perspective": perspective,
            "tone": tone,
            "length": length,
            "direction": "科技/AI",
            "keywords_style": "短句为主，一行不超过30字"
        },
        "publish": {
            "need_open_comment": int(need_open_comment),
            "only_fans_can_comment": 0
        },
        "cover": {
            "default_style": "minimal-grid",
            "palette": "auto",
            "rotate": "sequential",
            "seed": "title",
            "use_preview": True
        },
        "preview": {
            "send_cover_preview": 1,
            "require_confirm_before_publish": 1,
            "confirm_keyword": "确认发布"
        }
    }

    save_config(config)
    return config

def create_article(topic, config):
    """创建文章（调用子脚本）"""
    # 先生成简单 HTML，不包含封面
    script_path = os.path.join(SCRIPTS_DIR, "create_article.py")

    # 参数
    cmd = [
        "python3",
        script_path,
        "--topic", topic,
        "--author", config["author"],
        "--perspective", config["writing"]["perspective"],
        "--tone", config["writing"]["tone"],
        "--length", config["writing"]["length"]
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ 文章生成失败: {result.stderr}")
        return None, None

    print("✅ 文章内容已生成")

    # 解析输出
    output_lines = result.stdout.strip().split('\n')
    title = output_lines[0].replace("TITLE:", "").strip()
    digest = output_lines[1].replace("DIGEST:", "").strip() if len(output_lines) > 1 else ""
    html_path = output_lines[2].replace("HTML:", "").strip() if len(output_lines) > 2 else None

    return title, digest, html_path

def publish_draft(title, digest, content_file, cover_file, config):
    """推送到草稿箱"""
    script_path = os.path.join(SCRIPTS_DIR, "publish_draft.py")

    cmd = [
        "python3",
        script_path,
        "--title", title,
        "--author", config["author"],
        "--digest", digest,
        "--content-file", content_file,
        "--cover", cover_file,
        "--appid", config["appid"],
        "--appsecret", config["appsecret"],
        "--need-open-comment", str(config["publish"]["need_open_comment"]),
        "--only-fans-can-comment", "0"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ 推送失败: {result.stderr}")
        return None

    output_lines = result.stdout.strip().split('\n')
    media_id = None
    for line in output_lines:
        if line.startswith("MEDIA_ID:"):
            media_id = line.replace("MEDIA_ID:", "").strip()

    print(f"✅ 草稿已推送到公众号后台")
    print(f"📝 Media ID: {media_id}")
    print(f"🔗 下一步：进入公众号后台「内容管理 → 草稿箱」预览并发布")

    return media_id

def main():
    import argparse

    parser = argparse.ArgumentParser(description='微信公众号文章创作与草稿推送')
    parser.add_argument('topic', nargs='?', help='文章主题')
    parser.add_argument('--init', action='store_true', help='初始化配置')
    parser.add_argument('--publish', action='store_true', help='推送到草稿箱')
    parser.add_argument('--title', help='文章标题（发布时）')
    parser.add_argument('--content', help='文章内容（发布时）')
    parser.add_argument('--cover', help='封面图片路径（发布时）')

    args = parser.parse_args()

    # 初始化配置
    if args.init:
        init_config()
        return

    # 加载配置
    config = load_config()
    if not config:
        print("❌ 配置文件不存在，请先运行 --init")
        print(f"   配置文件: {CONFIG_FILE}")
        return

    # 推送到草稿箱
    if args.publish:
        if not args.title or not args.content:
            print("❌ --publish 需要 --title 和 --content")
            return

        cover_file = args.cover or os.path.join(ASSETS_DIR, "cover-style-palette-preview-grid.jpg")

        print(f"📤 推送草稿...")
        publish_draft(args.title, "", args.content, cover_file, config)
        return

    # 创建文章
    if args.topic:
        print(f"📝 正在创作文章: {args.topic}")

        title, digest, html_path = create_article(args.topic, config)

        if title and html_path:
            print()
            print("="*60)
            print("文章预览:")
            print("="*60)
            print(f"标题: {title}")
            print(f"摘要: {digest}")
            print(f"HTML文件: {html_path}")
            print()
            print("="*60)

            # 读取内容并显示前几段
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()

            print("正文预览（前 200 字符）:")
            print(content[:200] + "...")
            print()
            print("="*60)
            print("📤 推送命令:")
            print(f"python3 {sys.argv[0]} --publish --title \"{title}\" --content {html_path}")
            print("="*60)
        return

    # 默认提示
    print("用法:")
    print(f"  首次配置: python3 {sys.argv[0]} --init")
    print(f"  创作文章: python3 {sys.argv[0]} \"文章主题\"")
    print(f"  推送草稿: python3 {sys.argv[0]} --publish --title \"标题\" --content <html文件>")

if __name__ == '__main__':
    main()
