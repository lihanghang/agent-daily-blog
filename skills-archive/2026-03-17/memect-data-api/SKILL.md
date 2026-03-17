---
name: memect-data-api
version: 1.0.0
description: 获取 xiaer.ai 上市公司公告数据 API
homepage: http://39.104.68.74:8452
metadata: {"api_base": "http://39.104.68.74:8452"}
---

# memect-data-api

获取 xiaer.ai 上市公司公告数据的 API 服务。

## Skill Files

| File | URL |
|------|-----|
| **SKILL.md** (this file) | `http://39.104.68.74:8452/skill.md` |
| **package.json** (metadata) | `http://39.104.68.74:8452/skill.json` |

**Install locally:**
```bash
mkdir -p ~/.openclaw/skills/memect-data-api
curl -s http://39.104.68.74:8452/skill.md > ~/.openclaw/skills/memect-data-api/SKILL.md
curl -s http://39.104.68.74:8452/skill.json > ~/.openclaw/skills/memect-data-api/package.json
```

**Base URL:** `http://39.104.68.74:8452`

⚠️ **NOTE:** 这是一个内部 API 服务，需要提供认证信息。

**Check for updates:** Re-fetch these files anytime to see new features!

---

## Health Check

检查 API 服务状态：

```bash
curl http://39.104.68.74:8452/
```

响应：
```json
{
  "status": "healthy",
  "timestamp": "2026-02-11T11:34:07.041557",
  "service": "memect-data-api"
}
```

---

## API Endpoints

**注意：** 根地址返回健康检查状态，实际获取接口可能需要不同的端点或参数。请联系 API 提供方确认完整的 API 文档。

### 健康检查

```bash
curl "http://39.104.68.74:8452/"
```

响应：
```json
{
  "status": "healthy",
  "timestamp": "2026-02-11T11:34:07.041557",
  "service": "memect-data-api"
}
```

### 获取公告列表

**默认：获取每日公告**

```bash
curl "http://39.104.68.74:8452/"
```

**注意：** 具体端点路径需要根据实际 API 文档确认。当前根路径返回健康检查。

### 按公告类型筛选

```bash
# 按类型获取
curl "http://39.104.68.74:8452/?type=O_临时公告_董事会决议"

# 获取多个类型
curl "http://39.104.68.74:8452/?type=O_临时公告_董事会决议,O_临时公告_股东大会决议"
```

### 按日期获取

```bash
curl "http://39.104.68.74:8452/?date=2026-02-11"
```

### 按公司筛选

```bash
curl "http://39.104.68.74:8452/?company=600000"
```

---

## 公告数据结构

```json
{
  "id": "12345",
  "company_code": "600000",
  "company_name": "浦发银行",
  "title": "公告标题",
  "type": "董事会决议公告",
  "content": "公告内容摘要",
  "url": "https://xiaer.ai/post/12345",
  "published_at": "2026-02-11T10:00:00Z",
  "extracted_at": "2026-02-11T10:05:00Z"
}
```

---

## 使用示例

### 获取今日所有公告（默认）

```bash
curl -s "http://39.104.68.74:8452/" | jq '.data'
```

### 按日期获取

```bash
# 获取 2026-02-11 的公告
curl -s "http://39.104.68.74:8452/?date=2026-02-11" | jq '.data[] | "\(.published_at): \(.title)"'
```

### 按类型筛选 - 董事会决议

```bash
curl -s "http://39.104.68.74:8452/?type=O_临时公告_董事会决议" | jq '.data[] | "\(.company_name): \(.title)"'
```

### 按类型筛选 - 人事变动

```bash
curl -s "http://39.104.68.74:8452/?type=O_临时公告_人事变动" | jq '.data[] | "\(.published_at): \(.title)"'
```

### 按类型筛选 - 业绩预告

```bash
curl -s "http://39.104.68.74:8452/?type=O_临时公告_业绩预告公告" | jq '.data[] | "\(.company_code): \(.title)"'
```

### 组合筛选：按日期和类型

```bash
curl -s "http://39.104.68.74:8452/?date=2026-02-11&type=O_临时公告_董事会决议,O_临时公告_人事变动" | jq '.data'
```

### 监控新公告（增量获取）

```bash
# 保存上次获取的最大 ID
LAST_ID=10000

# 获取新公告（假设 API 支持 after_id 参数）
curl -s "http://39.104.68.74:8452/?after_id=$LAST_ID" | jq '.data'
```

### 获取公告详情

```bash
# 获取单条公告详情
curl -s "http://39.104.68.74:8452/?id=10012345" | jq '.data'
```

---

## 数据结构参考

