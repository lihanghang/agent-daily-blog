# Content Collector 优化清单

> 基于 v1.1.0 代码审查，整理全部优化方向。
> 按优先级分层：P0 不修跑不起来，P1 架构基础，P2 体验提升，P3 生态联动。
>
> **状态说明**：✅ 已完成 | 🔄 部分完成 | ❌ 待处理
> **最后更新**：2026-03-14

---

## 一、架构问题（影响全局）

| # | 优先级 | 状态 | 问题 | 现状 | 建议 |
|---|--------|------|------|------|------|
| 1 | P1 | ❌ | **缺少统一输出 Schema** | 各提取器输出字段不一致（twitter 有 `stats`，jike/weixin 只返回 selector 提示） | 定义 `CollectedItem` JSON Schema，所有提取器统一输出，下游 skill（deep-writer、x-tweet-writer 等）可直接消费 |
| 2 | P0 | ✅ | **提取器大多是"空壳"** | ~~已删除~~ `extract_jike.py`、`extract_weixin.py`、`extract_reddit.py`，CSS selector 信息合并至 `extract_content.py` 的 `PLATFORM_RULES` 字典 | ~~要么真正实现提取逻辑，要么去掉这些脚本~~ → 已选择方案二：去掉空壳脚本，selector 指引内置到主入口 |
| 3 | P0 | ✅ | **硬编码路径** | ~~已修复~~ 移除了 `append_to_feishu.py` 中的 `sys.path.insert(0, '/root/...')` 和 `ocr_image.py` 中的硬编码 COS 配置路径 | ~~改用相对路径或环境变量~~ → 已改为环境无关实现 |
| 4 | P1 | ❌ | **存储只有单一飞书文档** | 所有内容堆在一个文档里，内容一多检索困难 | 支持飞书多维表格（Bitable）作为存储后端，天然支持按标签/平台/日期过滤和搜索 |

---

## 二、去重机制

| # | 优先级 | 状态 | 问题 | 建议 |
|---|--------|------|------|------|
| 5 | P2 | ✅ | **短链/变体 URL 漏判** | ~~已修复~~ `normalize_url()` 新增 `DOMAIN_ALIASES` 映射（twitter→x.com、okjike、reddit 等变体域名统一）+ `SHORT_URL_DOMAINS` 短链展开（t.co/bit.ly 等 HEAD 请求跟随重定向）+ 尾部斜杠剥离 |
| 6 | P3 | ❌ | **无语义去重** | 同一条内容从不同渠道收藏（比如 X 原帖 + 即刻转发），URL 不同但内容相同。需要内容指纹（simhash / 前 N 字符 hash） |
| 7 | P2 | ✅ | **缓存无上限、无清理** | ~~已修复~~ `_cleanup_cache()` 实现 30 天 TTL 过期 + 1000 条 LRU 上限，每次 `load_cache()` 时自动清理 |

---

## 三、内容提取

| # | 优先级 | 状态 | 问题 | 建议 |
|---|--------|------|------|------|
| 8 | P0 | ✅ | **X/Twitter 提取依赖不存在的 skill** | ~~需要适配实际可用的 skill~~ → 已重写 `extract_content.py`，使用 `x-tweet-fetcher` 作为 Twitter 首选 skill（已安装到 `~/.opencode/skills/x-tweet-fetcher/`） |
| 9 | P1 | 🔄 | **公众号/即刻反爬脆弱** | `PLATFORM_RULES` 中已定义每个平台的 `fallback_skills` 列表（`defuddle` → `baoyu-url-to-markdown`），但运行时自动降级逻辑尚未实现 |
| 10 | P2 | ❌ | **缺少 thread/长文支持** | X 的 thread（多条推文串）、公众号的多图文，现在只抓单条。需要递归抓取或 thread 展开逻辑 |
| 11 | P2 | ✅ | **原文截断 500 字** | ~~已修复~~ 移除 `content[:500]` 硬编码截断，全量存储原文 |

---

## 四、OCR

| # | 优先级 | 状态 | 问题 | 建议 |
|---|--------|------|------|------|
| 12 | P2 | ❌ | **pytesseract 在 macOS 上安装复杂** | 需要 `brew install tesseract` + 语言包，门槛高。macOS 可用系统 Vision framework（swift 脚本），零依赖 |
| 13 | P0 | ✅ | **腾讯云 OCR 路径也是硬编码** | ~~已修复~~ 移除了 `ocr_image.py` 中的硬编码 `/root/.openclaw/...` 路径，替换为环境无关的提示 |
| 14 | P1 | ❌ | **没有利用 agent 自身能力** | Agent 本身有 `look_at` 工具可以直接看图片，不需要额外 OCR 脚本。可简化为：agent 看图 → 提取文字/链接 → 走正常收集流程 |

