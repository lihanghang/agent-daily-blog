---
name: design-chat-layout
description: 设计专业的微信公众号文章视觉排版，包括层级、间距、色彩、图片规范和交互元素

capability:
  - hiearchy_design: 设计清晰的标题层级（H1/H2/H3/H4）和间距
  - spacing_optimization: 优化段落、列表、块之间的间距
  - color_system: 应用和谐的色彩方案（主色、辅助色、背景色、边框色）
  - highlight_tyles: 为重点内容设计突出样式（粗体、色块、边框、引用）
  - list_styling: 为有序和无序列表设计清晰样式（间距、标记、缩进）
  - blockquote_styling: 设计引用块的样式（背景、边框、斜体）
  - image_guidelines: 规范图片尺寸、对齐、说明文字、间距
  - separator_design: 设计分隔线（实线、虚线、空行）
  - cta_box: 设计行动号召框（背景、边框、居中、图标）
  - code_block_styling: 为代码块设计专业样式（背景、字体、等宽）
  - mobile_optimization: 优化手机端阅读体验（字体大小、图片宽度、避免横向滚动）
  - interactive_elements: 添加互动元素（评论区引导、相关文章推荐、关注引导）

parameters:
  primary_color: 主色（默认："#1a73e8"）
  secondary_color: 辅助色（默认："#e67e22"）
  success_color: 成功色（默认："#27ae60"）
  warning_color: 警示色（默认："#f39c12"）
  info_color: 信息色（默认："#999999"）
  background_color: 背景色（默认："#f6f6f6"）
  border_color: 边框色（默认："#e0e0e0"）
  heading_font_size: 标题字体大小（H1: 22px, H2: 18px, H3: 16px, H4: 15px）
  body_font_size: 正文字体大小（16px）
  body_line_height: 正文行高（2.0）
  paragraph_spacing: 段落间距（2-3 行）
  list_spacing: 列表项间距（0.5em）
  section_spacing: 章节间距（2em）

layout_patterns:
  header_section:
    title: "居中标题"
    html: |
      <div style="text-align: center; margin: 2em 0;">
        <h1 style="font-size: 22px; color: #000; margin-bottom: 0.5em;">文章主标题</h1>
      </div>
  
  content_section:
    title: "内容段落"
    html: |
      <p style="font-size: 16px; line-height: 2; color: #3f3f3f; text-indent: 2em; margin-bottom: 0; text-align: justify;">
        文章内容...
      </p>
  
  heading_with_line:
    title: "带线的标题"
    html: |
      <h2 style="margin-top: 2em; border-left: 4px solid #1a73e8; padding-left: 12px; font-size: 18px; color: #000; margin-bottom: 1em;">
        标题文字
      </h2>
  
  numbered_list:
    title: "有序列表"
    html: |
      <ol style="margin: 1.5em 0; padding-left: 2em; list-style-type: decimal;">
        <li style="margin-bottom: 0.5em; line-height: 1.8; color: #333;">
          <strong style="color: #333;">要点文字</strong>：详细说明
        </li>
      </ol>
  
  bullet_list_with_dots:
    title: "圆点列表"
    html: |
      <ul style="margin: 1.5em 0; padding-left: 2em; list-style-type: square;">
        <li style="margin-bottom: 0.5em; line-height: 1.8; color: #444;">
          <span style="display: inline-block; width: 8px; height: 8px; background: #1a73e8; border-radius: 50%;"></span>
          <strong style="color: #1a73e8;">要点文字</strong>：说明内容
        </li>
      </ul>
  
  highlight_block:
    title: "色块重点"
    html: |
      <span style="background-color: #f3f4f6; padding: 4px 12px; border-radius: 4px; color: #d71920; font-weight: bold;">
        重点内容
      </span>
  
  highlight_border_box:
    title: "边框重点"
    html: |
      <div style="border: 2px solid #e67e22; border-left: 4px solid #e67e22; padding: 12px; margin: 1em 0; background-color: #fff;">
        <strong style="color: #e67e22;">核心要点</strong>
        <div>具体内容...</div>
      </div>
  
  blockquote:
    title: "引用块"
    html: |
      <blockquote style="background-color: #f6f6f6; border-left: 4px solid #999; padding: 1em 1em; margin: 1.5em 0; color: #666; font-style: italic;">
        "引用内容"
      </blockquote>
  
  image_with_caption:
    title: "居中图片"
    html: |
      <center>
        <img src="图片URL" style="width: 100%; max-width: 677px; border-radius: 8px;" alt="图片说明">
        <p style="font-size: 12px; color: #999; margin-top: 8px;">
          图 1：图片说明
        </p>
      </center>
  
  separator_line:
    title: "分隔线"
    html: |
      <hr style="border: 0; border-top: 1px solid #e0e0e0; margin: 2em 0;">
  
  separator_dashed:
    title: "虚线分隔"
    html: |
      <hr style="border: 0; border-top: 1px dashed #ccc; margin: 2em 0;">
  
  cta_box:
    title: "行动号召框"
    html: |
      <div style="background-color: #fff3cd; border: 1px solid #ffb300; border-radius: 8px; padding: 1.5em; text-align: center; margin: 2em 0;">
        <h3 style="margin: 0 0 0.5em 0; color: #856404; font-size: 16px;">
          🎯 今日行动建议
        </h3>
        <p style="margin: 0 0 1em 0; line-height: 1.6; color: #333;">
          行动建议内容
        </p>
        <p style="margin: 0;">
          在评论区分享你的想法，与更多人交流！
        </p>
      </div>
  
  code_block:
    title: "代码块"
    html: |
      <pre style="background-color: #282c34; color: #abb2bf; padding: 1em; border-radius: 6px; overflow-x: auto; line-height: 1.5; font-size: 13px; font-family: 'Courier New', monospace;">
