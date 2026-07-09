# progress.md 模板 / 状态枚举 / 目录约定

> 写或更新 progress.md、初始化任务目录时读本文件。`progress.md` 是流程**唯一状态源**。

## 状态枚举

**需求/里程碑级状态**：`DISCUSSING | ANALYZING | PENDING_DESIGN_REVIEW | DEVELOPING | PENDING_PLAN_REVIEW | PENDING_CR_REVIEW | REVIEWING | PENDING_ACCEPT_REVIEW | ACCEPT_FIXING | COMPLETED`（多里程碑需求级用 `IN_PROGRESS`）

**任务级状态流转**：`TODO →（复杂任务：PLANNING → PLAN_CONFIRMED →）CODING → CR_SCANNED(待人工确认) → CR_CONFIRMED → REWRITING → VERIFYING → DONE`

## 任务编号规范

所有任务统一使用 `X.Y` 格式编号（禁止 T1、0.1、波次1 等非标格式）：

- **X** = 任务组编号（按模块分组，从 1 起始）
- **Y** = 组内子任务编号（从 1 起始）
- 示例：`1.1`、`1.2`、`2.1`、`2.2`、`3.1`

编号在阶段 2 产出 dev-tasks.md 时确定，后续 progress.md、plans/、done/、review/ 文件名均引用同一编号，全流程一致。

| 场景 | 文件名格式 |
|------|-----------|
| plan | `.task/plans/{模块名}-{X.Y}.md` |
| done 报告 | `.task/done/{模块名}-{X.Y}.md` |
| CR 报告 | `.task/review/{模块名}-{X.Y}.md` |

---

## 目录约定

**单里程碑（默认）**：
```
docs/                              # 需求级参考文档（业务说明、接口文档、原始材料等，用户手动放入）
.task/
  progress.md
  analysis/  design-consensus.md  dev-tasks.md  plans/  done/  review/  rework/
                                                 ↑ plans=复杂任务LLD  rework=返工单（缺陷返工时才有）
```
**多里程碑（split 后）**：
```
docs/                              # 需求级参考文档（同上，跨里程碑共享）
.task/
  progress.md                 # 含里程碑进度表（唯一状态源）
  design-foundation.md        # 可选：跨里程碑公共设计骨架
  milestones/
    {里程碑A}/  analysis/ design-consensus.md dev-tasks.md plans/ done/ review/ rework/
    {里程碑B}/  analysis/ design-consensus.md dev-tasks.md plans/ done/ review/ rework/
```
另：`docs/discuss/.workflow-active` 是活动上下文指针（单行 `{需求ID}[#里程碑]`，便捷用，非状态源）。

**产出物根路径约定**：阶段 2~5 产出物路径写作 `.task/{...}` 时，单里程碑指 `docs/discuss/{需求ID}/.task/{...}`；多里程碑下除讨论文档、架构时序图、`design-foundation.md` 等需求级共享物外，分析/设计/任务/审查一律落到 `.task/milestones/{里程碑}/{...}`，各 agent 工作范围限定在该里程碑覆盖的模块。两种模式执行逻辑一致，仅根路径不同。

---

## 单里程碑（默认）progress.md 模板

