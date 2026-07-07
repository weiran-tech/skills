# 阶段 2：分析与设计（ANALYZING）

> **作用域：子需求级**。本阶段在单个子需求上独立推进；两个无依赖的子需求可同时进入 ANALYZING 状态（AC8）。所有产物落到子需求目录 `docs/discuss/{域}/{父需求名}/.task/{子需求名}/`，不在父需求层或里程碑层共享。子需求 ID 格式为 `{域}/{父需求名}#{子需求名}`，见 templates.md §0。完成本阶段后须更新 `metadata.md` 的「阶段产物引用」字段，登记 analysis/design.md 路径。

## 步骤 1：受影响模块独立分析

1. 从讨论文档的影响分析章节提取受影响的模块列表
2. 将模块列表写入 metadata.md 的「阶段产物引用」对应分析条目（路径见 templates.md §1）
3. 优先复用已有架构文档 `docs/architecture/{模块名}/`；若文档缺失或过期，对相关模块启动分析

**复用已有文档（推荐，省成本）**：直接读取 `docs/architecture/{模块名}/{overview,business,contracts,flows}.md` 和 `docs/architecture/cross-module.md` 作为分析基础，再针对本次需求做 GAP 分析。

**需要新鲜分析时**，按模块启动 analyst：
```
/oh-my-claudecode:team {N}:analyst "
针对子需求 {域}/{父需求名}#{子需求名}，按照父需求讨论文档 docs/discuss/{域}/{父需求名}.md 和子需求讨论文档 docs/discuss/{域}/{父需求名}/.task/{子需求名}/discussion.md 的影响分析，分别分析各受影响模块（同一仓库内）：
{对每个受影响的模块生成一行}
- {module_root_glob}/{模块名} → 读代码 + 读 docs/architecture/{模块名}/ → 产出 docs/discuss/{域}/{父需求名}/.task/{子需求名}/analysis/{模块名}.md

每个 analyst 产出（输出文档首行必须为子需求 ID 头：'# 子需求：{域}/{父需求名}#{子需求名}'，用于与父需求关联）：
a. 当前模块与子需求相关的现有代码结构、主要入口、对外契约
b. 需要新增/修改的接口、数据模型、事件/监听契约（{contract_type} 通道）
c. 与讨论文档设计建议的 GAP 分析

每个 analyst 只读自己负责的模块目录，不跨模块写文件。
Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"
```

## 步骤 2：汇总设计（分析完成后自动执行）

```
ralph: "针对子需求 {域}/{父需求名}#{子需求名}，读取 docs/discuss/{域}/{父需求名}/.task/{子需求名}/analysis/ 下全部分析文档，
结合 docs/discuss/{域}/{父需求名}.md 父需求讨论文档和 docs/discuss/{域}/{父需求名}/.task/{子需求名}/discussion.md 子需求讨论文档，
参照 docs/architecture/cross-module.md 校验跨模块契约链（通过 {contract_type} 通道）的完整性。

生成（输出文档首行必须为子需求 ID 头：'# 子需求：{域}/{父需求名}#{子需求名}'）：
- docs/discuss/{域}/{父需求名}/.task/{子需求名}/design-consensus.md —— 共识/契约层，**必含清单**（缺项视为未完成）：
  1. 对外契约：接口定义、{contract_type} 契约、跨模块调用
  2. 模块边界：本子需求触碰的模块职责、谁不该被改
  3. 关键机制决策：核心方案选型 + **为什么这么选**（取舍理由）
  4. 验收标准
  5. 未决项登记：所有 `待确认 / TODO` 集中成一张表（编号 / 描述 / 影响 / 处置：待定|编码用 placeholder 上线前补）
  6. 简单任务的实现要点：对预计可直接编码的任务，补足够开工的签名/字段/关键流程（复杂任务不在此展开，留给阶段 4 的任务级 plan）
- docs/discuss/{域}/{父需求名}/.task/{子需求名}/dev-tasks.md（含开发任务、依赖顺序、模块路径 {module_root_glob}/{模块名}；并对每个任务标注复杂度 简单|复杂，复杂任务在阶段 4 编码前需出 plan）

如存在接口冲突或设计分歧，写入 docs/discuss/{域}/{父需求名}/.task/{子需求名}/conflicts.md 后停止，
更新 metadata.md 的 currentState 为 BLOCKED（在状态枚举外的临时值，需经 version create 流程重新激活；本字段变更必须伴随 updatedAt 刷新）。

遵守项目 CLAUDE.md 与 .claude/rules/ 的架构与编码规范。
如项目已配置 {discovery_cmd}（静态分析器），可作为黑盒工具调用以补充契约信息。
执行约束见 SKILL.md 不变量 12：Bash 命令必须可静态分析；产出物只落项目内 .task/。"
```

完成后更新 metadata.md：`currentStage = 2`、`currentState = PENDING_DESIGN_REVIEW`，同步刷新 `updatedAt`，并在「阶段产物引用」表登记 `analysis/` 和 `design.md` 路径（templates.md §1）。随后输出设计摘要，等待用户 `/dev-workflow approve {子需求ID}`（审核走阶段 3，见 stage-3-review.md）。

> **设计分两层**：design-consensus = 共识/契约层（小需求够用）；复杂任务的实现细节留给阶段 4 的任务级 plan/LLD。详见 stage-4-dev.md。
