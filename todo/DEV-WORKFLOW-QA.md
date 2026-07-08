# dev-workflow QA — 交互流程 / 文件追踪 / 节点清单

```



  - 哪些文件的作用存在冲突, 
  - 哪些命令应当移除, 
  - 命令的边界是什么, 
  - 不同文件应当承担什么样的作用
```

> 目的：把 `/devops-workflow/` 下的全部内容做一份"测试与排查手册"——读完它就能照着走完一遍流程、知道每个文件管什么、知道每个节点该读谁/写谁/校验谁。
>
> 本 QA 文档基于以下文件（2026-07-07 读取快照）：

| 路径                           | 角色                                                                  |
| ------------------------------ | --------------------------------------------------------------------- |
| `SKILL.md`                     | 路由器 + 常驻安全规则（19 启用 + 3 删除命令）                         |
| `README.md`                    | 总体流程、设计理念、命令速查、使用示例（人读的叙事）                  |
| `references/discovery.md`      | 上下文发现机制（manifest + CLAUDE.md → DiscoveryContext）             |
| `references/templates.md`      | `metadata.md` 模板、状态枚举、目录约定（Schema 权威）                 |
| `references/commands.md`       | 各 `/devops-workflow` 子命令的详细处理逻辑（命令权威）                |
| `references/stage-2-design.md` | 阶段 2 分析与设计（analyst + ralph 流程）                             |
| `references/stage-3-review.md` | 阶段 3 设计审核（PENDING_DESIGN_REVIEW 人工门）                       |
| `references/stage-4-dev.md`    | 阶段 4 开发与逐任务审查（含 plan/code/CR/改写）                       |
| `references/stage-5-accept.md` | 阶段 5 收尾验收 + 异常处理（BLOCKED / 回退 / 恢复）                   |
| `references/rework.md`         | rework 返工通道（实现级 / 设计级 / 需求级）                           |
| `references/summary.md`        | `/devops-workflow summary` 交付清单（DDL / 队列 / API，含 `--merge`） |

---

## 一、整体交互流程（一次子需求从 0 到 COMPLETED）

### 1.1 五阶段 + 三道人工门

```
阶段 1 需求讨论        /devops-workflow req create {service-name}/{父需求名}
                          ↓
                          /devops-workflow req split {service-name}/{父需求名}   （交互式向导逐个创建子需求 metadata.md）
                          ↓
                                  （产生父需求讨论文档 docs/discuss/{service-name}/{父需求名}/{父需求名}.md + 子需求 discussion.md）
   ▼
阶段 2 分析与设计      /devops-workflow next {子需求ID}
                          （产生 analysis/、design.md、design-consensus.md、dev-tasks.md）
   ▼
┌────────────────────────────────────────────────┐
│ 阶段 3 设计审核门  ★人工★  PENDING_DESIGN_REVIEW │  ← 清单式审核，缺项打回阶段 2
│   /devops-workflow approve {子需求ID}                           │
└────────────────────────────────────────────────┘
   ▼
阶段 4 开发与逐任务审查   /devops-workflow next {子需求ID}
                          （plan → 编码 → CR → 改写 → 复验 → DONE）
   ▼
阶段 5 收尾验收        /devops-workflow next {子需求ID}
   │  （产生 acceptance.md）
   ▼
COMPLETED ──→ /devops-workflow version ready ... close ... archive
            ──→ /devops-workflow summary {版本号}              →  change-manifest.md（DDL / Job·MQ / API，给 DBA 与前端）
            ──→ /devops-workflow summary --merge {V1} {V2} ...  →  docs/version/.merged/change-manifest-{Y}-{M}-{D}.md

※ 阶段 4/5 若发现设计/需求层缺陷 → /devops-workflow rework {子需求ID} 按根因层级回退

※ 任何时候变更 manifest / CLAUDE.md / docs/workflow/ → /devops-workflow discovery refresh
```

### 1.2 阶段 4 任务级闭环（每个任务独立走完）

```
TODO
 │ ⓪ 复杂度判断（Claude）
 ├─ 简单 ──────────────────────────────────┐
 └─ 复杂 → 出 plan/LLD (architect/planner, 只读)
          ▼ PLANNING
       ┌────────────────────────────────────────┐
       │ plan 人工门 ★人工★ PENDING_PLAN_REVIEW  │
       │   /devops-workflow approve {子需求ID}      │
       └────────────────────────────────────────┘
          ▼ PLAN_CONFIRMED
 ┌─────────────────────────────────────────────┘
 │ ① 编码 (executor；简单对照 design.md / 复杂对照已确认 plan)
 ▼ CODING
 │ ② DoD：{test_cmd} 绿 + {lint_cmd} 语法校验通过
 │ ③ CR 扫描 (code-reviewer，只读，只产出编号问题清单，不改代码)
 ▼ CR_SCANNED
       ┌────────────────────────────────────────┐
       │ CR 问题人工门 ★人工★ PENDING_CR_REVIEW  │  ← 逐条裁决 ACCEPTED/REJECTED/MODIFIED
       │   /devops-workflow approve {子需求ID}      │
       └────────────────────────────────────────┘
 ▼ CR_CONFIRMED
 │ ⑤ 改写 (executor，只改已采纳项)
 ▼ REWRITING
 │ ⑥ 复验 + 进度回写（强制）：{test_cmd} 绿 + {lint_cmd} 通过 → 回写 metadata.md 任务状态行 + dev-tasks.md
 ▼ VERIFYING → DONE
```

### 1.3 三道人工门汇总

| 门                         | 触发状态                | 操作命令                              | 通过标志                                | 落地动作                                                                |
| -------------------------- | ----------------------- | ------------------------------------- | --------------------------------------- | ----------------------------------------------------------------------- |
| 设计审核门                 | `PENDING_DESIGN_REVIEW` | `/devops-workflow approve {子需求ID}` | design-consensus 必含清单逐项 ✓         | design-consensus.md 末尾追加 `## 设计确认: APPROVED`，状态置 DEVELOPING |
| 任务 plan 门（仅复杂任务） | `PENDING_PLAN_REVIEW`   | `/devops-workflow approve {子需求ID}` | plan 必含项齐全                         | plan.md 末尾追加 `## 设计确认: APPROVED`，任务状态置 PLAN_CONFIRMED     |
| CR 问题裁决门（逐任务）    | `PENDING_CR_REVIEW`     | `/devops-workflow approve {子需求ID}` | 全部问题标注 ACCEPTED/REJECTED/MODIFIED | 任务状态置 CR_CONFIRMED → 走改写⑤ / 复验⑥                               |

### 1.4 状态机（子需求级 + 版本级，独立运转）

子需求状态（8 态，写 metadata.md.currentState）：

```
DISCUSSING ──next──> ANALYZING ──next──> PENDING_DESIGN_REVIEW ──approve──> DEVELOPING
                                                                              │
                                                                  (复杂任务) │
                                                                          ↓    │
                                                              PENDING_PLAN_REVIEW
                                                                          │    │
                                                              approve ↓     │    │
                                                                          ↓    │
                                                  PENDING_CR_REVIEW ←  CR_SCANNED
                                                          │ approve
                                                          ↓
                                                      REVIEWING ──next──> COMPLETED
                                                          ↑                    │
                                                          └─── rework ─────────┘
                                                                  (实现级)
                                                              ANALYZING ←──┘
                                                              DISCUSSING ←──┘ (需求级)
```

版本状态（5 态，写 docs/version/{版本号}.status，独立于子需求状态机）：

```
DRAFT ──version start──> IN_PROGRESS ──version ready──> READY ──version close──> RELEASED ──version archive──> ARCHIVED
                                                                                                              ↑
                                                                                                     永久封存（不可逆）
```

任务级状态：`TODO → (PLANNING → PLAN_CONFIRMED) → CODING → CR_SCANNED → CR_CONFIRMED → REWRITING → VERIFYING → DONE`

---

## 二、文件过程追踪清单（按"读谁 → 写谁 → 校验谁"组织）

### 2.1 阶段 1：需求讨论（`req create` + `req split`）