<code style="color: #abb2bf;">
# 代码示例
def function():
    return "Hello World"
</code>
</pre>
      <p style="font-size: 12px; color: #999; margin-top: 8px;">
        图 1：代码示例
      </p>
      </center>
  
  mobile_optimized_list:
    title: "手机端列表（小段落）"
    html: |
      <ul style="margin: 1.5em 0; padding-left: 0;">
        <li style="margin-bottom: 0.8em; line-height: 1.8; color: #333;">
          <strong style="color: #333;">要点 1</strong>：详细说明。短句控制在 20 字内，更适合手机阅读。
        </li>
        <li style="margin-bottom: 0.8em; line-height: 1.8; color: #333;">
          <strong style="color: #333;">要点 2</strong>：详细说明。保持段落简短，避免长篇大论。
        </li>
      </ul>

version: "1.0.0"
author: 虾说
created: "2026-03-14"

quality_gates:
  - readability_score: 可读性评分（段落长度、句子长度、语言流畅度）
  - visual_balance: 视觉平衡度（文字密度、图片分布、空白利用）
  - color_harmony: 色彩和谐度（配色是否协调、对比度是否合理）
  - mobile_score: 手机端评分（是否适合小屏、是否有横向滚动）
  - interaction_score: 互动评分（是否有 CTA、评论区引导、相关文章推荐）

notes: |
  这是文章视觉排版的核心技能。
  
  使用方法：
  1. 从 write-chat-article 获取优化后的文章内容
  2. 应用排版模板增强视觉效果
  3. 输出完整的 HTML（可直接粘贴到公众号编辑器）
  
  排版原则：
  1. 层次清晰：H1 → H2 → H3 → H4，左侧彩色竖线增强层次感
  2. 间距合理：段落之间空 2-3 行，标题上下空 1-2 行
  3. 重点突出：用粗体、色块、边框区分重点内容
  4. 色彩和谐：主色 + 2 个辅助色，保持色调统一
  5. 移动端优化：段落控制在 3-5 行，避免长段落
  
  配色方案（推荐）：
  - 主色调：#1a73e8（科技蓝）
  - 辅助色：#e67e22（活力橙）、#27ae60（成长绿）
  - 信息色：#999999（灰色）
  - 警示色：#f39c12（警示红）
  - 背景色：#f6f6f6（浅灰）
  - 边框色：#e0e0e0（中灰）
