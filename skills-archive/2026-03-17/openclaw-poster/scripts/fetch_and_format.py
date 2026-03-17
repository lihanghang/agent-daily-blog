#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从公告数据接口获取数据，按公司聚合，生成 Markdown 格式的帖子内容。

用法:
    python fetch_and_format.py --infotype "O_临时公告_董事会决议" --start_date 2026-01-14 --end_date 2026-01-16
    python fetch_and_format.py --infotype "O_临时公告_人事变动" --start_date 2026-01-14 --end_date 2026-01-16 --output post.md
    python fetch_and_format.py --infotype "O_临时公告_董事会决议" --start_date 2026-01-14 --end_date 2026-01-16 --api_base http://192.168.41.96:8452
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.parse
from collections import defaultdict
from datetime import date


DEFAULT_API_BASE = "http://39.104.68.74:8452"
PAGE_SIZE = 100


def call_llm_for_analysis(prompt: str, timeout: int = 60) -> dict:
    """调用大语言模型进行公告分析
    
    通过调用子会话来使用自身的模型分析能力
    """
    try:
        # 创建临时提示文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(f"请分析以下公告并返回JSON格式结果：\n\n{prompt}\n\n分析要求：\n1. 返回纯JSON，不要任何其他文字\n2. JSON格式严格符合：{{\"market_overview\": \"...\", \"notable_companies\": [...], \"investment_focus\": \"...\"}}\n3. 市场概况1-2句话\n4. 值得关注的公司最多5家，每家原因20字以内\n5. 投资关注点3-5条，每条20字以内，用分号分隔")
            prompt_file = f.name
        
        # 调用openclaw命令触发子会话（使用subprocess）
        # 注意：这里简化处理，实际可以集成 sessions_spawn API
        # 由于当前环境限制，我们使用规则分析作为后备
        
        print(f"[INFO] LLM分析已准备，使用规则分析作为后备", file=sys.stderr)
        
        return None
        
    except Exception as e:
        print(f"[WARN] LLM调用失败: {e}", file=sys.stderr)
        return None

# infotype 中文显示名映射
INFOTYPE_DISPLAY = {
    "O_临时公告_董事会决议": "董事会决议",
    "O_临时公告_人事变动": "人事变动",
    "O_临时公告_设立产业基金": "设立产业基金",
    "O_临时公告_与私募基金合作投资": "与私募基金合作投资",
    "O_临时公告_药品批准": "药品批准",
    "O_临时公告_应当披露交易": "应当披露交易",
    "O_临时公告_转债付息": "转债付息",
    "O_临时公告_重大资产重组终止": "重大资产重组终止",
    "O_临时公告_股东大会通知_议案表": "股东大会通知议案表",
    "O_临时公告_股票交易异常波动": "股票交易异常波动",
    "O_临时公告_股票交易风险提示": "股票交易风险提示",
    "O_临时公告_经营情况简报_601668": "经营情况简报(601668)",
    "O_临时公告_股东大会召开通知": "股东大会召开通知",
    "O_临时公告_生产经营数据_601006": "生产经营数据(601006)",
    "O_临时公告_用募集资金置换预先投入的自筹资金": "用募集资金置换预先投入的自筹资金",
    "O_临时公告_变更证券简称": "变更证券简称",
    "O_临时公告_召开业绩说明会": "召开业绩说明会",
    "O_临时公告_可转债到期兑付及摘牌": "可转债到期兑付及摘牌",
    "O_临时公告_取消重大资产重组并复牌": "取消重大资产重组并复牌",
    "O_临时公告_变更会计师事务所": "变更会计师事务所",
    "O_临时公告_公告元信息": "公告元信息",
    "O_临时公告_中标候选人公示": "中标候选人公示",
    "O_临时公告_主要业务经营情况_000069": "主要业务经营情况(000069)",
    "股东大会延期": "股东大会延期",
    "股东大会通知": "股东大会通知",
    "推选职工董事或者监事": "推选职工董事或者监事",
    "核心技术人员离职": "核心技术人员离职",
    "职工代表大会决议": "职工代表大会决议",
    "优先股股息分派": "优先股股息分派",
    "取得发明专利证书": "取得发明专利证书",
    "业务资格获批": "业务资格获批",
}


