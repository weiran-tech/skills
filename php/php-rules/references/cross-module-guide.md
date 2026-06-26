# cross-module-guide.md 生成指南

cross-module-guide.md 是跨模块改动时的操作手册。包含改动前必读、跨模块引用约束、常见改动的操作步骤、完成后的汇报格式。

## frontmatter

```yaml
---
description: 跨模块改动指南，修改涉及多个模块时必读
globs:
  - "modules/*/src/Events/**"
  - "modules/*/src/Listeners/**"
  - "modules/*/src/Action/**"
---
```

globs 限定在跨模块交互的高频代码路径。只有操作事件、监听器、Action 时才加载。

## 文档结构

### 第一部分：改动前必读

列出 docs/ 目录下实际存在的文件，说明什么时候需要看：

```md
## 改动前必读

| 文档 | 什么时候看 |
|------|-----------|
| `docs/{module}/contracts.md` | 新增/修改 Event 或跨模块调用前（避免事件冲突、参数不兼容） |
| `docs/{module}/flows.md` | 评估改动的下游影响范围时 |
| `docs/{module}/business.md` | 实现业务逻辑前（理解状态机和业务规则） |
| `docs/{module}/overview.md` | 初次进入某个模块时 |
| `docs/cross-module.md` | 改动涉及多个模块时（理解模块间依赖关系） |
```

如果 docs/ 目录不存在，此部分改为提醒阅读 CLAUDE.md 和 .claude/rules/ 下的规则文件。

### 第二部分：跨模块引用约束（通用 + 项目特有）

**通用内容（固定输出）：**

```md
## 跨模块引用约束

### 允许的引用

| 引用类型 | 示例 | 说明 |
|---------|------|------|
| 引用其他模块的 Model | `use User\Models\Store` | 读取数据、建立关联 |
| 引用其他模块的 Action | `use User\Action\StoreAction` | 调用业务方法（只调公开方法）|
| 引用其他模块的 Event | `use Account\Events\XxxEvent` | 监听其他模块的事件 |
| 引用其他模块的 Classes | `use Misc\Classes\XxxHelper` | 使用工具类 |

### 禁止的引用

| 引用类型 | 原因 |
|---------|------|
| 引用其他模块的 Request 类 | Request 是 HTTP 入口，模块边界内使用 |
| 引用其他模块的 Listener | Listener 是内部实现，不应被外部依赖 |
| 引用其他模块的 Middleware | 中间件是模块内部路由配置 |
| 在 Model 中直接引用其他模块的 Action | Model 层不应有业务逻辑依赖 |
```

**项目特有内容（扫描填充）：**

- 从扫描结果中列出实际存在的跨模块引用，标注哪些符合规范、哪些需要重构
- 标注"基础模块"（被多个模块引用的，如 user、misc）

### 第三部分：改动类型清单（清单 + 引用）

```md
## 改动类型清单

| 改动类型 | 操作步骤摘要 | 详细规范 |
|---------|------------|---------|
| 新增 Event | 创建事件类 → 创建 Listener → ServiceProvider 绑定 → 编译 | 见 `event-conventions.md` |
| 新增 Job | 创建 Job 类 → 配置重试 → 在 Action 中 dispatch → 编译 | 见 `event-conventions.md` |
| 跨模块调用 Action | 确认目标 Action 公开方法 → use 引用 → 调用 → 编译 | 见本文"跨模块引用约束" |
| 新增 API 路由 | 创建 Request 类 → 路由文件注册 → 编译 | 见 `architecture.md` 路由约定 |
| 新增 Artisan 命令 | 创建 Command 类 → ServiceProvider 注册 → 编译 | 标准 Laravel Command |
```

末尾附上项目的编译/检查命令：

```bash
# 路由缓存检查
php artisan route:list

# 语法检查
php -l modules/{module}/src/{file}.php

# 运行测试
php artisan test --filter={TestClass}
```

### 第四部分：完成后的汇报格式（通用，固定输出）

```md
## 完成后汇报格式

## 改动摘要

- 模块: {module-name}
- 改动类型: [新增事件 / 新增Job / 跨模块调用 / 新增API / ...]

## Event 契约（如有）

- 事件类: {EventClass}
- 构造参数: { field1: Type, field2: Type }
- 监听器: [Listener1, Listener2]

## 跨模块调用（如有）

- 调用方: {Module}\{CallerClass}
- 目标方: {Module}\{TargetClass}::{method}()

## 检查结果

- 语法检查: PASS / FAIL
- 路由缓存: PASS / FAIL
- 测试: PASS / FAIL（如有失败列出失败用例）

## 影响范围

- 新增文件: [列表]
- 修改文件: [列表]
- 影响的模块: [列表]
```
