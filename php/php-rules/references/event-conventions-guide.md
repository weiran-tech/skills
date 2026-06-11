# event-conventions.md 生成指南

event-conventions.md 包含 Event/Listener/Job 开发规范。通用部分固定输出，项目特有部分从代码扫描填充。

## frontmatter

```yaml
---
description: Event/Listener/Job 开发规范、命名约定、幂等要求
globs:
  - "modules/*/src/Events/**"
  - "modules/*/src/Listeners/**"
  - "modules/*/src/Jobs/**"
---
```

globs 覆盖所有模块的事件、监听器、Job 目录。只有操作这些文件时才加载。

## 文档结构

### 第一部分：新增 Event（通用 + 项目特有）

**通用内容（固定输出）：**

```markdown
## 新增 Event

### 文件位置

`modules/{module}/src/Events/{BusinessDomain}/` 或 `modules/{module}/src/Events/`

如果事件属于某个业务子域（如回收议价），放在对应子目录下。

### 类模板

```php
<?php

namespace {Module}\Events;

class XxxEvent
{
    public function __construct(
        public readonly int $id,
        // 只传必要的标识符，不传整个 Model 对象
    ) {
    }
}
```

### 命名约定

- 事件类名：`{业务动作}{Event}`，如 `RecycleGoodsEvent`、`BidOverEvent`
- 事件表达"已发生的事"，用过去式或动作名词
- 子目录名与业务域对齐：`Events/RecycleGoodsBid/BidOverEvent.php`
```

**项目特有内容（扫描填充）：**

- 列出当前项目已有的事件命名示例（从 Events/ 目录扫描）
- 列出使用了子目录组织的事件（帮助新增事件时选择合适的位置）

### 第二部分：新增 Listener（通用 + 项目特有）

**通用内容（固定输出）：**

```markdown
## 新增 Listener

### 文件位置

`modules/{module}/src/Listeners/{BusinessDomain}/`

Listener 通常按业务域分子目录，与 Event 子目录对应。

### 类模板

```php
<?php

namespace {Module}\Listeners\{BusinessDomain};

class XxxListener
{
    public function handle(XxxEvent $event): void
    {
        // 1. 委托给 Action 处理，Listener 自身不写复杂业务逻辑
        // 2. 如果需要异步处理，dispatch Job 而不是在 Listener 中做耗时操作
        app(XxxAction::class)->doSomething($event->id);
    }
}
```

### 注册绑定

在模块的 `ServiceProvider.php` 中注册 Event → Listener 映射：

```php
protected $listen = [
    XxxEvent::class => [
        XxxListener::class,
    ],
];
```

### 规范

- Listener 命名：`{业务动作}{Listener/Listeners}`
- 一个 Event 可以有多个 Listener，每个 Listener 只做一件事
- Listener 中禁止写超过 10 行的业务逻辑，应委托给 Action
- 如果 Listener 执行失败不应影响主流程，考虑使用 Job 异步化
```

**项目特有内容（扫描填充）：**

- 列出现有的 Listener 子目录组织结构
- 列出 ServiceProvider 中的事件绑定示例

### 第三部分：新增 Job（通用 + 项目特有）

**通用内容（固定输出）：**

```markdown
## 新增 Job

### 文件位置

`modules/{module}/src/Jobs/`

### 类模板

```php
<?php

namespace {Module}\Jobs;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;

class XxxJob implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;
    public int $backoff = 60;

    public function __construct(
        private readonly int $id,
    ) {
    }

    public function handle(): void
    {
        // 委托给 Action 处理
        app(XxxAction::class)->doSomething($this->id);
    }
}
```

### 规范

- Job 命名：`{业务动作}Job`，如 `GoodsSyncJob`、`GoodsEstimatePriceJob`
- Job 构造函数只传标识符（ID），不传 Model 对象（序列化风险）
- Job 的 handle 方法委托给 Action，自身只做参数传递
- 必须配置 `$tries`（重试次数）和 `$backoff`（重试间隔）
- 需要延迟执行的使用 `dispatch()->delay()`
```

**项目特有内容（扫描填充）：**

- 列出当前项目使用的队列驱动（从 config/queue.php）
- 列出现有 Job 的重试配置示例

### 第四部分：幂等约定（通用，固定输出）

```markdown
## 幂等约定

所有 Listener 和 Job 必须实现幂等。推荐做法：

1. **状态判断幂等**：处理前检查业务实体当前状态，已处理则跳过
2. **唯一键幂等**：通过数据库唯一索引防止重复写入
3. **延迟任务幂等**：delay dispatch 的 Job 不可撤销，handle 时必须检查当前状态是否仍然需要处理

Listener 中的幂等检查应在委托 Action 之前完成，避免不必要的 Action 调用。
```

### 第五部分：事件级联注意事项（通用，固定输出）

```markdown
## 事件级联注意事项

- Listener 中可以触发新的 Event 或 dispatch Job，但要注意级联深度
- 禁止形成事件环路（A → B → C → A）
- 如果修改了 Event 的构造参数，必须同步更新所有 Listener
- 在 contracts.md 中记录事件级联关系，便于影响评估
```
