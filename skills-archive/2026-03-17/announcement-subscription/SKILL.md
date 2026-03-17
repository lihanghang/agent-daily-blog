---
name: announcement-subscription
version: 1.0.0
description: 深交所公告订阅推送服务，支持按公司、类别订阅上市公司公告，并通过邮件/钉钉/飞书实时推送结构化提取结果
homepage: http://39.104.68.74:8452
metadata: {"api_base": "http://39.104.68.74:8452", "api_key": "mk_6b06aedefda608f513dd02599ff04c56"}
---

# announcement-subscription

深交所公告订阅推送服务，支持按公司、类别订阅上市公司公告，并通过邮件/钉钉/飞书实时推送结构化提取结果。

**Base URL:** `http://39.104.68.74:8452`

**API Key:** `mk_6b06aedefda608f513dd02599ff04c56`

**当前订阅配额：** 免费版（最多 3 个类别订阅）

---

## 快速开始

### 查看我的订阅列表

```bash
curl "http://39.104.68.74:8452/api/v1/subscriptions?page=1&page_size=20" \
  -H "X-API-Key: mk_6b06aedefda608f513dd02599ff04c56"
```

### 查看可订阅的类别

```bash
curl "http://39.104.68.74:8452/api/v1/subscriptions/available-categories" \
  -H "X-API-Key: mk_6b06aedefda608f513dd02599ff04c56"
```

### 创建新订阅

```bash
curl -X POST "http://39.104.68.74:8452/api/v1/subscriptions" \
  -H "X-API-Key: mk_6b06aedefda608f513dd02599ff04c56" \
  -H "Content-Type: application/json" \
  -d '{
    "sub_type": "category",
    "notify_method": "email",
    "notify_target": "lihanghang@memect.co",
    "category_code": "人事变动",
    "category_name": "人事变动"
  }'
```

### 删除订阅

```bash
curl -X DELETE "http://39.104.68.74:8452/api/v1/subscriptions/{subscription_id}" \
  -H "X-API-Key: mk_6b06aedefda608f513dd02599ff04c56"
```

---

## 订阅类型 (sub_type)

| 类型 | 说明 | 配额消耗 |
|------|------|---------|
| `company` | 订阅某公司所有已开放类别 | 1 |
| `category` | 订阅所有公司的某类别 | 1 |
| `company_category` | 精准订阅某公司某类别 | 1 |
| `daily_digest` | 每日聚合推送 | 不消耗配额 |

---

## 通知方式 (notify_method)

| 方式 | 说明 | 参数格式 |
|------|------|---------|
| `email` | 邮件推送 | 邮箱地址 |
| `dingtalk` | 钉钉机器人 | Webhook URL |
| `feishu` | 飞书机器人 | Webhook URL |

---

## 常用操作

### 1. 订阅某类别的所有公告

订阅所有公司的"董事会决议"公告，推送到飞书：

```bash
curl -X POST "http://39.104.68.74:8452/api/v1/subscriptions" \
  -H "X-API-Key: mk_6b06aedefda608f513dd02599ff04c56" \
  -H "Content-Type: application/json" \
  -d '{
    "sub_type": "category",
    "notify_method": "feishu",
    "notify_target": "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_URL",
    "category_code": "ctb_company_0081",
    "category_name": "董事会决议"
  }'
```

### 2. 订阅某公司的所有公告

订阅"平安银行"的所有公告，推送到邮件：

```bash
curl -X POST "http://39.104.68.74:8452/api/v1/subscriptions" \
  -H "X-API-Key: mk_6b06aedefda608f513dd02599ff04c56" \
  -H "Content-Type: application/json" \
  -d '{
    "sub_type": "company",
    "notify_method": "email",
    "notify_target": "lihanghang@memect.co",
    "company_code": "000001",
    "company_name": "平安银行"
  }'
```

### 3. 每日聚合推送

每天早上 9:00 收取昨日公告汇总：