| 动作                             | 触发                                          | 读取                                                 | 写入                                                          | 校验                         |
| -------------------------------- | --------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------- | ---------------------------- |
| 校验域合法性                     | `/devops-workflow req create {service-name}/{父需求名}` | `{discovery_cmd}` 域清单 / `docs/workflow/` 模块命名 | —                                                             | 域 ∈ manifest 声明的模块清单 |
| 校验父需求不存在                 | 同上                                          | `docs/discuss/{service-name}/{父需求名}/` 是否存在             | —                                                             | 不存在才能创建               |
| 创建父需求目录骨架               | 同上                                          | —                                                    | `docs/discuss/{service-name}/{父需求名}/.task/parent.md`                | —                            |
| 列出已存在子需求（用于重名检查） | `/devops-workflow req split {service-name}/{父需求名}`  | `.task/` 子目录扫描                                  | —                                                             | 用于交互式向导重名检查       |
| 交互式向导循环                   | 同上                                          | —                                                    | 每个子需求一个目录 + `metadata.md`（8 字段）                  | 描述非空                     |
| 父需求讨论文档                   | 阶段 1                                        | —                                                    | `docs/discuss/{service-name}/{父需求名}/{父需求名}.md`                  | 含「影响分析」章节           |
| 子需求讨论文档                   | 阶段 1 触发                                   | —                                                    | `docs/discuss/{service-name}/{父需求名}/.task/{子需求名}/discussion.md` | 包含子需求特定讨论           |
| 回写 metadata.md 引用            | 子需求创建时                                  | `references/templates.md` §1                         | `metadata.md` 阶段产物引用表                                  | 8 字段齐全                   |

### 2.2 阶段 2：分析与设计（`next` → ANALYZING）

| 动作                 | 触发                               | 读取                                                                                             | 写入                                                                                     | 校验                                               |
| -------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- | -------------------------------------------------- |
| 提取受影响模块       | `/devops-workflow next {子需求ID}` | 父需求讨论文档 + 子需求 `discussion.md` 影响分析                                                 | `metadata.md` 阶段产物引用表                                                             | —                                                  |
| 优先复用架构文档     | 同上                               | `docs/workflow/{模块名}/{overview,business,contracts,flows}.md`、`docs/workflow/cross-module.md` | —                                                                                        | 文档缺失或过期时启动分析                           |
| 逐模块分析（必要时） | 启动 `team {N}:analyst`            | `{module_root_glob}` 代码 + 架构文档                                                             | `.task/{子需求名}/analysis/{模块名}.md`                                                  | a/b/c 三段齐全                                     |
| 汇总设计             | 启动 `ralph`                       | 全部 `analysis/*.md` + 讨论文档 + `cross-module.md`                                              | `.task/{子需求名}/design-consensus.md`（必含 6 项清单）+ `.task/{子需求名}/dev-tasks.md` | 必含清单完整；冲突时写 `conflicts.md` 并标 BLOCKED |
| 更新 metadata.md     | 完成后                             | —                                                                                                | `currentStage=2`、`currentState=PENDING_DESIGN_REVIEW`、`updatedAt` 刷新                 | —                                                  |

**design-consensus.md 必含清单（缺项打回阶段 2）**：

1. 对外契约（接口 / {contract_type} 通道 / 跨模块调用）
2. 模块边界（谁该改 / 谁不该改）
3. 关键机制决策 + **取舍理由**
4. 验收标准
5. 未决项登记表（编号 / 描述 / 影响 / 处置：待定｜编码用 placeholder 上线前补）
6. 简单任务的实现要点（签名 / 字段 / 关键流程，复杂任务留 plan）

**dev-tasks.md 必含项**：
- 每个任务标注 `简单|复杂`
- 依赖顺序
- 模块路径 `{module_root_glob}/{模块名}/`

### 2.3 阶段 3：设计审核（`approve` → PENDING_DESIGN_REVIEW）

| 动作               | 触发                                  | 读取                       | 写入                                                                | 校验                             |
| ------------------ | ------------------------------------- | -------------------------- | ------------------------------------------------------------------- | -------------------------------- |
| 定位目标           | `/devops-workflow approve {子需求ID}` | `metadata.md.currentState` | —                                                                   | 必须处于 `PENDING_DESIGN_REVIEW` |
| 主 Agent 自查清单  | 同上                                  | `design-consensus.md`      | —                                                                   | 6 项逐项 ✓/✗                     |
| 提示用户审核       | 同上                                  | —                          | 输出提示（含自查结论）                                              | —                                |
| 通过：追加确认标记 | 人工逐项 ✓                            | —                          | `design-consensus.md` 末尾追加 `## 设计确认: APPROVED`              | —                                |
| 更新 metadata.md   | 通过后                                | —                          | `currentState=PENDING_DESIGN_REVIEW → DEVELOPING`、`updatedAt` 刷新 | —                                |

**审核清单**（缺项 / 过浅一律打回）：

- [ ] 对外契约齐全（接口 / {contract_type} 通道 / 跨模块调用）
- [ ] 模块边界清晰（谁该改、谁不该改）
- [ ] 关键机制决策有"为什么"
- [ ] 验收标准可执行
- [ ] 未决项已登记成表，每条有处置方式（不许悬空 TODO）
- [ ] 简单任务实现要点足以直接开工；复杂任务在 dev-tasks 标 `复杂`

### 2.4 阶段 4：开发与逐任务审查（`next` → DEVELOPING）

**进入阶段 4 首次**：

| 动作                 | 读取                             | 写入                              | 校验                                            |
| -------------------- | -------------------------------- | --------------------------------- | ----------------------------------------------- |
| 决定编码并行/串行    | `dev-tasks.md` 依赖图 + 模块目录 | `metadata.md` 阶段记录决策 + 理由 | 互不依赖 + 目录不重叠 → 并行；否则串行 / 按波次 |
| 推进当前未 DONE 任务 | —                                | —                                 | 复杂任务先 PLANNING；简单任务直接 CODING        |

**任务内闭环（每个任务独立走完）**：

| 子步骤                           | 状态变迁                                       | agent                                 | 读                                                                                                                | 写                                                                                                        | DoD 校验                                                    |
| -------------------------------- | ---------------------------------------------- | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| ⓪ 复杂度判断                     | TODO → PLANNING（复杂）/ TODO → CODING（简单） | Claude 自评                           | dev-tasks.md 标注                                                                                                 | —                                                                                                         | —                                                           |
| 出 plan（复杂）                  | PLANNING → PENDING_PLAN_REVIEW                 | `architect` / `planner`（只读）       | `design-consensus.md` + `docs/workflow/{service-name}` + 现有代码                                                 | `.task/{子需求名}/plans/{序号}-{模块名}.md`                                                               | 6 项齐全（签名 / 数据模型 / 时序 / 边界 / 测试用例 / 迁移） |
| 人工确认 plan                    | PENDING_PLAN_REVIEW → PLAN_CONFIRMED           | —                                     | plan.md                                                                                                           | plan.md 末尾追加 `## 设计确认: APPROVED`                                                                  | plan 不达标 → 打回重出                                      |
| ① 编码                           | PLAN_CONFIRMED / TODO → CODING                 | `executor`（并行 `team` / 串行单）    | `design-consensus.md` 或已确认 plan + 前序契约                                                                    | `{module_root_glob}` 代码 + 单测 + `.task/{子需求名}/done/{模块名}.md`                                    | DoD：单测绿 + {lint_cmd} 通过                               |
| ② DoD 自检                       | CODING                                         | 同上                                  | 改动文件                                                                                                          | —                                                                                                         | `{test_cmd}` 绿 + `{lint_cmd}` 通过                         |
| ③ CR 扫描                        | CODING → CR_SCANNED                            | `code-reviewer`（只读）               | `git diff <默认分支>...HEAD -- {module_root_glob}` + done.md + design-consensus.md + docs/workflow/{service-name} | `.task/{子需求名}/review/{模块名}-{任务序号}.md`（编号清单 + 严重度 + 文件:行 + 建议改法 + 裁决:PENDING） | **绝不允许直接改代码**                                      |
| ④ 人工裁决                       | CR_SCANNED → PENDING_CR_REVIEW                 | 人工                                  | 报告『人工裁决』区                                                                                                | 报告『人工裁决』区填 ACCEPTED / REJECTED / MODIFIED                                                       | 全部 PENDING 必须变更为三选一                               |
| 锁定裁决 + CR_CONFIRMED          | PENDING_CR_REVIEW → CR_CONFIRMED               | `/devops-workflow approve {子需求ID}` | —                                                                                                                 | `metadata.md` 任务状态置 CR_CONFIRMED                                                                     | —                                                           |
| ⑤ 改写（仅 ACCEPTED / MODIFIED） | CR_CONFIRMED → REWRITING                       | `executor`                            | 已确认问题清单 + 当前代码                                                                                         | `{module_root_glob}/`                                                                                     | REJECTED 项禁止改动                                         |
| ⑥ 复验 + 进度回写                | REWRITING → VERIFYING → DONE                   | 主 Agent                              | —                                                                                                                 | `metadata.md` 任务状态行 + `dev-tasks.md` 子项 `[ ]→[x]`                                                  | `{test_cmd}` 绿 + `{lint_cmd}` 通过 + 已采纳问题修复        |

**★ 子 agent 返回后四步协议（必须立刻执行，禁止静默结束本轮）**：