# 生成总体投资分析（使用大语言模型）
def generate_overall_analysis(infotype: str, items: list) -> str:
    """根据公告类型和所有公告生成总体投资分析"""
    if not items:
        return None

    display_name = INFOTYPE_DISPLAY.get(infotype, infotype)

    # 准备分析数据（限制前20条，避免token过多）
    analysis_items = items[:20]

    # 构建公告摘要
    items_summary = []
    for item in analysis_items:
        code = item["met_meta"]["met_sec_code"]
        name = item["met_meta"]["met_sec_name"]
        title = item["met_meta"]["met_title"]
        date = item["met_meta"]["met_date"]

        item_text = f"- {name}（{code}）：{title}（{date}）"

        # 添加提取信息摘要
        extracted_list = item.get("extracted_info", [])
        if extracted_list:
            for ei in extracted_list[:1]:  # 最多1条提取信息
                info = ei.get("info", {})
                if info and isinstance(info, dict):
                    # 只取前2个字段
                    keys = list(info.keys())[:2]
                    info_text = " | ".join([f"{k}={info[k]}" for k in keys if info[k] and info[k].strip()])
                    if info_text:
                        item_text += f"\n  提取：{info_text}"

        items_summary.append(item_text)

    # 构建分析提示
    prompt = f"""你是专业的投资分析师，正在分析{display_name}类型的上市公司公告。

以下是最新的{len(analysis_items)}条公告：

{chr(10).join(items_summary)}

请分析这些公告，提供以下分析（用JSON格式返回，格式严格符合）：

{{
  "market_overview": "简要总结市场概况，1-2句话",
  "notable_companies": [
    {{
      "code": "证券代码",
      "name": "公司名称",
      "reason": "值得关注的原因（20字以内）"
    }}
  ],
  "investment_focus": "投资关注点（3-5条，每条20字以内，用分号分隔）"
}}

注意：
- notable_companies 最多选择3-5家最值得关注的公司
- 关注标准包括：高管变动、重大投资、战略调整、业绩相关等
- 保持客观专业，不构成投资建议
- 只返回JSON，不要其他文字
"""

    # 尝试调用大语言模型分析
    llm_result = call_llm_for_analysis(prompt, timeout=30)

    if llm_result:
        # 使用LLM分析结果
        analysis_parts = [llm_result.get("market_overview", "")]
        suggestion_parts = [llm_result.get("investment_focus", "")]
        notable_companies_raw = llm_result.get("notable_companies", [])

        notable_companies = []
        for nc in notable_companies_raw:
            notable_companies.append({
                "code": nc.get("code", ""),
                "name": nc.get("name", ""),
                "reason": nc.get("reason", "")
            })
    else:
        # 回退到规则分析（作为备选）
        analysis_parts = []
        suggestion_parts = []
        notable_companies = []

        # 统计公告数量（通用规则）
        from collections import Counter
        company_counts = Counter()
        company_codes = {}

        for item in items:
            code = item["met_meta"]["met_sec_code"]
            name = item["met_meta"]["met_sec_name"]
            company_counts[code] += 1
            company_codes[code] = name

        # 识别公告数量最多的公司（通用规则）
        for code, count in company_counts.most_common(5):
            if count > 1:
                notable_companies.append({
                    "code": code,
                    "name": company_codes[code],
                    "reason": f"公告数量最多（{count}条）"
                })

        # 通用市场概况和分析
        analysis_parts.append(f"本次共{len(company_counts)}家公司发布{len(items)}条公告。")

        # 简化的建议（通用）
        suggestion_parts.append("关注：1) 公告内容对公司经营和财务的影响；2) 是否涉及重大事项（高管变动、重大投资、重组等）；3) 结合公司基本面进行独立判断。")

    # 根据不同类型生成总体分析
    if infotype in ["O_临时公告_药品批准"]:
        analysis_parts.append("药品相关公告反映了公司研发管线推进情况。")
        suggestion_parts.append("关注：1) 新药审评进度和获批概率；2) 已上市药品的市场表现；3) 研发投入占营收比重，评估研发效率。")

    elif infotype in ["O_临时公告_人事变动", "核心技术人员离职"]:
        # 统计离职/聘任情况
        resign_count = sum(1 for item in items 
                          if any(w in item.get("met_meta", {}).get("met_title", "").lower() 
                                 for w in ["辞职", "离职"]))
        hire_count = sum(1 for item in items 
                        if any(w in item.get("met_meta", {}).get("met_title", "").lower() 
                               for w in ["聘任", "任命", "选举"]))
        
        if resign_count > hire_count:
            analysis_parts.append(f"人员流出较多（{resign_count}起离职 vs {hire_count}起聘任）。")
            suggestion_parts.append("关注：1) 离职人员是否为核心管理/技术人员；2) 继任者背景和经验；3) 是否存在公司治理或经营问题。")
        elif hire_count >= resign_count:
            analysis_parts.append(f"组织架构正常调整（{hire_count}起聘任 vs {resign_count}起离职）。")
            suggestion_parts.append("建议：关注新任高管履历，评估战略方向是否延续。")

    elif infotype in ["O_临时公告_董事会决议", "O_临时公告_股东大会召开通知"]:
        # 统计议案类型（从标题和提取信息中查找）
        all_titles = " ".join([item.get("met_meta", {}).get("met_title", "") for item in items]).lower()
        
        # 同时检查所有提取信息
        for item in items:
            extracted_list = item.get("extracted_info", [])
            for ei in extracted_list:
                info = ei.get("info", {})
                if info:
                    all_titles += " " + str(info).lower()
        
        analysis_parts.append(f"本次共 {len(items)} 家公司发布董事会决议，涉及{len(items)} 项议案。")
        
        # 统计各类别数量
        keywords_count = {
            "募投": 0,
            "担保": 0,
            "分红": 0,
            "派息": 0,
            "回购": 0,
            "投资": 0,
            "合资": 0,
            "注销": 0,
            "变更": 0
        }
        
        for k in keywords_count:
            keywords_count[k] = all_titles.count(k)
        
        suggestions = []
        if keywords_count["募投"] > 0:
            suggestions.append(f"募投项目（{keywords_count['募投']}项）：关注项目进展和调整原因，评估对未来业绩的影响。")
        if keywords_count["担保"] > 0:
            suggestions.append(f"关联担保（{keywords_count['担保']}项）：核实担保金额、被担保方资质及潜在风险。")
        if keywords_count["分红"] > 0 or keywords_count["派息"] > 0:
            suggestions.append(f"分红方案（{keywords_count['分红'] + keywords_count['派息']}项）：关注分红比例和持续性，评估现金流状况。")
        if keywords_count["回购"] > 0:
            suggestions.append(f"股份回购（{keywords_count['回购']}项）：关注回购价格与当前股价对比，评估管理层信心。")
        if keywords_count["投资"] > 0 or keywords_count["合资"] > 0:
            suggestions.append(f"对外投资/合资（{keywords_count['投资'] + keywords_count['合资']}项）：评估项目协同效应、回报周期及整合风险。")
        if keywords_count["注销"] > 0:
            suggestions.append(f"资产处置/注销（{keywords_count['注销']}项）：关注对公司营收和资产结构的影响。")
        if keywords_count["变更"] > 0:
            suggestions.append(f"相关事项变更（{keywords_count['变更']}项）：关注变更原因及对现有业务的影响。")
        
        if not suggestions:
            suggestions.append(f"关注董事会通过的 {len(items)} 项议案对公司经营和财务的具体影响。")
        
        suggestion_parts.append("\n".join(f"- {s}" for s in suggestions))

    elif infotype in ["O_临时公告_应当披露交易", "O_临时公告_应当披露交易的进展", 
                      "O_临时公告_应当披露交易的提示", "O_临时公告_应当披露交易已完成"]:
        analysis_parts.append(f"披露交易事项共{len(items)}起，涉及并购、资产处置等。")
        suggestion_parts.append("关注：1) 交易对财务报表的影响（商誉减值风险）；2) 交易价格公允性；3) 对公司主营业务的协同效应。")

    elif infotype in ["O_临时公告_股票交易异常波动", "O_临时公告_股票交易风险提示"]:
        analysis_parts.append("股价波动异常需警惕短期风险。")
        suggestion_parts.append("建议：理性分析公告内容，控制风险，避免盲目追涨。关注基本面变化。")

    elif infotype in ["O_临时公告_董事会秘书辞职", "O_临时公告_公司董事长、法定代表人辞职",
                      "O_临时公告_公司董事、监事、高级管理人员（董事长和董秘除外）辞职"]:
        analysis_parts.append("管理层变动可能影响公司治理和战略执行。")
        suggestion_parts.append("关注：1) 变动原因是否涉及经营问题；2) 继任计划及过渡安排；3) 对股价和业务稳定性的影响。")

    elif infotype in ["O_临时公告_获得财政补贴", "政府补助"]:
        analysis_parts.append("财政补贴属于非经常性收益，可持续性需评估。")
        suggestion_parts.append("建议：关注主营业务的实际盈利能力，将补贴收入与经营利润区分看待。")

    elif infotype in ["O_临时公告_股权激励计划授予", "O_临时公告_股权激励计划实施完成",
                      "O_临时公告_股权激励计划终止"]:
        analysis_parts.append("股权激励将员工利益与公司发展绑定。")
        suggestion_parts.append("关注：1) 行权条件和业绩目标；2) 股份来源和摊薄影响；3) 激励方案设计是否合理。")

    elif infotype in ["O_临时公告_回购实施进展", "O_临时公告_回购预案"]:
        analysis_parts.append("股份回购是维护股价和股东回报的重要手段。")
        suggestion_parts.append("关注：1) 回购价格与当前股价对比；2) 回购数量占总股本比例；3) 资金来源对现金流的影响。")

    elif "立案调查" in infotype or "被调查" in infotype:
        analysis_parts.append("涉及立案调查，存在合规和监管风险。")
        suggestion_parts.append("建议：暂时观望，等待调查结果。可能涉及行政处罚或监管措施。")

    elif "可转债" in infotype:
        analysis_parts.append("可转债事项反映公司融资和债务管理情况。")
        suggestion_parts.append("关注：1) 转股价格与正股价格关系；2) 转股稀释效应；3) 债券评级及信用风险。")

    elif infotype in ["O_临时公告_取得发明专利证书", "O_临时公告_取得商标注册证书"]:
        analysis_parts.append("新增知识产权有助于构筑技术护城河。")
        suggestion_parts.append("建议：关注专利质量（是否为核心技术）、专利商业化进展及收入贡献。")

    elif infotype in ["O_临时公告_设立产业基金", "O_临时公告_与私募基金合作投资"]:
        analysis_parts.append("设立产业基金是外延式发展的探索。")
        suggestion_parts.append("关注：1) 基金投资方向与主业的协同性；2) 基金规模和出资方；3) 后续投资标的及回报。")

    elif infotype in ["O_临时公告_业绩预告"]:
        analysis_parts.append("业绩预告反映公司盈利趋势。")
        suggestion_parts.append("关注：1) 预告是否超市场预期；2) 增长或下滑驱动因素；3) 是否包含一次性收益或损失。")

    elif infotype in ["O_临时公告_对外投资", "O_临时公告_购买资产", "O_临时公告_出售资产"]:
        analysis_parts.append("资产配置调整反映公司战略选择。")
        suggestion_parts.append("关注：1) 投资标的估值是否合理；2) 项目回报周期和现金流影响；3) 与主业的战略协同。")

    # 生成总体分析
    lines = []
    lines.append("## 💰 总体投资分析")
    lines.append("")

    # 值得关注的公司
    if notable_companies:
        lines.append("### ⭐ 值得关注的公司")
        lines.append("")
        for company in notable_companies[:5]:  # 最多显示5个
            lines.append(f"- **{company['name']}（{company['code']}）**: {company['reason']}")
        if len(notable_companies) > 5:
            lines.append(f"- ...及其他 {len(notable_companies) - 5} 家公司")
        lines.append("")
        lines.append("---")
        lines.append("")

    if analysis_parts:
        lines.append("**市场概况：**")
        for part in analysis_parts:
            lines.append(f"- {part}")
        lines.append("")

    if suggestion_parts:
        lines.append("**投资关注点：**")
        for part in suggestion_parts:
            if "\n" in part:
                # 多行格式
                lines.append(part)
            else:
                lines.append(f"- {part}")
        lines.append("")

    lines.append("**风险提示：**")
    lines.append("- 本分析基于公告内容，不构成投资建议。请结合公司基本面、行业趋势和宏观经济进行独立判断。")
    lines.append("- 投资有风险，决策需谨慎。")
    lines.append("")
    lines.append("---")
    lines.append("")

    return "\n".join(lines)


