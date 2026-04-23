---
name: memect-ppx
version: 0.0.2
title: memect-ppx — High-Accuracy PDF / Image Parser
description: Parse PDF and images into structured Markdown / JSON using PPX. Supports OCR, table extraction, formulas, multi-column layouts, and LLM backends.
metadata:
  openclaw:
    requires:
      bins:
        - ppx
    primaryEnv: null
---

# PPX 解析 Skill

PPX（memect-ppx）是一款本地运行的高精度文档解析引擎，将 PDF / 图片转换为
结构化 Markdown 和 JSON，无需 GPU，开箱即用。

## 安装

```bash
pip install memect-ppx
pip install onnxruntime
pip install opencv-contrib-python
```

Python ≥ 3.12。在 Linux 无头环境下将 `opencv-contrib-python` 替换为
`opencv-python-headless`。

## 基本用法

```bash
# 解析单个 PDF，输出到 output/ 目录
ppx parse report.pdf -o output/

# 解析图片
ppx parse scan.png -o output/

# 批量解析目录
ppx parse docs/ -o output/

# 只解析指定页面
ppx parse report.pdf --pages "1-5,10,15-20" -o output/
```

输出结构（写入 `<file>.out/`）：

| 路径 | 说明 |
| ---- | ---- |
| `doc.md` | 完整文档 Markdown，含图形引用 |
| `doc.json` | JSON 树：文档 → 页面 → 对象，每个对象含坐标 |
| `pages/` | 逐页 Markdown / JSON，适合页面级处理 |
| `images/` | 提取的图像区域（检测到图形时存在） |

## OCR 控制

```bash
ppx parse report.pdf --ocr auto    # 默认：自动判断
ppx parse report.pdf --ocr yes     # 强制 OCR（扫描件）
ppx parse report.pdf --ocr no      # 跳过 OCR（原生 PDF）
```

## 表格解析模式

```bash
ppx parse file.pdf --table auto    # 默认：自动选择
ppx parse file.pdf --table wbk     # 白底表格（推荐普通文档）
ppx parse file.pdf --table ybk     # 彩色/深色背景表格
ppx parse file.pdf --table llm     # LLM 辅助（最高精度，需配置后端）
ppx parse file.pdf --table no      # 跳过表格解析
```

## LLM 后端

| 后端 | 场景 | 显存需求 |
| ---- | ---- | -------- |
| `default` | 隐私、离网、CI | CPU，无需 GPU |
| `deepseek` | 复杂版面最高精度 | ~20 GB |
| `paddle` | 精度较好、显存小 | ~10 GB |
| `glm` | 快速推理 | ~10 GB |

```bash
# 使用 DeepSeek-OCR-2 后端（需本地 vLLM 服务）
ppx parse report.pdf --backend deepseek \
  --deepseek '{"base_url":"http://127.0.0.1:4000/v1","model":"deepseek-ocr-2","api_key":""}'

# 使用 PaddleOCR-VL 后端
ppx parse report.pdf --backend paddle \
  --paddle '{"base_url":"http://127.0.0.1:4001/v1","model":"paddleocr-vl","api_key":""}'

# 使用 GLM-OCR 后端
ppx parse report.pdf --backend glm \
  --glm '{"base_url":"http://127.0.0.1:4002/v1","model":"glmocr","api_key":""}'
```

持久化配置（避免每次重复填写）：

```bash
ppx parse report.pdf --set backend="deepseek" \
  --set deepseek.base_url="http://127.0.0.1:4000/v1"
```

## 其他选项

```bash
--mode page|tree|ppt     # 解析模式（默认 page）
--workers N              # 目录并行解析线程数
--docx / --no-docx       # 输出 DOCX
--pptx / --no-pptx       # 输出 PPTX
--json                   # 仅输出 JSON
--cpu                    # 强制 CPU（即使有 GPU）
--debug / -x             # 输出调试信息和中间图
--dev                    # 开发模式，保存中间结果
```

## Python API

```python
from memect.pdf.parser import Parser
from memect.pdf.base import KDocument

# 单次解析
with Parser() as parser:
    doc = KDocument("/path/your.pdf")
    parser.parse(doc)

# 批量多进程
from memect.pdf.base import KDocumentFactory
docs = [KDocumentFactory("/path/your.pdf", params=None)]
Parser.batch(docs, max_workers=4)
```

`Parser` 对象全局共享，多次调用时只需实例化一次。

## 常见问题

- **Linux `ImportError: libGL.so.1`** → `pip install opencv-python-headless`
  或 `sudo apt-get install -y libgl1`
- **Mac 无法 GPU 加速** → Apple Silicon / Intel Mac 不支持 CUDA，CPU 模式正常运行
- **`onnxruntime` 与 `onnxruntime-gpu` 冲突** → 只安装其中一个

## 许可证

非商业免费（PolyForm Noncommercial 1.0.0）。商用联系 `contact@memect.co`。
在线体验：https://pdf2x.cn/
