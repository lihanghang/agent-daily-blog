#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量发布今天的所有公告类型到 Lemmy 论坛。
"""

import os
import subprocess
import sys
import time
from datetime import date

# 所有支持的公告类型（按数量排序，高频在前）
INFOTYPES = [
    "O_临时公告_董事会决议",
    "O_临时公告_应当披露交易的进展",
    "O_临时公告_股东大会召开通知",
    "O_临时公告_应当披露交易的提示",
    "O_临时公告_应当披露交易已完成",
    "O_临时公告_股东大会法律意见书",
    "O_临时公告_股票交易异常波动",
    "O_临时公告_股份被质押",
    "O_临时公告_股东大会决议",
    "O_临时公告_股权激励计划授予",
    "O_临时公告_人事变动",
    "O_临时公告_转债付息",
    "O_临时公告_可转债发行",
    "O_临时公告_购买资产",
    "O_临时公告_回购实施进展",
    "O_临时公告_对外投资",
    "O_临时公告_获得财政补贴",
    "O_临时公告_推选职工董事或者监事",
    "O_临时公告_业绩预告",
    "O_临时公告_变更公司名称",
    "O_临时公告_利润分配",
    "O_临时公告_可转债到期兑付及摘牌",
    "O_临时公告_增加临时提案",
    "O_临时公告_新建项目",
    "O_临时公告_开展套期保值业务",
    "O_临时公告_归还募集资金",
    "O_临时公告_募集资金临时补充流动资金",
    "O_临时公告_股权激励计划终止",
    "O_临时公告_董事会秘书辞职",
    "O_临时公告_重大资产重组终止",
    "O_临时公告_药品批准",
    "O_临时公告_股票交易风险提示",
    "O_临时公告_变更募集资金用途",
    "O_临时公告_提供财务资助",
    "O_临时公告_股票解除限售",
    "O_临时公告_其他股权变动",
    "O_临时公告_出售资产",
    "O_临时公告_变更证券简称",
    "O_临时公告_员工持股计划实施进展",
    "O_临时公告_控股股东或实际控制人发生变动的提示",
    "O_临时公告_法院裁定重整、和解或破产清算",
    "O_临时公告_生产经营数据_601006",
    "O_临时公告_取得发明专利证书",
    "O_临时公告_签署合作协议",
    "O_临时公告_更换持续督导保荐代表人",
    "O_临时公告_子公司注销",
    "O_临时公告_变更会计师事务所",
    "O_临时公告_设立产业基金",
    "O_临时公告_接受财务资助",
    "O_临时公告_股东大会延期",
    "O_临时公告_监事会决议",
    "O_临时公告_发生重大债务或重大债权到期未清偿",
    "O_临时公告_用募集资金置换预先投入的自筹资金",
    "O_临时公告_召开业绩说明会",
    "O_临时公告_取消重大资产重组并复牌",
    "O_临时公告_公告元信息",
    "O_临时公告_中标候选人公示",
    "O_临时公告_与私募基金合作投资",
    "股东大会通知",
    "核心技术人员离职",
    "职工代表大会决议",
    "优先股股息分派",
    "业务资格获批",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FETCH_SCRIPT = os.path.join(SCRIPT_DIR, "fetch_and_format.py")
PUBLISH_SCRIPT = os.path.join(SCRIPT_DIR, "publish_to_lemmy.py")


def publish_infotype(infotype: str, today: str, community: str = "main") -> bool:
    """发布单个公告类型"""
    print(f"\n{'='*60}")
    print(f"处理: {infotype}")
    print(f"{'='*60}")

    # 生成 Markdown 内容
    cmd_fetch = [
        "python3",
        FETCH_SCRIPT,
        "--infotype", infotype,
        "--start_date", today,
        "--end_date", today,
    ]

    print(f"[INFO] 获取公告数据...")
    result = subprocess.run(cmd_fetch, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[WARN] 获取数据失败: {result.stderr}", file=sys.stderr)
        return False

    content = result.stdout

    if not content.strip():
        print(f"[INFO] 今日无数据，跳过")
        return False

    # 从内容中提取标题（第一行或 # 开头的行）
    lines = content.split('\n')
    title = None
    for line in lines[:10]:
        line = line.strip()
        if line.startswith('#'):
            # 去掉 # 号和可能的 emoji
            title = line.lstrip('#').strip()
            # 去掉开头的 emoji（如 📊 📋 等）
            while title and title[0] in ('📊', '📋', '💰', '📑', '💡', '🔍', '📈'):
                title = title[1:].strip()
            break

    if not title:
        title = f"{infotype}公告汇总（{today}）"

    print(f"[INFO] 生成标题: {title}")
    print(f"[INFO] 内容长度: {len(content)} 字符")

    # 发布到 Lemmy（使用管道传递内容，避免参数过长）
    cmd_publish = [
        "python3",
        PUBLISH_SCRIPT,
        "--title", title,
        "--community", community,
    ]

    print(f"[INFO] 发布到 Lemmy...")
    result = subprocess.run(cmd_publish, input=content, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[ERROR] 发布失败: {result.stderr}", file=sys.stderr)
        return False

    print(f"[SUCCESS] 发布成功！")
    return True


def main():
    today = date.today().isoformat()
    community = "general"

    print(f"\n{'='*60}")
    print(f"开始批量发布今日公告")
    print(f"日期: {today}")
    print(f"目标版块: {community}")
    print(f"公告类型数: {len(INFOTYPES)}")
    print(f"预计耗时: {len(INFOTYPES) * 10 / 60:.1f} 分钟")
    print(f"{'='*60}\n")

    success_count = 0
    skip_count = 0
    failed_count = 0

    for idx, infotype in enumerate(INFOTYPES):
        print(f"\n[进度] {idx+1}/{len(INFOTYPES)}")

        try:
            result = publish_infotype(infotype, today, community)
            if result:
                success_count += 1
            else:
                skip_count += 1
        except Exception as e:
            print(f"[ERROR] 处理 {infotype} 时出错: {e}", file=sys.stderr)
            failed_count += 1

        # 每次请求后等待，避免触发速率限制
        # 登录和发帖都会触发请求，所以每次类型之间等待 5 秒
        time.sleep(5)

    print(f"\n{'='*60}")
    print(f"批量发布完成")
    print(f"成功: {success_count} | 跳过(无数据): {skip_count} | 失败: {failed_count}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
