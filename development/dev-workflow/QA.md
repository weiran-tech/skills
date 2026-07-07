# dev-workflow QA — 交互流程 / 文件追踪 / 节点清单

> 目的：把 `development/dev-workflow/` 下的全部内容做一份"测试与排查手册"——读完它就能照着走完一遍流程、知道每个文件管什么、知道每个节点该读谁/写谁/校验谁。
>
> 本 QA 文档基于以下文件（2026-07-07 读取快照）：

| 路径 | 角色 |
|------|------|
| `SKILL.md` | 路由器 + 常驻安全规则 |
| `README.md` | 总体流程、设计理念、命令速查、使用示例 |
| `references/discovery.md` | 上下文发现机制（manifest 文件 + CLAUDE.md → DiscoveryContext） |
| `references/templates.md` | `metadata.md` 模板、状态枚举、目录约定 |
| `references/commands.md` | 各 `/dev-workflow` 子命令的详细处理逻辑 |
| `references/stage-2-design.md` | 阶段 2 分析与设计（analyst + ralph 流程） |
| `references/stage-3-review.md` | 阶段 3 设计审核（PENDING_DESIGN_REVIEW 人工门） |
| `references/stage-4-dev.md` | 阶段 4 开发与逐任务审查（含 plan/code/CR/改写） |
| `references/stage-5-accept.md` | 阶段 5 收尾验收 + 异常处理（BLOCKED / 回退 / 恢复） |
| `references/rework.md` | rework 返工通道（实现级 / 设计级 / 需求级） |
| `references/summary.md` | `/dev-workflow summary` 交付清单（DDL / 队列 / API） |

---

## 一、整体交互流程（一次需求从 0 到 COMPLETED）

### 1.1 五阶段 + 三道人工门

```
阶段 1 需求讨论        /dev-workflow start {需求名}
   │  (产出 docs/discuss/{域}/{需求名}.md)
   ▼
阶段 2 分析与设计      /dev-workflow next
   │  (产出 analysis/、design-consensus.md、dev-tasks.md)
   ▼
┌────────────────────────────────────────────────┐
│ 阶段 3 设计审核门  ★人工★  PENDING_DESIGN_REVIEW │  ← 清单式审核，缺项打回阶段 2
│   /dev-workflow approve                          │
└────────────────────────────────────────────────┘
   ▼
阶段 4 开发与逐任务审查   /dev-workflow next
   │
   ▼
阶段 5 收尾验收        /dev-workflow next
   │  (产出 acceptance.md)
   ▼
COMPLETED ──→ /dev-workflow summary  →  change-manifest.md（DDL / Job·MQ / API）

※ 阶段 4/5 若发现设计/需求层缺陷 → /dev-workflow rework 按根因层级回退
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
       │   /dev-workflow approve                  │
       └────────────────────────────────────────┘
          ▼ PLAN_CONFIRMED
 ┌─────────────────────────────────────────────┘
 │ ① 编码 (executor；简单对照 design-consensus / 复杂对照已确认 plan)
 ▼ CODING
 │ ② DoD：{test_cmd} 绿 + {lint_cmd} 语法校验通过
 │ ③ CR 扫描 (code-reviewer，只读，只产出编号问题清单，不改代码)
 ▼ CR_SCANNED
       ┌────────────────────────────────────────┐
       │ CR 问题人工门 ★人工★ PENDING_CR_REVIEW  │  ← 逐条裁决 ACCEPTED/REJECTED/MODIFIED
       │   /dev-workflow approve                  │
       └────────────────────────────────────────┘
 ▼ CR_CONFIRMED
 │ ⑤ 改写 (executor，只改已采纳项)
 ▼ REWRITING
 │ ⑥ 复验 + 进度回写（强制）：{test_cmd} 绿 + {lint_cmd} 通过 → 回写 progress.md + dev-tasks.md
 ▼ VERIFYING → DONE
```

### 1.3 三道人工门汇总

| 门 | 触发状态 | 操作命令 | 通过标志 | 落地动作 |
|----|---------|---------|---------|---------|
| 设计审核门 | `PENDING_DESIGN_REVIEW` | `/dev-workflow approve` | design-consensus 必含清单逐项 ✓ | design-consensus.md 末尾追加 `## 设计确认: APPROVED`，状态置 DEVELOPING |
| 任务 plan 门（仅复杂任务） | `PENDING_PLAN_REVIEW` | `/dev-workflow approve` | plan 必含项齐全 | plan.md 末尾追加 `## 设计确认: APPROVED`，任务状态置 PLAN_CONFIRMED |
| CR 问题裁决门（逐任务） | `PENDING_CR_REVIEW` | `/dev-workflow approve` | 全部问题标注 ACCEPTED/REJECTED/MODIFIED | 任务状态置 CR_CONFIRMED → 走改写⑤ / 复验⑥ |

### 1.4 状态机（需求 / 里程碑级）

```
DISCUSSING ─→ ANALYZING ─→ PENDING_DESIGN_REVIEW ─→ DEVELOPING ─→ REVIEWING ─→ COMPLETED
                                          │                              │
                                          └──── rework 回退（设计/需求层） ┘
```

