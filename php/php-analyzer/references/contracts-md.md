# docs/{module}/contracts.md 生成指南

contracts.md 记录模块所有对内对外的交互契约。这是其他模块负责人和前端开发最需要查阅的文档。

**核心要求**：路由路径、事件类名、Job 类名必须从代码中取真实值，不能写占位符或猜测值。

## 扫描要点

- 从 `Http/Routes/*.php` 路由文件取完整路由定义（HTTP 方法、URI、Controller/Request 类、中间件）
- 从 `Events/` 目录取事件类定义，记录事件携带的数据属性
- 从 `Listeners/` 目录取监听器，记录监听的事件和执行的业务逻辑
- 从 `ServiceProvider` 中的 `$listen` 或 `EventServiceProvider` 取事件-监听器绑定关系
- 从 `Jobs/` 目录取队列任务，记录队列名、延迟配置、数据载荷
- **事件级联追踪**：对每个 Listener，追踪其内部调用链（Listener → Action → Model），检查是否有 `event()` 调用或 `dispatch()` Job。如果有，记录到"产生的事件/任务"列。这是还原完整事件级联链路的关键信息
- 从模块代码中扫描对其他模块类的引用，识别跨模块调用契约

## 输出模板

```markdown
# 对外契约

## API 路由（api_v1.php）
| HTTP方法 | URI | 请求类/控制器 | 中间件 | 说明 |
|---------|-----|-------------|--------|------|
| {GET/POST/...} | {/api/v1/...} | {RequestClass} | {auth, throttle...} | {接口用途} |

## 管理后台路由（backend.php）
| HTTP方法 | URI | 请求类/控制器 | 说明 |
|---------|-----|-------------|------|
| {GET/POST/...} | {/backend/...} | {RequestClass} | {后台操作} |

## Web 路由（web.php）
| HTTP方法 | URI | 请求类/控制器 | 说明 |
|---------|-----|-------------|------|

## 其他路由文件（如 api_third.php、api_up.php、tao_bao.php）
{按实际存在的路由文件逐个列出}

## 发布的事件（本模块对外发布）
| 事件类 | 携带数据 | 触发时机 | 监听方 |
|--------|---------|---------|--------|
| {EventClass} | {构造函数参数} | {在哪个 Action/方法中触发} | {本模块/其他模块的 Listener} |

## 监听的事件（本模块消费）
| 监听器类 | 监听的事件 | 业务动作 | 产生的事件/任务 |
|---------|-----------|---------|---------------|
| {ListenerClass} | {EventClass} | {调用了哪个 Action，做了什么} | {处理过程中触发的事件或 dispatch 的 Job，无则填"—"} |

## 队列任务
| Job 类 | 队列名 | 延迟 | 触发来源 | 业务动作 |
|--------|--------|------|---------|---------|
| {JobClass} | {queue name} | {delay config} | {哪个 Action/Listener dispatch 的} | {做什么} |

## Artisan 命令
| 命令签名 | 说明 | 调度方式 |
|---------|------|---------|
| {command:signature} | {用途} | {手动 / schedule} |

## 跨模块调用（本模块调用其他模块）
| 本模块调用方 | 目标模块 | 目标类 | 调用方法 | 场景 |
|-------------|---------|--------|---------|------|
| {CallerClass} | {Module} | {TargetClass} | {method()} | {为什么需要调用} |

## 被其他模块调用（本模块被引用）
| 调用方模块 | 调用方类 | 本模块目标类 | 调用方法 | 场景 |
|-----------|---------|------------|---------|------|
| {Module} | {CallerClass} | {TargetClass} | {method()} | {使用场景} |
```

## 多路由文件时的组织方式

如果模块有多个路由文件（如 api_v1.php、api_third.php、api_up.php），按文件分组展示：

```markdown
## API 路由

### api_v1.php（面向前端/App）
| HTTP方法 | URI | 请求类 | 说明 |
...

### api_third.php（面向第三方）
| HTTP方法 | URI | 请求类 | 说明 |
...

### api_up.php（上游回调）
| HTTP方法 | URI | 请求类 | 说明 |
...
```

## 注意事项

- 路由路径必须完整，包含前缀（从 RouteServiceProvider 或路由组中取）
- 如果路由绑定的是 Request 类而非传统 Controller，说明这是 weiran 框架的请求处理模式
- 跨模块调用的"被引用"部分可能需要扫描其他模块才能填全，当前模块分析时先留"待确认"
