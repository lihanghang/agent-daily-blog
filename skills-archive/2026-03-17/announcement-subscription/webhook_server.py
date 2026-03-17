#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公告推送 Webhook 接收服务
接收公告订阅 API 的推送，并进行处理
"""

import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from pathlib import Path

# 配置
LOG_DIR = Path.home() / ".openclaw" / "workspace" / "memory" / "announcements"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def save_announcement(data):
    """保存公告到文件"""
    try:
        # 按日期保存
        today = datetime.now().strftime("%Y-%m-%d")
        filename = LOG_DIR / f"announcements-{today}.jsonl"

        # 添加接收时间
        if isinstance(data, dict):
            data["received_at"] = datetime.now().isoformat()
        else:
            data = {
                "raw_data": data,
                "received_at": datetime.now().isoformat()
            }

        # 追加到文件（JSONL 格式）
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

        logger.info(f"✅ 公告已保存到 {filename}")
        return True
    except Exception as e:
        logger.error(f"❌ 保存公告失败: {e}")
        return False


def log_announcement(data):
    """记录公告到内存日志"""
    try:
        memory_file = Path.home() / ".openclaw" / "workspace" / "memory" / f"{datetime.now().strftime('%Y-%m-%d')}.md"

        if isinstance(data, dict):
            company = data.get("company_name", "未知公司")
            title = data.get("title", data.get("公告标题", "未知标题"))
            category = data.get("category_name", data.get("公告类别", "未知类别"))
            url = data.get("url", "")
            content = data.get("content", data.get("公告内容", ""))[:200]  # 只取前200字
        else:
            company = "未知公司"
            title = str(data)[:50]
            category = "未知类别"
            url = ""
            content = str(data)[:200]

        log_entry = f"""
## {datetime.now().strftime('%H:%M')} - 收到公告推送

- **公司**: {company}
- **标题**: {title}
- **类别**: {category}
- **摘要**: {content}...
- **链接**: {url}
- **接收时间**: {datetime.now().isoformat()}
"""

        with open(memory_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

        logger.info("✅ 已记录到内存日志")
        return True
    except Exception as e:
        logger.error(f"❌ 记录内存日志失败: {e}")
        return False


def process_announcement(data):
    """处理公告数据"""
    # 1. 保存到文件
    save_announcement(data)

    # 2. 记录到内存日志
    log_announcement(data)

    # 3. 这里可以添加更多处理逻辑
    #    - 发送到飞书/钉钉
    #    - 生成分析报告
    #    - 触发其他任务

    return True


@app.route("/webhook/announcement", methods=["POST"])
def webhook_announcement():
    """接收公告推送"""
    try:
        # 获取推送数据
        content_type = request.content_type

        if "application/json" in content_type:
            data = request.get_json()
        else:
            # 尝试解析表单数据
            data = request.form.to_dict()
            if not data:
                # 如果都不是，尝试获取原始数据
                data = request.get_data(as_text=True)

        logger.info(f"📬 收到推送 - Content-Type: {content_type}")
        logger.info(f"📋 数据内容: {json.dumps(data, ensure_ascii=False)[:500]}...")

        # 处理公告
        process_announcement(data)

        # 返回成功响应
        return jsonify({
            "status": "success",
            "message": "公告已接收并处理",
            "received_at": datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"❌ 处理推送失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/webhook/health", methods=["GET"])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "announcement-webhook",
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route("/webhook/stats", methods=["GET"])
def stats():
    """统计信息"""
    try:
        # 统计今天收到的公告数量
        today = datetime.now().strftime("%Y-%m-%d")
        filename = LOG_DIR / f"announcements-{today}.jsonl"

        if filename.exists():
            with open(filename, "r", encoding="utf-8") as f:
                count = len(f.readlines())
        else:
            count = 0

        return jsonify({
            "status": "success",
            "date": today,
            "count": count,
            "log_file": str(filename)
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    logger.info("🚀 公告推送 Webhook 服务启动")
    logger.info(f"📂 日志目录: {LOG_DIR}")
    logger.info("🔗 端点:")
    logger.info("   - POST /webhook/announcement  (接收公告推送)")
    logger.info("   - GET  /webhook/health        (健康检查)")
    logger.info("   - GET  /webhook/stats         (统计信息)")
    logger.info("\n⚠️  提醒: 请使用 tunnel 工具暴露到公网，例如:")
    logger.info("   tunnel --port 5000")
    logger.info("   ngrok http 5000")

    # 启动服务
    app.run(host="0.0.0.0", port=5000, debug=False)
