# 阶段 2：分析与设计（ANALYZING）

> 将模块分析和汇总设计自动串联为一个阶段。产出物根路径见 templates.md。

## 步骤 1：受影响模块独立分析

1. 从讨论文档的影响分析章节提取受影响的模块列表
2. 将模块列表写入 progress.md 的"影响模块"字段
3. 优先复用已有架构文档 `docs/{模块名}/`；若文档缺失或过期，对相关模块启动分析

**复用已有文档（推荐，省成本）**：直接读取 `docs/{模块名}/{overview,business,contracts,flows}.md` 和 `docs/cross-module.md` 作为分析基础，再针对本次需求做 GAP 分析。

**需要新鲜分析时**，按模块启动 analyst：
```
/oh-my-claudecode:team {N}:analyst "
按照讨论文档 docs/.req-discuss/{域}/{需求名}.md 的影响分析，分别分析各受影响模块（同一仓库内）：
{对每个受影响的模块生成一行}
- modules/{模块名} → 读代码 + 读 docs/{模块名}/ → 产出 docs/.req-discuss/{域}/{需求名}/.task/analysis/{模块名}.md

每个 analyst 产出：
a. 当前模块与需求相关的现有代码结构、Controller/Action/Service 入口、对外契约
b. 需要新增/修改的接口、数据模型、Event/Listener
c. 与讨论文档设计建议的 GAP 分析

每个 analyst 只读自己负责的模块目录，不跨模块写文件。
Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"
```

## 步骤 2：汇总设计（分析完成后自动执行）

```
ralph: "读取 docs/.req-discuss/{域}/{需求名}/.task/analysis/ 下全部分析文档，
结合 docs/.req-discuss/{域}/{需求名}.md 讨论文档，
参照 docs/cross-module.md 校验跨模块事件链（Event/Listener）的完整性。

生成：
- docs/.req-discuss/{域}/{需求名}/.task/design-consensus.md —— 共识/契约层，**必含清单**（缺项视为未完成）：
  1. 对外契约：接口定义、Event/Listener 契约、跨模块 RPC/Service 调用
  2. 模块边界：本需求触碰的模块职责、谁不该被改
  3. 关键机制决策：核心方案选型 + **为什么这么选**（取舍理由）
  4. 验收标准
  5. 未决项登记：所有 `待确认 / TODO` 集中成一张表（编号 / 描述 / 影响 / 处置：待定|编码用 placeholder 上线前补）
  6. 简单任务的实现要点：对预计可直接编码的任务，补足够开工的签名/字段/关键流程（复杂任务不在此展开，留给阶段 4 的任务级 plan）
- docs/.req-discuss/{域}/{需求名}/.task/dev-tasks.md（含开发任务、依赖顺序、模块路径 modules/{模块名}；并对每个任务标注复杂度 简单|复杂，复杂任务在阶段 4 编码前需出 plan）

如存在接口冲突或设计分歧，写入 .task/conflicts.md 后停止，
在 progress.md 标记 BLOCKED 并说明冲突原因。

遵守项目 CLAUDE.md 与 .claude/rules/ 的架构与编码规范。"
```

完成后更新 progress.md 为 PENDING_DESIGN_REVIEW，输出设计摘要，等待用户 `/php-workflow approve`（审核走阶段 3，见 stage-3-review.md）。

> **设计分两层**：design-consensus = 共识/契约层（小需求够用）；复杂任务的实现细节留给阶段 4 的任务级 plan/LLD。详见 stage-4-dev.md。