任务级状态：`TODO → (PLANNING → PLAN_CONFIRMED) → CODING → CR_SCANNED → CR_CONFIRMED → REWRITING → VERIFYING → DONE`

---

## 二、文件过程追踪清单（按"读谁 → 写谁 → 校验谁"组织）

### 2.1 阶段 1：需求讨论（`start`）

| 动作 | 触发 | 读取 | 写入 | 校验 |
|------|------|------|------|------|
| 询问业务域 | `/dev-workflow start {需求名}` | manifest 文件（autoload/workspaces/modules/...）/ `docs/architecture/` 列表 | — | 必须唯一确定域 |
| 检查讨论文档是否已存在 | 同上 | `docs/discuss/{域}/{需求名}.md` | — | 若存在，询问是否基于已有继续 |
| 调用讨论 skill | 同上 | — | `docs/discuss/{域}/{需求名}.md` | 必须含影响分析章节 |
| 初始化 progress.md | 讨论完成 | `references/templates.md` | `.task/progress.md`（状态 `ANALYZING`） | 模板必填字段齐全 |
| 写活动上下文 | 同上 | — | `docs/discuss/.workflow-active` | 单行 `{需求ID}[#里程碑]` |

### 2.2 阶段 2：分析与设计（`next` → ANALYZING）

| 动作 | 触发 | 读取 | 写入 | 校验 |
|------|------|------|------|------|
| 提取受影响模块 | `/dev-workflow next` | `docs/discuss/{域}/{需求名}.md` 影响分析章节 | `.task/progress.md` "影响模块" 字段 | — |
| 优先复用架构文档 | 同上 | `docs/architecture/{模块名}/{overview,business,contracts,flows}.md`、`docs/architecture/cross-module.md` | — | 文档缺失或过期时启动分析 |
| 逐模块分析（必要时） | 启动 `team {N}:analyst` | `{module_root_glob}` 代码 + 架构文档 | `.task/analysis/{模块名}.md` | a/b/c 三段齐全 |
| 汇总设计 | 启动 `ralph` | 全部 `.task/analysis/*.md` + 讨论文档 + `cross-module.md` | `.task/design-consensus.md`（必含 6 项）+ `.task/dev-tasks.md` | 必含清单完整；冲突时写 `.task/conflicts.md` 并标 BLOCKED |
| 更新 progress.md | 完成后 | — | `.task/progress.md` 阶段记录 + 状态置 `PENDING_DESIGN_REVIEW` | — |

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
- 模块路径 `{module_root_glob}/{模块名}`

### 2.3 阶段 3：设计审核（`approve` → PENDING_DESIGN_REVIEW）

| 动作 | 触发 | 读取 | 写入 | 校验 |
|------|------|------|------|------|
| 定位目标 | `/dev-workflow approve` | progress.md 当前状态 | — | 必须处于 `PENDING_DESIGN_REVIEW` |
| 主 Agent 自查清单 | 同上 | design-consensus.md | — | 6 项逐项 ✓/✗ |
| 提示用户审核 | 同上 | — | 输出提示（含自查结论） | — |
| 通过：追加确认标记 | 人工逐项 ✓ | — | design-consensus.md 末尾追加 `## 设计确认: APPROVED` | — |
| 更新 progress.md | 通过后 | — | 阶段记录完成时间 + 状态置 `DEVELOPING` | — |

**审核清单**（缺项 / 过浅一律打回）：
- [ ] 对外契约齐全（接口 / {contract_type} 通道 / 跨模块调用）
- [ ] 模块边界清晰（谁该改、谁不该改）
- [ ] 关键机制决策有"为什么"
- [ ] 验收标准可执行
- [ ] 未决项已登记成表，每条有处置方式（不许悬空 TODO）
- [ ] 简单任务实现要点足以直接开工；复杂任务在 dev-tasks 标 `复杂`

### 2.4 阶段 4：开发与逐任务审查（`next` → DEVELOPING）

**进入阶段 4 首次**：

| 动作 | 读取 | 写入 | 校验 |
|------|------|------|------|
| 决定编码并行/串行 | `dev-tasks.md` 依赖图 + 模块目录 | progress.md 阶段记录决策 + 理由 | 互不依赖 + 目录不重叠 → 并行；否则串行 / 按波次 |
| 推进当前未 DONE 任务 | — | — | 复杂任务先 PLANNING；简单任务直接 CODING |

**任务内闭环（每个任务独立走完）**：