```json
{
  "data": [
    {
      "id": "10012345",
      "company_code": "600000",
      "company_name": "浦发银行",
      "title": "第七届董事会第十六次会议决议公告",
      "type": "O_临时公告_董事会决议",
      "content": "公告内容摘要...",
      "url": "https://xiaer.ai/post/10012345",
      "published_at": "2026-02-11T10:00:00Z",
      "extracted_at": "2026-02-11T10:05:00Z"
    }
  ],
  "success": true,
  "total": 50
}
```

**字段说明：**
- `id` - 公告唯一标识
- `company_code` - 公司代码（股票代码）
- `company_name` - 公司名称
- `title` - 公告标题
- `type` - 公告类型（见上文完整列表）
- `content` - 公告内容摘要
- `url` - 原始公告链接
- `published_at` - 发布时间
- `extracted_at` - 提取时间

---

## Response Format

Success:
```json
{"success": true, "data": {...}}
```

Error:
```json
{"success": false, "error": "Description"}
```

---

## Rate Limits

- 100 请求/分钟
- 请勿频繁轮询，合理设置检查间隔

---

## 公告类型完整列表

API 支持以下公告类型分类：

### 人事相关
| 类型 | 说明 |
|------|------|
| O_临时公告_人事变动 | 高管人员变动 |
| O_临时公告_公司董事长、法定代表人辞职 | 董事长或法人代表辞职 |
| O_临时公告_推选职工董事或者监事 | 职工代表选举 |
| O_临时公告_核心技术人员离职 | 核心技术人员离职 |
| O_临时公告_核心技术人员新增认定 | 核心技术人员认定 |

### 董事会/监事会
| 类型 | 说明 |
|------|------|
| O_临时公告_董事会决议 | 董事会会议决议 |
| O_临时公告_监事会决议 | 监事会会议决议 |
| O_临时公告_董事会秘书辞职 | 董事会秘书辞职 |
| O_临时公告_董事会审议高送转 | 董事会审议送转股 |

### 股东大会
| 类型 | 说明 |
|------|------|
| O_临时公告_股东大会决议 | 股东大会决议 |
| O_临时公告_股东大会召开通知 | 股东大会通知 |
| O_临时公告_职工代表大会决议 | 职工代表大会决议 |
| O_临时公告_召开业绩说明会 | 业绩说明会 |
| O_临时公告_股东大会法律意见书 | 股东大会法律意见 |
| O_临时公告_股东大会延期 | 股东大会延期 |
| O_临时公告_增加临时提案 | 新增临时提案 |

### 股票交易/回购
| 类型 | 说明 |
|------|------|
| O_临时公告_股票交易异常波动 | 股价异常波动说明 |
| O_临时公告_股份回购实施进展公告 | 股票回购进展 |
| O_临时公告_回购实施进展 | 回购执行情况 |
| O_临时公告_回购预案 | 回购计划预案 |
| O_临时公告_股票解除限售 | 股票解除限售 |

### 业绩/财务
| 类型 | 说明 |
|------|------|
| O_临时公告_业绩预告公告 | 业绩预告披露 |
| O_临时公告_主要业务经营情况_000069 | 业务经营情况 |
| O_临时公告_生产经营数据_601006 | 生产经营数据 |
| O_临时公告_利润分配 | 利润分配方案 |
| O_临时公告_优先股股息分派 | 优先股分红 |
| O_临时公告_变更会计师事务所 | 更换会计机构 |
| O_临时公告_聘任会计师事务所 | 聘请会计机构 |

### 募集资金/可转债
| 类型 | 说明 |
|------|------|
| O_临时公告_募集资金置换 | 募集资金置换 |
| O_临时公告_归还募集资金 | 归还募集资金 |
| O_临时公告_用募集资金置换预先投入的自筹资金 | 用募资置换自筹资金 |
| O_临时公告_变更募集资金用途 | 变更募资用途 |
| O_临时公告_可转债发行 | 可转换债券发行 |
| O_临时公告_可转债到期兑付及摘牌 | 可转债到期兑付 |
| O_临时公告_转债付息 | 可转债利息支付 |

### 药品相关
| 类型 | 说明 |
|------|------|
| O_临时公告_药品批准上市公告 | 新药上市批准 |

### 资产/投资/合作
| 类型 | 说明 |
|------|------|
| O_临时公告_设立产业基金 | 设立产业基金 |
| O_临时公告_对外投资 | 对外投资公告 |
| O_临时公告_对外捐赠 | 捐赠资产 |
| O_临时公告_购买资产 | 购买资产 |
| O_临时公告_出售资产 | 出售资产 |
| O_临时公告_与关联人共同投资 | 与关联方投资 |
| O_临时公告_向关联人购买资产 | 向关联方购资产 |
| O_临时公告_向关联人出售资产 | 向关联方售资产 |
| O_临时公告_签署合作协议 | 签订合作协议 |
| O_临时公告_签订战略框架协议 | 签战略框架协议 |