---

## 五、飞书输出

| # | 优先级 | 状态 | 问题 | 建议 |
|---|--------|------|------|------|
| 15 | P2 | ❌ | **序号递增靠正则匹配文档** | `get_next_index()` 用正则从整个文档找最大序号，文档大时性能差且易误匹配。改用缓存记录 counter |
| 16 | P2 | ❌ | **无日期分组** | 所有内容平铺，没有按天/周分组。至少加日期分隔线，更好方案是按日期分文档或用 Bitable |
| 17 | P3 | ❌ | **格式不支持自定义** | 输出模板硬编码在 Python 里。应抽成 Jinja2 模板或写在 SKILL.md 里，方便用户改 |

---

## 六、工作流缺失

| # | 优先级 | 状态 | 问题 | 建议 |
|---|--------|------|------|------|
| 18 | P2 | ❌ | **无批量导入** | 只支持一条条丢链接。应支持：导入 X 书签列表、即刻收藏夹、浏览器书签导出文件 |
| 19 | P3 | ❌ | **无"回流"加工** | 存完就完了，没有二次利用。加周报汇总（按主题聚类）、趋势发现（高频关键词）、自动生成阅读笔记 |
| 20 | P3 | ❌ | **无 skill 联动接口** | 收集的数据是死的，没有标准化输出供其他 skill 消费。定义好 Schema 后可一键触发：收集 → `deep-writer` 写文 / `x-tweet-writer` 发推 / `baoyu-infographic` 出图 |
| 21 | P2 | ❌ | **每日提醒只是通知** | 现在只发"你今天收藏了 N 条"。应带摘要、带分类、带"你可能还没看的 3 条" |

---

## 七、工程质量

| # | 优先级 | 状态 | 问题 | 建议 |
|---|--------|------|------|------|
| 22 | P1 | ❌ | **无错误处理标准** | 各脚本 error 返回格式不统一，有的是 `{'error': str}`，有的是 `sys.exit(1)`。统一错误输出格式 |
| 23 | P2 | ❌ | **无测试** | 没有任何测试用例。至少加 URL 标准化、去重逻辑、平台检测的单元测试 |
| 24 | P0 | ✅ | **引用了不存在的文件** | ~~已修复~~ 从 SKILL.md v1.2.0 中移除了对 `references/example-output.md` 的引用 |
| 25 | P1 | ✅ | **bare except** | ~~已修复~~ `append_to_feishu.py` 中 `except:` → `except (ValueError, TypeError):`；`ocr_image.py` 类型注解同步修正 |

---

## 优先级执行顺序

### P0 — 不修跑不起来（✅ 全部完成）
- ✅ #2 删除空壳脚本，selector 合并至 `extract_content.py` 的 `PLATFORM_RULES`
- ✅ #3 移除所有硬编码路径（`append_to_feishu.py`、`ocr_image.py`）
- ✅ #8 适配 `x-tweet-fetcher` 作为 Twitter 首选 skill
- ✅ #13 移除 `ocr_image.py` 中硬编码的腾讯云 COS 配置路径
- ✅ #24 从 SKILL.md 中移除对不存在文件的引用

### P1 — 架构基础（#1 #4 #9 #14 #22 #25）
- ❌ #1 定义统一 CollectedItem Schema
- ❌ #4 引入 Bitable 存储
- 🔄 #9 建立 fallback 提取链（`PLATFORM_RULES` 已定义 fallback_skills，运行时降级逻辑待实现）
- ❌ #14 用 agent 原生 `look_at` 能力替代外部 OCR 依赖
- ❌ #22 统一错误处理
- ✅ #25 修复 bare except

### P2 — 体验提升（#5 #7 #10 #11 #12 #15 #16 #18 #21 #23）
- ✅ #5 短链 resolve + domain alias 映射 + 尾部斜杠剥离
- ✅ #7 缓存 TTL 30天 + LRU 1000 条上限
- ✅ #11 取消 500 字截断，全量存储
- ❌ #10 thread/长文支持（已暂缓）
- ❌ #12 macOS Vision OCR
- ❌ #15 序号递增优化
- ❌ #16 日期分组
- ❌ #18 批量导入
- ❌ #21 智能提醒
- ❌ #23 单元测试

### P3 — 生态联动（#6 #17 #19 #20）
- 全部 ❌ 待处理
- 语义去重
- 可自定义输出模板
- 回流加工（周报、趋势）
- skill 联动接口标准化