# 公告评价模板（根据关键字和内容生成简短评价）
def generate_comment(infotype: str, title: str, extracted_info: dict) -> str:
    """根据公告类型和内容生成简短评价及投资建议"""
    # 将提取信息转为字符串用于关键字匹配
    info_text = str(extracted_info).lower() if extracted_info else ""
    title_lower = title.lower()

    comment = None
    suggestion = None

    # 药品相关
    if infotype in ["O_临时公告_药品批准"]:
        if any(w in title_lower for w in ["受理", "申请"]):
            comment = "药品研发推进到注册阶段，是重要的里程碑事件"
            suggestion = "投资者可关注后续审评进度，药品若获批将打开市场空间"
        elif any(w in title_lower for w in ["批准", "注册"]):
            comment = "药品成功获批，可正式上市销售"
            suggestion = "新产品放量有望增厚业绩，建议关注销售推广进度"

    # 人事变动
    elif infotype in ["O_临时公告_人事变动", "核心技术人员离职"]:
        if any(w in title_lower for w in ["辞职", "离职"]):
            # 检查是否是核心人员
            if any(k in str(extracted_info) for k in ["董事长", "总经理", "技术"]):
                comment = "核心管理层变动，可能影响公司战略执行"
                suggestion = "需关注继任者背景及交接安排，短期波动可能加大"
            else:
                comment = "正常人事调整"
                suggestion = "影响有限，关注公司治理结构稳定性"
        elif any(w in title_lower for w in ["聘任", "任命", "选举"]):
            comment = "新管理层到位，组织架构优化"
            suggestion = "关注新任高管履历，战略方向是否有调整"

    # 设立产业基金
    elif infotype in ["O_临时公告_设立产业基金", "O_临时公告_与私募基金合作投资"]:
        comment = "设立产业基金，探索外延式发展路径"
        suggestion = "产业基金可通过投资并购快速获取优质资产，关注后续投资标的"

    # 董事会决议 - 根据议案内容深入分析
    elif infotype in ["O_临时公告_董事会决议", "O_临时公告_股东大会召开通知"]:
        # 募投项目相关
        if "募投" in info_text:
            if "延期" in info_text or "调整" in info_text:
                comment = "募投项目延期或调整，说明项目建设进展不及预期"
                suggestion = "需了解延期原因，若因市场环境变化需评估长期影响"
            elif "结项" in info_text or "置换" in info_text:
                comment = "募投项目结项或资金用途调整，优化资金使用效率"
                suggestion = "资金用于补充流动资金或新项目，关注后续使用计划"
        # 资产处置
        elif "注销" in info_text or "出售" in info_text:
            comment = "处置不良或非核心资产，优化资产结构"
            suggestion = "剥离低效资产可聚焦主业，同时回收资金改善现金流"
        # 担保相关
        elif "担保" in info_text:
            comment = "涉及关联担保，需关注担保风险敞口"
            suggestion = "建议核实担保金额及被担保方资质，评估潜在风险"
        # 分红回购
        elif any(w in info_text for w in ["分红", "利润分配", "派息"]):
            comment = "推出分红方案，现金回报股东"
            suggestion = "分红比例和持续性是关键，关注公司盈利质量和现金流"
        elif "回购" in info_text:
            comment = "公司回购股份，彰显管理层信心"
            suggestion = "回购价格低于估值时安全边际较高，可择机关注"
        # 投资相关
        elif "投资" in info_text or "合资" in info_text:
            comment = "对外投资布局新业务或扩大产能"
            suggestion = "评估投资项目的协同效应和回报周期，关注整合风险"

    # 重大交易
    elif infotype in ["O_临时公告_应当披露交易"]:
        # 检查交易金额
        if "金额" in str(extracted_info) or "元" in str(extracted_info):
            comment = "披露重大交易，需评估对公司业绩的影响"
            suggestion = "关注交易价格公允性及对财务报表的影响，警惕利益输送"
        else:
            comment = "重要交易事项披露"
            suggestion = "交易完成后需持续跟踪整合效果和业绩兑现情况"

    # 可转债相关
    elif infotype in ["O_临时公告_转债付息", "O_临时公告_可转债到期兑付及摘牌"]:
        comment = "可转债相关事项按计划执行，信用记录良好"
        suggestion = "若转股价格低于正股价格，存在套利机会，但需注意转股后稀释效应"

    # 专利/技术
    elif infotype in ["取得发明专利证书"]:
        comment = "新增发明专利，技术护城河持续拓宽"
        suggestion = "专利数量和质量是科技企业核心竞争力，关注专利商业化进展"

    # 风险提示类
    elif infotype in ["O_临时公告_股票交易异常波动", "O_临时公告_股票交易风险提示"]:
        comment = "股价波动异常，发布风险提示公告"
        suggestion = "注意控制风险，避免盲目追涨，理性分析公告内容"

    elif "立案调查" in infotype or "被调查" in infotype:
        comment = "公司或高管涉及立案调查，存在合规风险"
        suggestion = "调查结果可能涉及行政处罚或监管措施，建议暂时观望"

    elif "风险提示" in infotype or "澄清" in infotype:
        comment = "发布澄清或风险提示公告"
        suggestion = "仔细阅读公告内容，核实市场传闻，避免信息不对称"

    # 中标
    elif infotype in ["O_临时公告_中标候选人公示"]:
        comment = "成功中标重大项目，未来业绩有望提升"
        suggestion = "关注项目合同金额、执行周期及对公司营收的增量贡献"

    # 财政补贴
    elif any(w in title_lower for w in ["补贴", "补助", "资助"]):
        comment = "获得财政补贴，一次性增厚利润"
        suggestion = "需区分经常性和非经常性损益，关注主营业务的实际盈利能力"

    # 股权激励
    elif "股权激励" in infotype:
        if "授予" in title_lower:
            comment = "股权激励计划实施，绑定核心员工利益"
            suggestion = "行权条件反映公司业绩目标，可据此评估管理层预期"
        elif "终止" in title_lower or "注销" in title_lower:
            comment = "股权激励计划终止或注销"
            suggestion = "可能影响员工激励效果，需关注原因及替代方案"

    # 回购
    elif "回购" in infotype:
        comment = "公司启动回购，维护股价稳定"
        suggestion = "回购价格和数量反映管理层对估值的判断，可参考操作"

    # 债务重组
    elif "债务重组" in infotype:
        comment = "进行债务重组，优化财务结构"
        suggestion = "关注债务重组方案是否改善流动性，警惕债权人的让渡条件"

    # 业绩预告
    elif "业绩预告" in infotype:
        # 根据预告内容判断
        if "扭亏" in info_text or "增长" in info_text:
            comment = "业绩预喜，超出市场预期"
            suggestion = "需关注增长驱动因素是否可持续，警惕一次性收益"
        elif "亏损" in info_text or "下降" in info_text:
            comment = "业绩预警，经营面临挑战"
            suggestion = "需了解下滑原因，评估是行业周期性还是公司自身问题"

    # 如果没有匹配到具体类型，根据关键字补充
    if not comment:
        if "投资" in title_lower:
            comment = "对外投资布局"
            suggestion = "评估项目协同效应及回报周期"
        elif "合作" in title_lower or "协议" in title_lower:
            comment = "签署合作协议"
            suggestion = "关注合作方实力及协议条款对双方的利益影响"
        elif "变更" in title_lower:
            comment = "相关事项发生变更"
            suggestion = "关注变更原因及对现有业务的影响"

    # 组合返回评价和建议
    if comment and suggestion:
        return f"{comment}\n💰 **投资建议**：{suggestion}"
    elif comment:
        return comment
    else:
        return None


