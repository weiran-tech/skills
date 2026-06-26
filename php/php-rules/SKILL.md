---
name: php-rules
description: 为 PHP/Laravel 伪多模块项目生成标准化的 Claude Code 规则文件（CLAUDE.md + .claude/rules/）。当用户说 "php-rules"、"生成规则文件"、"生成PHP规则"、"PHP开发规范"、"init rules"、"init php rules"、"生成开发规范" 时触发。适用于：新项目初始化开发规范、统一团队 Claude Code 使用标准、为跨模块 Agent 协作准备仓库级规则。
---

# PHP Arch Rules

为当前 PHP/Laravel 伪多模块项目生成标准化的 Claude Code 规则文件。

**定位**：只生成开发规范和操作指南，不分析业务逻辑和执行流程（业务分析由 php-analyzer 负责）。

## 产出物

| 文件                                    | 类型   | 来源       | 说明                                    |
|---------------------------------------|------|----------|---------------------------------------|
| `CLAUDE.md`                           | 项目级  | 模板 + 扫描  | 纯入口导航（一句话职责 + 文档阅读顺序 + 规则索引）          |
| `.claude/rules/architecture.md`       | 通用规则 | 模板直出     | 分层约束 + 编码标准 + 完成检查清单                  |
| `.claude/rules/module-map.md`         | 项目特有 | docs 或扫描 | 模块速查表（命名空间、目录结构、职责）                   |
| `.claude/rules/event-conventions.md`  | 混合   | 模板 + 扫描  | Event/Listener 开发模板 + Job 队列规范 + 幂等约定 |
| `.claude/rules/cross-module-guide.md` | 混合   | 模板 + 扫描  | 跨模块改动清单 + 引用约束 + 完成汇报格式               |

### 信息归属原则

每个文件只回答一个问题，零重复，文档间只做单向引用：

```
CLAUDE.md                → 纯入口（一句话 + 导航）
docs/{service-name}/overview   → 事实（模块是什么、目录结构、依赖）     ← php-analyzer 生成
docs/{service-name}/business   → 规则（为什么这么处理）                 ← php-analyzer 生成
docs/{service-name}/contracts  → 契约（路由、事件、Job）                ← php-analyzer 生成
docs/{service-name}/flows      → 链路（怎么流转）                       ← php-analyzer 生成
architecture.md          → 通用编码规则（分层约束、设计原则、编码标准）
module-map.md            → 速查（模块在哪、管什么）
event-conventions.md     → Event/Listener/Job 开发模板
cross-module-guide.md    → 跨模块改动清单（做什么 → 引用去哪看）
```

## 执行流程

### 第一步：获取项目信息

优先从 `docs/` 目录获取，回退到代码扫描。

**模式 A：docs 存在（推荐）**

检查 `docs/` 目录是否包含各模块的文档。如果存在，直接读取：

- `docs/{service-name}/overview.md` → 模块职责、目录结构、技术栈、跨模块依赖
- `docs/{service-name}/contracts.md` → 事件契约、路由清单、Job 列表、跨模块调用
- `docs/cross-module.md` → 模块间依赖矩阵

仅补充读取 `composer.json` 获取模块命名空间映射。

**模式 B：docs 不存在（回退）**

并行执行代码扫描，建立项目认知：

- **项目结构**：读取 `composer.json` 获取 `autoload.psr-4` 命名空间映射；扫描 `modules/` 获取模块列表
- **模块职责**：读取每个模块的 `ServiceProvider.php` 了解注册的路由、事件、命令
- **事件扫描**：扫描所有 `Events/` 目录获取事件类列表；扫描 `Listeners/` 获取监听器列表；追踪 `ServiceProvider` 中的事件绑定
- **Job 扫描**：扫描所有 `Jobs/` 目录获取队列任务列表
- **跨模块引用**：grep 各模块代码中对其他模块命名空间的 `use` 引用
- **路由扫描**：扫描所有 `Http/Routes/` 获取路由文件类型和数量

### 第二步：生成通用规则文件（模板直出）

读取 `templates/` 目录下的模板，直接写入目标项目：

1. **`.claude/rules/architecture.md`** ← 读取 `templates/architecture.md`，直接复制
2. **`.claude/rules/coding.md`** ← 读取 `templates/coding.md`，直接复制

这个文件是通用标准，所有 PHP 项目完全一致，不做任何定制。

### 第三步：生成项目特有规则文件（模板 + 扫描填充）

读取 `references/` 目录下的生成指南，结合第一步获取的项目信息生成：

1. **`.claude/rules/module-map.md`** ← 读取 `references/module-map-guide.md`
2. **`.claude/rules/event-conventions.md`** ← 读取 `references/event-conventions-guide.md`
3. **`.claude/rules/cross-module.md`** ← 读取 `references/cross-module-guide.md`

### 第三步补充：globs 动态生成

event-conventions.md 和 cross-module-guide.md 的 frontmatter globs 必须从第一步扫描结果中提取实际路径：

- 事件在 `modules/account/src/Events/` → globs 写 `modules/*/src/Events/**`
- 监听器在 `modules/account/src/Listeners/` → globs 写 `modules/*/src/Listeners/**`

architecture.md 和 module-map.md 不设 globs（无条件加载）。

### 第四步：生成 / 更新 CLAUDE.md

读取 `references/claude-md-guide.md`，结合第一步获取的项目信息生成或更新项目根目录的 CLAUDE.md。

CLAUDE.md 是纯入口导航文件，不持有任何事实内容或编码规则。

**增量更新原则**：

- CLAUDE.md 不存在 → 完整生成
- CLAUDE.md 已存在 → 保留手动补充的章节，只更新导航和索引部分
- 已有的 rules 文件 → 保留手动补充的内容，只更新可从代码推断的部分

### 第五步：完成摘要

输出简短摘要：

- 信息来源：docs 模式 / 代码扫描模式
- 模块数量、事件数量、监听器数量、Job 数量
- 生成 / 更新了哪些文件
- 跨模块引用数量和方向
- 标注"待确认"的信息
