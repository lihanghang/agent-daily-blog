#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公告推送 Webhook 接收服务（简化版 - 使用 Python 内置 http.server）
接收公告订阅 API 的推送，并进行处理
"""

import json
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
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


class WebhookHandler(BaseHTTPRequestHandler):
    """Webhook 请求处理器"""

    def send_json_response(self, status_code, data):
        """发送 JSON 响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/webhook/health':
            # 健康检查
            self.send_json_response(200, {
                "status": "healthy",
                "service": "announcement-webhook",
                "timestamp": datetime.now().isoformat()
            })

        elif parsed_path.path == '/webhook/stats':
            # 统计信息
            try:
                today = datetime.now().strftime("%Y-%m-%d")
                filename = LOG_DIR / f"announcements-{today}.jsonl"

                if filename.exists():
                    with open(filename, "r", encoding="utf-8") as f:
                        count = len(f.readlines())
                else:
                    count = 0

                self.send_json_response(200, {
                    "status": "success",
                    "date": today,
                    "count": count,
                    "log_file": str(filename)
                })
            except Exception as e:
                self.send_json_response(500, {"status": "error", "message": str(e)})

        elif parsed_path.path == '/':
            # 根路径
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b"""
<!DOCTYPE html>
<html>
<head>
    <title>公告推送 Webhook 服务</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>📬 公告推送 Webhook 服务</h1>
    <p>服务运行正常</p>
    <h2>可用端点：</h2>
    <ul>
        <li><code>POST /webhook/announcement</code> - 接收公告推送</li>
        <li><code>GET  /webhook/health</code> - 健康检查</li>
        <li><code>GET  /webhook/stats</code> - 统计信息</li>
    </ul>
</body>
</html>
            """)

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """处理 POST 请求"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/webhook/announcement':
            try:
                # 读取请求体
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')

                content_type = self.headers.get('Content-Type', '')

                # 解析数据
                if 'application/json' in content_type:
                    data = json.loads(body) if body else {}
                else:
                    # 尝试解析表单数据
                    data = parse_qs(body)
                    if not data:
                        data = body

                logger.info(f"📬 收到推送 - Content-Type: {content_type}")
                logger.info(f"📋 数据内容: {str(data)[:500]}...")

                # 处理公告
                process_announcement(data)

                # 返回成功响应
                self.send_json_response(200, {
                    "status": "success",
                    "message": "公告已接收并处理",
                    "received_at": datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"❌ 处理推送失败: {e}")
                self.send_json_response(500, {
                    "status": "error",
                    "message": str(e)
                })

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """自定义日志输出"""
        logger.info(f"{self.address_string()} - {format % args}")


def run_server(host='0.0.0.0', port=5000):
    """启动服务器"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, WebhookHandler)

    logger.info("🚀 公告推送 Webhook 服务启动")
    logger.info(f"📂 日志目录: {LOG_DIR}")
    logger.info(f"🔗 服务地址: http://{host}:{port}")
    logger.info("🔗 端点:")
    logger.info("   - POST /webhook/announcement  (接收公告推送)")
    logger.info("   - GET  /webhook/health        (健康检查)")
    logger.info("   - GET  /webhook/stats         (统计信息)")
    logger.info("\n⚠️  提醒: 请使用 tunnel 工具暴露到公网，例如:")
    logger.info("   tunnel --port 5000")
    logger.info("   ngrok http 5000")
    logger.info("   lt --port 5000")
    logger.info("\n按 Ctrl+C 停止服务")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n🛑 服务已停止")
        httpd.shutdown()


if __name__ == "__main__":
    run_server()