| 子步骤 | 状态变迁 | agent | 读 | 写 | DoD 校验 |
|--------|---------|-------|----|----|---------|
| ⓪ 复杂度判断 | TODO → PLANNING（复杂）/ TODO → CODING（简单） | Claude 自评 | dev-tasks.md 标注 | — | — |
| 出 plan（复杂） | PLANNING → PENDING_PLAN_REVIEW | `architect` / `planner`（只读） | design-consensus + `docs/architecture/{模块}` + 现有代码 | `.task/{...}/plans/{序号}-{模块名}.md` | 6 项齐全（签名 / 数据模型 / 时序 / 边界 / 测试用例 / 迁移） |
| 人工确认 plan | PENDING_PLAN_REVIEW → PLAN_CONFIRMED | — | plan.md | plan.md 末尾追加 `## 设计确认: APPROVED` | plan 不达标 → 打回重出 |
| ① 编码 | PLAN_CONFIRMED / TODO → CODING | `executor`（并行 `team` / 串行单） | design-consensus 或已确认 plan + 前序契约 | `{module_root_glob}` 代码 + 单测 + `.task/done/{模块名}.md` | DoD：单测绿 + {lint_cmd} 通过 |
| ② DoD 自检 | CODING | 同上 | 改动文件 | — | `{test_cmd}` 绿 + `{lint_cmd}` 通过 |
| ③ CR 扫描 | CODING → CR_SCANNED | `code-reviewer`（只读） | `git diff <默认分支>...HEAD -- {module_root_glob}` + done.md + design-consensus + docs/architecture/{模块} | `.task/review/{模块名}-{任务序号}.md`（编号清单 + 严重度 + 文件:行 + 建议改法 + 裁决:PENDING） | **绝不允许直接改代码** |
| ④ 人工裁决 | CR_SCANNED → PENDING_CR_REVIEW | 人工 | 报告『人工裁决』区 | 报告『人工裁决』区填 ACCEPTED / REJECTED / MODIFIED | 全部 PENDING 必须变更为三选一 |
| 锁定裁决 + CR_CONFIRMED | PENDING_CR_REVIEW → CR_CONFIRMED | `/dev-workflow approve` | — | progress.md 任务状态置 CR_CONFIRMED | — |
| ⑤ 改写（仅 ACCEPTED / MODIFIED） | CR_CONFIRMED → REWRITING | `executor` | 已确认问题清单 + 当前代码 | `{module_root_glob}/` | REJECTED 项禁止改动 |
| ⑥ 复验 + 进度回写 | REWRITING → VERIFYING → DONE | 主 Agent | — | progress.md（任务状态 + 里程碑进度计数）+ dev-tasks.md（子项 `[ ]→[x]`） | `{test_cmd}` 绿 + `{lint_cmd}` 通过 + 已采纳问题修复 |

**★ 子 agent 返回后四步协议（必须立刻执行，禁止静默结束本轮）**：

1. **读产出**：读取子 agent 写出的产出文件（以文件为准，不以子 agent 返回文本为准）
2. **回写状态**：更新 progress.md 任务状态行 + 里程碑进度表
3. **向用户输出结果摘要**：简述产出内容
4. **明确告知下一步**：该 `approve` 还是 `next`，或主 Agent 将自动执行什么

### 2.5 阶段 5：收尾验收（`next` → REVIEWING）

| 动作 | 读取 | 写入 | 校验 |
|------|------|------|------|
| 启动 `verifier` | — | — | — |
| 任务清单核查 | `.task/progress.md` | — | 全部勾选；各任务审查均 PASSED |
| 全量回归 | `{test_cmd}` | — | 全绿 |
| 语法校验 | 改动文件 | — | `{lint_cmd}` 全通过（`{static_analysis_cmd}` 默认不纳入） |
| 跨模块一致性 | `.task/design-consensus.md` + `docs/architecture/cross-module.md` | — | {contract_type} 通道契约闭合 |
| 迁移检查 | `{module_root_glob}/*/resources/migrations/`（或项目约定路径） | — | 迁移与回滚可用 |
| 写验收报告 | — | `.task/acceptance.md` | — |
| 更新 progress.md | acceptance.md | 阶段 5 状态 + 里程碑进度表 | 通过 → COMPLETED；不通过 → 标注问题 |
| 输出流程完成摘要 | — | 对话输出 | — |

**异常分流**：
- 单任务实现问题 → 退回该任务 executor，重走该任务 CR → 改写 → 复验
- 设计错 / 多任务受牵连 → `/dev-workflow rework`（设计级）

### 2.6 收尾：`/dev-workflow summary`

| 动作 | 读取 | 写入 | 校验 |
|------|------|------|------|
| 启动 `writer` / `document-specialist`（只读） | 本里程碑产物 + 定向 grep | `.task/[milestones/{里程碑}/]change-manifest.md` | — |
| 三大块汇总 | `{module_root_glob}/*/resources/migrations/` + 路由 + 控制器 + design-consensus 契约 | 同上 | DDL N 张表 / 队列 M 个 / API K 个 |
| 主 Agent 呈现结果 | change-manifest.md | 对话输出 | 必须给用户三条数摘要 + 文件路径 |

**change-manifest.md 模板三块**：
1. DDL 变更（给 DBA）—— 直接可执行的 SQL
2. 新增队列（给运维）—— 仅 queue name 一行一个
3. API 接口清单（给前端）—— Method+Path / 入参 / 出参要点 / 用途

### 2.7 返工：`/dev-workflow rework`