1. **读产出**：读取子 agent 写出的产出文件（以文件为准，不以子 agent 返回文本为准）
2. **回写状态**：更新 metadata.md 任务状态行（`PLANNING` / `CODING` / `CR_SCANNED` / `CR_CONFIRMED` / `REWRITING` / `VERIFYING` / `DONE`）
3. **向用户输出结果摘要**：简述产出内容（编码改了什么 / CR 扫出几条 / plan 要点等）
4. **明确告知下一步**：该 `approve` 还是 `next`，或主 Agent 将自动执行什么

### 2.5 阶段 5：收尾验收（`next` → REVIEWING）

| 动作             | 读取                                                           | 写入                                                     | 校验                                                       |
| ---------------- | -------------------------------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------- |
| 启动 `verifier`  | `metadata.md` + `dev-tasks.md`                                 | —                                                        | 全部勾选；各任务审查均 PASSED                              |
| 全量回归         | `{test_cmd}`（全量）                                           | —                                                        | 全绿                                                       |
| 语法校验         | 改动文件                                                       | —                                                        | `{lint_cmd}` 全通过（`{static_analysis_cmd}` 默认不纳入）  |
| 跨模块一致性     | `design-consensus.md` + `docs/workflow/cross-module.md`        | —                                                        | {contract_type} 契约闭合                                   |
| 迁移检查         | `{module_root_glob}/*/resources/migrations/`（或项目约定路径） | —                                                        | 迁移与回滚可用                                             |
| 写验收报告       | —                                                              | `.task/{子需求名}/acceptance.md`                         | —                                                          |
| 更新 metadata.md | acceptance.md                                                  | `currentState=REVIEWING → COMPLETED`（或不通过标注问题） | —                                                          |
| 输出流程完成摘要 | —                                                              | 对话输出                                                 | 必须告知 `summary` 是用户主动触发，不在阶段 5 流程内自动跑 |

**异常分流**：

- 单任务实现问题 → 退回该子需求任务 executor，重走该任务 CR → 改写 → 复验
- 设计错 / 多任务受牵连 → `/devops-workflow rework {子需求ID}`（设计级，强门禁：version ∈ {DRAFT/IN_PROGRESS/READY}）

### 2.6 收尾：`/devops-workflow summary {版本号}`

| 动作                               | 读取                                                                                             | 写入                                                                                                                               | 校验                                   |
| ---------------------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| 启动 `document-specialist`（只读） | 版本号对应的所有 `metadata.md` + 关联 `design-consensus.md` / `dev-tasks.md` / `acceptance.md`   | 单域：`docs/discuss/{service-name}/{父需求名}/.task/.versions/{版本号}/change-manifest.md`；跨域：`docs/version/{版本号}/change-manifest.md` | version ∈ {IN_PROGRESS/READY/RELEASED} |
| 三大块汇总                         | 实际代码 `{module_root_glob}/*/resources/migrations/`、路由 / 控制器、`design-consensus.md` 契约 | 同上                                                                                                                               | DDL N 张表 / 队列 M 个 / API K 个      |
| 主 Agent 呈现结果                  | change-manifest.md                                                                               | 对话输出                                                                                                                           | 必须给用户三条数摘要 + 文件路径        |

**change-manifest.md 模板三块**：

1. DDL 变更（给 DBA）—— 直接可执行的 SQL
2. 新增队列（给运维）—— 仅 queue name 一行一个
3. API 接口清单（给前端）—— Method+Path / 入参 / 出参要点 / 用途

### 2.7 多版本合并：`/devops-workflow summary --merge {版本A} {版本B} ...`

| 动作                  | 读取                                                                              | 写入                                                  | 校验                                   |
| --------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------- | -------------------------------------- |
| 用户显式触发          | `docs/version/{V1}/change-manifest.md`、`docs/version/{V2}/change-manifest.md` 等 | `docs/version/.merged/change-manifest-{Y}-{M}-{D}.md` | 各版本必须全部 RELEASED                |
| 拼接三块              | 各版本 change-manifest                                                            | 同上                                                  | 每行带 `(来源: {版本号} / {子需求ID})` |
| 不重新读 dev-tasks.md | 直接合并已生成清单                                                                | —                                                     | 避免重复劳动                           |

> `--merge` 必须显式传，缺省不触发；缺参时报错 + 扫描已存在 change-manifest 列出可选版本。

### 2.8 返工：`/devops-workflow rework {子需求ID}`

| 步骤                          | 读取                                                          | 写入                                                                                                                  | 校验                                                                               |
| ----------------------------- | ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| 强门禁 — 版本状态校验         | `metadata.md.versionBinding` → `docs/version/{版本号}.status` | —                                                                                                                     | version ∈ {DRAFT/IN_PROGRESS/READY} 通过；RELEASED/ARCHIVED 报错                   |
| 子需求状态校验                | `metadata.md.currentState`                                    | —                                                                                                                     | 必须 == COMPLETED                                                                  |
| 确认缺陷描述 + 根因层级       | 当前进度 + 用户陈述                                           | `.task/{子需求名}/rework/R{N}-{YYYY-MM-DD}.md`                                                                        | 三层级：实现 / 设计 / 需求                                                         |
| 依赖扩散（自动算 + 人工确认） | `dev-tasks.md` 依赖图 + version.subRequirements[]             | —                                                                                                                     | 列下游受影响子需求给用户确认                                                       |
| 按层级回退                    | —                                                             | `design-consensus.md` 追加 `## 返工修订 R{N}：{原因}`（仅设计级）                                                     | —                                                                                  |
| 回写 metadata.md              | rework 单 + 依赖图                                            | 受影响子需求 → TODO（标返工轮次）+ `currentState=COMPLETED → ANALYZING` 或 `→ DISCUSSING`；未受影响的 DONE 子需求保留 | —                                                                                  |
| 重跑                          | —                                                             | —                                                                                                                     | 设计级：阶段 2→3→4（含 plan 重出）→5；实现级：阶段 4（重 code+CR）；需求级：阶段 1 |

### 2.9 发现失效：`/devops-workflow discovery refresh`

| 步骤                 | 读取                                                                  | 写入                          | 校验                                                                                                                |
| -------------------- | --------------------------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| 清空 §7 缓存         | 当前会话内存的 DiscoveryContext                                       | —                             | —                                                                                                                   |
| 重新执行 §1 全部发现 | manifest 文件（mtime）/ CLAUDE.md（mtime）/ `docs/workflow/`（mtime） | 更新会话内存 DiscoveryContext | 三段式错误格式不变                                                                                                  |
| 输出新发现结果       | —                                                                     | 对话输出                      | 列出 language / test_cmd / lint_cmd / static_analysis_cmd / module_root_glob / contract_type / discovery_cmd 7 字段 |

---

## 三、节点追踪表（所有节点的读 / 写 / 状态 / 主 Agent 收尾动作）

### 3.1 命令节点

| 节点                        | 触发命令                                                         | 读取                                           | 写入                                                                                      | 状态变迁              | 主 Agent 收尾动作            |
| --------------------------- | ---------------------------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------- | --------------------- | ---------------------------- |
| N1 创建父需求               | `/devops-workflow req create {service-name}/{父需求名}`                    | manifest 模块清单                              | `docs/discuss/{service-name}/{父需求名}/.task/parent.md`                                            | —                     | 提示下一步 `req split`       |
| N2 拆分子需求（向导）       | `/devops-workflow req split {service-name}/{父需求名}`                     | `.task/` 子目录                                | 子需求目录 + `metadata.md`（8 字段）                                                      | —                     | 提示下一步 `version create`  |
| N3 创建版本                 | `/devops-workflow version create {版本号}`                       | 全局 `metadata.md.versionBinding` 为空的子需求 | `docs/version/{版本号}` + 各 `metadata.md.versionBinding` 回填                            | version.status: DRAFT | 提示下一步 `version start`   |
| N4 增量加子需求（仅 DRAFT） | `/devops-workflow version add-sub {版本号} {子需求ID}`           | metadata.md.versionBinding / version.status    | 各 metadata.md + version.subRequirements[]                                                | version.status 不变   | 回显 subRequirements 总数    |
| N5 推进子需求下一阶段       | `/devops-workflow next {子需求ID}`                               | `metadata.md` + 各阶段产物                     | 各阶段产物 + `metadata.md.currentStage/currentState`                                      | 详见 §3.2             | 按 §1.2 流水线推进           |
| N6 确认人工门               | `/devops-workflow approve {子需求ID}`                            | 当前状态                                       | `design-consensus.md` / `plan.md` / 任务状态 / `metadata.md`                              | 视门类                | 详见 §3.3                    |
| N7 查看子需求或版本状态     | `/devops-workflow status [子需求ID\|版本号]`                     | metadata.md 或 version 文件                    | —                                                                                         | —                     | 输出进度展示；缺参时扫描全部 |
| N8 列父需求                 | `/devops-workflow req list`                                      | 所有 `.task/parent.md`                         | —                                                                                         | —                     | 输出清单 + 子需求数          |
| N9 列版本                   | `/devops-workflow version list`                                  | 所有版本文件                                   | —                                                                                         | —                     | 输出清单                     |
| N10 推进版本状态            | `/devops-workflow version start\|ready\|close\|archive {版本号}` | version.status + 子需求聚合                    | version.status + stageRecord                                                              | 见 §1.4 版本状态机    | 回显新状态                   |
| N11 返工                    | `/devops-workflow rework {子需求ID}`                             | 缺陷描述 + 依赖图 + version.status             | `.task/{子需求名}/rework/R{N}-{日期}.md` + `design-consensus.md`（设计级）+ `metadata.md` | 按层级回退            | 列出受影响子需求等用户确认   |
| N12 出交付清单              | `/devops-workflow summary {版本号}`                              | 版本的子需求产物 + 实际代码                    | 单域 / 跨域 change-manifest.md                                                            | —                     | 输出 DDL N / 队列 M / API K  |
| N13 多版本合并清单          | `/devops-workflow summary --merge {V1} {V2} ...`                 | 各版本 `change-manifest.md`                    | `docs/version/.merged/change-manifest-{Y}-{M}-{D}.md`                                     | —                     | 输出合并清单                 |
| N14 发现刷新                | `/devops-workflow discovery refresh`                             | manifest / CLAUDE.md / 架构文档                | 会话内存 DiscoveryContext                                                                 | —                     | 输出新发现字段               |