```markdown
# {需求名} 开发进度

## 基本信息
- 需求ID: {域}/{需求名}
- 创建时间: {ISO 时间}
- 里程碑模式: 单里程碑
- 父需求: {无 | {域}/{父需求名}（已完成，设计参考见 docs/parent/）}
- 当前阶段: {1-5}
- 当前状态: {DISCUSSING | ANALYZING | PENDING_DESIGN_REVIEW | DEVELOPING | PENDING_PLAN_REVIEW | PENDING_CR_REVIEW | REVIEWING | COMPLETED}

## 影响模块
- {模块名列表，阶段 2 开始时填入}

## 阶段记录
| 阶段 | 状态 | 开始时间 | 完成时间 | 备注 |
|------|------|---------|---------|------|
| 1 需求讨论 | {状态} | | | |
| 2 分析与设计 | {状态} | | | |
| 3 设计审核 | {状态} | | | |
| 4 开发与逐任务审查 | {状态} | | | |
| 5 收尾验收 | {状态} | | | |

## 任务清单（逐任务跟踪，与 dev-tasks.md 同步）
> 每个任务的完成定义（DoD）：代码写完 + 单测写完 + 该模块 phpunit 绿 + php -l 语法校验通过 + CR 扫描 + **CR 问题人工确认** + 已采纳问题改写完成 + 复验通过 → 才勾选。（phpstan 默认不纳入 DoD）
> 任务状态流转：`TODO →（复杂任务：PLANNING → PLAN_CONFIRMED →）CODING → CR_SCANNED(待人工确认) → CR_CONFIRMED → REWRITING → VERIFYING → DONE`
- [ ] {X.Y} {模块名} · {任务标题} [{简单|复杂}] — 状态: {TODO|PLANNING|PLAN_CONFIRMED|CODING|CR_SCANNED|CR_CONFIRMED|REWRITING|VERIFYING|DONE} — plan: .task/plans/{模块名}-{X.Y}.md — CR: .task/review/{模块名}-{X.Y}.md

## 返工记录（无返工时省略；由 /php-workflow rework 追加）
| 轮次 | 日期 | 根因层级 | 影响任务 | 返工单 |
|------|------|---------|---------|--------|
| R1 | {YYYY-MM-DD} | {实现|设计|需求}级 | {X.Y 列表} | {rework/R1-...md} |
```

---

## 多里程碑（split 后）progress.md 模板

需求层只保留共享信息与里程碑进度表；阶段记录与任务清单下沉到每个里程碑。

```markdown
# {需求名} 开发进度

## 基本信息
- 需求ID: {域}/{需求名}
- 创建时间: {ISO 时间}
- 里程碑模式: 多里程碑
- 父需求: {无 | {域}/{父需求名}（已完成，设计参考见 docs/parent/）}
- 需求级状态: {DISCUSSING(阶段1) | IN_PROGRESS | COMPLETED}   # 全部里程碑 COMPLETED → 需求 COMPLETED

## 影响模块（需求级汇总）
- {全部里程碑涉及的模块并集}

## 共享产出物
- 讨论文档 / 架构时序图 / design-foundation.md（公共设计骨架）

## 里程碑进度表
| 里程碑 | 影响模块 | 依赖 | 阶段 | 状态 | 任务进度 |
|--------|---------|------|------|------|---------|
| {里程碑A} | {模块} | - | {1-5} | {状态} | {x/N} |
| {里程碑B} | {模块} | {里程碑A} | {1-5} | {状态} | {x/N} |

## 返工记录（无返工时省略；由 /php-workflow rework 追加）
| 轮次 | 日期 | 里程碑 | 根因层级 | 影响任务数 | 返工单 |
|------|------|--------|---------|-----------|--------|
| R1 | {YYYY-MM-DD} | {里程碑} | {实现|设计|需求}级 | {N} | {rework/R1-...md} |

---
## 里程碑：{里程碑A}
### 阶段记录
| 阶段 | 状态 | 开始时间 | 完成时间 | 备注 |
|------|------|---------|---------|------|
| 2 分析与设计 | {状态} | | | |
| 3 设计审核 | {状态} | | | |
| 4 开发与逐任务审查 | {状态} | | | |
| 5 收尾验收 | {状态} | | | |
### 任务清单（逐任务，与 milestones/{里程碑A}/dev-tasks.md 同步）
- [ ] {X.Y} {模块名} · {任务标题} [{简单|复杂}] — 状态: {TODO|PLANNING|PLAN_CONFIRMED|CODING|CR_SCANNED|CR_CONFIRMED|REWRITING|VERIFYING|DONE} — plan: milestones/{里程碑A}/plans/{模块名}-{X.Y}.md — CR: milestones/{里程碑A}/review/{模块名}-{X.Y}.md

---
## 里程碑：{里程碑B}
（结构同上）
```

> 多里程碑下不存在需求级"当前阶段"——各里程碑各自推进；需求级状态只反映总体进展。
