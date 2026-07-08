# {项目名称}

{项目一句话职责描述，从 composer.json name + 核心模块 Action 类推断}

## 文档阅读顺序

| 顺序 | 文档                                | 什么时候看                                      |
| ---- | ----------------------------------- | ----------------------------------------------- |
| 1    | docs/workflow/{module}/overview.md  | 初次进入某个模块：模块职责、目录结构、依赖      |
| 2    | docs/workflow/{module}/business.md  | 实现业务逻辑前：状态机、业务规则                |
| 3    | docs/workflow/{module}/contracts.md | 改 Event/路由前：事件契约、API 清单、跨模块调用 |
| 4    | docs/workflow/{module}/flows.md     | 评估影响范围：执行流程、事件级联链路            |
| 5    | docs/workflow/cross-module.md       | 跨模块改动时：模块间依赖矩阵                    |

{只列出 docs/workflow/ 下实际存在的文件，如果 docs/workflow/ 不存在则省略此部分}

## 模块清单

| 模块       | 命名空间  | 职责     |
| ---------- | --------- | -------- |
| account    | Account\  | {一句话} |
| user       | User\     | {一句话} |
| game       | Game\     | {一句话} |
| platform   | Platform\ | {一句话} |
| misc       | Misc\     | {一句话} |
| tao-ai-wan | TaoAiWan\ | {一句话} |

详细模块信息见 `.claude/rules/module-map.md`

## 规则文件（.claude/rules/）

### 始终加载

| 文件              | 内容                                               |
| ----------------- | -------------------------------------------------- |
| `architecture.md` | 分层约束、编码标准、目录约定、完成检查清单         |
| `module-map.md`   | 模块速查表（命名空间、目录、职责、跨模块引用方向） |

### 按需加载（globs 匹配时自动加载）

| 文件                   | 内容                                   |
| ---------------------- | -------------------------------------- |
| `event-conventions.md` | Event/Listener/Job 开发模板、幂等约定  |
| `coding.md`            | 在进行编码任务时候读取                 |
| `cross-module.md`      | 跨模块改动清单、引用约束、完成汇报格式 |