### 3.2 阶段推进节点（`next` 命令内部）

| 节点        | 前置状态                       | 启动的 agent                     | 读取                                      | 写入                                                                     | 后置状态                            |
| ----------- | ------------------------------ | -------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------ | ----------------------------------- |
| S2 模块分析 | ANALYZING                      | `team {N}:analyst`（并行按模块） | 父需求讨论文档 + 架构文档 + 代码          | `.task/{子需求名}/analysis/{模块名}.md`                                  | —                                   |
| S2 汇总设计 | （分析完成后自动）             | `ralph`                          | 全部 analysis + 讨论 + cross-module.md    | `.task/{子需求名}/design-consensus.md` + `.task/{子需求名}/dev-tasks.md` | PENDING_DESIGN_REVIEW（或 BLOCKED） |
| S4 编码并行 | DEVELOPING + 至少 2 任务无依赖 | `team {N}:executor`              | design-consensus 或已确认 plan            | `{module_root_glob}` 代码 + 单测 + `.task/{子需求名}/done/{模块名}.md`   | CODING → VERIFYING 待 CR            |
| S4 编码串行 | DEVELOPING                     | 单个 `executor`                  | 同上                                      | 同上                                                                     | 同上                                |
| S4 CR 扫描  | CODING                         | 单 `code-reviewer`               | diff + done + design-consensus + 架构文档 | `.task/{子需求名}/review/{service-name}-{序号}.md`                       | CR_SCANNED → PENDING_CR_REVIEW      |
| S5 验收     | REVIEWING                      | `verifier`                       | 全量                                      | `.task/{子需求名}/acceptance.md`                                         | COMPLETED 或带问题回退              |

### 3.3 人工门节点（`approve` 命令内部）

| 门节点       | 前置状态              | 校验项                                              | 通过后动作                                         | 后置状态            |
| ------------ | --------------------- | --------------------------------------------------- | -------------------------------------------------- | ------------------- |
| G1 设计审核  | PENDING_DESIGN_REVIEW | 必含 6 项清单                                       | `design-consensus.md` 追加 `## 设计确认: APPROVED` | DEVELOPING          |
| G2 任务 plan | PENDING_PLAN_REVIEW   | plan 必含 6 项（签名/数据模型/时序/边界/测试/迁移） | plan.md 追加 `## 设计确认: APPROVED`               | 任务 PLAN_CONFIRMED |
| G3 CR 裁决   | PENDING_CR_REVIEW     | 每条问题已填 ACCEPTED/REJECTED/MODIFIED             | 任务 CR_CONFIRMED；走改写⑤+复验⑥                   | DONE                |

### 3.4 任务级状态机（每个 dev-task 项独立）

```
TODO ──→ [复杂] ──→ PLANNING ──→ PENDING_PLAN_REVIEW ──→ PLAN_CONFIRMED ──→ CODING
                  [简单] ──────────────────────────────────────────────→ CODING
                                                                              │
                                                                              ▼
CODING ──→ CR_SCANNED ──→ PENDING_CR_REVIEW ──→ CR_CONFIRMED ──→ REWRITING ──→ VERIFYING ──→ DONE
                                                              ↘ 零问题/全部 REJECTED → 跳过改写直接复验
```

---

## 四、上下文发现层（取代 v1 「活动上下文」段）

### 4.1 v2 没有活动指针

**v2 没有 `docs/discuss/.workflow-active`，也没有 `use` 命令。**每次命令必须显式传子需求 ID 或版本号（AC16/D19）。状态源是 `metadata.md`，不依赖任何粘性文件。`next/approve/status/rework/summary/discovery refresh` 缺参 → 立刻报错 + 扫描 `docs/discuss/` 与 `docs/version/` 列出可选项。

### 4.2 DiscoveryContext 由什么构成

会话内有效的是"发现上下文"——由 `references/discovery.md` §1 描述的运行时发现机制维护，**只缓存于主 Agent 内存，不落盘**：

| 字段                                            | 来源（优先级 1 → 3）                                         | 失效触发（自动）                |
| ----------------------------------------------- | ------------------------------------------------------------ | ------------------------------- |
| `language`                                      | CLAUDE.md → manifest#engines → docs/workflow 命名            | manifest / CLAUDE.md mtime 变更 |
| `test_cmd` / `lint_cmd` / `static_analysis_cmd` | CLAUDE.md → manifest scripts                                 | 同上                            |
| `module_root_glob`                              | CLAUDE.md → manifest workspaces → docs/workflow 命名         | 同上 + 新增模块                 |
| `contract_type`                                 | `docs/workflow/{module}/contracts.md` → CLAUDE.md → manifest | `docs/workflow/` mtime 变更     |
| `discovery_cmd`                                 | CLAUDE.md → manifest 推断                                    | 同上                            |

### 4.3 强制刷新时机（命令触发）

调用 `/devops-workflow discovery refresh` 的典型场景：

- 用户新增模块后需要刷新 `module_root_glob` 匹配
- 用户修改 `CLAUDE.md` 后希望立即生效
- `docs/workflow/` 重新生成后需要重新发现契约
- 缓存出现字段冲突 / missing 错误后人工排查

### 4.4 哪些命令依赖显式 ID

v2 全部命令（除 `req list` / `version list` 这种"扫描全部"类命令外）都强制要求：

- 传子需求 ID：格式 `{service-name}/{父需求名}#{子需求名}`，按最后一个 `#` 拆分
- 传版本号：任意非空字符串（不做 SemVer 校验）

切换子需求 / 版本时不需要任何中间指针，直接新一次命令传新 ID。

---

## 五、产出物目录结构

```
docs/
├── discuss/                                  # 子需求树（按 域/父需求/子需求 组织，扁平）
│   └── {service-name}/{父需求名}/
│       ├── {父需求名}.md                      # 阶段 1 父需求讨论文档
│       └── .task/
│           ├── parent.md                      # 父需求摘要（req create 创建）
│           └── {子需求名}/                    # 子需求目录（req split 向导逐个创建）
│               ├── metadata.md                # ★唯一状态源（8 字段）
│               ├── discussion.md              # 阶段 1 子需求讨论文档
│               ├── analysis/                  # 阶段 2 分析产物
│               ├── design.md                  # 阶段 2 设计文档初稿（可选）
│               ├── design-consensus.md        # 阶段 2 ralph 汇总 + 阶段 3 追加 ## 设计确认: APPROVED
│               ├── dev-tasks.md               # 阶段 2 任务拆分（标注 简单|复杂）
│               ├── plans/                     # 阶段 4 复杂任务 LLD
│               ├── done/                      # 阶段 4 已完成任务归档
│               ├── review/                    # 阶段 4 CR 记录
│               ├── acceptance.md              # 阶段 5 验收报告
│               ├── rework/                    # 返工单（R{N}-{根因}.md）
│               └── .versions/                 # 单域版本的 change-manifest.md（summary 触发）
│                   └── {版本号}/
│                       └── change-manifest.md
└── version/                                  # 版本聚合（全局，跨父需求/跨域）
    ├── v1.0                                  # 无扩展名；9 字段；status ∈ {DRAFT/IN_PROGRESS/READY/RELEASED/ARCHIVED}
    ├── v1.0.change-manifest.md               # 仅跨域版本时存在
    └── .merged/                              # 多版本合并清单（--merge 触发）
        └── change-manifest-{Y}-{M}-{D}.md
```