| 步骤 | 读取 | 写入 | 校验 |
|------|------|------|------|
| 确认缺陷描述 + 根因层级 | 当前进度 + 用户陈述 | `.task/[milestones/{里程碑}/]rework/R{轮次}-{YYYY-MM-DD}.md` | 三层级：实现 / 设计 / 需求 |
| 依赖扩散（自动算 + 人工确认） | `dev-tasks.md` 依赖图 | — | 列下游受影响任务给用户确认 |
| 按层级回退 | — | design-consensus.md 追加 `## 返工修订 R{N}：{原因}`（仅设计级） | — |
| 回写 progress.md | rework 单 + 依赖图 | 受影响任务→TODO（标返工轮次）+ 阶段按层级回退 + 追加返工记录 | 未受影响的 DONE 任务保留 |
| 重跑 | — | — | 设计级：阶段 2→3→4（含 plan 重出）→5；实现级：阶段 4（重 code+CR）；需求级：阶段 1 |

---

## 三、节点追踪表（所有节点的读 / 写 / 状态 / 主 Agent 收尾动作）

### 3.1 命令节点

| 节点 | 触发命令 | 读取 | 写入 | 状态变迁 | 主 Agent 收尾动作 |
|------|---------|------|------|---------|-----------------|
| N1 设定活动上下文 | `/dev-workflow use [ID][#M]` | 当前 `.workflow-active` | `docs/discuss/.workflow-active` | 覆盖 | 回显当前活动 + 阶段/状态 |
| N2 起需求 | `/dev-workflow start {名}` | manifest 文件 / `{module_root_glob}`、`docs/architecture/` 是否存在 | `docs/discuss/{域}/{需求名}.md`、`.task/progress.md`、`.workflow-active` | DISCUSSING → ANALYZING | 提示下一步 `next` |
| N3 拆分里程碑 | `/dev-workflow split [ID] {列表}` | 阶段 1 文档 | `.task/milestones/{M}/`、`design-foundation.md`、progress.md（多里程碑） | — | 设活动上下文为前置里程碑 |
| N4 推进下一阶段 | `/dev-workflow next [ID][#M]` | progress.md | 各阶段产物 + progress.md | 详见 §3.2 | 按 §1.2 流水线推进 |
| N5 确认人工门 | `/dev-workflow approve [ID][#M]` | 当前状态 | design-consensus.md / plan.md / 任务状态 | 视门类 | 详见 §3.3 |
| N6 查看状态 | `/dev-workflow status [ID][#M]` | progress.md（们） | — | — | 输出进度展示 |
| N7 列需求 | `/dev-workflow list` | 所有 `.task/progress.md` | — | — | 仅未 COMPLETED |
| N8 返工 | `/dev-workflow rework [ID][#M]` | 缺陷描述 + 依赖图 | `.task/.../rework/R{N}-...md`、design-consensus.md（设计级）、progress.md | 按层级回退 | 列出受影响任务等用户确认 |
| N9 出交付清单 | `/dev-workflow summary [ID][#M]` | 本里程碑产物 + 实际代码 | `.task/[milestones/{M}/]change-manifest.md` | — | 输出 DDL N / 队列 M / API K |

### 3.2 阶段推进节点（`next` 命令内部）

| 节点 | 前置状态 | 启动的 agent | 读取 | 写入 | 后置状态 |
|------|---------|-------------|------|------|---------|
| S2 模块分析 | ANALYZING | `team {N}:analyst`（并行按模块） | `docs/discuss/{域}/{需求名}.md`、架构文档、代码 | `.task/analysis/{模块名}.md` | — |
| S2 汇总设计 | （分析完成后自动） | `ralph` | 全部 analysis + 讨论 + cross-module.md | `.task/design-consensus.md`、`.task/dev-tasks.md` | PENDING_DESIGN_REVIEW（或 BLOCKED） |
| S4 编码并行 | DEVELOPING + 至少 2 任务无依赖 | `team {N}:executor` | design-consensus 或已确认 plan | `{module_root_glob}` 代码 + 单测 + `.task/done/{模块名}.md` | CODING → VERIFYING 待 CR |
| S4 编码串行 | DEVELOPING | 单个 `executor` | 同上 | 同上 | 同上 |
| S4 CR 扫描 | CODING | 单 `code-reviewer` | diff + done + design-consensus + 架构文档 | `.task/review/{模块}-{序号}.md` | CR_SCANNED → PENDING_CR_REVIEW |
| S5 验收 | REVIEWING | `verifier` | 全量 | `.task/acceptance.md` | COMPLETED 或带问题回退 |

### 3.3 人工门节点（`approve` 命令内部）

| 门节点 | 前置状态 | 校验项 | 通过后动作 | 后置状态 |
|--------|---------|--------|-----------|---------|
| G1 设计审核 | PENDING_DESIGN_REVIEW | 必含 6 项清单 | design-consensus.md 追加 `## 设计确认: APPROVED` | DEVELOPING |
| G2 任务 plan | PENDING_PLAN_REVIEW | plan 必含 6 项（签名/数据模型/时序/边界/测试/迁移） | plan.md 追加 `## 设计确认: APPROVED` | 任务 PLAN_CONFIRMED |
| G3 CR 裁决 | PENDING_CR_REVIEW | 每条问题已填 ACCEPTED/REJECTED/MODIFIED | 任务 CR_CONFIRMED；走改写⑤+复验⑥ | DONE |

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

