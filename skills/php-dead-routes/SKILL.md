---
name: php-dead-routes
description: 按模块扫描已注释掉的路由，全链路追踪关联代码（Controller → Service/Action → Event/Listener），生成废弃接口清理报告。当用户说 "dead-routes"、"废弃路由"、"注释路由"、"清理路由"、"dead routes scan" 时触发。
---

# Dead Routes Scanner

按模块扫描已注释掉的路由定义，全链路追踪关联的废弃代码，生成结构化清理报告。

## 用法

```
/php-dead-routes <module_name>        # 扫描指定模块，如 /php-dead-routes account
/php-dead-routes list                 # 列出所有可扫描的模块
/php-dead-routes all                  # 逐模块扫描全部（按模块分批输出）
```

## 第一步：定位模块

1. 参数为 `list` 时：列出 `modules/*/` 下所有模块名，附带每个模块的路由文件数量，结束。
2. 参数为具体模块名时：确认 `modules/{module}/src/Http/Routes/` 存在，不存在则报错。
3. 参数为 `all` 时：获取全部模块列表，按顺序逐个执行第二步到第五步。

## 第二步：提取注释路由

扫描 `modules/{module}/src/Http/Routes/*.php`，提取被注释掉的路由定义行。

### 匹配规则

匹配以 `//` 开头（允许前导空白）且包含路由注册模式的行：

```
^\s*//\s*\$route->(any|get|post|put|delete|patch)\s*\(
^\s*//\s*Route::(any|get|post|put|delete|patch)\s*\(
```

### 提取信息

从每条匹配行提取：
- **路由文件**：相对路径（如 `Routes/api.php`）
- **行号**
- **HTTP 方法**：any/get/post/put/delete/patch
- **URI 路径**：括号内第一个字符串参数
- **Controller@method**：括号内第二个字符串参数（如 `'UserController@goodsStatus'`）

对于多行注释路由（如链式调用 `->name()` 也被注释），合并为一条记录。

### 排除规则

排除纯描述性注释（不包含 `$route->` 或 `Route::` 的注释行）。

## 第三步：追踪 Controller 层

对每个提取到的 `Controller@method`：

1. **定位 Controller 文件**：在 `modules/{module}/src/Http/Request/` 下递归搜索对应的 Controller 文件。
   - Controller 可能在子目录中：`Api/`、`ApiV2/`、`ApiV3/`、`Backend/`、`Web/` 等。
2. **检查方法状态**：
   - 方法是否存在
   - 方法是否也被注释掉
   - 方法是否仍然活跃（可能被其他活跃路由引用）
3. **提取方法调用链**：读取方法体，识别其调用的 Service/Action 类和方法：
   - `$this->someService->methodName()` 或通过依赖注入
   - `app(SomeAction::class)->execute()` 
   - `SomeAction::run()` 或静态调用
   - `new SomeClass()` 后的方法调用

## 第四步：追踪 Service/Action/Event 层

对第三步发现的每个 Service/Action 调用：

1. **定位类文件**：在 `modules/{module}/src/` 下搜索：
   - `Action/` 目录
   - `Services/` 目录
   - `Classes/` 目录
2. **检查方法是否仅被废弃路由使用**：
   - grep 该方法名在整个模块中的引用次数
   - 如果只有注释路由中的 Controller 调用它 → 标记为「可安全清理」
   - 如果有其他活跃代码调用它 → 标记为「仍在使用」
3. **提取 Event 派发**：检查方法体中的 `event()` / `Event::dispatch()` / `dispatch()` 调用：
   - 定位 Event 类（`modules/{module}/src/Events/`）
   - 定位关联的 Listener（`modules/{module}/src/Listeners/`）
   - 检查这些 Event/Listener 是否仅被废弃链路触发

## 第五步：生成报告

输出文件：`docs/dead-routes/{module}-dead-routes.md`（目录不存在则创建）。

### 报告格式

```markdown
# {Module} 模块 - 废弃路由分析报告

> 扫描时间：{date}
> 注释路由数：{N}
> 可安全清理的代码文件数：{M}

## 废弃路由清单

### {route_file} (如 Routes/api_kf.php)

| # | URI | HTTP方法 | Controller@Method | 方法状态 | 关联 Service/Action | 清理建议 |
|---|-----|---------|-------------------|---------|-------------------|---------|
| 1 | user/goods_status | any | UserController@goodsStatus | 方法存在,无其他引用 | UserService@getGoodsStatus | 可安全删除 |
| 2 | order/info | any | OrderController@info | 方法存在,有其他路由引用 | — | 仅删除路由注释 |

## 全链路追踪详情

### 1. UserController@goodsStatus

**路由**：`// $route->any('user/goods_status', 'UserController@goodsStatus')`
**文件**：`src/Http/Request/Api/UserController.php:120`
**方法状态**：存在，未被其他活跃路由引用

**调用链**：
- → `UserService@getGoodsStatus` (`src/Services/UserService.php:45`) — 无其他引用，可清理
  - → `event(new GoodsStatusChanged(...))` — Event 仅此处派发
    - → `GoodsStatusListener@handle` (`src/Listeners/GoodsStatusListener.php`) — 仅监听此 Event

**清理建议**：可安全删除以下文件/方法：
- [ ] `Routes/api_kf.php:46` — 删除注释行
- [ ] `UserController@goodsStatus` — 删除方法
- [ ] `UserService@getGoodsStatus` — 删除方法
- [ ] `Events/GoodsStatusChanged.php` — 删除文件
- [ ] `Listeners/GoodsStatusListener.php` — 删除文件

## 清理汇总

### 可安全清理
- 注释路由行：{N} 行
- Controller 方法：{N} 个
- Service/Action 方法：{N} 个
- Event 类：{N} 个
- Listener 类：{N} 个

### 需人工确认
- Controller 方法被其他路由引用：{N} 个
- Service 方法被多处调用：{N} 个
```

## 注意事项

- 每次只处理一个模块，避免上下文过载。
- 追踪调用链时，只在当前模块内搜索。跨模块调用标记为「跨模块引用，需人工确认」。
- 如果 Controller 方法不存在（已被删除），标记为「仅需清理路由注释」。
- 对于 `all` 模式，每个模块生成独立报告文件，最后输出汇总统计。