def fetch_all_pages(api_base: str, infotype: str, start_date: str, end_date: str) -> list:
    """分页获取所有公告数据"""
    all_items = []
    page = 1
    while True:
        params = urllib.parse.urlencode({
            "infotype": infotype,
            "start_date": start_date,
            "end_date": end_date,
            "page": page,
            "page_size": PAGE_SIZE,
        })
        url = f"{api_base}/api/v1/announcements?{params}"
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"[ERROR] 请求失败 page={page}: {e}", file=sys.stderr)
            break

        if data.get("code") != 200:
            print(f"[ERROR] API 返回错误: {data.get('message')}", file=sys.stderr)
            break

        items = data["data"]["items"]
        all_items.extend(items)
        total_pages = data["data"]["total_pages"]
        if page >= total_pages:
            break
        page += 1

    return all_items


def group_by_company(items: list) -> dict:
    """按公司（证券代码+简称）聚合公告"""
    groups = defaultdict(list)
    for item in items:
        meta = item["met_meta"]
        key = (meta["met_sec_code"], meta["met_sec_name"])
        groups[key].append(item)
    # 按证券代码排序
    return dict(sorted(groups.items(), key=lambda x: x[0][0]))


def group_by_type(items: list) -> dict:
    """按公告类型聚合公告"""
    groups = defaultdict(list)
    for item in items:
        extracted = item.get("extracted_info", [])
        if extracted:
            infotype = extracted[0].get("infotype", "其他")
            # 使用中文显示名
            display_name = INFOTYPE_DISPLAY.get(infotype, infotype)
            groups[display_name].append(item)
    # 按类型排序
    return dict(sorted(groups.items()))


