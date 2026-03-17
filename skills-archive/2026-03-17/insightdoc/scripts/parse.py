#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InsightDoc 文档解析入口脚本

用法:
  # 解析本地文件
  python parse.py --file report.pdf --type docparse --format md

  # 解析远程 URL
  python parse.py --url https://example.com/report.pdf --format md

  # 查询已有任务
  python parse.py --task-id abc123 --format md
"""

import argparse
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

# 支持从 .env 文件加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv 未安装时，尝试手动读取 .env
    _env_file = Path(__file__).resolve().parents[3] / ".env"
    if _env_file.exists():
        for line in _env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

from client import InsightDocClient

SKILL_PATH = Path(__file__).resolve().parent.parent / "SKILL.md"


def record_experience(error_type: str, detail: str) -> None:
    """将异常经验追加到 SKILL.md"""
    if not SKILL_PATH.exists():
        return
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n- **[{ts}]** `{error_type}`: {detail}\n"
    with open(SKILL_PATH, "a", encoding="utf-8") as f:
        f.write(entry)


def resolve_api_key(args_key: str | None) -> str:
    """按优先级解析 API Key: 命令行参数 > 环境变量"""
    key = args_key or os.environ.get("INSIGHTDOC_API_KEY", "")
    if not key:
        print("❌ 未找到 API Key，请通过以下方式之一配置：")
        print("   1. 环境变量: export INSIGHTDOC_API_KEY='sk-xxx'")
        print("   2. .env 文件: INSIGHTDOC_API_KEY=sk-xxx")
        print("   3. 命令行:   --api-key sk-xxx")
        sys.exit(1)
    return key


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="InsightDoc 文档解析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # 输入源（三选一）
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="本地文件路径 (PDF/JPG/PNG)")
    source.add_argument("--url", help="远程文件 URL")
    source.add_argument("--task-id", help="已有任务 ID，直接查询结果")

    # 解析参数
    p.add_argument("--type", choices=["docparse", "finance_ocr"], default="docparse",
                   help="任务类型 (默认: docparse)")
    p.add_argument("--format", dest="fmt",
                   help="输出格式: md/html/block_md/docx (通用) 或 matrix/normalization (财报)")
    p.add_argument("--version", help="解析版本 (如 v1, v2)，仅通用解析有效")
    p.add_argument("--output", help="结果保存路径 (默认输出到 stdout)")
    p.add_argument("--api-key", help="临时指定 API Key (覆盖环境变量)")
    return p


def main() -> None:
    args = build_parser().parse_args()
    api_key = resolve_api_key(args.api_key)
    client = InsightDocClient(api_key=api_key)

    try:
        task_id = args.task_id

        # ── 步骤 1: 创建任务（如果没有 task_id）──
        if not task_id:
            file_path = args.file
            if args.url:
                print(">>> 下载远程文件...")
                file_path = InsightDocClient.download_file(args.url)

            print(f">>> 创建任务: type={args.type}, file={Path(file_path).name}")
            task_res = client.create_task(file_path, task_type=args.type)
            task_id = task_res.get("id")
            print(f">>> 任务已创建: {task_id}")

            # 等待完成
            print(">>> 等待解析完成...")
            client.wait_for_completion(task_id)

        # ── 步骤 2: 查询结果 ──
        extra_info = None
        if args.version:
            extra_info = {"parse_version": args.version}

        print(f">>> 查询结果: format={args.fmt or '默认'}, version={args.version or '默认'}")
        result = client.get_task_detail(task_id, result_type=args.fmt, extra_info=extra_info)

        # ── 步骤 3: 输出 ──
        output_text = json.dumps(result, ensure_ascii=False, indent=2)

        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output_text, encoding="utf-8")
            print(f"\n✅ 结果已保存: {out_path}")
        else:
            print("\n" + "=" * 50)
            print(output_text)
            print("=" * 50)

        print(f"\n✅ 解析完成 | task_id={task_id}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        record_experience(type(e).__name__, str(e))
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