## 四、活动上下文（粘性指针）详解

### 4.1 指针位置与格式

- 文件：`docs/discuss/.workflow-active`（单行）
- 格式：`{需求ID}[#里程碑]`，如 `order/订单取消优化`、`payment/支付渠道重构#alipay`
- 性质：**便捷指针非状态源**；状态源是 `progress.md`

### 4.2 解析优先级

**显式参数 > 活动指针 > 旧回退规则**（唯一进行中自动选；多个列出让选；无则提示 start）

支持前缀/子串模糊匹配，唯一即定位，多个则列出让选（如 `trade#共` → `trade/...#共享基础`）。

### 4.3 里程碑"粘住"机制（避免每步重复敲 `#`）

- 指针只有需求而该需求是多里程碑时：
  1. `next`/`approve` 解析里程碑——唯一进行中 → 自动选中；多个 → 列出选择
  2. 解析出里程碑后**立即写回指针**，粘住为 `{需求ID}#里程碑`
  3. 切换到别的里程碑用 `/dev-workflow use #{里程碑}`（只敲 `#`）
- 该里程碑 COMPLETED 后，指针自动改指剩余唯一在跑的里程碑（或提示重新 `use`）

### 4.4 哪些命令不改活动指针

- 显式传参命令（`next [ID]`、`approve [ID]` 等）只临时切换操作目标，不动 `.workflow-active`
- `status` 解析不写回指针

---

## 五、产出物目录结构（单里程碑 vs 多里程碑）

### 5.1 单里程碑（默认）

```
docs/discuss/{域}/{需求名}/
  {需求名}.md                 # 阶段 1 讨论文档
  .task/
    progress.md               # ★唯一状态源
    analysis/                 # 阶段 2 逐模块分析
    design-consensus.md       # 阶段 2 共识/契约层（必含清单）
    dev-tasks.md              # 阶段 2 任务拆分（标注 简单|复杂）
    plans/                    # 阶段 4 复杂任务的 plan/LLD
    done/                     # 阶段 4 各任务完成标记
    review/                   # 阶段 4 各任务 CR 问题清单 + 裁决
    rework/                   # 返工单（缺陷返工时才有）
    acceptance.md             # 阶段 5 收尾验收报告
    change-manifest.md        # /dev-workflow summary 交付清单
```

### 5.2 多里程碑（`split` 后）

```
docs/discuss/{域}/{需求名}/
  {需求名}.md                            # 阶段 1（共享）
  .task/
    progress.md                          # 含里程碑进度表
    design-foundation.md                 # 跨里程碑公共骨架
    milestones/
      {里程碑A}/
        analysis/  design-consensus.md  dev-tasks.md  plans/  done/  review/  rework/
        acceptance.md  change-manifest.md
      {里程碑B}/
        （结构同上）
```

> 多里程碑下"分析/设计/任务/审查/返工/验收/清单"全部下沉到 `milestones/{里程碑}/`，仅讨论文档、`design-foundation.md`、架构时序图留在 `.task/` 根。各 agent 工作范围限定在该里程碑覆盖的模块。

---

## 六、Agent 权限与职责矩阵

| 阶段 | agent / skill | 权限 | 职责 |
|------|--------------|------|------|
| 阶段 1 需求讨论 | `dev-discuss` | 读写 | 多轮对话厘清目标 / 影响 |
| 阶段 2 模块分析 | `{discovery_cmd}` / `analyst` | 只读 | 读代码 + 读架构文档 → 产出模块分析 |
| 阶段 2 汇总设计 | `ralph` | 读写 | 汇总 analysis → design-consensus + dev-tasks |
| 阶段 4 任务详细设计（仅复杂任务） | `architect` / `planner` | 只读 | 出任务级 plan/LLD，不写业务代码 |
| 阶段 4 编码 | `executor`（并行 `team` / 串行单） | 读写 | 对照 design-consensus 或已确认 plan 编码 + 单测 |
| 阶段 4 CR 扫描（逐任务） | `code-reviewer` | 只读 | 只产问题清单，**绝不自动改代码** |
| 阶段 4 改写（逐任务） | `executor` | 读写 | 只改已采纳项 |
| 阶段 5 收尾验收 | `verifier` | 只读 | 全量回归 + 一致性把关 |
| 阶段 5 交付清单 | `writer` / `document-specialist` | 只读 | 汇总 change-manifest.md |
| 阶段 4/5 返工 | `team` / `analyst` / `executor` / `verifier` | 视场景 | 按根因层级回退重做 |

人工门：阶段 3 设计审核、阶段 4 plan 确认、阶段 4 CR 裁决（均为 `/dev-workflow approve`）。

---

