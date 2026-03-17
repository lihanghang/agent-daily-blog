#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公告订阅推送 API 包装脚本
用于通过自然语言或命令行管理公告订阅
"""

import requests
import json
import sys
from typing import Optional, List, Dict

API_BASE = "http://39.104.68.74:8452"
API_KEY = "mk_6b06aedefda608f513dd02599ff04c56"


def get_headers():
    """获取请求头"""
    return {"X-API-Key": API_KEY, "Content-Type": "application/json"}


def list_subscriptions(page: int = 1, page_size: int = 20) -> Dict:
    """
    查看所有订阅

    Args:
        page: 页码
        page_size: 每页数量

    Returns:
        订阅列表
    """
    response = requests.get(
        f"{API_BASE}/api/v1/subscriptions",
        params={"page": page, "page_size": page_size},
        headers=get_headers()
    )
    return response.json()


def create_subscription(
    sub_type: str,
    notify_method: str,
    notify_target: str,
    category_code: Optional[str] = None,
    category_name: Optional[str] = None,
    company_code: Optional[str] = None,
    company_name: Optional[str] = None,
    digest_time: Optional[str] = None
) -> Dict:
    """
    创建订阅

    Args:
        sub_type: 订阅类型 (company/category/company_category/daily_digest)
        notify_method: 通知方式 (email/dingtalk/feishu)
        notify_target: 通知目标 (邮箱地址或 Webhook URL)
        category_code: 类别代码
        category_name: 类别名称
        company_code: 公司代码
        company_name: 公司名称
        digest_time: 每日推送时间 (HH:MM，仅 daily_digest 使用)

    Returns:
        创建结果
    """
    data = {
        "sub_type": sub_type,
        "notify_method": notify_method,
        "notify_target": notify_target
    }

    if category_code:
        data["category_code"] = category_code
    if category_name:
        data["category_name"] = category_name
    if company_code:
        data["company_code"] = company_code
    if company_name:
        data["company_name"] = company_name
    if digest_time:
        data["digest_time"] = digest_time

    response = requests.post(
        f"{API_BASE}/api/v1/subscriptions",
        headers=get_headers(),
        json=data
    )
    return response.json()


def delete_subscription(subscription_id: int) -> Dict:
    """
    删除订阅

    Args:
        subscription_id: 订阅 ID

    Returns:
        删除结果
    """
    response = requests.delete(
        f"{API_BASE}/api/v1/subscriptions/{subscription_id}",
        headers=get_headers()
    )
    return response.json()


def update_subscription(
    subscription_id: int,
    is_active: Optional[bool] = None,
    notify_method: Optional[str] = None,
    notify_target: Optional[str] = None
) -> Dict:
    """
    更新订阅

    Args:
        subscription_id: 订阅 ID
        is_active: 是否激活
        notify_method: 通知方式
        notify_target: 通知目标

    Returns:
        更新结果
    """
    data = {}
    if is_active is not None:
        data["is_active"] = is_active
    if notify_method is not None:
        data["notify_method"] = notify_method
    if notify_target is not None:
        data["notify_target"] = notify_target

    response = requests.put(
        f"{API_BASE}/api/v1/subscriptions/{subscription_id}",
        headers=get_headers(),
        json=data
    )
    return response.json()


def get_available_categories() -> Dict:
    """
    获取可订阅类别

    Returns:
        类别列表
    """
    response = requests.get(
        f"{API_BASE}/api/v1/subscriptions/available-categories",
        headers=get_headers()
    )
    return response.json()


def get_available_companies(keyword: Optional[str] = None, page: int = 1, page_size: int = 20) -> Dict:
    """
    获取可订阅公司

    Args:
        keyword: 搜索关键词
        page: 页码
        page_size: 每页数量

    Returns:
        公司列表
    """
    params = {"page": page, "page_size": page_size}
    if keyword:
        params["keyword"] = keyword

    response = requests.get(
        f"{API_BASE}/api/v1/subscriptions/available-companies",
        headers=get_headers(),
        params=params
    )
    return response.json()


def format_subscriptions(result: Dict) -> str:
    """
    格式化订阅列表输出

    Args:
        result: API 返回结果

    Returns:
        格式化后的字符串
    """
    if result.get("code") != 200:
        return f"❌ 错误: {result.get('message')}"

    items = result.get("data", {}).get("items", [])
    if not items:
        return "暂无订阅"

    lines = ["📋 我的订阅列表\n"]
    lines.append("-" * 80)
    lines.append(f"{'ID':<5} {'类型':<12} {'类别':<25} {'通知方式':<10} {'状态'}")
    lines.append("-" * 80)

    for sub in items:
        type_name = {
            "company": "公司订阅",
            "category": "类别订阅",
            "company_category": "精准订阅",
            "daily_digest": "每日聚合"
        }.get(sub.get("sub_type"), sub.get("sub_type"))

        category = sub.get("category_name", "") or sub.get("company_name", "N/A")
        category = category[:25] if len(category) > 25 else category

        status = "✅" if sub.get("is_active") else "❌"

        lines.append(
            f"{sub.get('subscription_id'):<5} {type_name:<12} {category:<25} "
            f"{sub.get('notify_method', ''):<10} {status}"
        )

    lines.append("-" * 80)
    lines.append(f"总计: {len(items)} 个订阅")

    return "\n".join(lines)


def format_categories(result: Dict) -> str:
    """
    格式化类别列表输出

    Args:
        result: API 返回结果

    Returns:
        格式化后的字符串
    """
    if result.get("code") != 200:
        return f"❌ 错误: {result.get('message')}"

    items = result.get("data", {}).get("items", [])
    if not items:
        return "暂无可用类别"

    lines = ["📂 可订阅类别\n"]
    lines.append("-" * 80)
    lines.append(f"{'类别代码':<45} {'类别名称':<20} {'准确率':<10}")
    lines.append("-" * 80)

    for cat in items:
        code = cat.get("category_code", "")
        code = code[:45] if len(code) > 45 else code

        name = cat.get("category_name", "")
        name = name[:20] if len(name) > 20 else name

        accuracy = f"{cat.get('accuracy_rate', 0) * 100:.2f}%"

        lines.append(f"{code:<45} {name:<20} {accuracy:<10}")

    lines.append("-" * 80)
    lines.append(f"总计: {len(items)} 个类别")

    return "\n".join(lines)


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python api_wrapper.py list                          # 查看订阅列表")
        print("  python api_wrapper.py categories                   # 查看可订阅类别")
        print("  python api_wrapper.py companies [keyword]          # 搜索公司")
        print("  python api_wrapper.py create <type> <method> <target> [category_code] [category_name]")
        print("  python api_wrapper.py delete <subscription_id>")
        print("\n示例:")
        print("  python api_wrapper.py create category email lihanghang@memect.co 人事变动 人事变动")
        print("  python api_wrapper.py delete 7")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        result = list_subscriptions()
        print(format_subscriptions(result))

    elif command == "categories":
        result = get_available_categories()
        print(format_categories(result))

    elif command == "companies":
        keyword = sys.argv[2] if len(sys.argv) > 2 else None
        result = get_available_companies(keyword=keyword)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "create":
        if len(sys.argv) < 5:
            print("用法: python api_wrapper.py create <type> <method> <target> [category_code] [category_name]")
            sys.exit(1)

        sub_type = sys.argv[2]
        notify_method = sys.argv[3]
        notify_target = sys.argv[4]
        category_code = sys.argv[5] if len(sys.argv) > 5 else None
        category_name = sys.argv[6] if len(sys.argv) > 6 else None

        result = create_subscription(
            sub_type=sub_type,
            notify_method=notify_method,
            notify_target=notify_target,
            category_code=category_code,
            category_name=category_name
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "delete":
        if len(sys.argv) < 3:
            print("用法: python api_wrapper.py delete <subscription_id>")
            sys.exit(1)

        subscription_id = int(sys.argv[2])
        result = delete_subscription(subscription_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
