---
name: write-chat-article
description: 创作高质量的微信公众号文章内容

capability:
  - content_optimization: 优化文章开篇、结构、观点、数据支撑、价值承诺
  - storytelling: 增强故事性和情感连接
  - research_based: 用数据和案例支撑观点

parameters:
  topic: 文章主题（必填）
  angle: 切入角度（如：痛点、数据、案例）
  tone: 语调（专业/轻松/幽默）
  length: 文章长度（1500-2500字 / 800-1500字 / 2500-3500字）

input_data:
  target_audience: 目标受众（如：开发者、产品经理、创业团队）
  pain_points: [痛点列表]
  key_insights: [核心洞察列表]
  supporting_data: [数据/案例列表]
  value_proposition: 价值主张

output_format:
  title: 优化后的文章标题
  opening: 抓人开篇（100-200字）
  structure: 文章结构（3-5个核心部分）
  content: 完整文章内容
  value_summary: 价值承诺总结

content_rules:
  - 黄金3秒：开篇必须在前3-5秒抓住读者
  - 观点清晰：每个小节有独立观点
  - 数据支撑：用具体案例或数据增强说服力
  - 语言风格：口语化，"你"代替"读者"，避免"本文旨在"

writing_principles:
  - 直接切入：不要冗长开场白
  - 先抛问题：给出挑战或现象
  - 给出答案：你的解决方案或观点
  - 具体建议： actionable 的建议，不是空泛谈论
  - 建立共鸣：用"我们都遇到过..."、"你有没有发现..."

structure_template:
  1. 开篇（痛点/现象 + 数据/案例）
  2. 核心观点（分3-5个小节）
  3. 案例分析（具体例子、数据支撑）
  4. 总结/行动建议

quality_checks:
  - 字数控制在目标范围
  - 段落不超过300字（手机友好）
  - 关键词密度适中（避免堆砌）
  - 每个部分都有价值贡献

version: "1.0.0"
author: 虾说
created: "2026-03-14"