## 七、关键不变量（10 条铁律）

1. **子 agent 返回 ≠ 流程推进**：每次子 agent 返回后必须立刻：① 读取产出文件 → ② 回写 progress.md → ③ 输出摘要 + 下一步指令。**绝不允许静默结束本轮**。
2. **CR 问题人工门**：code-reviewer 只产清单，**绝不直接改代码**；扫出问题必须经人工逐条裁决并 `approve` 后才由另一个 executor 改写。
3. **编码与审查分两轮**：编码 / CR / 改写各自独立 agent，CR 与编码不共享上下文，禁止自审。
4. **进度即时回写（阻塞）**：每次状态变化立刻写回 progress.md 任务状态行 + 里程碑进度表，并同步 dev-tasks.md 子项；**回写未完成不得推进下一个任务**。
5. **设计分两层**：design-consensus = 共识/契约层（阶段 3 清单式审核）；复杂任务级 plan/LLD = 实现细节（阶段 4 编码前出，人工 approve 后才编码）。
6. **未决项不许悬空**：design-consensus 的 `待确认/TODO` 必须登记成表并有处置方式。
7. **设计/需求层缺陷走 rework**，不要硬塞进 CR 改写：CR 改写只解决任务内小问题；牵动设计或多任务用 `/dev-workflow rework`。
8. **子需求默认单个**：只有大需求才 `req split`；跨模块交互一律通过 `{contract_type}` 通道，禁止直接访问他模块实现细节（具体实现细节按语言而异，统一表述为"直接调用对模块内部的实体"）。
9. **中断恢复**：流程可在任意阶段中断，下次 `/dev-workflow next` 从 progress.md 恢复。
10. **所有 agent prompt 必须含 Bash 静态分析约束**：禁止 `for` / `while` / `if` / `case` / here-doc / 嵌套 `$()`；产出物只落项目内 `.task/`，禁止写 home 或仓库外。

---

## 八、验收基线（强制）

| 项 | 命令 | 通过标准 |
|----|------|---------|
| 单测 | `{test_cmd} {module_root_glob}/{模块}/tests`（或项目约定的单测路径） | 绿 |
| 语法 | `{lint_cmd} <改动文件>` | 通过 |
| 全量回归（阶段 5） | `{test_cmd}`（全量） | 绿 |
| 跨模块一致性（阶段 5） | 对照 design-consensus + `docs/architecture/cross-module.md` | {contract_type} 契约闭合 |
| 迁移（阶段 5，若涉及） | `{module_root_glob}/*/resources/migrations/`（或项目约定路径） | 迁移与回滚可用 |
| {static_analysis_cmd} | — | **默认不纳入 DoD / 验收**（存量项目历史告警多）；项目有干净基线时再可选开启 |

> 命令模板里的 `{test_cmd}` / `{lint_cmd}` / `{static_analysis_cmd}` / `{module_root_glob}` 由 `references/discovery.md` 描述的发现机制从项目 manifest 文件 + CLAUDE.md 解析得到；项目侧未声明时按 `[字段 {X} {当前值}] {原因}。建议: {修复}` 三段式硬阻断，**不允许猜测默认值**。

---

## 九、命令速查（含最少必要参数）

| 命令 | 必带 / 可选 | 关键效果 |
|------|------------|---------|
| `/dev-workflow use [ID][#M]` | 可不带 → 显示当前；带 → 切换 | 写 `.workflow-active` |
| `/dev-workflow start {需求名}` | 必带需求名 | 创建需求 + 设活动 + 进入阶段 1 |
| `/dev-workflow split [ID] {M列表}` | 列表用逗号分隔 | 多里程碑结构 + 设前置里程碑为活动 |
| `/dev-workflow next [ID][#M]` | 可省 | 推进到下一阶段 / 下一个任务 |
| `/dev-workflow approve [ID][#M]` | 可省 | 按当前状态分发：设计审核 / plan / CR 裁决 |
| `/dev-workflow status [ID][#M]` | 可省 | 单里程碑简版；多里程碑表 + 高亮 |
| `/dev-workflow list` | 无 | 未完成需求 + 多里程碑子简况 |
| `/dev-workflow rework [ID][#M]` | 可省 | 缺陷返工（需用户选根因层级） |
| `/dev-workflow summary [ID][#M]` | 可省 | 产出 change-manifest.md + 输出条数摘要 |

需求 ID 格式：`{域}/{需求名}`（如 `order/订单取消优化`），与 `docs/discuss/` 目录一致。

---

## 十、典型路径示例（端到端走查）

### 10.1 单里程碑普通需求

