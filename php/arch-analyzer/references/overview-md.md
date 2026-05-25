# overview.md 生成指南

overview.md 是模块的"门面"，定位是让人和 AI 工具在 30 秒内建立对这个模块的基本认知。保持简洁，控制在 1-2 屏内。

## 模块名称获取

1. `composer.json` 的 `autoload.psr-4` 中对应的命名空间名
2. 模块目录名（`modules/{name}`）

## 输出模板

```markdown
# {模块名}（{命名空间}）

## 模块职责
{一句话。从模块名 + 核心 Action 类名 + 路由前缀 + 事件类型推断，说明这个模块"管什么"。
例：账号交易模块，负责商品上架、回收定价、议价竞拍、订单管理等核心交易流程。}

## 目录结构
| 目录 | 职责 | 文件数 |
|------|------|--------|
| Action | 业务逻辑层（等同 Service 层） | {N} |
| Models | Eloquent 模型 + DAO + Filter + Resource + Policy | {N} |
| Events | 领域事件定义 | {N} |
| Listeners | 事件监听器 | {N} |
| Jobs | 队列任务 | {N} |
| Http/Request | 请求处理（API/Backend/Web） | {N} |
| Http/Routes | 路由定义 | {N} |
| Commands | Artisan 命令 | {N} |
| Classes | 工具类、配置类、第三方封装 | {N} |
| Hooks | 框架扩展点（菜单、权限等） | {N} |

## 技术栈
| 技术 | 版本/说明 |
|------|---------|
| PHP | {版本，从 composer.json 的 require.php 提取} |
| Laravel | {版本，从 laravel/framework 版本提取} |
| 模块框架 | {weiran/framework，从 composer.json 提取} |
| ORM | Eloquent |
| 队列 | {从 config/queue.php 推断驱动：Redis/Database/SQS} |
| 缓存 | {从 config/cache.php 推断} |
| 认证 | {JWT / Session，从 config/auth.php 和 composer.json 推断} |
| 其他关键依赖 | {如：淘宝 SDK、短信服务、OSS 等} |

## 路由概览
| 路由文件 | 类型 | 前缀 | 路由数 | 说明 |
|---------|------|------|--------|------|
| api_v1.php | API | {prefix} | {N} | {面向前端/App 的接口} |
| backend.php | 管理后台 | {prefix} | {N} | {管理后台操作接口} |
| web.php | Web页面 | {prefix} | {N} | {前端页面路由} |

## 模型清单
| 模型 | 数据表 | 关键关联 | 说明 |
|------|--------|---------|------|
| {ModelClass} | {table_name} | {hasMany(X), belongsTo(Y)} | {一句话说明} |

## 依赖的其他模块
| 模块 | 引用方式 | 说明 |
|------|---------|------|
| {module-name} | use {Namespace}\Models\{Class} | {引用了什么，为什么需要} |
| {module-name} | use {Namespace}\Action\{Class} | {调用了什么业务方法} |

## 被其他模块依赖
| 模块 | 引用方式 | 说明 |
|------|---------|------|
| {module-name} | {引用了本模块的什么} | {使用场景} |

## 边界说明（不负责的事项）
- {从代码缺失推断：看起来相关但明显不在这里处理的功能}

## 文档索引
- 业务逻辑 → [business.md](business.md)
- 对外契约 → [contracts.md](contracts.md)
- 执行流程 → [flows.md](flows.md)
```

## 注意事项

- "边界说明"很重要，明确说出哪些不归这个模块管，可以避免跨模块职责混乱
- "依赖的其他模块"重点关注直接 `use` 引用，区分模型引用和 Action 调用
- 模型清单只列本模块定义的模型，不列引用其他模块的模型
- 路由概览按路由文件分组，给出数量级即可，详细路由在 contracts.md