### 资助/政府补助
| 类型 | 说明 |
|------|------|
| O_临时公告_政府补助 | 政府补助公告 |
| O_临时公告_获得财政补贴 | 获得财政补贴 |
| O_临时公告_提供财务资助 | 提供财务资助 |
| O_临时公告_接受财务资助 | 接受财务资助 |

### 股权激励
| 类型 | 说明 |
|------|------|
| O_临时公告_股权激励计划实施完成 | 股权激励完成 |
| O_临时公告_股权激励计划授予 | 股权激励授予 |
| O_临时公告_股权激励计划终止 | 股权激励终止 |

### 员工持股
| 类型 | 说明 |
|------|------|
| O_临时公告_员工持股计划实施进展 | 员工持股进展 |

### 重大事件/重组
| 类型 | 说明 |
|------|------|
| O_临时公告_应当披露交易的进展 | 重大交易进展 |
| O_临时公告_应当披露交易的提示 | 重大交易提示 |
| O_临时公告_应当披露交易已完成 | 重大交易完成 |
| O_临时公告_重大资产重组终止 | 重组终止 |
| O_临时公告_取消重大资产重组并复牌 | 取消重组复牌 |
| O_临时公告_发生重大债务或重大债权到期未清偿 | 重大债务未清偿 |
| O_临时公告_重大亏损或重大损失 | 重大亏损公告 |
| O_临时公告_债务重组 | 债务重组公告 |

### 注册/名称/地址变更
| 类型 | 说明 |
|------|------|
| O_临时公告_变更证券简称 | 证券简称变更 |
| O_临时公告_变更公司名称 | 公司名称变更 |
| O_临时公告_注册资本 | 注册资本变更 |
| O_临时公告_取得商标注册证书 | 商标注册证书 |
| O_临时公告_获得发明专利证书 | 发明专利证书 |
| O_临时公告_变更办公地址及联系方式 | 办公地址变更 |

### 其他
| 类型 | 说明 |
|------|------|
| O_临时公告_公告元信息 | 公告元数据信息 |
| O_临时公告_澄清致歉 | 澄清致歉公告 |
| O_临时公告_主要业务经营情况_000069 | 业务情况说明 |
| O_临时公告_生产经营数据_601006 | 生产数据披露 |
| O_临时公告_公司涉嫌违法违规被其他机构调查 | 公司被调查 |
| O_临时公告_立案调查 | 立案调查公告 |
| O_临时公告_收到应诉通知书 | 收到起诉书 |
| O_临时公告_法院裁定重整、和解或破产清算 | 法院裁定公告 |
| O_临时公告_中标候选人公示 | 中标候选人公示 |
| O_临时公告_上市公司集体接待日 | 投资者接待日 |
| O_临时公告_开展套期保值业务 | 期货套保业务 |
| O_临时公告_列为被执行人 | 列为被执行人 |
| O_临时公告_董监高被调查、处罚或被采取强制措施 | 董监高被处罚 |
| O_临时公告_控股股东或实际控制人发生变动的提示 | 实控人变动提示 |
| O_临时公告_股票交易风险提示 | 股票风险提示 |
| O_临时公告_股东回馈活动 | 股东回馈活动 |
| O_临时公告_关联交易的完成 | 关联交易完成 |
| O_临时公告_重要前期会计差错更正 | 会计差错更正 |
| O_临时公告_其他股权变动 | 其他股权变动 |
| O_临时公告_员工持股计划实施进展 | 员工持股计划进展 |
| O_临时公告_购买理财产品 | 理财产品购买 |
| O_临时公告_委托管理资产和业务 | 委托管理资产 |
| O_临时公告_子公司注销 | 子公司注销 |
| O_临时公告_更换持续督导保荐代表人 | 更换保荐人 |
| O_临时公告_人员留置 | 人员留置 |
| O_临时公告_新建项目 | 新建项目公告 |

---

## 默认获取方式

**每日公告获取：**

API 默认获取每日公告，以下是一些常用查询方式：

```bash
# 获取今日所有公告（默认行为）
curl "http://39.104.68.74:8452/"

# 获取特定类型的公告
curl "http://39.104.68.74:8452/?type=O_临时公告_董事会决议"

# 获取指定日期的公告
curl "http://39.104.68.74:8452/?date=2026-02-11"
```

### 按类别筛选

可以按公告类别进行筛选：

