#!/usr/bin/env python3
"""
微信公众号文章抓取脚本
支持图文文章和视频号抓取
"""

import requests
import json
import sys
import re
from urllib.parse import urlparse, parse_qs

def fetch_wechat_article(url):
    """
    抓取微信公众号文章

    Args:
        url: 文章链接

    Returns:
        dict: 包含标题、作者、正文、配图等信息
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        html = response.text

        # 判断是否为视频号
        if 'mp.weixin.qq.com/mp/videoplayer' in url or '__biz=' not in url:
            return extract_video_article(html, url)

        # 图文文章
        return extract_text_article(html, url)

    except Exception as e:
        return {
            'error': str(e),
            'url': url
        }

def extract_text_article(html, url):
    """提取图文文章内容"""
    import re
    from html import unescape

    # 提取标题
    title_match = re.search(r'<meta\s+property="og:title"\s+content="([^"]*)"', html)
    title = unescape(title_match.group(1)) if title_match else "未知标题"

    # 提取作者
    author_match = re.search(r'<meta\s+name="author"\s+content="([^"]*)"', html)
    author = unescape(author_match.group(1)) if author_match else "未知作者"

    # 提取正文
    content_div = re.search(r'<div\s+id="js_content"[^>]*>(.*?)</div>', html, re.DOTALL)
    content = ""
    images = []

    if content_div:
        content_html = content_div.group(1)
        # 提取图片
        img_pattern = r'<img[^>]+data-src="([^"]+)"[^>]*>'
        for match in re.finditer(img_pattern, content_html):
            img_url = match.group(1)
            images.append(img_url)

        # 移除HTML标签，提取纯文本
        content = re.sub(r'<[^>]+>', '\n', content_html)
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = unescape(content).strip()

    return {
        'title': title,
        'author': author,
        'type': '图文文章',
        'url': url,
        'content': content,
        'images': images,
        'image_count': len(images)
    }

def extract_video_article(html, url):
    """提取视频号信息"""
    import re
    from html import unescape

    # 尝试提取标题
    title_match = re.search(r'<meta\s+property="og:title"\s+content="([^"]*)"', html)
    title = unescape(title_match.group(1)) if title_match else "视频号视频"

    # 尝试提取描述
    desc_match = re.search(r'<meta\s+property="og:description"\s+content="([^"]*)"', html)
    description = unescape(desc_match.group(1)) if desc_match else ""

    return {
        'title': title,
        'author': '视频号',
        'type': '视频号',
        'url': url,
        'content': description or "视频内容，无法直接获取",
        'images': [],
        'image_count': 0
    }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 fetch_wechat_article.py <wechat_url>")
        sys.exit(1)

    url = sys.argv[1]
    result = fetch_wechat_article(url)

    # 输出JSON格式
    print(json.dumps(result, ensure_ascii=False, indent=2))
