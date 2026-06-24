# CLAUDE.md 生成指南

CLAUDE.md 是项目的核心规则文件，启动时始终加载。保持精简（<80 行），只放项目特有信息和索引。

通用的架构规则、设计原则、编码标准已拆到 `.claude/rules/architecture.md`，CLAUDE.md 中不再重复。

## 输出模板

CLAUDE.md 是纯入口文件，不持有任何事实内容或编码规则。只包含三部分：项目一句话、文档阅读顺序、规则文件索引。

```markdown
{项目一句话职责描述，从 composer.json name + 核心模块 Action 类推断}

## 文档阅读顺序

| 顺序 | 文档 | 什么时候看 |
|------|------|-----------|
| 1 | [docs/{module}/overview.md] | 初次进入某个模块：模块职责、目录结构、依赖 |
| 2 | [docs/{module}/business.md] | 实现业务逻辑前：状态机、业务规则 |
| 3 | [docs/{module}/contracts.md] | 改 Event/路由前：事件契约、API 清单、跨模块调用 |
| 4 | [docs/{module}/flows.md] | 评估影响范围：执行流程、事件级联链路 |
| 5 | [docs/cross-module.md] | 跨模块改动时：模块间依赖矩阵 |

{只列出 docs/ 下实际存在的文件，如果 docs/ 不存在则省略此部分}

## 模块清单

| 模块 | 命名空间 | 职责 |
|------|---------|------|
| account | Account\ | {一句话} |
| user | User\ | {一句话} |
| game | Game\ | {一句话} |
| platform | Platform\ | {一句话} |
| misc | Misc\ | {一句话} |
| tao-ai-wan | TaoAiWan\ | {一句话} |

详细模块信息见 `.claude/rules/module-map.md`

## 规则文件（.claude/rules/）

### 始终加载

| 文件 | 内容 |
|------|------|
| `architecture.md` | 分层约束、编码标准、目录约定、完成检查清单 |
| `module-map.md` | 模块速查表（命名空间、目录、职责、跨模块引用方向） |

### 按需加载（globs 匹配时自动加载）

| 文件 | 内容 |
|------|------|
| `event-conventions.md` | Event/Listener/Job 开发模板、幂等约定 |
| `cross-module-guide.md` | 跨模块改动清单、引用约束、完成汇报格式 |
```

**关键原则**：
- 模块职责和目录结构由 `docs/{module}/overview.md` 持有，CLAUDE.md 只放一句话速查
- 架构规则和编码标准由 `architecture.md` 持有
- Event/Job 规范由 `event-conventions.md` 持有
- CLAUDE.md 不重复以上任何内容

## 增量更新规则

- CLAUDE.md 不持有事实内容（模块详情、技术栈）和编码规则
- 已有的 CLAUDE.md 如果包含这些内容，迁移到对应文件后从 CLAUDE.md 中移除
- 禁止删除已有的自定义章节（如果不属于上述迁移范围）