> **v1 已删除（不存在的）路径**：`docs/discuss/.workflow-active`、`docs/discuss/{service-name}/{需求名}/.task/progress.md`、`docs/discuss/{service-name}/{需求名}/.task/milestones/{M}/`、`docs/discuss/{service-name}/{需求名}/.task/design-foundation.md`。

---

## 六、Agent 权限与职责矩阵

| 阶段                              | agent / skill                                | 权限   | 职责                                               |
| --------------------------------- | -------------------------------------------- | ------ | -------------------------------------------------- |
| 阶段 1 需求讨论                   | `dev-workflow req split` 交互式向导          | 读写   | 逐个创建子需求 metadata.md                         |
| 阶段 2 模块分析                   | `{discovery_cmd}` / `analyst`                | 只读   | 读代码 + 读架构文档 → 产出模块分析                 |
| 阶段 2 汇总设计                   | `ralph`                                      | 读写   | 汇总 analysis → design-consensus.md + dev-tasks.md |
| 阶段 4 任务详细设计（仅复杂任务） | `architect` / `planner`                      | 只读   | 出任务级 plan/LLD，不写业务代码                    |
| 阶段 4 编码                       | `executor`（并行 `team` / 串行单）           | 读写   | 对照 design-consensus.md 或已确认 plan 编码 + 单测 |
| 阶段 4 CR 扫描（逐任务）          | `code-reviewer`                              | 只读   | 只产问题清单，**绝不自动改代码**                   |
| 阶段 4 改写（逐任务）             | `executor`                                   | 读写   | 只改已采纳项                                       |
| 阶段 5 收尾验收                   | `verifier`                                   | 只读   | 全量回归 + 一致性把关                              |
| 阶段 5 交付清单                   | `document-specialist`                        | 只读   | 汇总 change-manifest.md                            |
| 阶段 4/5 返工                     | `team` / `analyst` / `executor` / `verifier` | 视场景 | 按根因层级回退重做                                 |

人工门：阶段 3 设计审核、阶段 4 plan 确认、阶段 4 CR 裁决（均为 `/devops-workflow approve {子需求ID}`）。

---

## 七、关键不变量（12 条铁律）

1. **子 agent 返回 ≠ 流程推进**：每次子 agent 返回后必须立刻：① 读取产出文件 → ② 回写 metadata.md → ③ 输出摘要 + 下一步指令。**绝不允许静默结束本轮**。
2. **CR 问题人工门**：code-reviewer 只产清单，**绝不直接改代码**；扫出问题必须经人工逐条裁决并 `approve` 后才由另一个 executor 改写。
3. **编码与审查分两轮**：编码 / CR / 改写各自独立 agent，CR 与编码不共享上下文，禁止自审。
4. **进度即时回写（阻塞）**：每次状态变化立刻写回 metadata.md `currentStage` / `currentState` / `updatedAt`，并同步 `dev-tasks.md` 子项 `[ ]→[x]`；**回写未完成不得推进下一个任务**。
5. **设计分两层**：design-consensus.md = 共识/契约层（阶段 3 清单式审核）；复杂任务级 plan/LLD = 实现细节（阶段 4 编码前出，人工 approve 后才编码）。
6. **未决项不许悬空**：design-consensus.md 的 `待确认/TODO` 必须登记成表并有处置方式。
7. **设计/需求层缺陷走 rework**，不要硬塞进 CR 改写：CR 改写只解决任务内小问题；牵动设计或多任务用 `/devops-workflow rework {子需求ID}`。
8. **子需求默认单个**：只有大需求才 `req split`；跨模块交互一律通过 `{contract_type}` 通道，禁止直接访问他模块实现细节。
9. **无活动指针**：所有命令必须显式传子需求 ID 或版本号；`next/approve/status/rework/summary/discovery refresh` 缺参 → 报错 + 列可选项。
10. **版本状态机 5 态**：DRAFT / IN_PROGRESS / READY / RELEASED / ARCHIVED；全手动转换，每个转换有严格前置校验。ARCHIVED 永久封存，禁止任何修改类命令；RELEASED 禁止 rework。
11. **metadata.md 单源**：子需求状态唯一权威源是 `docs/discuss/{service-name}/{父需求名}/.task/{子需求名}/metadata.md`；version 文件不缓存子需求状态，只存 `subRequirements` 列表 + 阶段记录。
12. **所有 agent prompt 必须含 Bash 静态分析约束**：禁止 `for` / `while` / `if` / `case` / here-doc / 嵌套 `$()`；产出物只落项目内 `.task/` 或 `docs/version/`，禁止写 home 或仓库外。

---

## 八、验收基线（强制）

| 项                     | 命令                                                                         | 通过标准                                                                    |
| ---------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| 单测                   | `{test_cmd} {module_root_glob}/{service-name}/tests`（或项目约定的单测路径） | 绿                                                                          |
| 语法                   | `{lint_cmd} <改动文件>`                                                      | 通过                                                                        |
| 全量回归（阶段 5）     | `{test_cmd}`（全量）                                                         | 绿                                                                          |
| 跨模块一致性（阶段 5） | 对照 design-consensus.md + `docs/workflow/cross-module.md`                   | {contract_type} 契约闭合                                                    |
| 迁移（阶段 5，若涉及） | `{module_root_glob}/*/resources/migrations/`（或项目约定路径）               | 迁移与回滚可用                                                              |
| {static_analysis_cmd}  | —                                                                            | **默认不纳入 DoD / 验收**（存量项目历史告警多）；项目有干净基线时再可选开启 |

> 命令模板里的 `{test_cmd}` / `{lint_cmd}` / `{static_analysis_cmd}` / `{module_root_glob}` 由 `references/discovery.md` 描述的发现机制从项目 manifest 文件 + CLAUDE.md 解析得到；项目侧未声明时按 `[字段 {X} {当前值}] {原因}。建议: {修复}` 三段式硬阻断，**不允许猜测默认值**。

---

## 九、命令速查（含最少必要参数）

| 命令                                 | 必带 / 可选               | 关键效果                                                   |
| ------------------------------------ | ------------------------- | ---------------------------------------------------------- |
| `/devops-workflow req create`        | `{service-name}/{父需求名}`         | 创建父需求 + parent.md                                     |
| `/devops-workflow req show`          | `{service-name}/{父需求名}`         | 显示父需求详情 + 子需求清单                                |
| `/devops-workflow req list`          | （无）                    | 列出所有父需求                                             |
| `/devops-workflow req split`         | `{service-name}/{父需求名}`         | 交互式向导逐个创建子需求                                   |
| `/devops-workflow version create`    | `{版本号}`                | 4 步交互式建版本（DRAFT + 扫描 + 多选 + 回写）             |
| `/devops-workflow version show`      | `{版本号}`                | 显示版本详情 + 子需求状态聚合                              |
| `/devops-workflow version list`      | （无）                    | 列出所有版本                                               |
| `/devops-workflow version add-sub`   | `{版本号} {子需求ID}`     | DRAFT 增量加子需求                                         |
| `/devops-workflow version start`     | `{版本号}`                | DRAFT → IN_PROGRESS                                        |
| `/devops-workflow version ready`     | `{版本号}`                | IN_PROGRESS → READY                                        |
| `/devops-workflow version close`     | `{版本号}`                | READY → RELEASED                                           |
| `/devops-workflow version archive`   | `{版本号}`                | RELEASED → ARCHIVED（永久封存）                            |
| `/devops-workflow next`              | `{子需求ID}`              | 推进子需求到下一阶段                                       |
| `/devops-workflow approve`           | `{子需求ID}`              | 按当前状态分发：设计审核 / plan / CR 裁决                  |
| `/devops-workflow status`            | `[子需求ID\|版本号]`      | 显示进度                                                   |
| `/devops-workflow rework`            | `{子需求ID}`              | 缺陷返工（需用户选根因层级）                               |
| `/devops-workflow summary`           | `{版本号}`                | 产出 change-manifest.md（DDL/Job·MQ/API）                  |
| `/devops-workflow summary --merge`   | `{版本号A} {版本号B} ...` | 多版本合并清单（→ .merged/change-manifest-{Y}-{M}-{D}.md） |
| `/devops-workflow discovery refresh` | （无）                    | 清空发现缓存，重新解析必需字段                             |

> **总命令数**：19 启用（4 req + 8 version + 7 保留）+ 3 删除（use / split / start，v1 已硬切换废弃）。

子需求 ID 格式：`{service-name}/{父需求名}#{子需求名}`（按最后一个 `#` 拆分；ID 中如含 `#`，取最后一个为子需求分隔）。

---

## 十、典型路径示例（端到端走查）

### 10.1 单子需求普通需求

