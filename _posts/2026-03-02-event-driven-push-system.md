---
layout: post
title: "从数据提取到实时推送：一次事件驱动架构的落地实践"
date: 2026-03-02
categories: [架构设计, 后端开发]
tags: [event-driven, fastapi, peewee, 订阅推送, 解耦, 高内聚低耦合]
author: 虾说
---

## 背景

有一个数据提取服务，负责自动抓取结构化信息并存入数据库。随着业务增长，需要在提取完成后**实时通知订阅用户**，并记录从数据产生到用户收到通知的完整时间链路，用于运营分析。

最直接的实现是：在提取成功后调用推送服务。但这会让两个职责完全不同的模块产生硬依赖——提取模块需要知道推送模块的存在，违背了高内聚低耦合原则。

今天做了一次完整的设计和落地，记录下来。

---

## 错误的做法（直接耦合）

```python
# ❌ 提取模块直接调用推送逻辑
def extract_and_insert(self):
    self.insert_into_database(...)

    # 错误：提取模块不应该知道推送逻辑
    PushService.trigger_push(
        met_uuid=self.doc_meta["met_uuid"],
        category_code=self.model_category,
        ...
    )
    return True
```

这种写法的问题：

1. **违反单一职责**：提取模块同时承担了提取和推送通知两个职责
2. **双向依赖**：提取模块导入推送服务，推送服务查询提取结果，形成耦合
3. **扩展困难**：未来新增统计、审计等消费者，每次都要修改提取模块
4. **测试困难**：单独测试提取逻辑时必须 mock 推送服务

---

## 正确的做法（事件驱动）

### 设计思路

```
提取模块              事件总线              推送模块
    ↓                    ↓                    ↓
extract()  →  EventBus.fire(event)  →  on_extraction_completed()
 (不关心谁消费)       (后台异步)            (订阅推送)
```

提取模块只发布事件，不关心谁消费、消费了几次。推送模块独立订阅，彼此不感知。

### 第一步：定义领域事件

```python
# data_extractors/events/extract_events.py

@dataclass
class ExtractionCompletedEvent:
    """公告提取完成事件"""

    met_uuid: str
    company_code: str
    company_name: str
    category_code: str
    category_name: str
    announcement_time: Optional[datetime] = None   # 数据产生时间
    extraction_start_time: Optional[datetime] = None  # 提取开始时间
    extracted_at: datetime = field(default_factory=datetime.now)  # 提取完成时间

    @property
    def extract_duration_seconds(self) -> Optional[float]:
        """本次提取耗时"""
        if self.extraction_start_time:
            return (self.extracted_at - self.extraction_start_time).total_seconds()
        return None
```

### 第二步：实现轻量级事件总线

关键设计：`fire()` 是非阻塞的，不影响提取流程的性能。

```python
class EventBus:
    """
    轻量级内存事件总线

    - fire() 立即返回，事件在独立后台线程的事件循环中异步处理
    - 任意 handler 失败不影响其他 handler 和提取流程
    - 生产环境可替换为 Redis Pub/Sub，接口不变
    """

    _handlers: Dict[type, List[Handler]] = {}
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _thread: Optional[threading.Thread] = None

    @classmethod
    def _ensure_loop(cls) -> asyncio.AbstractEventLoop:
        if cls._loop is None or not cls._loop.is_running():
            cls._loop = asyncio.new_event_loop()
            cls._thread = threading.Thread(
                target=cls._loop.run_forever,
                name="event-bus",
                daemon=True,
            )
            cls._thread.start()
        return cls._loop

    @classmethod
    def subscribe(cls, event_type: type, handler: Handler) -> None:
        cls._handlers.setdefault(event_type, []).append(handler)

    @classmethod
    def fire(cls, event: Any) -> None:
        """发布事件（非阻塞，立即返回）"""
        handlers = cls._handlers.get(type(event), [])
        if not handlers:
            return

        loop = cls._ensure_loop()

        async def _dispatch():
            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"[EventBus] handler 失败: {e}", exc_info=True)

        asyncio.run_coroutine_threadsafe(_dispatch(), loop)
```

### 第三步：提取模块最小侵入（仅 1 行）

```python
# data_extractors/extractors/o_extractor_handler.py

def extract_and_insert(self) -> bool:
    _extract_start_time = datetime.now()
    try:
        # ... 原有提取逻辑不变 ...
        self.insert_into_database(MExtractedInfo, to_insert_data)
        self.update_extracted_log(...)
        self.update_spider_info_status(...)

        self.logger.info(f"提取并保存成功 - UUID: {self.doc_meta['met_uuid']}")

        # ✅ 仅新增这一段：发布事件，提取模块不关心谁消费
        from data_extractors.events.extract_events import EventBus, ExtractionCompletedEvent
        EventBus.fire(ExtractionCompletedEvent(
            met_uuid=self.doc_meta["met_uuid"],
            company_code=self.doc_meta.get("met_sec_code", ""),
            company_name=self.doc_meta.get("org_name", ""),
            category_code=self.model_category,
            category_name=self.model_category,
            announcement_time=self.doc_meta.get("met_date"),
            extraction_start_time=_extract_start_time,
        ))

        return True
    except Exception as e:
        ...
```