```bash
curl -X POST "http://39.104.68.74:8452/api/v1/subscriptions" \
  -H "X-API-Key: mk_6b06aedefda608f513dd02599ff04c56" \
  -H "Content-Type: application/json" \
  -d '{
    "sub_type": "daily_digest",
    "notify_method": "email",
    "notify_target": "lihanghang@memect.co",
    "digest_time": "09:00"
  }'
```

### 4. 查看可订阅公司

```bash
curl "http://39.104.68.74:8452/api/v1/subscriptions/available-companies?keyword=平安&page=1&page_size=20" \
  -H "X-API-Key: mk_6b06aedefda608f513dd02599ff04c56"
```

---

## 可订阅类别

当前支持以下 14 个类别：

| 类别代码 | 类别名称 | 准确率 |
|---------|---------|--------|
| 人事变动 | 人事变动 | 97.73% |
| 业绩预告 | 业绩预告 | 98.66% |
| O_临时公告_股票交易异常波动 | 股票交易异常波动 | 100% |
| O_临时公告_变更证券简称 | 变更证券简称 | 100% |
| O_临时公告_召开业绩说明会 | 召开业绩说明会 | 97% |
| 核心技术人员离职 | 核心技术人员离职 | 100% |
| 业务资格获批 | 业务资格获批 | 100% |
| O_临时公告_用募集资金置换预先投入的自筹资金 | 用募集资金置换预先投入的自筹资金 | 95.3% |
| O_临时公告_变更会计师事务所 | 变更会计师事务所 | 100% |
| O_临时公告_中标候选人公示 | 中标候选人公示 | 96.88% |
| O_临时公告_取消重大资产重组并复牌 | 取消重大资产重组并复牌 | 100% |
| O_临时公告_重大资产重组终止 | 重大资产重组终止 | 95% |
| O_临时公告_应当披露交易的提示 | 应当披露交易的提示 | 98.03% |
| O_临时公告_股票交易风险提示 | 股票交易风险提示 | 97.29% |

---

## 当前订阅状态

### 我的订阅（2026-03-05）

| ID | 订阅类型 | 类别 | 通知方式 | 目标 | 状态 |
|----|---------|------|---------|------|------|
| 8 | 每日聚合 | 人事变动 | 邮件 | lihanghang@memect.co | ✅ |
| 7 | 类别订阅 | 股票交易风险提示 | 钉钉 | (webhook) | ✅ |
| 6 | 类别订阅 | 股票交易异常波动 | 飞书 | (webhook) | ✅ |
| 4 | 类别订阅 | 人事变动 | 飞书 | (webhook) | ✅ |
| 3 | 类别订阅 | 人事变动 | 钉钉 | (webhook) | ✅ |
| 2 | 类别订阅 | 人事变动 | 邮件 | lihanghang@memect.co | ✅ |

### 配额使用情况

- **免费版配额：** 3 个类别订阅
- **当前使用：** 3 个（订阅 #6, #4, #3）
- **每日聚合：** 不消耗配额（订阅 #8）
- **风险提示订阅：** 需要释放配额或升级

---

## 响应格式

### 成功响应

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "total": 6,
    "page": 1,
    "page_size": 20,
    "items": [...]
  }
}
```

### 错误响应

```json
{
  "detail": "关键词订阅配额已用完 (5/3)，当前等级: free"
}
```

---

## 注意事项

⚠️ **重要提示：**

1. **配额限制：** 免费版最多 3 个类别订阅
2. **删除机制：** 订阅删除为软删除（is_active = false），可能不立即释放配额
3. **重复订阅：** 重复订阅会返回错误
4. **推送重试：** 推送失败会自动重试（最多 3 次）
5. **更新限制：** 某些字段（如 notify_method）可能无法通过 API 更新

💡 **最佳实践：**

- 建议先查询可订阅类别和公司列表
- 测试时可使用邮件方式，生产环境推荐使用机器人
- 钉钉/飞书机器人需要配置加签密钥以提高安全性
- 使用 `daily_digest` 汇总推送，避免过于频繁的通知

---

## 对接建议

### 1. 集成到 OpenClaw

创建 Python 包装脚本，方便通过自然语言调用：

```python
#!/usr/bin/env python3
# scripts/announcement_subscription.py