```
/devops-workflow req create order/订单取消优化
  → 创建 docs/discuss/order/订单取消优化/.task/parent.md
  → 提示：下一步用 req split 创建子需求

/devops-workflow req split order/订单取消优化
  → 向导询问子需求名 > 描述 > 模块影响，逐个创建
  → 创建 docs/discuss/order/订单取消优化/.task/订单取消逻辑/metadata.md（8 字段）

/devops-workflow version create v1.0
  → 步骤1：建空 DRAFT docs/version/v1.0（9 字段）
  → 步骤2：扫描未绑定子需求
  → 步骤3：交互多选 → 选中 1 个
  → 步骤4：回写 metadata.md.versionBinding = "v1.0"

/devops-workflow version start v1.0
  → 校验 DRAFT + ≥1 子需求 + ≥1 子需求已推进
  → 版本状态：DRAFT → IN_PROGRESS

/devops-workflow next order/订单取消优化#订单取消逻辑
  → 阶段 2：analyst 逐模块分析 → ralph 汇总 design-consensus.md + dev-tasks.md
  → 停在 PENDING_DESIGN_REVIEW，给出设计审核清单自查结论

/devops-workflow approve order/订单取消优化#订单取消逻辑
  → design-consensus.md 标 APPROVED → DEVELOPING

/devops-workflow next order/订单取消优化#订单取消逻辑
  → 任务1（简单）：编码 → DoD → CR 扫描 → 停在 PENDING_CR_REVIEW，呈现问题清单

# 用户裁决：#1 ACCEPTED、#2 REJECTED、#3 MODIFIED
/devops-workflow approve order/订单取消优化#订单取消逻辑
  → 改写 #1/#3 → 复验绿 → 任务1 置 DONE → 回写 metadata.md + dev-tasks.md

/devops-workflow next order/订单取消优化#订单取消逻辑       # 推进任务2... 直到全部 DONE

/devops-workflow next order/订单取消优化#订单取消逻辑       # 阶段 5：verifier 全量 {test_cmd} + {lint_cmd} + 跨模块一致性
  → 通过 → COMPLETED

/devops-workflow version ready v1.0        # 所有子需求 COMPLETED 后推进版本
/devops-workflow version close v1.0        # 二次确认 → RELEASED
/devops-workflow summary v1.0              # 产出 change-manifest.md（DDL/Job·MQ/API）
```

### 10.2 多子需求跨域 + 复杂任务 plan 门

```
/devops-workflow req create order/订单取消优化
/devops-workflow req create payment/支付渠道重构
  → 各创建 docs/discuss/{order,payment}/{需求名}/.task/parent.md

/devops-workflow req split order/订单取消优化        # 创建订单取消逻辑
/devops-workflow req split payment/支付渠道重构      # 创建 alipay、wechat

/devops-workflow version create v1.0
  → 扫描跨父需求子需求：order/...#订单取消逻辑 + payment/...#alipay + payment/...#wechat
  → 交互多选：> 1,2
  → 跨域版本，回写两个子需求 metadata.md.versionBinding = "v1.0"
  → summary 落地默认走 docs/version/v1.0.change-manifest.md（跨域路径）

# 两个子需求并行推进阶段 2-5（互不依赖、目录不重叠时由 Claude 判断可并行）
/devops-workflow next order/订单取消优化#订单取消逻辑
/devops-workflow approve order/订单取消优化#订单取消逻辑
/devops-workflow next order/订单取消优化#订单取消逻辑
# ... 该子需求某任务被判为【复杂】 → architect 出 plan → PENDING_PLAN_REVIEW
/devops-workflow approve order/订单取消优化#订单取消逻辑   # plan 确认 → 编码 → CR ...
```

### 10.3 收尾发现设计错 → rework

```
# 阶段 5 验收发现 design-consensus.md 方案有缺陷
/devops-workflow rework order/订单取消优化#订单取消逻辑
  → 强门禁：version v1.0 ∈ {DRAFT/IN_PROGRESS/READY} → 通过；RELEASED/ARCHIVED 直接拒绝
  → 子需求状态校验：currentState == COMPLETED
  → 确认根因 = 设计级
  → design-consensus.md 末尾追加 "## 返工修订 R1：{原因}"
  → 子需求退回阶段 2（currentState → ANALYZING）
  → 自动算出下游受影响子需求（在 version.subRequirements[] 范围内），列给用户确认
  → 确认后这些子需求 → TODO（标 返工R1），未受影响的 DONE 保留
  → metadata.md 追加返工记录 R1

/devops-workflow next order/订单取消优化#订单取消逻辑    # 阶段 2 修订 design-consensus.md
/devops-workflow approve order/订单取消优化#订单取消逻辑 # 阶段 3 重审通过
/devops-workflow next order/订单取消优化#订单取消逻辑    # 复杂任务重出 plan → 重 code → 重 CR
```

### 10.4 发现失效强制刷新

```
# 修改了 CLAUDE.md 后想立刻生效
/devops-workflow discovery refresh
  → 清空会话内 DiscoveryContext 缓存
  → 重新从 manifest + CLAUDE.md + docs/workflow/ 解析
  → 输出新字段：language / test_cmd / lint_cmd / static_analysis_cmd / module_root_glob / contract_type / discovery_cmd
```

### 10.5 多版本合并清单（用户主动触发）

```
# v1.0 + v1.1 + v1.2 全部 RELEASED 后
/devops-workflow summary --merge v1.0 v1.1 v1.2
  → 读三个版本的 change-manifest.md，拼成一份合并清单
  → 落地：docs/version/.merged/change-manifest-{Y}-{M}-{D}.md
  → 每行带 (来源: {版本号} / {子需求ID}) 标注
```

---

## 十一、QA 自检清单（排查用）

按以下清单逐项核对，可以定位 90% 的卡死 / 卡门问题：

### 11.1 卡在 PENDING_DESIGN_REVIEW

- [ ] 是否调用 `/devops-workflow approve {子需求ID}`（而非 `next`）
- [ ] design-consensus.md 必含 6 项是否齐全（对外契约 / 模块边界 / 决策+理由 / 验收标准 / 未决项 / 简单任务实现要点）
- [ ] 是否有 `.task/{子需求名}/conflicts.md`（冲突未解决 → BLOCKED）

### 11.2 卡在 PENDING_PLAN_REVIEW

- [ ] 该任务是否在 dev-tasks.md 标为 `复杂`
- [ ] plan.md 是否含 6 项（签名 / 数据模型 / 时序 / 边界 / 测试用例 / 迁移）
- [ ] plan.md 末尾是否有 `## 设计确认: APPROVED`

### 11.3 卡在 PENDING_CR_REVIEW

- [ ] 是否仍有问题标注为 `PENDING`（必须三选一）
- [ ] 子 agent 返回后主 Agent 是否输出了 `/devops-workflow approve` 提示字符串（漏了说明漏了第 3 步）
- [ ] 是否区分了"零问题 PASSED"（直接 approve 走复验）和"有问题"（必须先裁决）

### 11.4 子 agent 跑完没动静

- [ ] 主 Agent 是否按"四步协议"操作：① 读产出 → ② 回写 metadata.md → ③ 输出摘要 → ④ 明确下一步
- [ ] 是否读了**文件**（而非子 agent 返回文本）
- [ ] 是否漏改 metadata.md 任务状态行（`PLANNING` / `CODING` / `CR_SCANNED` / `CR_CONFIRMED` / `REWRITING` / `VERIFYING` / `DONE`）
- [ ] 是否漏改 dev-tasks.md 子项 `[ ]→[x]`
- [ ] （跨域版本时）是否漏改 docs/version/{版本号} 的 stageRecord

### 11.5 编码 / 改写没限制

- [ ] 是否注入了 `Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()`
- [ ] 并行 executor 是否限定了模块目录（`{module_root_glob}/{service-name}/`）
- [ ] 改写 executor 是否明确"只处理 ACCEPTED / MODIFIED 的问题，REJECTED 不动"
- [ ] 是否禁止写入 home 或仓库外的路径

### 11.6 返工用错通道

- [ ] 只改当前子需求任务能解决 → 用 CR 改写
- [ ] 牵动设计或别的子需求 → 用 `/devops-workflow rework {子需求ID}`
- [ ] rework 是否选择了正确层级：实现 / 设计 / 需求
- [ ] 受影响子需求是否包含"依赖被改设计的下游"（自动算 + 人工确认）
- [ ] 未受影响的 DONE 子需求是否保留

### 11.7 版本状态门禁拦截

- [ ] version.status = RELEASED 时，rework / 子需求推进 / version 修改类命令 立即报错「版本已发布」
- [ ] version.status = ARCHIVED 时，所有修改类命令拒绝
- [ ] version.start 是否校验 ≥1 子需求 + ≥1 子需求已推进
- [ ] version.ready 是否校验所有子需求 currentState == COMPLETED
- [ ] version.add-sub 是否在 DRAFT 状态才允许

### 11.8 中断恢复

