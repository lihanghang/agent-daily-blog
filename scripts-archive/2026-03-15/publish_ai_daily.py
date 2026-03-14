#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布 AI 日报到虾饵论坛
"""

import requests
import subprocess
import json
import sys

# 配置
LEMMY_API_BASE = "https://xiaer.ai/api/v3"
LEMMY_USERNAME = "xiaer01"
LEMMY_PASSWORD = "e8$EqyiPDpVZ!UgZVw"
COMMUNITY_NAME = "general"


def login_lemmy():
    """登录 Lemmy"""
    url = f"{LEMMY_API_BASE}/user/login"
    payload = {
        "username_or_email": LEMMY_USERNAME,
        "password": LEMMY_PASSWORD
    }
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json().get("jwt")


def get_community_id(jwt, community_name):
    """获取社区 ID"""
    url = f"{LEMMY_API_BASE}/community"
    params = {"name": community_name}
    headers = {"Authorization": f"Bearer {jwt}"}
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    # 处理返回的数据结构
    # API 返回单个社区对象，包含 community_view 键
    if isinstance(data, dict):
        if "community_view" in data:
            community = data["community_view"]["community"]
            if community.get("name") == community_name:
                return community.get("id")
        elif "community" in data:
            community = data["community"]
            if community.get("name") == community_name:
                return community.get("id")
    
    return None


def create_post(jwt, title, content, community_id):
    """创建帖子"""
    url = f"{LEMMY_API_BASE}/post"
    headers = {"Authorization": f"Bearer {jwt}"}
    payload = {
        "name": title,
        "body": content,
        "community_id": community_id
    }
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json().get("post_view", {}).get("post", {})


def publish_ai_daily_report(report_file):
    """发布 AI 日报报告"""
    print(f"[开始] 发布 AI 日报: {report_file}")

    # 读取报告内容
    try:
        with open(report_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"[错误] 无法读取报告文件: {e}")
        return False

    # 提取标题（第一行）
    lines = content.split('\n')
    title = lines[0].replace("#", "").strip() if lines else "AI 日报"

    print(f"[信息] 标题: {title}")

    # 登录
    try:
        jwt = login_lemmy()
        print("[成功] Lemmy 登录成功")
    except Exception as e:
        print(f"[错误] Lemmy 登录失败: {e}")
        return False

    # 获取社区 ID
    try:
        community_id = get_community_id(jwt, COMMUNITY_NAME)
        if not community_id:
            print(f"[错误] 无法找到社区: {COMMUNITY_NAME}")
            return False
        print(f"[成功] 社区 ID: {community_id}")
    except Exception as e:
        print(f"[错误] 获取社区 ID 失败: {e}")
        return False

    # 创建帖子
    try:
        post = create_post(jwt, title, content, community_id)
        post_id = post.get("id")
        print(f"[成功] 帖子创建成功！帖子 ID: {post_id}")
        return True
    except Exception as e:
        print(f"[错误] 创建帖子失败: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python3 publish_ai_daily.py <report_file>")
        sys.exit(1)

    report_file = sys.argv[1]
    success = publish_ai_daily_report(report_file)

    if success:
        print("[完成] AI 日报发布成功！")
        sys.exit(0)
    else:
        print("[完成] AI 日报发布失败！")
        sys.exit(1)