def format_extracted_info(info) -> str:
    """将 extracted_info.info 字典或列表格式化为 Markdown 表格，跳过空值字段"""
    if not info:
        return "_无提取信息_"

    # 如果 info 是列表，则遍历列表中的每个字典元素
    if isinstance(info, list):
        results = []
        for idx, item in enumerate(info):
            if isinstance(item, dict):
                item_result = _format_dict_as_table(item)
                if item_result and item_result != "_无提取信息_" and item_result != "_无有效信息_":
                    if len(info) > 1:
                        results.append(f"**提取信息 {idx + 1}：**\n{item_result}")
                    else:
                        results.append(item_result)
        if not results:
            return "_无提取信息_"
        return "\n\n".join(results)
    elif isinstance(info, dict):
        return _format_dict_as_table(info)
    else:
        return f"_不支持的格式: {type(info).__name__}_"


def _format_dict_as_table(info: dict) -> str:
    """将字典格式化为 Markdown 表格，跳过空值字段（内部辅助函数）"""
    if not info:
        return "_无提取信息_"

    # 过滤掉空值字段
    filtered_items = []
    for k, v in info.items():
        if isinstance(v, dict):
            if not v:
                continue  # 跳过空字典
            # 过滤嵌套字典中的空值
            dict_items = [f"{dk}: {dv}" for dk, dv in v.items() if dv]
            if dict_items:
                v_str = "；".join(dict_items)
                filtered_items.append((k, v_str))
        elif isinstance(v, list):
            if not v:
                continue  # 跳过空列表
            # 过滤列表中的空值
            list_items = [str(i) for i in v if i]
            if list_items:
                v_str = "；".join(list_items)
                filtered_items.append((k, v_str))
        else:
            if not v:
                continue  # 跳过空字符串、None、0等
            filtered_items.append((k, str(v)))

    if not filtered_items:
        return "_无有效信息_"

    lines = []
    lines.append("| 字段 | 内容 |")
    lines.append("|------|------|")
    for k, v_str in filtered_items:
        # 表格内换行用 <br>
        v_str = v_str.replace("\n", "<br>")
        lines.append(f"| {k} | {v_str} |")

    return "\n".join(lines)