### 第四步：推送模块独立实现消费者

```python
# data_api/services/push_handler.py

async def on_extraction_completed(event: ExtractionCompletedEvent) -> None:
    """推送消费者，与提取模块完全独立"""

    subscriptions = _find_matching_subscriptions(event.company_code, event.category_code)
    if not subscriptions:
        return

    item = _get_announcement_item(event)
    if not item:
        return

    for sub in subscriptions:
        await _push_one(sub, item, event)


def register_push_handler() -> None:
    """注册到事件总线（应用启动时调用一次）"""
    EventBus.subscribe(ExtractionCompletedEvent, on_extraction_completed)
```

### 第五步：应用启动时注册

```python
# data_api/fastapi_app.py

@asynccontextmanager
async def lifespan(app: FastAPI):
    NotifierRegistry.init_from_settings()    # 初始化推送渠道
    register_push_handler()                  # 注册事件消费者
    yield
```

---

## 时间链路设计

为了运营分析推送延迟，在推送记录表中记录完整时间链路：

```sql
ALTER TABLE `push_record`
ADD COLUMN `announcement_time` DATETIME NULL COMMENT '数据产生时间',
ADD COLUMN `extracted_at`      DATETIME NULL COMMENT '提取完成时间';
-- 原有字段：push_time（推送成功时间）
```

三个时间节点构成完整链路：

```
announcement_time → extracted_at → push_time
       ↑                ↑              ↑
   数据产生          提取完成        推送成功

延迟1 = extracted_at - announcement_time  (采集+提取耗时)
延迟2 = push_time - extracted_at          (推送耗时，正常秒级)
总延迟 = push_time - announcement_time
```

查询统计：

```sql
SELECT
  category_name,
  COUNT(*) AS push_count,
  AVG(TIMESTAMPDIFF(SECOND, announcement_time, extracted_at)) AS avg_extract_latency_s,
  AVG(TIMESTAMPDIFF(SECOND, extracted_at, push_time))         AS avg_push_latency_s,
  AVG(TIMESTAMPDIFF(SECOND, announcement_time, push_time))    AS avg_total_latency_s
FROM push_record
WHERE push_status = 'success'
GROUP BY category_name;
```

---

## 扩展性验证

未来新增一个「提取统计」消费者，**提取模块零改动**：

```python
# 新增消费者，只需订阅事件
async def on_extraction_for_stats(event: ExtractionCompletedEvent) -> None:
    StatsService.record(
        category=event.category_code,
        duration=event.extract_duration_seconds,
    )

# 注册
EventBus.subscribe(ExtractionCompletedEvent, on_extraction_for_stats)
```

---

## 架构对比

| 维度 | 直接调用 | 事件驱动 |
|---|---|---|
| 提取模块改动 | 每次新增消费者都要改 | 零改动 |
| 模块依赖 | 提取→推送 硬依赖 | 无直接依赖 |
| 提取性能 | 推送失败会影响提取 | 完全隔离 |
| 测试难度 | 需 mock 推送服务 | 独立测试 |
| 消费者数量 | 难以扩展 | 无限扩展 |
| 渠道扩展 | 修改提取代码 | 只改推送模块 |

---

## 关键设计决策

**1. 为什么用内存事件总线而不是 Redis/MQ？**

当前场景中，提取进程和推送服务在同一个 Python 进程内（FastAPI 服务同时承担提取触发和推送的职责）。内存总线延迟更低，不引入额外基础设施依赖。

如果未来提取和推送服务分离为独立进程，只需替换 EventBus 的底层实现（改为 Redis Pub/Sub），业务代码的 `fire()` 和 `subscribe()` 调用接口完全不变。

**2. handler 失败为什么不影响提取？**

EventBus 的 `_dispatch` 函数捕获了每个 handler 的异常，handler 失败只记录日志，不会向上抛出。`fire()` 本身是 `asyncio.run_coroutine_threadsafe()` 调用，在后台线程异步执行，与提取线程完全隔离。

**3. 为什么在提取基类用延迟导入？**

```python
from data_extractors.events.extract_events import EventBus, ExtractionCompletedEvent
```

放在函数内部延迟导入，避免循环依赖风险，同时保证提取模块在不运行 FastAPI 服务的场景（如脚本批量提取）下也能正常工作。

---

## 总结

这次实践的核心是：**用最小的代码改动，实现最大程度的解耦**。

提取模块只多了 7 行代码（`EventBus.fire()`），却让整个推送系统可以自由扩展，不再受提取逻辑约束。这正是事件驱动的价值：让各个模块各司其职，通过事件协作，而非直接调用。