```
/dev-workflow start 订单取消优化
  → 询问业务域=order，多轮讨论，产出 docs/discuss/order/订单取消优化.md

/dev-workflow next
  → 阶段 2：analyst 逐模块分析 → ralph 汇总 design-consensus + dev-tasks
  → 停在 PENDING_DESIGN_REVIEW，给出设计审核清单自查结论

/dev-workflow approve
  → design-consensus 标 APPROVED，进入开发

/dev-workflow next
  → 任务1（简单）：编码 → DoD → CR 扫描 → 停在 PENDING_CR_REVIEW，呈现问题清单

# 用户裁决：#1 ACCEPTED、#2 REJECTED、#3 MODIFIED
/dev-workflow approve
  → 改写 #1/#3 → 复验绿 → 任务1 置 DONE → 回写 progress.md + dev-tasks.md

/dev-workflow next       # 推进任务2... 直到全部 DONE

/dev-workflow next       # 阶段 5：verifier 全量 {test_cmd} + {lint_cmd} + 跨模块一致性
  → 通过 → COMPLETED

/dev-workflow summary    # 产出 change-manifest.md（DDL/Job·MQ/API）
```

### 10.2 多里程碑 + 复杂任务 plan 门

```
/dev-workflow split payment/支付渠道重构 alipay,wechat
  → 抽取 design-foundation.md（公共骨架先定稿）

/dev-workflow use payment/支付渠道重构#alipay     # 也可模糊 use payment#alipay
/dev-workflow next        # 阶段 2 → PENDING_DESIGN_REVIEW
/dev-workflow approve     # 设计审核通过
/dev-workflow next        # 阶段 4：某任务判为【复杂】→ architect 出 plan，停在 PENDING_PLAN_REVIEW
/dev-workflow approve     # plan 确认 → 编码 → CR → PENDING_CR_REVIEW ...

/dev-workflow use #wechat
/dev-workflow next

/dev-workflow status
  ▶ 活动: payment/支付渠道重构#wechat
  里程碑 alipay     阶段 4/5 — 开发（进行中）  任务 2/6
  里程碑 wechat ◀   阶段 3/5 — 设计审核（待审核）任务 0/9
```

### 10.3 收尾发现设计错 → rework

```
# 阶段 5 验收发现 design-consensus 方案有缺陷
/dev-workflow rework payment/支付渠道重构#alipay
  → 确认根因 = 设计级
  → design-consensus 标 "## 返工修订 R1"，里程碑退回阶段 2
  → 自动算出下游受影响任务，列给用户确认
  → 确认后这些任务回 TODO（标 返工R1），未受影响的 DONE 保留
  → progress.md 追加返工记录 R1

/dev-workflow next payment/支付渠道重构#alipay     # 阶段 2 修订 design-consensus
/dev-workflow approve payment/支付渠道重构#alipay  # 阶段 3 重审通过
/dev-workflow next payment/支付渠道重构#alipay     # 复杂任务重出 plan → 重 code → 重 CR
```

---

## 十一、QA 自检清单（排查用）

按以下清单逐项核对，可以定位 90% 的卡死 / 卡门问题：

### 11.1 卡在 PENDING_DESIGN_REVIEW

- [ ] 是否调用 `/dev-workflow approve`（而非 `next`）
- [ ] design-consensus.md 必含 6 项是否齐全（对外契约 / 模块边界 / 决策+理由 / 验收标准 / 未决项 / 简单任务实现要点）
- [ ] 是否有 `.task/conflicts.md`（冲突未解决 → BLOCKED）

### 11.2 卡在 PENDING_PLAN_REVIEW

- [ ] 该任务是否在 dev-tasks.md 标为 `复杂`
- [ ] plan.md 是否含 6 项（签名 / 数据模型 / 时序 / 边界 / 测试用例 / 迁移）
- [ ] plan.md 末尾是否有 `## 设计确认: APPROVED`

### 11.3 卡在 PENDING_CR_REVIEW

- [ ] 是否仍有问题标注为 `PENDING`（必须三选一）
- [ ] 子 agent 返回后主 Agent 是否输出了 `/dev-workflow approve` 提示字符串（漏了说明漏了第 3 步）
- [ ] 是否区分了"零问题 PASSED"（直接 approve 走复验）和"有问题"（必须先裁决）

### 11.4 子 agent 跑完没动静

- [ ] 主 Agent 是否按"四步协议"操作：① 读产出 → ② 回写 progress.md → ③ 输出摘要 → ④ 明确下一步
- [ ] 是否读了**文件**（而非子 agent 返回文本）
- [ ] 是否漏改 progress.md 任务状态行（`PLANNING` / `CODING` / `CR_SCANNED` / `CR_CONFIRMED` / `REWRITING` / `VERIFYING` / `DONE`）
- [ ] 是否漏改里程碑进度表计数（如 `2/9 → 3/9`）
- [ ] dev-tasks.md 子项是否漏勾 `[ ]→[x]`

### 11.5 编码 / 改写没限制

- [ ] 是否注入了 `Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()`
- [ ] 并行 executor 是否限定了模块目录（`{module_root_glob}/{模块}/`）
- [ ] 改写 executor 是否明确"只处理 ACCEPTED / MODIFIED 的问题，REJECTED 不动"
- [ ] 是否禁止写入 home 或仓库外的路径

### 11.6 返工用错通道

