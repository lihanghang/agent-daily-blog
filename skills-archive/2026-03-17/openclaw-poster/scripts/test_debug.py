#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本
"""
import subprocess
import sys
from datetime import date

SCRIPT_DIR = "/home/openclaw/.openclaw/workspace/skills/openclaw-poster/scripts"
FETCH_SCRIPT = f"{SCRIPT_DIR}/fetch_and_format.py"

today = date.today().isoformat()
print(f"测试日期: {today}")

# 测试第一个公告类型
infotype = "O_临时公告_股东大会召开通知"

print(f"\n{'='*60}")
print(f"处理: {infotype}")
print(f"{'='*60}")

cmd_fetch = [
    "python3",
    FETCH_SCRIPT,
    "--infotype", infotype,
    "--start_date", today,
    "--end_date", today,
]

print(f"[DEBUG] 命令: {' '.join(cmd_fetch)}")
print(f"[INFO] 获取公告数据...")

result = subprocess.run(cmd_fetch, capture_output=True, text=True)

print(f"[DEBUG] 返回码: {result.returncode}")
print(f"[DEBUG] stdout 长度: {len(result.stdout)}")
print(f"[DEBUG] stderr 长度: {len(result.stderr)}")
print(f"[DEBUG] stdout 内容:")
print(result.stdout[:500] if result.stdout else "(空)")
print(f"[DEBUG] stderr 内容:")
print(result.stderr[:500] if result.stderr else "(空)")

if result.returncode == 0 and result.stdout.strip():
    print(f"[SUCCESS] 获取成功")
else:
    print(f"[FAIL] 获取失败或无数据")
