# ppx-parse Skill

将 PDF / 图片解析为结构化 Markdown / JSON 的 ClawHub AI Agent Skill，
基于 [PPX](https://github.com/memect/memect-ppx) 引擎。

## 功能

- 解析 PDF、扫描件、图片为 Markdown / JSON
- 支持 OCR、表格结构提取、公式、多列版面
- 可选接入 DeepSeek-OCR、PaddleOCR-VL、GLM-OCR 等 LLM 后端
- 本地运行，无需 GPU，保护隐私

## 安装

```bash
clawhub skill install memect/ppx-parse
```

## 前置条件

需本地安装 PPX CLI：

```bash
pip install memect-ppx onnxruntime opencv-contrib-python
```

## 使用示例

在 Claude Code 中直接提问：

> "帮我解析 report.pdf，提取所有表格"
> "把这个扫描件 PDF 转成 Markdown"
> "用 DeepSeek 后端解析这份复杂版面文档"

## 链接

- [PPX GitHub](https://github.com/memect/memect-ppx)
- [在线体验](https://pdf2x.cn/)
- [ClawHub 页面](https://clawhub.ai/memect/ppx-parse)
