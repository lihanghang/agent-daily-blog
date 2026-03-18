#!/bin/bash
# 将对话内容保存到有道云笔记
# 用法：bash save-conversation-to-youdaonote.sh "对话主题" "对话内容"

set -e

THEME="${1:-对话记录}"
CONTENT="${2:-无内容}"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)
TITLE="Agent World/${DATE} - ${THEME}"

# 将纯文本转换为 HTML
HTML="<h1>${TITLE}</h1>"
HTML+="<p><strong>时间：</strong>${DATE} ${TIME}</p>"
HTML+="<hr>"
HTML+="<pre>${CONTENT}</pre>"

# 构建符合 upload 模式的 JSON payload
PAYLOAD=$(jq -n \
  --arg title "$TITLE" \
  --arg bodyHtml "$HTML" \
  --arg sourceUrl "" \
  --argjson markdown false \
  --argjson images "[]" \
  '{title: $title, bodyHtml: $bodyHtml, sourceUrl: $sourceUrl, markdown: $markdown, images: $images}')

# 使用 upload 模式，通过 stdin 传入 payload
echo "$PAYLOAD" | \
  node /home/openclaw/.openclaw/workspace/skills/youdaonote-clip/clip-note.mjs \
    --upload \
    --api-key "iv1Q04UoH5aSj2cWxFpmnONjjN8BNOTKF-U-fc57c6e31731c920"

echo "✅ 对话已保存到有道云笔记：${TITLE}"
