# 公告数据 API 参考

## 基础信息

- **Base URL**: `http://192.168.41.96:8452`
- **认证**: 无需认证

## 接口: 获取公告列表

```
GET /api/v1/announcements
```

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| infotype | string | 是 | 公告类型编码 |
| start_date | string | 是 | 开始日期 YYYY-MM-DD |
| end_date | string | 是 | 结束日期 YYYY-MM-DD |
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页条数，默认 100 |

### 支持的 infotype

| infotype 编码 | 中文名 |
|---------------|--------|
| O_临时公告_董事会决议 | 董事会决议 |
| O_临时公告_人事变动 | 人事变动 |
| O_临时公告_设立产业基金 | 设立产业基金 |
| O_临时公告_与私募基金合作投资 | 与私募基金合作投资 |
| O_临时公告_药品批准 | 药品批准 |
| O_临时公告_应当披露交易 | 应当披露交易 |

### 响应结构

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 220,
    "page": 1,
    "page_size": 100,
    "total_pages": 3,
    "items": [
      {
        "met_meta": {
          "met_uuid": "uuid",
          "met_date": "2026-01-15",
          "met_time": "2026-01-15 19:00:11",
          "met_sec_code": "301511",
          "met_sec_name": "德福科技",
          "met_title": "第三届董事会第二十次会议决议公告",
          "met_link": "http://static.cninfo.com.cn/finalpage/...",
          "met_link_oss": "...",
          "met_link_html_oss": "..."
        },
        "extracted_info": [
          {
            "infotype": "董事会决议",
            "infotype_code": "董事会决议",
            "version": "O_临时公告_董事会决议",
            "extract_nums": 0,
            "info": {
              "原文_公告名称": "...",
              "原文_董事会届次": "...",
              "原文_通过议案名称": "..."
            },
            "metadata": [{"source": "o_extractor", "timestamp": "..."}]
          }
        ]
      }
    ]
  }
}
```

### 关键字段说明

**met_meta（公告元数据）**:
- `met_sec_code`: 证券代码（用于按公司聚合）
- `met_sec_name`: 证券简称
- `met_title`: 公告标题
- `met_date`: 公告日期
- `met_link`: 原文 PDF 链接（cninfo）
- `met_link_oss`: OSS 存储的 PDF 链接
- `met_link_html_oss`: HTML 版本链接

**extracted_info（提取信息）**:
- `info`: 核心提取字段字典，字段名以 `原文_` 前缀开头
- `infotype`: 信息类型中文名
- `extract_nums`: 提取的子记录数量
- `metadata.source`: 提取器来源标识