def format_post(items: list, infotype: str, start_date: str, end_date: str) -> str:
    """生成完整的 Markdown 帖子"""
    display_name = INFOTYPE_DISPLAY.get(infotype, infotype)
    groups = group_by_company(items)
    total = len(items)
    company_count = len(groups)

    # 数据统计：统计每家公司的公告数量
    company_stats = []
    for (sec_code, sec_name), company_items in groups.items():
        company_stats.append({
            "code": sec_code,
            "name": sec_name,
            "count": len(company_items)
        })
    # 按公告数量降序排序
    company_stats.sort(key=lambda x: x["count"], reverse=True)
    # 公告最多的公司
    top_company = company_stats[0] if company_stats else None

    # 生成洞察分析
    insights = []
    if top_company:
        insights.append(f"📊 **最活跃公司**：{top_company['name']}（{top_company['code']}）共 {top_company['count']} 条公告")
    if company_count >= 5:
        insights.append(f"🏢 **市场集中度**：公告分布较为分散，涉及 {company_count} 家公司")
    if total >= 20:
        insights.append(f"📈 **公告密度**：今日公告较为密集，共 {total} 条")

    lines = []
    # 标题：包含类别和总条数
    lines.append(f"# 【{company_count}家公司】{display_name}公告汇总（{start_date} ~ {end_date}）【共{total}条】")
    lines.append("")

    # 基本统计摘要
    lines.append("## 📋 概览")
    lines.append("")
    lines.append(f"- **公告类型**：{display_name}")
    lines.append(f"- **时间范围**：{start_date} ~ {end_date}")
    lines.append(f"- **公告总数**：{total} 条")
    lines.append(f"- **涉及公司**：{company_count} 家")
    lines.append(f"- **数据来源**：文因互联公告提取服务")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 总体投资分析（移到前面，便于人类快速了解投资价值）
    overall_analysis = generate_overall_analysis(infotype, items)
    if overall_analysis:
        lines.append(overall_analysis)

    # 数据统计与洞察
    lines.append("## 📊 数据统计与洞察")
    lines.append("")
    if insights:
        for insight in insights:
            lines.append(f"{insight}")
        lines.append("")

    # 公司公告数量排行榜
    if company_stats:
        lines.append("**公司公告数量排行榜：**")
        lines.append("")
        lines.append("| 排名 | 公司 | 证券代码 | 公告数量 |")
        lines.append("|------|------|----------|----------|")
        for idx, stat in enumerate(company_stats, 1):  # 显示所有公司
            lines.append(f"| {idx} | {stat['name']} | {stat['code']} | {stat['count']} |")
        lines.append("")
    lines.append("---")
    lines.append("")

    # 目录（Lemmy 不支持 Markdown 锚点链接，改为纯文本列表）
    lines.append("## 📑 目录")
    lines.append("")
    for idx, ((sec_code, sec_name), _) in enumerate(groups.items(), 1):
        lines.append(f"{idx}. {sec_name}（{sec_code}）")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 按公司展示
    for idx, ((sec_code, sec_name), company_items) in enumerate(groups.items(), 1):
        # 使用 emoji 作为视觉锚点
        lines.append(f'## 📍 {sec_name}（{sec_code}）')
        lines.append("")

        for item in company_items:
            meta = item["met_meta"]
            title = meta["met_title"]
            date = meta["met_date"]
            link = meta["met_link"]

            lines.append(f"### 📄 {title}")
            lines.append("")
            lines.append(f"- **日期**：{date}")
            lines.append(f"- **证券代码**：{sec_code}")
            lines.append(f"- **证券简称**：{sec_name}")
            lines.append(f"- **原文链接**：[查看PDF]({link})")
            lines.append("")

            # 提取信息
            extracted_list = item.get("extracted_info", [])
            if extracted_list:
                for ei in extracted_list:
                    info = ei.get("info", {})
                    lines.append("**提取信息：**")
                    lines.append("")
                    lines.append(format_extracted_info(info))
                    lines.append("")
            else:
                lines.append("_暂无提取信息_")
                lines.append("")

        lines.append("---")
        lines.append("")

    # 尾部：产品推广
    lines.append("## 关于文因互联")
    lines.append("")
    lines.append("以上数据由 **文因互联** 智能文档解析服务自动提取。")
    lines.append("")
    lines.append("### 🔗 产品推荐")
    lines.append("")
    lines.append(
        "- **InsightDoc 文档解析** — 轻松解析发票、财务表格及其他文档 "
        "👉 [insightdoc.memect.cn/workspace]"
        "(https://insightdoc.memect.cn/workspace)"
    )
    lines.append(
        "- **PDF2Skills2App** — 书→App 的魔法，PDF2Skills 让书活起来了 "
        "👉 [pdf2skills.memect.cn/quick-start]"
        "(https://pdf2skills.memect.cn/quick-start) "
        "| [详细介绍]"
        "(https://mp.weixin.qq.com/s/r3ryXnz8YRncCULcJDNbiQ)"
    )
    lines.append("")
    lines.append("### 📡 数据接口")
    lines.append("")
    lines.append(f"- **公告数据 API** — http://39.104.68.74:8452")
    lines.append("")

    return "\n".join(lines)


