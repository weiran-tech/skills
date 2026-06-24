# progress.md 模板 / 状态枚举 / 目录约定

> 写或更新 progress.md、初始化任务目录时读本文件。`progress.md` 是流程**唯一状态源**。

## 状态枚举

**需求/里程碑级状态**：`DISCUSSING | ANALYZING | PENDING_DESIGN_REVIEW | DEVELOPING | PENDING_PLAN_REVIEW | PENDING_CR_REVIEW | REVIEWING | COMPLETED`（多里程碑需求级用 `IN_PROGRESS`）

**任务级状态流转**：`TODO →（复杂任务：PLANNING → PLAN_CONFIRMED →）CODING → CR_SCANNED(待人工确认) → CR_CONFIRMED → REWRITING → VERIFYING → DONE`

## 目录约定

**单里程碑（默认）**：
```
.task/
  progress.md
  analysis/  design-consensus.md  dev-tasks.md  plans/  done/  review/  rework/
                                                 ↑ plans=复杂任务LLD  rework=返工单（缺陷返工时才有）
```
**多里程碑（split 后）**：
```
.task/
  progress.md                 # 含里程碑进度表（唯一状态源）
  design-foundation.md        # 可选：跨里程碑公共设计骨架
  milestones/
    {里程碑A}/  analysis/ design-consensus.md dev-tasks.md plans/ done/ review/ rework/
    {里程碑B}/  analysis/ design-consensus.md dev-tasks.md plans/ done/ review/ rework/
```
另：`docs/.req-discuss/.workflow-active` 是活动上下文指针（单行 `{需求ID}[#里程碑]`，便捷用，非状态源）。

**产出物根路径约定**：阶段 2~5 产出物路径写作 `.task/{...}` 时，单里程碑指 `docs/.req-discuss/{域}/{需求名}/.task/{...}`；多里程碑下除讨论文档、架构时序图、`design-foundation.md` 等需求级共享物外，分析/设计/任务/审查一律落到 `.task/milestones/{里程碑}/{...}`，各 agent 工作范围限定在该里程碑覆盖的模块。两种模式执行逻辑一致，仅根路径不同。

---

## 单里程碑（默认）progress.md 模板

```markdown
# {需求名} 开发进度

## 基本信息
- 需求ID: {域}/{需求名}
- 创建时间: {ISO 时间}
- 里程碑模式: 单里程碑
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
- [ ] {序号} {模块名} · {任务标题} [{简单|复杂}] — 状态: {TODO|PLANNING|PLAN_CONFIRMED|CODING|CR_SCANNED|CR_CONFIRMED|REWRITING|VERIFYING|DONE} — plan: .task/plans/{序号}-{模块名}.md — CR: .task/review/{模块名}-{任务序号}.md

## 返工记录（无返工时省略；由 /php-workflow rework 追加）
| 轮次 | 日期 | 根因层级 | 影响任务 | 返工单 |
|------|------|---------|---------|--------|
| R1 | {YYYY-MM-DD} | {实现|设计|需求}级 | {任务序号列表} | {rework/R1-...md} |
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
- [ ] {序号} {模块名} · {任务标题} [{简单|复杂}] — 状态: {TODO|PLANNING|PLAN_CONFIRMED|CODING|CR_SCANNED|CR_CONFIRMED|REWRITING|VERIFYING|DONE} — plan: milestones/{里程碑A}/plans/{序号}-{模块名}.md — CR: milestones/{里程碑A}/review/{模块名}-{任务序号}.md

---
## 里程碑：{里程碑B}
（结构同上）
```

> 多里程碑下不存在需求级"当前阶段"——各里程碑各自推进；需求级状态只反映总体进展。