- [ ] 只改当前任务能解决 → 用 CR 改写
- [ ] 牵动设计或别的任务 → 用 `/dev-workflow rework`
- [ ] rework 是否选择了正确层级：实现 / 设计 / 需求
- [ ] 受影响任务是否包含"依赖被改设计的下游"（自动算 + 人工确认）
- [ ] 未受影响的 DONE 任务是否保留

### 11.7 里程碑切换 / 活动指针问题

- [ ] 多里程碑下当前里程碑是否正确解析（粘住机制是否生效）
- [ ] 切换里程碑用 `/dev-workflow use #{M]` 而非长 ID
- [ ] 显式传参是否临时改动了操作目标但没改 `.workflow-active`

### 11.8 中断恢复

- [ ] progress.md 当前阶段记录是否最新
- [ ] 任务清单状态是否与实际一致
- [ ] 下次 `/dev-workflow next` 是否从该阶段继续

### 11.9 上下文缺失 / 冲突（dev-workflow 特有）

- [ ] 项目根是否有 manifest 文件（缺失 → `[字段 manifest {当前值}] 缺失/未声明` 硬阻断）
- [ ] `CLAUDE.md` 是否声明 `## 跨模块调用` 段与 `类型: {rpc|event|queue|http|grpc|kafka|...}`（缺失 → `[字段 cross_module_contract {当前值}] 未声明` 硬阻断）
- [ ] manifest 文件与 CLAUDE.md 在同一字段上是否冲突（冲突 → `[字段 {X} {当前值}] {原因}。建议: {修复}` 硬阻断）
- [ ] 是否出现歧义（如多份 manifest 无 tie-breaker / `engines.node` 与 `engines.deno` 冲突 / `pnpm-workspace.yaml` 与 `package.json#workspaces` 冲突）—— 全部走 §11.9 错误格式硬阻断

---

## 十二、错误格式约定（三段式）

dev-workflow 的所有错误 / 阻断消息一律采用三段式：

```
[字段 {X} {当前值}] {原因}。建议: {修复}
```

- **字段**：定位失败的对象名（manifest / cross_module_contract / versionStatus / subReqId / currentState / ...）
- **当前值**：该字段的当前取值；如缺失可写 `缺失/未声明`
- **原因**：人类可读的失败描述
- **修复**：可执行的修复建议（指向具体文件 / 命令）

示例：

```
[字段 manifest 缺失/未声明] 项目根未发现任何 manifest 文件。原因: dev-workflow 需从 manifest 文件推断 {test_cmd}/{lint_cmd}/模块布局。建议: 在仓库根新增一份 manifest 文件（Node: package.json / Go: go.mod / Java: pom.xml / Rust: Cargo.toml / Python: pyproject.toml），并保证其声明测试命令与模块根。

[字段 cross_module_contract 缺失/未声明] CLAUDE.md 中未发现 ## 跨模块调用 段。原因: dev-workflow 必须从 CLAUDE.md 读取跨模块调用类型（rpc/event/queue/http/grpc/kafka/...）。建议: 在 CLAUDE.md 中新增 ## 跨模块调用 段，注明 类型: {rpc|event|queue|http|grpc|kafka|...}。

[字段 versionStatus RELEASED] 版本已发布，禁止 rework。原因: RELEASED/ARCHIVED 状态下不允许 rework，需走新版本重做。建议: 如需修复请新建子需求并 /dev-workflow version add-sub 加入新版本。

[字段 language {node}] manifest 与 CLAUDE.md 冲突。原因: 两份声明的主语言不一致。建议: 删除冗余 manifest，或在 CLAUDE.md 中显式声明 ## 主语言。
```

CI 中由 `.ci/check-error-format.sh` 用正则 `\[字段 .*?\] .+?。建议: .+` 静态校验所有错误字符串，确保无漂移。

---

## 十三、参考索引（速查对应文件）

| 你要做 | 先读 |
|--------|------|
| 了解上下文发现机制（manifest 文件 + CLAUDE.md → DiscoveryContext） | `references/discovery.md` |
| 写/更新 progress.md、初始化任务目录、查状态枚举 | `references/templates.md` |
| 执行任意 `/dev-workflow` 子命令的详细逻辑 | `references/commands.md` |
| 执行**阶段 2** 分析与设计 | `references/stage-2-design.md` |
| 执行**阶段 3** 设计审核清单门 | `references/stage-3-review.md` |
| 执行**阶段 4** 开发（复杂度/并行 + plan/编码/CR/改写 全部 prompts） | `references/stage-4-dev.md` |
| 执行**阶段 5** 收尾验收 + 异常处理（BLOCKED / 回退 / 恢复） | `references/stage-5-accept.md` |
| 执行 `/dev-workflow rework` 返工 | `references/rework.md` |
| 执行 `/dev-workflow summary` 产出交付清单 | `references/summary.md` |
| 总览、设计理念、命令速查、使用示例 | `README.md` |
| 路由器 + 常驻安全规则 | `SKILL.md` |

> **执行某阶段/命令前必须先读对应 reference 文件**再行动——尤其阶段 4，prompts 和人工门的精确措辞都在 `stage-4-dev.md`，凭记忆执行易漏步、易卡死。