def format_post_by_type(items: list, start_date: str, end_date: str) -> str:
    """按类型聚合生成帖子内容"""
    groups = group_by_type(items)
    total = len(items)
    type_count = len(groups)

    # 统计每种类型的数量
    type_stats = []
    for infotype, type_items in groups.items():
        type_stats.append({
            "type": infotype,
            "count": len(type_items)
        })
    type_stats.sort(key=lambda x: x["count"], reverse=True)

    lines = []
    # 标题
    lines.append(f"# 📊 公告智能解析（按类型聚合）")
    lines.append(f"**日期：** {start_date} ~ {end_date}")
    lines.append("")
    lines.append(f"**公告总数：** {total} 条 | **类型数量：** {type_count} 类")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 按类型展示
    for infotype, type_items in groups.items():
        lines.append(f"## {infotype}")
        lines.append("")
        lines.append(f"**公告数量：** {len(type_items)} 条")
        lines.append("")

        # 按公司分组（便于阅读）
        by_company = group_by_company(type_items)
        for (sec_code, sec_name), company_items in by_company.items():
            lines.append(f"### {sec_name}（{sec_code}）")
            lines.append("")
            
            for item in company_items:
                meta = item.get("met_meta", {})
                extracted = item.get("extracted_info", [])
                if extracted:
                    info = extracted[0].get("info")
                    
                    # 公告标题
                    title = meta.get("met_title", "")
                    date = meta.get("met_date", "")
                    link = meta.get("met_link", "")
                    
                    lines.append(f"> {title}")
                    lines.append("")
                    
                    if link:
                        lines.append(f"📄 [查看原文]({link})")
                        lines.append("")
                    
                    # 提取信息
                    if isinstance(info, dict):
                        for key, value in info.items():
                            if key.startswith('原文_') and value and not key.endswith('重要内容提示'):
                                key_label = key.replace('原文_', '').replace('_', ' ')
                                # 处理多行文本
                                if isinstance(value, str) and '\n' in value:
                                    value = value.replace('\n', ' ')
                                if isinstance(value, str) and len(value) > 100:
                                    value = value[:100] + "..."
                                lines.append(f"- **{key_label}**：{value}")
                    
                    lines.append("")
            
            lines.append("---")
            lines.append("")

    # 类型统计
    lines.append("## 📊 类型统计")
    lines.append("")
    lines.append("| 排名 | 类型 | 公告数量 |")
    lines.append("|------|------|----------|")
    for idx, stat in enumerate(type_stats, 1):
        lines.append(f"| {idx} | {stat['type']} | {stat['count']} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 产品信息
    lines.append("## 🔧 技术支持")
    lines.append("")
    lines.append("- [📄 文档解析](https://insightdoc.memect.cn/workspace) - 轻松解析发票、财务表格及其他文档")
    lines.append("- [📚 pdf2skills](https://pdf2skills.memect.cn/quick-start) - 书→App的魔法")
    lines.append("- [微信公众号](https://mp.weixin.qq.com/s/r3ryXnz8YRncCULcJDNbiQ) - 了解更多")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*本内容由 AI 智能解析生成，数据来源：巨潮资讯网*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="公告数据获取与 Markdown 排版工具")
    parser.add_argument("--infotype", required=True, help="公告类型，如 O_临时公告_董事会决议")
    parser.add_argument("--start_date", default=None, help="开始日期 YYYY-MM-DD，默认当天")
    parser.add_argument("--end_date", default=None, help="结束日期 YYYY-MM-DD，默认当天")
    parser.add_argument("--api_base", default=DEFAULT_API_BASE, help="API 基础地址")
    parser.add_argument("--output", "-o", default=None, help="输出文件路径，默认输出到 stdout")
    parser.add_argument("--group-by", choices=["company", "type"], default="company", 
                       help="聚合方式：company=按公司聚合（默认），type=按类型聚合")
    parser.add_argument("--limit", type=int, default=None, 
                       help="限制公告数量（只显示前N条），默认显示全部")
    args = parser.parse_args()

    today = date.today().isoformat()
    start = args.start_date or today
    end = args.end_date or today

    print(f"[INFO] 获取 {args.infotype} 公告 ({start} ~ {end})...", file=sys.stderr)
    items = fetch_all_pages(args.api_base, args.infotype, start, end)
    print(f"[INFO] 共获取 {len(items)} 条公告", file=sys.stderr)

    # 应用数量限制
    if args.limit and items:
        items = items[:args.limit]
        print(f"[INFO] 限制显示前 {args.limit} 条公告", file=sys.stderr)

    if not items:
        print("[WARN] 未获取到任何公告数据，无输出", file=sys.stderr)
        sys.exit(0)

    # 根据聚合方式选择不同的格式化函数
    if args.group_by == "type":
        md_content = format_post_by_type(items, start, end)
    else:
        md_content = format_post(items, args.infotype, start, end)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"[INFO] 已写入 {args.output}", file=sys.stderr)
    else:
        print(md_content)


if __name__ == "__main__":
    main()
