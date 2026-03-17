---
name: insightdoc
description: 调用 InsightDoc API 解析 PDF/图片文档，输出 md、json、html 等格式。支持财报解析(finance_ocr)和通用文档解析(docparse)。
---

# InsightDoc 文档解析技能

基于 InsightDoc API (`https://insightdoc.memect.cn/`) 的文档解析技能，支持将 PDF 或图片转换为结构化数据。

## API Key 配置（重要）

本技能需要 API Key 认证，按以下优先级获取：

1. **环境变量**（推荐）：`export INSIGHTDOC_API_KEY="sk-xxxxxxxxxxxx"`
2. **`.env` 文件**：在项目根目录创建 `.env` 文件，写入 `INSIGHTDOC_API_KEY=sk-xxxxxxxxxxxx`
3. **命令行参数**：`--api-key sk-xxxxxxxxxxxx`（临时使用）

> ⚠️ 禁止将 API Key 硬编码到代码或 SKILL.md 中。`.env` 文件已在 `.gitignore` 中排除。

## 核心能力

| 功能 | 说明 |
|------|------|
| 本地文件解析 | 上传本地 PDF/图片，等待解析完成，返回结果 |
| URL 文件解析 | 先下载远程 PDF，再上传解析 |
| 多格式输出 | md、html、block_md、docx（通用）；matrix、normalization（财报） |
| 多版本支持 | 通用解析支持 v1/v2 版本切换 |
| 结果导出 | 导出为指定格式文件 |

## 使用方式

### 1. 解析本地文件

```bash
python .cursor/skills/insightdoc/scripts/parse.py --file <文件路径> --type <任务类型> --format <输出格式> [--version <版本>]
```

### 2. 解析远程 URL 文件

```bash
python .cursor/skills/insightdoc/scripts/parse.py --url <PDF的URL> --type <任务类型> --format <输出格式>
```

### 3. 查询已有任务

```bash
python .cursor/skills/insightdoc/scripts/parse.py --task-id <任务ID> --format <输出格式>
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--file` | 与 `--url`/`--task-id` 三选一 | 本地文件路径（PDF/JPG/PNG，≤50MB） |
| `--url` | 与 `--file`/`--task-id` 三选一 | 远程 PDF 文件 URL |
| `--task-id` | 与 `--file`/`--url` 三选一 | 已有任务 ID，直接查询结果 |
| `--type` | 否 | `docparse`（默认）或 `finance_ocr` |
| `--format` | 否 | 输出格式，见下表 |
| `--version` | 否 | 解析版本（如 `v1`、`v2`），仅通用解析有效 |
| `--output` | 否 | 结果保存路径（默认输出到 stdout） |
| `--api-key` | 否 | 临时指定 API Key，覆盖环境变量 |

### 输出格式对照

| 任务类型 | 可选格式 |
|----------|----------|
| `docparse` | `md`（默认）、`html`、`block_md`、`docx` |
| `finance_ocr` | `matrix`、`normalization` |

## 智能体调用示例

当用户说：
- "解析这个 PDF" → `--file <路径> --type docparse --format md`
- "把这个财报转成矩阵格式" → `--file <路径> --type finance_ocr --format matrix`
- "解析这个链接的文档" → `--url <URL> --type docparse --format md`
- "用 v2 版本解析" → 加 `--version v2`
- "输出 JSON 到文件" → 加 `--output result.json`

## 进化机制

- 脚本运行异常时自动向下方追加经验记录
- 执行任务前请先查看"自动记录"部分

## 自动记录

- **[2026-02-12 11:57]** `RuntimeError`: API 请求失败 [400]: {"detail":"Unable to detect file type"}

- **[2026-02-12 18:44]** `RuntimeError`: API 请求失败 [403]: {"detail":"Usage limit exceeded"}

- **[2026-02-12 18:50]** `RuntimeError`: API 请求失败 [403]: {"detail":"Usage limit exceeded"}
