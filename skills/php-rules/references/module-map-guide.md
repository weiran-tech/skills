# module-map.md 生成指南

module-map.md 是模块速查表，让 agent 快速定位"我要改的东西在哪个模块"。

**数据来源优先级**：`docs/workflow/` > `composer.json`，不做文件数量统计扫描。

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
    "Game\\": "modules/game/src",
    "Account\\": "modules/account/src"
}
```

### 2. 获取模块职责

优先从 `docs/workflow/{module}/overview.md` 的"模块职责"段落提取一句话描述。

如果 docs 不存在，从模块名推断（account → 账号/交易、user → 用户/店铺、game → 游戏），标注"待确认"。

### 3. 获取跨模块引用方向

优先从 `docs/workflow/cross-module.md` 的"模块依赖矩阵"提取。

如果 docs 不存在，标注"待确认——请先运行 `/php-analyzer` 生成文档"。

### 4. 获取技术栈

从 `composer.json` 提取：

- `require.php` → PHP 版本
- `require.laravel/framework` → Laravel 版本
- `require.{poppy,weiran}/framework` → {poppy/weiran} 框架 和版本
- 其他关键依赖

## 输出格式

```markdown
---
description: 项目模块速查，帮助快速定位代码位置和模块职责
---

# 模块速查表

## 项目信息

- 项目名：{从 composer.json 的 name 字段}
- 框架：Laravel {版本} + {poppy,weiran}/framework {poppy/weiran framework 版本}
- PHP：{版本}
- 模块数：{N}

## 模块清单

| 模块    | 命名空间 | 目录            | 职责                               |
| ------- | -------- | --------------- | ---------------------------------- |
| account | Account\ | modules/account | {从 docs/workflow/account/overview.md 提取} |
| user    | User\    | modules/user    | {从 docs/workflow/user/overview.md 提取}    |
| ...     |          |                 |                                    |

## 模块目录速查

要找什么 → 去哪里：

`[<X>/]` 表示可选子目录，按下方「子目录判定规则」决定是否建立。

| 类别              | 路径（命名）                                                                        | 备注                   |
|-----------------|-------------------------------------------------------------------------------|----------------------|
| **核心层**         |                                                                               |                      |
| 业务逻辑            | `src/Action/`（`Act{Service}.php`）                                             | 业务逻辑唯一落点             |
| 数据模型            | `src/Models/`（`<Table>.php`，大驼峰与表名一致）                                         | Eloquent 模型 + 关联     |
| 模型 DAO          | `src/Models/Dao/`（`<Model>Dao.php`）                                           | 复杂查询封装               |
| 模型 Filter       | `src/Models/Filters/`（`<Model>Filter.php`）                                    | 查询过滤器                |
| 模型 Resource     | `src/Models/Resources/`（`<Model>Resource.php`）                                | API 资源转换             |
| 模型 Policy       | `src/Models/Policies/`（`<Model>Policy.php`）                                   | Laravel Policies     |
| **事件层**         |                                                                               |                      |
| 领域事件            | `src/Events/`（`<Domain>Event.php`）                                            | 过去式或动作名词             |
| 事件监听器           | `src/Listeners/<Domain>/`（`<Verb>Listener.php`）                               | 必带业务域子目录（按 Event 域）  |
| 队列任务            | `src/Jobs/`（`<Verb>Job.php`）                                                  | `handle()` 委托 Action |
| **HTTP 层**      |                                                                               |                      |
| 控制器（前端 API）     | `src/Http/[Request/]Api/`（`<Fun>Controller.php` + `<Fun>/<Fun>XxRequest.php`） | 面向前端 API             |
| 控制器（后台）         | `src/Http/[Request/]Backend/`（同前端 API 命名）                                     | 管理后台                 |
| 控制器（商户/工作台）     | `src/Http/[Request/]Web/`（同前端 API 命名）                                         | 商户/客服工作台             |
| 路由              | `src/Http/Routes/`（`api.php` / `web.php` / `backend.php`）                     | 与 HTTP 层一一对应         |
| 中间件             | `src/Http/Middleware/`（`<Affect>Middleware.php`）                              |                      |
| **支撑层**         |                                                                               |                      |
| 工具类 / SDK 封装    | `src/Classes/`                                                                | 见下方「Def/Enum 决策」     |
| Traits          | `src/Classes/Traits/`（`<Function>Trait.php`）                                  |                      |
| Auth 相关         | `src/Classes/Auth/`                                                           |                      |
| 通知              | `src/Notifications/`（`<Affect>Notification.php`）                              |                      |
| 命令              | `src/Commands/`（`<Function>Command.php`）                                      | Cli命令                |
| 钩子              | `src/Hooks/`                                                                  | 业务钩子                 |
| **模块入口**        |                                                                               |                      |
| ServiceProvider | `src/ServiceProvider.php`                                                     | 路由/事件/命令注册           |
| **资源**          |                                                                               |                      |
| 数据库迁移           | `resources/migrations/`（Laravel 迁移文件）                                         |                      |
| 多语言             | `resources/lang/<lang>/`                                                      |                      |
| 视图              | `resources/views/{backend,web,...}/`                                          |                      |
| **配置**          |                                                                               |                      |
| 权限定义            | `configurations/permissions.yaml`                                             |                      |
| 菜单定义            | `configurations/menus.yaml`                                                   |                      |
| 服务定义            | `configurations/services.yaml`                                                |                      |
| 服务钩子            | `configurations/hooks.yaml`                                                   |                      |
| **测试**          |                                                                               |                      |
| 单元测试            | `tests/`                                                                      |                      |

{注：以上为通用路径模式，具体模块可能不包含所有目录。实际存在的目录以各模块 overview.md 的"目录结构"为准。}

## 跨模块引用方向

{从 docs/workflow/cross-module.md 提取，如果不存在则标注"待确认"}

| 引用方 → 被引用方       | 主要引用类型           |
| ----------------------- | ---------------------- |
| {module_a} → {module_b} | Model引用 / Action调用 |
| ...                     |                        |
```



## 注意事项

- 不做文件数量统计——数量会快速过时，维护成本高于收益
- 模块职责和跨模块引用从 docs 提取，保持与 php-analyzer 产出的文档一致
- 目录速查表是通用模板，不随项目变化
- 如果某个模块被多个模块引用（如 user、misc），在备注中标记为"基础模块"
