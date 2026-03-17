# API 接口速查

## 目录

- [认证接口](#认证接口)
- [文档管理](#文档管理)
- [Schema 对话](#schema-对话)
- [Session 管理](#session-管理)
- [提取与修正](#提取与修正)
- [归档与历史](#归档与历史)
- [SSE 事件类型](#sse-事件类型)

---

## 认证接口

### 注册
`POST /api/v1/auth/register`
```json
{"username": "...", "password": "...", "email": "..."}
```
返回: `data.user_id`, `data.username`

### 登录
`POST /api/v1/auth/login`
```json
{"username": "...", "password": "..."}
```
返回: `data.access_token` — 后续所有请求需携带 `Authorization: Bearer <token>`

---

## 文档管理

### 上传文档
`POST /api/v1/documents/upload` (multipart/form-data)

| 字段 | 类型 | 说明 |
|------|------|------|
| files | File[] | 1-3 个 PDF 文件 |

返回: `data.documents[].document_id`, `data.documents[].filename`

---

## Schema 对话

### 创建对话
`POST /api/v1/session/schema-conversation/create`
```json
{"document_ids": ["abc123", "def456"]}
```
返回: `data.conversation_id`

### 对话设计 Schema (SSE)
`POST /api/v1/session/schema-conversation/{conversation_id}/chat`
```json
{"message": "请分析文档并设计提取Schema"}
```
返回: SSE 流，关注 `schema_updated` 事件获取生成的 Schema

### 获取对话状态
`GET /api/v1/session/schema-conversation/{conversation_id}`

返回: `data.current_schema`, `data.conversation_history`

---

## Session 管理

### 创建 Session
`POST /api/v1/session/create`
```json
{
  "session_name": "任务名称",
  "schema_json": { "type": "object", "properties": {...} },
  "initial_document_ids": ["abc123"]
}
```
返回: `data.session_id`

### Session 列表
`GET /api/v1/session/list`

返回: `data.sessions[]`

### 加载 Session
`GET /api/v1/session/load?session_id=1`

返回: `data.schema_json`, `data.extraction_code`, `data.experience_json`, `data.archived_results`

---

## 提取与修正

### 执行提取 (SSE)
`POST /api/v1/extract`
```json
{"session_id": 1, "documents_list": ["abc123", "def456"]}
```
返回: SSE 流，关注 `batch_created`（获取 batch_id）和 `result_update`（获取提取结果）

### 对话修正 (SSE)
`POST /api/v1/chat/{batch_id}`
```json
{"message": "作者列表不完整，请重新提取"}
```
返回: SSE 流，事件类型同提取接口

---

## 归档与历史

### 结束归档
`POST /api/v1/batch/end/{batch_id}`

返回: `data.experience_task_id`, `data.code_summary_task_id`（可选）

### 查看历史
`GET /api/v1/history/{session_id}`

返回: `data.results[].doc_id`, `data.results[].final_json`

---

## SSE 事件类型

所有 SSE 接口统一使用 `data: {JSON}\n\n` 格式：

| type | 说明 | 关键字段 |
|------|------|----------|
| `user_message` | 用户消息回显 | `content` |
| `message` | AI 回复 | `content`, `role` |
| `tool_call` | 工具调用 | `tool_name`, `result` |
| `batch_created` | Batch 创建 | `batch_id` |
| `result_update` | 提取结果更新 | `content` (结果数组) |
| `schema_updated` | Schema 更新 | `schema` |
| `error` | 错误 | `message` |
| `done` | 流结束 | — |

## 统一响应格式

非 SSE 接口统一信封格式：
```json
{"code": 200, "success": true, "message": "操作成功", "data": {...}}
```
