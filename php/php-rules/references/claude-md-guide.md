# CLAUDE.md 生成指南

CLAUDE.md 是项目的核心规则文件，启动时始终加载。保持精简（<80 行），只放项目特有信息和索引。

通用的架构规则、设计原则、编码标准已拆到 `.claude/rules/architecture.md`，CLAUDE.md 中不再重复。

## 输出模板

CLAUDE.md 是纯入口文件，不持有任何事实内容或编码规则。只包含三部分：项目一句话、文档阅读顺序、规则文件索引。

模版文件位置 [模板](../templates/claude.md)

**关键原则**：

- 模块职责和目录结构由 `docs/workflow/{module}/overview.md` 持有，CLAUDE.md 只放一句话速查
- 架构规则和编码标准由 `architecture.md` 持有
- Event/Job 规范由 `event-conventions.md` 持有
- CLAUDE.md 不重复以上任何内容

## 增量更新规则

- CLAUDE.md 不持有事实内容（模块详情、技术栈）和编码规则
- 已有的 CLAUDE.md 如果包含这些内容，迁移到对应文件后从 CLAUDE.md 中移除
- 禁止删除已有的自定义章节（如果不属于上述迁移范围）