- [ ] metadata.md 当前阶段 / 状态记录是否最新
- [ ] dev-tasks.md 子项是否与 metadata.md 一致
- [ ] 下次 `/devops-workflow next {子需求ID}` 是否从该阶段继续
- [ ] 跨子需求并行推进时各 metadata.md 状态相互独立

### 11.9 上下文缺失 / 冲突（dev-workflow 特有）

- [ ] 项目根是否有 manifest 文件（缺失 → `[字段 manifest {当前值}] 缺失/未声明` 硬阻断）
- [ ] `CLAUDE.md` 是否声明跨模块调用通道（缺失 → `[字段 contract_type {当前值}] 未声明` 硬阻断）
- [ ] manifest 文件与 CLAUDE.md 在同一字段上是否冲突（冲突 → `[字段 {X} {当前值}] {原因}。建议: {修复}` 硬阻断）
- [ ] 是否出现歧义（如多份 manifest 无 tie-breaker / `engines.node` 与 `engines.deno` 冲突 / `pnpm-workspace.yaml` 与 `package.json#workspaces` 冲突）—— 全部走 §11.9 错误格式硬阻断
- [ ] 何时调 `/devops-workflow discovery refresh`：CLAUDE.md 改了、新增模块、架构文档重新生成、字段冲突错误后

---

## 十二、错误格式约定（三段式）

dev-workflow 的所有错误 / 阻断消息一律采用三段式：

```
[字段 {X} {当前值}] {原因}。建议: {修复}
```

- **字段**：定位失败的对象名（manifest / contract_type / versionStatus / subReqId / currentState / ...）
- **当前值**：该字段的当前取值；如缺失可写 `缺失/未声明`
- **原因**：人类可读的失败描述
- **建议**：可执行的修复建议（指向具体文件 / 命令）

示例：

```
[字段 manifest 缺失/未声明] 项目根未发现任何 manifest 文件。原因: dev-workflow 需从 manifest 文件推断 {test_cmd}/{lint_cmd}/模块布局。建议: 在仓库根新增一份 manifest 文件（Node: package.json / Go: go.mod / Java: pom.xml / Rust: Cargo.toml / Python: pyproject.toml），并保证其声明测试命令与模块根。

[字段 contract_type 缺失/未声明] CLAUDE.md 中未发现跨模块调用段。原因: dev-workflow 必须从 CLAUDE.md 读取跨模块调用类型（rpc/event/queue/http/grpc/kafka/...）。建议: 在 CLAUDE.md 中新增跨模块调用段，注明类型: {rpc|event|queue|http|grpc|kafka|...}。

[字段 versionStatus RELEASED] 版本已发布，禁止 rework。原因: RELEASED/ARCHIVED 状态下不允许 rework，需走新版本重做。建议: 如需修复请新建子需求并 /devops-workflow version add-sub 加入新版本。

[字段 language {node}] manifest 与 CLAUDE.md 冲突。原因: 两份声明的主语言不一致。建议: 删除冗余 manifest，或在 CLAUDE.md 中显式声明 ## 主语言。
```

CI 中由 `.ci/check-error-format.sh` 用正则 `\[字段 .*?\] .+?。建议: .+` 静态校验所有错误字符串，确保无漂移。

---

## 十三、参考索引（速查对应文件）

| 你要做                                                              | 先读                           |
| ------------------------------------------------------------------- | ------------------------------ |
| 了解上下文发现机制（manifest 文件 + CLAUDE.md → DiscoveryContext）  | `references/discovery.md`      |
| 写/更新 metadata.md、初始化任务目录、查状态枚举                     | `references/templates.md`      |
| 执行任意 `/devops-workflow` 子命令的详细逻辑                        | `references/commands.md`       |
| 执行**阶段 2** 分析与设计                                           | `references/stage-2-design.md` |
| 执行**阶段 3** 设计审核清单门                                       | `references/stage-3-review.md` |
| 执行**阶段 4** 开发（复杂度/并行 + plan/编码/CR/改写 全部 prompts） | `references/stage-4-dev.md`    |
| 执行**阶段 5** 收尾验收 + 异常处理（BLOCKED / 回退 / 恢复）         | `references/stage-5-accept.md` |
| 执行 `/devops-workflow rework` 返工                                 | `references/rework.md`         |
| 执行 `/devops-workflow summary` 产出交付清单                        | `references/summary.md`        |
| 总览、设计理念、命令速查、使用示例                                  | `README.md`                    |
| 路由器 + 常驻安全规则                                               | `SKILL.md`                     |

> **执行某阶段/命令前必须先读对应 reference 文件**再行动——尤其阶段 4，prompts 和人工门的精确措辞都在 `stage-4-dev.md`，凭记忆执行易漏步、易卡死。

---

## 十四、源文件定义冲突清单（调研日期 2026-07-07）

> 本附录列出 `/devops-workflow/` 全部源文件与本文档的**冲突点**。冲突来源可能是文档陈旧、迁移期内的中间状态、或源文件本身的内部不一致。**按用户要求：本文档不修改既有章节内容，仅追加新发现的冲突**，修复待用户决策。

### 冲突 C1【严重度：中】 — 总命令数计算口径不一致（17 vs 19）

| 来源                             | 总数公式                                | 保留推进命令清单                                                                      |
| -------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------- |
| **MIGRATION.md §Migration path** | `4 req + 8 version + 5 保留 = 17`       | `next/approve/status/rework/summary`（漏算 `summary --merge` 与 `discovery refresh`） |
| **SKILL.md §命令速查**           | `4 req + 8 version + 7 保留 = 19`       | `next/approve/status/rework/summary/summary --merge/discovery refresh`                |
| **README.md §命令速查**          | `19 启用（4 req + 8 version + 7 保留）` | 同 SKILL.md                                                                           |
| **commands.md §F 计数修正**      | `4 + 8 + 7 = 19 个（AC3 修订）`         | 同 SKILL.md                                                                           |
| **本文档 §九、命令速查**         | `19 启用 + 3 删除`                      | ✓ 与 SKILL/README/commands 一致                                                       |

**冲突点**：MIGRATION.md 把保留推进命令数算成 5 个，与 SKILL.md 一致认定的 7 个保留、19 启用**不符**。

**判定**：MIGRATION.md 写在通用化重构早期（`summary --merge` 与 `discovery refresh` 还未划入「保留」族的命名空间），其「17 = 4 + 8 + 5」是**迁移时基线**；SKILL.md / README.md / commands.md 三者一致认定的 `19 = 4 + 8 + 7` 是**当前事实**。本文档 §九与现行事实一致。

**修复方向**：MIGRATION.md 加注「迁移时基线 17；当前启用 19；保留命令清单见 SKILL.md」。

---

### 冲突 C2【严重度：高】 — 架构文档路径 `docs/workflow/` vs `docs/workflow/`（重大冲突）

| 来源                                                    | 路径写法                                                                                          |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **本文档**（§四、§九、§十、§十一等 6 处以上）           | `docs/workflow/{模块名}/{overview,business,contracts,flows}.md` + `docs/workflow/cross-module.md` |
| **SKILL.md §项目约定**                                  | `docs/workflow/{模块名}/`                                                                         |
| **README.md §依赖与约定 + §产出物目录**                 | `docs/workflow/{模块名}/`                                                                         |
| **references/discovery.md**（§1/§5/§6/§7/§10 共 11 段） | `docs/workflow/{service-name}/`                                                                   |
| **references/templates.md §4 目录约定**                 | `docs/workflow/{模块名}/`                                                                         |
| **references/stage-2-design.md**（analyst prompt）      | `docs/workflow/{模块名}/`                                                                         |
| **references/stage-3-review.md**                        | （通过 `## 主语言` 引出，不直接出现路径）                                                         |
| **references/stage-4-dev.md**（CR 与 architect prompt） | `docs/workflow/{模块名}/`                                                                         |
| **references/stage-5-accept.md**（verifier prompt）     | `docs/workflow/cross-module.md`                                                                   |
| **references/summary.md §2.3**                          | `docs/workflow/cross-module.md`                                                                   |

**冲突点**：本文档大量出现 `docs/workflow/{service-name}/`，所有 6 份源文件（含 references 全部子文件）一致使用 `docs/workflow/{service-name}/`。

**判定**：**6 份源文件一致认定 `docs/workflow/` 是唯一正确路径**。本文档出现的 `docs/workflow/{模块名}/overview.md` 等引用都应改为 `docs/workflow/{模块名}/overview.md`。

**修复方向**：全文替换 `docs/workflow/` → `docs/workflow/`（涉及 §四、§九、§十节核心示例、§十一节错误格式示例、§五产出物目录图等共 6+ 处）。

---

### 冲突 C3【严重度：中】 — `summary` 输出路径：`docs/version/{V}.md` vs `docs/version/{V}/...md`（源文件内部冲突）

