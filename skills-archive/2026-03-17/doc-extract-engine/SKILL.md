---
name: doc-extract-engine
description: 通用文档提取引擎，通过远程 API 完成端到端文档信息提取。封装完整流程：认证 → 上传PDF → AI对话设计Schema → 创建Session → SSE流式提取 → 对话修正 → 归档。当用户需要：(1) 从PDF文档中提取结构化信息 (2) 设计文档提取Schema (3) 批量提取文档数据 (4) 修正提取结果 (5) 查看历史提取记录时使用此Skill。
---

# 文档提取引擎

通过远程 API 端到端完成 PDF 文档的结构化信息提取。

## 环境配置

使用前确保设置环境变量：

```bash
export EXTRACT_API_URL="http://39.104.68.74:8082"   # API 地址（默认值）
export EXTRACT_USERNAME="your_username"
export EXTRACT_PASSWORD="your_password"
# 或直接提供 token（跳过登录）
export EXTRACT_TOKEN="eyJhbGciOiJIUzI1NiIs..."
```

依赖：`pip install httpx`

## 核心流程

```
注册(首次) → 登录 → 上传PDF → Schema对话(AI设计) → 创建Session → 提取(SSE) → 对话修正 → 归档
```

## 使用方式

### 方式一：Python 编程式调用（推荐，Claude 直接使用）

将 `scripts/` 目录加入 `sys.path`，直接 import client：

```python
import sys
sys.path.insert(0, "<skill_path>/scripts")
from client import ExtractEngineClient

client = ExtractEngineClient("http://39.104.68.74:8082")

# 注册（首次使用，邮箱必须用合法域名如 @example.com，不能用 @xxx.local）
try:
    client.register("myuser", "mypassword", "myuser@example.com")
except Exception:
    pass  # 已注册则跳过

# 登录
client.login("myuser", "mypassword")

# 上传
docs = client.upload_documents(["doc1.pdf"])
doc_ids = [d["document_id"] for d in docs]

# Schema 对话（可多轮）
conv_id = client.create_schema_conversation(doc_ids)
result = client.chat_schema(conv_id, "提取论文标题和作者")

# ⚠️ schema 可能在 SSE 流中未返回，需 fallback 查询
schema = result.get("schema")
if not schema:
    conv_state = client.get_schema_conversation(conv_id)
    schema = conv_state.get("current_schema")

# 创建 Session 并提取
session_id = client.create_session("我的任务", schema, doc_ids)
result = client.extract(session_id, doc_ids)
batch_id = result["batch_id"]

# 修正（可选，可多轮）
client.chat_correct(batch_id, "作者列表不完整")

# 归档
client.end_batch(batch_id)
```

### 方式二：CLI 脚本（适合环境变量已配置的场景）

```bash
# 完整流程：上传 → Schema → 提取 → 归档
python scripts/extract_flow.py full \
  --files doc1.pdf doc2.pdf \
  --schema-prompt "提取论文标题、作者、摘要和关键词"

# 单步操作
python scripts/extract_flow.py upload --files doc1.pdf
python scripts/extract_flow.py extract --session-id 1 --doc-ids abc123
python scripts/extract_flow.py correct --batch-id 1 --message "作者不完整"
python scripts/extract_flow.py archive --batch-id 1
python scripts/extract_flow.py history --session-id 1
```

## 流程决策树

```
用户请求提取文档信息
  │
  ├─ 有现成 Session？
  │   ├─ 是 → 直接 extract（复用 schema）
  │   └─ 否 → 需要先设计 Schema
  │
  ├─ 有明确的 Schema？
  │   ├─ 是 → 跳过 Schema 对话，直接 create_session
  │   └─ 否 → 上传文档 → Schema 对话（AI 辅助设计）
  │
  ├─ 提取结果需要修正？
  │   ├─ 是 → chat_correct 多轮对话
  │   └─ 否 → 直接归档
  │
  └─ 需要查看历史？
      └─ get_history(session_id)
```

## SSE 流式接口处理

提取和对话接口返回 SSE 流。客户端已封装流式消费，关键事件：

- `batch_created` → 记录 batch_id，后续修正和归档需要
- `result_update` → 提取结果，`content` 字段为结果数组
- `schema_updated` → Schema 对话中生成的 Schema
- `error` → 错误信息，客户端自动抛出异常
- `done` → 流结束

自定义事件处理通过 `on_event` 回调：

```python
def my_handler(event):
    if event["type"] == "result_update":
        save_to_file(event["content"])

client.extract(session_id, doc_ids, on_event=my_handler)
```

## 关键约束与踩坑经验

- 每次上传限 1-3 个 PDF 文件
- Schema 对话支持多轮，直到 Schema 满意为止
- 对话修正支持多轮，直到结果满意为止
- 归档后系统自动触发经验总结和代码总结后台任务
- 所有非 SSE 接口返回统一信封格式 `{code, success, message, data}`

### 已知问题

- **注册邮箱校验严格**：不接受 `@xxx.local` 等保留域名，使用 `@example.com` 等合法域名
- **Schema fallback**：`chat_schema()` 的 SSE 流中 `schema_updated` 事件可能不携带 schema，务必用 `get_schema_conversation()` 兜底获取
- **SSE 超时**：提取和对话接口可能耗时较长，客户端 `_consume_sse` 已设置 `timeout=None`，不会超时断开

## 参考资料

- API 接口详情：参见 [references/api_guide.md](references/api_guide.md)
