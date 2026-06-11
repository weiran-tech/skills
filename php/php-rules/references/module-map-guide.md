# module-map.md 生成指南

module-map.md 是模块速查表，让 agent 快速定位"我要改的东西在哪个模块"。

**数据来源优先级**：`docs/` > `composer.json`，不做文件数量统计扫描。

## frontmatter

```yaml
---
description: 项目模块速查，帮助快速定位代码位置和模块职责
---
```

无 globs，无条件加载。模块速查是高频需求，任何开发场景都可能用到。

## 信息获取

### 1. 获取模块列表

从 `composer.json` 的 `autoload.psr-4` 获取模块命名空间映射：

```json
{
  "App\\": "modules/app/src",
  "Game\\": "modules/game/src",
  "Account\\": "modules/account/src"
}
```

### 2. 获取模块职责

优先从 `docs/{module}/overview.md` 的"模块职责"段落提取一句话描述。

如果 docs 不存在，从模块名推断（account → 账号/交易、user → 用户/店铺、game → 游戏），标注"待确认"。

### 3. 获取跨模块引用方向

优先从 `docs/cross-module.md` 的"模块依赖矩阵"提取。

如果 docs 不存在，标注"待确认——请先运行 arch-analyzer 生成文档"。

### 4. 获取技术栈

从 `composer.json` 提取：
- `require.php` → PHP 版本
- `require.laravel/framework` → Laravel 版本
- 其他关键依赖

## 输出格式

```markdown
---
description: 项目模块速查，帮助快速定位代码位置和模块职责
---

# 模块速查表

## 项目信息

- 项目名：{从 composer.json 的 name 字段}
- 框架：Laravel {版本} + weiran/framework
- PHP：{版本}
- 模块数：{N}

## 模块清单

| 模块 | 命名空间 | 目录 | 职责 |
|------|---------|------|------|
| account | Account\ | modules/account | {从 docs/account/overview.md 提取} |
| user | User\ | modules/user | {从 docs/user/overview.md 提取} |
| ... | | | |

## 模块目录速查

要找什么 → 去哪里：

| 要找 | 路径模式 | 说明 |
|------|---------|------|
| API 接口处理 | `modules/{module}/src/Http/Request/Api/` | 面向前端的请求处理类 |
| 后台接口处理 | `modules/{module}/src/Http/Request/Backend/` | 管理后台请求处理类 |
| 业务逻辑 | `modules/{module}/src/Action/` | 核心业务逻辑（等同 Service 层）|
| 数据模型 | `modules/{module}/src/Models/` | Eloquent 模型 |
| 事件定义 | `modules/{module}/src/Events/` | 领域事件 |
| 事件监听 | `modules/{module}/src/Listeners/` | 事件处理 |
| 队列任务 | `modules/{module}/src/Jobs/` | 异步任务 |
| 路由定义 | `modules/{module}/src/Http/Routes/` | 路由文件 |
| Artisan 命令 | `modules/{module}/src/Commands/` | CLI 命令 |
| 工具类/SDK封装 | `modules/{module}/src/Classes/` | 工具和第三方封装 |
| 数据库迁移 | `modules/{module}/resources/migrations/` | Migration 文件 |

{注：以上为通用路径模式，具体模块可能不包含所有目录。实际存在的目录以各模块 overview.md 的"目录结构"为准。}

## 跨模块引用方向

{从 docs/cross-module.md 提取，如果不存在则标注"待确认"}

| 引用方 → 被引用方 | 主要引用类型 |
|------------------|-------------|
| {module_a} → {module_b} | Model引用 / Action调用 |
| ... | |
```

## 注意事项

- 不做文件数量统计——数量会快速过时，维护成本高于收益
- 模块职责和跨模块引用从 docs 提取，保持与 arch-analyzer 产出的文档一致
- 目录速查表是通用模板，不随项目变化
- 如果某个模块被多个模块引用（如 user、misc），在备注中标记为"基础模块"
