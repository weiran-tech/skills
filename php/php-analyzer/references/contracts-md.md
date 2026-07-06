# docs/workflow/{module}/contracts.md 生成指南

contracts.md 记录模块所有对内对外的交互契约。这是其他模块负责人和前端开发最需要查阅的文档。

**核心要求**：路由路径、事件类名、Job 类名必须从代码中取真实值，不能写占位符或猜测值。

## 扫描要点

- 从 `Http/Routes/*.php` 路由文件取完整路由定义（HTTP 方法、URI、Controller/Request 类、中间件）
- 从 `Events/` 目录取事件类定义，记录事件携带的数据属性
- 从 `Listeners/` 目录取监听器，记录监听的事件和执行的业务逻辑
- 从 `ServiceProvider` 中的 `$listens` 或 `EventServiceProvider` 取事件-监听器绑定关系
- 从 `Jobs/` 目录取队列任务，记录队列名、延迟配置、数据载荷
- **事件级联追踪**：对每个 Listener，追踪其内部调用链（Listener → Action → Model），检查是否有 `event()` 调用或 `dispatch()`
  Job。如果有，记录到"产生的事件/任务"列。这是还原完整事件级联链路的关键信息
- 从模块代码中扫描对其他模块类的引用，识别跨模块调用契约

## 输出模板

模板读取 [模板](../templates/contracts.md)

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
- 跨模块调用的"被引用"部分可能需要扫描其他模块才能填全，当前模块分析时先留"待确认"
