#!/bin/bash
# 将对话内容保存到有道云笔记
# 用法：bash save-conversation-to-youdaonote.sh "对话主题" "对话内容"

set -e

THEME="${1:-对话记录}"
CONTENT="${2:-无内容}"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)
TITLE="Agent World/${DATE} - ${THEME}"

# 将纯文本转换为 Markdown
HTML="<h1>${TITLE}</h1>"
HTML+="<p><strong>时间：</strong>${DATE} ${TIME}</p>"
HTML+="<hr>"
HTML+="<pre>${CONTENT}</pre>"

echo "$HTML" | \
  node /home/openclaw/.openclaw/workspace/skills/youdaonote-clip/clip-note.mjs \
    --clip-web-page \
    --api-key "iv1Q04UoH5aSj2cWxFpmnONjjN8BNOTKF-U-fc57c6e31731c920" \
    --source-url "https://openclaw.ai/dialogue/$(date +%s)" \
    --title "${TITLE}" \
    --body-file /dev/stdin

echo "✅ 对话已保存到有道云笔记：${TITLE}"
