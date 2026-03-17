#!/usr/bin/env python3
"""
端到端提取流程脚本

用法:
    # 完整流程：上传 → Schema 设计 → 提取 → 归档
    python extract_flow.py full --files doc1.pdf doc2.pdf --schema-prompt "提取论文标题和作者"

    # 仅上传文档
    python extract_flow.py upload --files doc1.pdf doc2.pdf

    # 基于已有 session 提取新文档
    python extract_flow.py extract --session-id 1 --doc-ids abc123 def456

    # 对话修正
    python extract_flow.py correct --batch-id 1 --message "作者列表不完整，请重新提取"

    # 归档
    python extract_flow.py archive --batch-id 1

    # 查看历史
    python extract_flow.py history --session-id 1

环境变量:
    EXTRACT_API_URL    - API 地址 (默认 http://192.168.41.78)
    EXTRACT_USERNAME   - 用户名
    EXTRACT_PASSWORD   - 密码
    EXTRACT_TOKEN      - 直接提供 token（跳过登录）
"""

import argparse
import json
import os
import sys
from pathlib import Path

# 将 scripts 目录加入 path
sys.path.insert(0, str(Path(__file__).parent))
from client import ExtractEngineClient


def get_client() -> ExtractEngineClient:
    """从环境变量创建已认证的客户端"""
    base_url = os.environ.get("EXTRACT_API_URL", "http://192.168.41.78")
    token = os.environ.get("EXTRACT_TOKEN")

    client = ExtractEngineClient(base_url, token=token)

    if not token:
        username = os.environ.get("EXTRACT_USERNAME")
        password = os.environ.get("EXTRACT_PASSWORD")
        if not username or not password:
            print("错误: 需要设置 EXTRACT_TOKEN 或 EXTRACT_USERNAME + EXTRACT_PASSWORD", file=sys.stderr)
            sys.exit(1)
        client.login(username, password)
        print(f"✓ 已登录: {username}")

    return client


def print_event(event: dict):
    """SSE 事件回调：打印关键事件"""
    etype = event.get("type", "")
    if etype == "message":
        print(f"  AI: {event.get('content', '')[:200]}")
    elif etype == "batch_created":
        print(f"  ✓ Batch ID: {event.get('batch_id')}")
    elif etype == "result_update":
        print(f"  ✓ 结果更新: {len(event.get('content', []))} 条")
    elif etype == "schema_updated":
        print(f"  ✓ Schema 已更新")
    elif etype == "error":
        print(f"  ✗ 错误: {event.get('message')}", file=sys.stderr)
    elif etype == "done":
        print(f"  ✓ 流结束")


def cmd_upload(args, client: ExtractEngineClient):
    """上传文档"""
    docs = client.upload_documents(args.files)
    print(f"✓ 上传成功: {len(docs)} 个文档")
    for d in docs:
        print(f"  - {d['filename']} → {d['document_id']}")
    return docs


def cmd_extract(args, client: ExtractEngineClient):
    """提取文档"""
    result = client.extract(args.session_id, args.doc_ids, on_event=print_event)
    print(f"\n✓ 提取完成 (batch_id={result['batch_id']})")
    print(json.dumps(result["results"], ensure_ascii=False, indent=2))
    return result


def cmd_correct(args, client: ExtractEngineClient):
    """对话修正"""
    result = client.chat_correct(args.batch_id, args.message, on_event=print_event)
    print(f"\n✓ 修正完成")
    print(json.dumps(result["results"], ensure_ascii=False, indent=2))
    return result


def cmd_archive(args, client: ExtractEngineClient):
    """归档"""
    result = client.end_batch(args.batch_id)
    print(f"✓ 已归档 (batch_id={args.batch_id})")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def cmd_history(args, client: ExtractEngineClient):
    """查看历史"""
    results = client.get_history(args.session_id)
    print(f"✓ 历史结果: {len(results)} 条")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return results


def cmd_full(args, client: ExtractEngineClient):
    """完整流程"""
    # 1. 上传
    print("\n[1/5] 上传文档...")
    docs = client.upload_documents(args.files)
    doc_ids = [d["document_id"] for d in docs]
    print(f"✓ 上传 {len(docs)} 个文档: {doc_ids}")

    # 2. Schema 对话
    print("\n[2/5] 设计 Schema...")
    conv_id = client.create_schema_conversation(doc_ids)
    schema_result = client.chat_schema(conv_id, args.schema_prompt, on_event=print_event)

    schema = schema_result.get("schema")
    if not schema:
        conv_state = client.get_schema_conversation(conv_id)
        schema = conv_state.get("current_schema")
    if not schema:
        print("✗ 未能生成 Schema，请手动设计", file=sys.stderr)
        sys.exit(1)
    print(f"✓ Schema: {json.dumps(schema, ensure_ascii=False)[:200]}")

    # 3. 创建 Session
    print("\n[3/5] 创建 Session...")
    session_name = args.session_name or f"提取任务-{Path(args.files[0]).stem}"
    session_id = client.create_session(session_name, schema, doc_ids)
    print(f"✓ Session ID: {session_id}")

    # 4. 提取
    print("\n[4/5] 执行提取...")
    result = client.extract(session_id, doc_ids, on_event=print_event)
    batch_id = result["batch_id"]
    print(f"✓ 提取完成 (batch_id={batch_id})")

    # 5. 归档
    if not args.no_archive:
        print("\n[5/5] 归档...")
        client.end_batch(batch_id)
        print(f"✓ 已归档")

    # 输出结果
    print("\n" + "=" * 60)
    print("提取结果:")
    print(json.dumps(result["results"], ensure_ascii=False, indent=2))
    print(f"\nsession_id={session_id}, batch_id={batch_id}")

    return {"session_id": session_id, "batch_id": batch_id, "results": result["results"]}


def main():
    parser = argparse.ArgumentParser(description="文档提取引擎 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # full
    p = sub.add_parser("full", help="完整流程")
    p.add_argument("--files", nargs="+", required=True, help="PDF 文件路径")
    p.add_argument("--schema-prompt", required=True, help="Schema 设计提示语")
    p.add_argument("--session-name", help="Session 名称")
    p.add_argument("--no-archive", action="store_true", help="不自动归档")

    # upload
    p = sub.add_parser("upload", help="上传文档")
    p.add_argument("--files", nargs="+", required=True, help="PDF 文件路径")

    # extract
    p = sub.add_parser("extract", help="提取文档")
    p.add_argument("--session-id", type=int, required=True)
    p.add_argument("--doc-ids", nargs="+", required=True)

    # correct
    p = sub.add_parser("correct", help="对话修正")
    p.add_argument("--batch-id", type=int, required=True)
    p.add_argument("--message", required=True)

    # archive
    p = sub.add_parser("archive", help="归档")
    p.add_argument("--batch-id", type=int, required=True)

    # history
    p = sub.add_parser("history", help="查看历史")
    p.add_argument("--session-id", type=int, required=True)

    args = parser.parse_args()
    client = get_client()

    try:
        handler = {
            "full": cmd_full,
            "upload": cmd_upload,
            "extract": cmd_extract,
            "correct": cmd_correct,
            "archive": cmd_archive,
            "history": cmd_history,
        }[args.command]
        handler(args, client)
    finally:
        client.close()


if __name__ == "__main__":
    main()