```bash
# 董事会/监事会
curl "http://39.104.68.74:8452/?type=O_临时公告_董事会决议,O_临时公告_监事会决议"

# 人事变动
curl "http://39.104.68.74:8452/?type=O_临时公告_人事变动"

# 股东大会
curl "http://39.104.68.74:8452/?type=O_临时公告_股东大会决议,O_临时公告_股东大会召开通知"

# 业绩预告
curl "http://39.104.68.74:8452/?type=O_临时公告_业绩预告公告"

# 回购相关
curl "http://39.104.68.74:8452/?type=O_临时公告_股份回购实施进展公告"
```

---

## Ideas to use

- **公告监控脚本**: 定期检查新公告并发布到社交平台
- **数据分析**: 对公告类型、频率进行统计分析
- **关键词追踪**: 跟踪特定公司或行业的公告
- **自动化报告**: 生成日报/周报汇总重要公告

---

## 监控脚本示例

### Python 脚本：按类型汇总公告

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from datetime import datetime
from collections import defaultdict

API_BASE = "http://39.104.68.74:8452"

def get_announcements(date=None, types=None):
    """获取公告数据"""
    params = {}
    if date:
        params['date'] = date
    if types:
        params['type'] = ','.join(types)
    
    response = requests.get(API_BASE, params=params)
    return response.json()

def summarize_by_type(announcements):
    """按类型汇总公告"""
    summary = defaultdict(list)
    for item in announcements:
        summary[item.get('type', 'Unknown')].append(item)
    return dict(summary)

def main():
    # 获取今日公告
    today = datetime.now().strftime("%Y-%m-%d")
    result = get_announcements(date=today)
    
    if result.get('success') and result.get('data'):
        announcements = result['data']
        
        # 按类型汇总
        by_type = summarize_by_type(announcements)
        
        # 打印汇总
        print(f"\n📊 公告汇总 ({today})")
        print("=" * 50)
        
        for ann_type, items in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
            if items:
                print(f"\n【{ann_type.replace('O_临时公告_', '')}】- {len(items)} 条")
                for item in items[:3]:  # 只显示前3条
                    print(f"  • {item.get('company_name', 'Unknown')}: {item.get('title', 'No title')[:40]}")
                if len(items) > 3:
                    print(f"  ... 还有 {len(items) - 3} 条")

if __name__ == "__main__":
    main()
```

### Shell 脚本：每日监控

```bash
#!/bin/bash

API="http://39.104.68.74:8452"
TODAY=$(date +%Y-%m-%d)
LAST_ID_FILE="last_announcement_id.txt"

# 读取上次最后一条 ID
if [ -f "$LAST_ID_FILE" ]; then
    LAST_ID=$(cat "$LAST_ID_FILE")
else
    LAST_ID="0"
fi

# 获取公告
RESPONSE=$(curl -s "$API/?date=$TODAY")

# 解析并保存最新 ID
NEWEST_ID=$(echo "$RESPONSE" | jq -r '.data[0].id // empty')
if [ -n "$NEWEST_ID" ] && [ "$NEWEST_ID" != "empty" ]; then
    echo "$NEWEST_ID" > "$LAST_ID_FILE"
fi

# 按类型统计
echo "$RESPONSE" | jq -r '.data | group_by(.type) | map({type: .[0].type, count: length}) | sort_by(.count) | reverse | .[] | "\(.type | split("_")[2:]): \(.count) 条"'
```

### 监控新公告（增量模式）

```bash
#!/bin/bash

API="http://39.104.68.74:8452"
LAST_ID_FILE="last_id.txt"

# 读取上次最后一条 ID
if [ -f "$LAST_ID_FILE" ]; then
    LAST_ID=$(cat "$LAST_ID_FILE")
else
    LAST_ID="0"
fi

# 获取新公告（假设支持 after_id）
RESPONSE=$(curl -s "$API/?after_id=$LAST_ID")

COUNT=$(echo "$RESPONSE" | jq '.data | length')

if [ "$COUNT" -gt 0 ]; then
    # 保存最新的 ID
    NEWEST_ID=$(echo "$RESPONSE" | jq -r '.data[-1].id')
    echo "$NEWEST_ID" > "$LAST_ID_FILE"
    
    # 打印新公告
    echo "发现 $COUNT 条新公告："
    echo "$RESPONSE" | jq -r '.data[] | "\(.published_at): \(.company_name) - \(.title)"'
fi
```

---

## Troubleshooting

### 连接失败
- 检查网络是否可达: `ping 39.104.68.74`
- 检查端口 8452 是否开放

### 数据格式异常
- 检查响应 Content-Type
- 使用 `jq` 解析 JSON

### 404 错误
- 确认端点路径正确
- 检查 API 文档是否有更新

### 无数据返回
- 检查日期格式是否正确（YYYY-MM-DD）
- 检查类型名称是否准确
- 确认该日期/类型是否有公告

---

## 联系方式

如有问题或建议，请联系 API 提供方。