| 来源                                                            | 单域版本路径                                                               | 跨域版本路径                                                                |
| --------------------------------------------------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **references/summary.md §4 / §5（document-specialist prompt）** | `docs/discuss/{service-name}/{父需求名}/.task/.versions/{版本号}/change-manifest.md` | `docs/version/{版本号}/change-manifest.md`（子目录 + `change-manifest.md`） |
| **references/commands.md §C summary**                           | 同 summary.md                                                              | 同 summary.md（`/` 风格）                                                   |
| **references/commands.md §C summary --merge step 2**（读 side） | —                                                                          | `docs/version/{V1}.change-manifest.md`（**点风格，与 summary.md 矛盾**）    |
| **本文档 §2.6 / §2.7**                                          | 同 summary.md（`/` 风格）                                                  | `docs/version/{版本号}/change-manifest.md` ✓ 与 summary.md 一致             |

**冲突点**：commands.md §C summary --merge 的**读侧**用 `docs/version/{V}.change-manifest.md`（点风格），与 summary.md / commands.md §C summary 的**写侧**用 `docs/version/{V}/change-manifest.md`（斜杠风格）**内部冲突**。本文档 §2.6/§2.7 采用 `/` 风格，与 summary.md 写侧一致。

**判定**：commands.md 的「点风格」读侧与 summary.md 的「斜杠风格」写侧不自洽——`version create` 写完后再用 `summary --merge` 读，会两边都找不到文件。**本文档采用的 `/` 风格在写侧代表当前事实**，但读侧确实需要修复。

**修复方向**：
- 推荐接受 `/` 风格（隔离子目录），同步 commands.md §C summary --merge step 2 把 `docs/version/{V}.change-manifest.md` 改为 `docs/version/{V}/change-manifest.md`。
- 或采用点风格 + 调整 summary.md §4 跨域路径为 `docs/version/{V}.change-manifest.md`（避免与版本文件 `docs/version/{V}` 在同一目录命名混淆）。

---

### 冲突 C4【严重度：中】 — PENDING_CR_REVIEW 零问题处理（本文档 §11.3 漏列）

**来源约束**：
- **SKILL.md 不变量 1-2**：「零问题（PASSED）也要输出'无需裁决，执行 approve'，不许静默卡住」
- **stage-4-dev.md §★ CR 子 agent 返回后**：「零问题（PASSED）也要输出'无需裁决，执行 approve'」「自检：如果你的输出中没有包含 `/devops-workflow approve` 这个字符串，说明你漏了第 3 步，立刻补上」

**本文档**：
- §1.4 任务级状态机与 §3.4 / §11.3 列出了 CR 门「逐条裁决」流程
- **未单独点出「零问题也要输出 approve 提示字符串」**

**判定**：源文件新增了「零问题不许静默」的反卡死规则；本文档 §11.3 列了「子 agent 跑完没动静」排查清单，但未点出零问题情形。

**修复方向**：§11.3 PENDING_CR_REVIEW 自检清单补一项「零问题 → 也要输出'执行 /devops-workflow approve'，不许静默」。

---

### 冲突 C5【严重度：低】 — DRAFT + 子需求 COMPLETED 异常态（本文档 §11.7 未列）

**来源约束**：
- **commands.md §C rework 边界情况**：「版本 DRAFT 状态下子需求 COMPLETED：理论上不应存在（DRAFT 阶段子需求应未启动），若出现则报错提示用户检查 metadata.md」
- **references/rework.md 步骤 4**：「DRAFT 状态下子需求 COMPLETED 是异常态（如出现，按"理论不应存在"报错，提示检查 metadata.md）」

**本文档**：
- §2.8 / §11.7 版本状态门禁拦截检查表只列了 RELEASED / ARCHIVED 拦截
- **未提 DRAFT + COMPLETED 异常态的拦截行为**

**判定**：源文件增加了 corner case 拦截，本文档未跟进。

**修复方向**：§11.7 版本状态门禁拦截加一项「DRAFT + 子需求 COMPLETED → 视为异常态，提示检查 metadata.md」。

---

### 冲突 C6【严重度：低】 — 静态分析约束重复注入（结构性问题，不冲突）

**来源**：
- SKILL.md 不变量 12、stage-2-design.md §步骤 2、stage-4-dev.md（多 prompt 段）、stage-5-accept.md §verifier、summary.md §5 document-specialist prompt —— 全部重复同一约束「所有 Bash 命令必须可静态分析，禁止 for/while/if/case/here-doc/嵌套 `$(...)`」

**本文档 §七、不变量 12**：与源文件一致 ✓

**判定**：不构成冲突，仅结构性问题——该约束已在 5+ prompt 段复制，建议引入「Bash 静态分析公共 snippet」减少重复。

---

### 冲突 C7【不构成冲突】 — `req split` 向导重名检查提法

- **SKILL.md**：「重名检查」✓
- **commands.md §A req split 步骤 3**：「扫描现有子需求，列出……用于向导重名检查」✓
- **本文档 §2.1**：「列出已存在子需求（用于重名检查）」✓

全部一致，**不构成冲突**。

---

### 冲突 C8【不构成冲突】 — Dev-tasks.md 内容被 stage-4-dev.md 替换

- **SKILL.md**：「dev-tasks.md 子项 `[ ]→[x]`」
- **stage-4-dev.md §① 编码 prompt**：「把本任务在 dev-tasks.md 中已完成的子项 [ ] 勾成 [x]」
- **stage-4-dev.md §⑥ 复验**：dev-tasks.md 子项 `[ ]` 勾成 `[x]`
- **本文档 §1.2 / §3.2**：「dev-tasks.md 子项 [ ]→[x]」✓

全部一致，**不构成冲突**。仅命名约定（`dev-tasks.md` 中的 `.task/`）位置约定与 `metadata.md` 同级在 §1.4 中已有说明。

---

### 冲突汇总表

| ID     | 严重度 | 冲突点                                            | 涉及源文件                              | 涉及本文档                      | 主要判定                      |
| ------ | ------ | ------------------------------------------------- | --------------------------------------- | ------------------------------- | ----------------------------- |
| **C2** | **高** | **架构路径 `docs/workflow/` vs `docs/workflow/`** | **全部 6 份源文件**                     | **§四、§九、§十、§十一 6+ 处**  | **源文件一致 → 改本文档**     |
| C1     | 中     | 总命令数 17 vs 19                                 | MIGRATION.md vs SKILL/README/commands   | §九（已正确）                   | 源文件多数 → 改 MIGRATION.md  |
| C3     | 中     | `change-manifest.md` 路径 `/` vs `.`              | commands.md vs summary.md（源内部冲突） | §2.6/§2.7（与 summary.md 一致） | 源内部冲突 → 择一并同步两侧   |
| C4     | 中     | 零问题也要输出 approve                            | stage-4-dev.md / SKILL.md               | §11.3 漏列                      | 源文件新增规则 → 补本文档     |
| C5     | 低     | DRAFT+COMPLETED 异常态拦截                        | commands.md / rework.md                 | §11.7 漏列                      | 源文件 corner case → 补本文档 |
| C6     | 低     | 静态分析约束重复（结构）                          | 5+ 源文件 prompt 段                     | §七一致                         | 不构成冲突，纯重构            |
| C7     | —      | `req split` 重名检查提法                          | 全源文件一致                            | §2.1 一致                       | ✓ 不冲突                      |
| C8     | —      | dev-tasks.md 勾选约定                             | 全源文件一致                            | §1.2/§3.2 一致                  | ✓ 不冲突                      |

---

### 调研基础 & 方法

- **基线**：`DEV-WORKFLOW-QA.md`（2026-07-07 13 版，771 行快照）
- **扫描源**：`/devops-workflow/` 全部 12 个文件（SKILL.md / README.md / MIGRATION.md + references/{commands, discovery, templates, stage-2-design, stage-3-review, stage-4-dev, stage-5-accept, rework, summary}.md）
- **方法**：逐文件 Read + 横向比较关键定义（命令总数 / 路径惯例 / 状态机口径 / 不变量细节 / corner case）
- **优先级**：高（C2，需修正至少 6 处）→ 中（C1/C3/C4）→ 低（C5/C6）
- **总冲突数**：5 处实质冲突（C1-C5）+ 1 处结构问题（C6）+ 2 处已对齐确认（C7-C8）

> **待用户决策**：
> 1. 是否同步修改本文档 C2 涉及的 6+ 处 `docs/workflow/` → `docs/workflow/` 替换？
> 2. 是否同意让本文档继续保留 `19 启用 + 3 删除` 口径，由 MIGRATION.md 加注迁移基线说明？
> 3. 是否同意在 §11.3 与 §11.7 追加 C4/C5 两项 corner case 自检项？
> 4. C3 的「`/` vs `.` 风格」冲突是否需在执行 dev-workflow 时实测两个版本目录的命名实情后再裁决？