import requests
import json
import sys

API_BASE = "http://39.104.68.74:8452"
API_KEY = "mk_6b06aedefda608f513dd02599ff04c56"

def get_headers():
    return {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def list_subscriptions():
    """查看所有订阅"""
    response = requests.get(
        f"{API_BASE}/api/v1/subscriptions?page=1&page_size=20",
        headers=get_headers()
    )
    return response.json()

def create_subscription(sub_type, notify_method, notify_target, category_code=None, category_name=None, company_code=None, company_name=None, digest_time=None):
    """创建订阅"""
    data = {
        "sub_type": sub_type,
        "notify_method": notify_method,
        "notify_target": notify_target
    }
    if category_code:
        data["category_code"] = category_code
        data["category_name"] = category_name
    if company_code:
        data["company_code"] = company_code
        data["company_name"] = company_name
    if digest_time:
        data["digest_time"] = digest_time

    response = requests.post(
        f"{API_BASE}/api/v1/subscriptions",
        headers=get_headers(),
        json=data
    )
    return response.json()

def delete_subscription(subscription_id):
    """删除订阅"""
    response = requests.delete(
        f"{API_BASE}/api/v1/subscriptions/{subscription_id}",
        headers=get_headers()
    )
    return response.json()

def get_available_categories():
    """获取可订阅类别"""
    response = requests.get(
        f"{API_BASE}/api/v1/subscriptions/available-categories",
        headers=get_headers()
    )
    return response.json()

def get_available_companies(keyword=None, page=1, page_size=20):
    """获取可订阅公司"""
    params = {"page": page, "page_size": page_size}
    if keyword:
        params["keyword"] = keyword
    response = requests.get(
        f"{API_BASE}/api/v1/subscriptions/available-companies",
        headers=get_headers(),
        params=params
    )
    return response.json()

if __name__ == "__main__":
    # 示例：查看订阅列表
    result = list_subscriptions()
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

### 2. 日常使用场景

用户可以直接说：

- "帮我查看订阅列表"
- "订阅人事变动公告到邮件"
- "删除订阅 #7"
- "看看有哪些类别可以订阅"
- "搜索平安银行"

### 3. Webhook 集成

**飞书机器人：**
1. 在飞书群设置 → 添加群机器人
2. 获取 Webhook URL
3. 使用订阅 API 创建订阅

**钉钉机器人：**
1. 在钉钉群设置 → 智能群助手 → 添加机器人
2. 获取 Webhook URL
3. 配置加签密钥（推荐）
4. 使用订阅 API 创建订阅

---

## 故障排查

### 配额已用完

**问题：** `detail: "关键词订阅配额已用完 (5/3)，当前等级: free"`

**解决方案：**
1. 删除不需要的订阅
2. 使用 `daily_digest` 汇总推送（不消耗配额）
3. 联系服务方升级套餐

### 订阅删除后配额未释放

**问题：** 删除订阅后仍提示配额已用完

**可能原因：** 软删除机制，配额未立即释放

**解决方案：**
1. 等待一段时间后重试
2. 联系服务方手动清理
3. 尝试更新订阅而不是删除

### 无法更新 notify_method

**问题：** 更新订阅时 `notify_method` 字段无变化

**解决方案：**
1. 删除订阅后重新创建
2. 联系服务方确认 API 限制

---

## 技术支持

- **API 文档：** http://39.104.68.74:8452/api-docs
- **官网：** http://39.104.68.74:8452
- **API Key：** mk_6b06aedefda608f513dd02599ff04c56

---

## 更新记录

- **2026-03-05:** 初始版本，集成公告订阅推送 API
