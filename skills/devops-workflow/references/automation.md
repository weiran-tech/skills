# 自动化协议

> 涉及自动化判定时读本文件。定义所有 auto 配置项的行为规范，各 stage 文件统一引用。

## 配置文件

`{讨论根目录}.workflow-config`（项目级，所有需求共享）。不存在则全部走手动，向后兼容。

```
# 流程推进
auto_advance=true              # 阶段/任务完成后自动推进，不等 /devops-workflow next

# 复杂度与 CR
simple_task_skip_cr=true       # 简单任务跳过 CR 门，编码+DoD 通过后直接 DONE
auto_cr_minor=true             # CR 的 MINOR 问题自动 ACCEPTED，仅 MAJOR 停人工门

# Plan
auto_plan_check=true           # critic agent 自动校验 plan 齐全性，齐全则自动 approve

# 验收
auto_accept_pass=true          # 验收零问题自动 COMPLETED
auto_accept_fix=true           # 验收失败自动修复+重跑验收，超限才停人工门
auto_accept_fix_max=2          # 自动修复最大轮次

# 交付
auto_summary=true              # 验收通过 COMPLETED 后自动产出交付清单（change-manifest.md）
```

---

## auto_advance 协议

阶段或任务完成后，读取 `.workflow-config` 的 `auto_advance`（不存在视为 false）：
- **true**：向用户输出完成摘要后，**立刻执行下一阶段/下一任务**，不等 `/devops-workflow next`
- **false（默认）**：输出完成摘要 + 提示 `/devops-workflow next`

### 适用时机

| 触发点 | auto_advance=true 时的行为 |
|-------|--------------------------|
| 阶段 1 讨论完成 | 自动进入阶段 2 分析 |
| 阶段 3 approve 后 | 自动进入阶段 4 开发 |
| 阶段 4 任务 DONE | 自动取下一个 TODO 任务 |
| 阶段 4 全部 DONE | 自动进入阶段 5 验收，立刻启动 verifier |

### 不适用

- 四道人工门（设计审核 / plan 确认 / CR 裁决 / 验收问题裁决）由 `/devops-workflow approve` 驱动，不受 auto_advance 影响
- **编码完成后的 CR 扫描**：编码 → CR → 裁决 → 改写 → 复验 → DONE 的闭环不可压缩，auto_advance 只在 DONE 之后触发，不在 CODING 之后触发

---

## auto_accept_pass 协议

verifier 返回后，验收结果为 PASSED + 零问题时，读取 `.workflow-config` 的 `auto_accept_pass`（不存在视为 false）：
- **true**：直接回写 progress.md 状态为 COMPLETED，不停门
- **false（默认）**：回写 COMPLETED（零问题无需裁决，但仍输出确认提示）

验收有问题（FAILED）时不受此配置影响，始终走人工裁决门。

---

## 引用方式

各 stage 文件中引用协议时使用一行格式：

```markdown
> 按 automation.md「auto_advance 协议」处理：auto_advance=true 时自动推进到 {目标}，否则提示 `/devops-workflow next`。
```

不在 stage 文件中重复协议细节，修改只改本文件。

---

## simple_task_skip_cr 协议

简单任务编码 + DoD 通过后，读取 `.workflow-config` 的 `simple_task_skip_cr`（不存在视为 false）：
- **true**：简单任务跳过 CR 扫描 / 人工裁决 / 改写 / 复验，编码 + DoD 通过后直接回写 progress.md 为 DONE
- **false（默认）**：简单任务与普通任务走同样的完整闭环（编码 → CR → 裁决 → 改写 → 复验 → DONE）

### 三级复杂度判定

每个任务编码前，Claude 基于 dev-tasks.md 任务描述 + design-consensus 改动范围判定复杂度：

| 级别 | 判定条件 | 流程 |
|------|---------|------|
| **简单** | 单范围 + 1-2 个文件 + 无跨范围契约变更 + 改动性质为加字段/改配置/加日志/简单 CRUD | 编码 → DoD → DONE（跳过 CR，需 `simple_task_skip_cr=true`） |
| **普通** | 业务逻辑调整，不满足简单条件但也非复杂 | 编码 → DoD → CR → 人工裁决 → 改写 → 复验 → DONE |
| **复杂** | 跨范围 / 核心流程 / 资金链路 / 并发一致性 / 设计有未决项 | plan 门 → 编码 → DoD → CR → 人工裁决 → 改写 → 复验 → DONE |

拿不准时按普通处理。判定结果记录到 progress.md 任务状态行（`[简单]` / `[普通]` / `[复杂]`）。

### 风险控制

- 阶段 5 verifier 仍做全局回归 + 一致性校验，兜底简单任务可能的遗漏
- `simple_task_skip_cr=false` 时简单任务仍走完整 CR 闭环（保守默认）
- 判定结果可追溯（progress.md 任务行标记）

---

## auto_cr_minor 协议（L2）

code-reviewer 产出问题清单后，读取 `.workflow-config` 的 `auto_cr_minor`（不存在视为 false）：

- **true**：主 Agent 自动对问题清单按严重度分流：
  - **零问题**：自动置 CR_CONFIRMED，跳过人工门，直接进入复验⑥
  - **全部 MINOR**：全部自动裁决为 ACCEPTED，自动置 CR_CONFIRMED，自动派 executor 改写 → 复验⑥
  - **含 MAJOR**：停在 PENDING_CR_REVIEW 等待人工裁决（与原流程一致）
- **false（默认）**：所有问题不论严重度均停人工门

### 向用户输出

自动裁决时仍向用户输出问题清单和裁决结论，明确标注「auto_cr_minor: {N} 个 MINOR 问题已自动 ACCEPTED」。用户可通过 `/devops-workflow rework` 推翻自动裁决。

### 与 simple_task_skip_cr 的关系

简单任务（`simple_task_skip_cr=true`）直接跳过整个 CR 环节；`auto_cr_minor` 作用于普通/复杂任务的 CR 门——二者正交，不冲突。

---

## auto_plan_check 协议（L2）

architect/planner 产出 plan 后，读取 `.workflow-config` 的 `auto_plan_check`（不存在视为 false）：

- **true**：主 Agent 自动派 `critic` agent 校验 plan 必含项齐全性（改动文件清单 / 改动步骤 / 类与方法签名 / 测试用例清单 — 对照 stages/stage-4.1-plan.md 的模板）：
  - **齐全**：自动置 PLAN_CONFIRMED，跳过人工门，进入编码
  - **缺项**：打回 architect 重出 plan（最多重试 1 次），仍缺项则停在 PENDING_PLAN_REVIEW 等待人工
- **false（默认）**：所有复杂任务 plan 均停人工门

### critic agent prompt 要点

```
critic "
校验 plan .task/plans/{范围标签}-{X.Y}.md 的齐全性，逐项检查：
1. 改动文件清单（每个文件有路径 + 操作 + 说明）
2. 改动步骤序列（按执行顺序，有依赖关系）
3. 类与方法签名（新增/修改的，精确到参数和返回类型）
4. 测试用例清单（用例名 + 覆盖点 + 文件路径）
5. 集成点（与现有代码的接入位置）

输出：PASS（全部齐全）或 FAIL + 缺失项列表。
只做齐全性校验，不做方案正确性判断。"
```

### 向用户输出

自动 approve 时输出「auto_plan_check: plan 齐全性校验通过，已自动确认」。

---

## auto_accept_fix 协议（L2）

verifier 返回 FAILED 后，读取 `.workflow-config` 的 `auto_accept_fix`（不存在视为 false）：

- **true**：自动进入修复循环，不停人工门：
  1. 将所有问题视为 ACCEPTED，按关联任务分组派 executor 修复
  2. 修复后重新启动 verifier 做全局回归
  3. 循环最多 **2 轮**（可配置 `auto_accept_fix_max=2`），超限仍 FAILED 则停在 PENDING_ACCEPT_REVIEW 等待人工
  4. 每轮向用户输出修复摘要和验收结果
- **false（默认）**：FAILED 始终停在 PENDING_ACCEPT_REVIEW 等待人工裁决

### 安全阀

- 循环上限防止死循环（默认 2 轮，可通过 `auto_accept_fix_max=N` 调整）
- 设计/需求层缺陷（verifier 标注为 design-level）不进入自动修复，直接停门并建议 `/devops-workflow rework`
- 每轮修复后的 verifier 是全新启动，不复用上一轮上下文

---

## auto_summary 协议

验收通过（COMPLETED）后，读取 `.workflow-config` 的 `auto_summary`（不存在视为 false）：

- **true**：COMPLETED 输出完成摘要后，**立刻自动执行** `/devops-workflow summary` 产出交付清单（change-manifest.md），不等用户手动触发
- **false（默认）**：仅在完成摘要中提示用户可执行 `/devops-workflow summary`

### 触发时机

仅在以下场景触发：
- 验收通过（PASSED）→ COMPLETED 时
- 验收人工裁决 approve 后零 ACCEPTED 项 → COMPLETED 时
- 自动修复循环通过 → COMPLETED 时

不触发：PENDING_ACCEPT_REVIEW 停门时不触发（未完成不汇总）。

### 多里程碑

每个里程碑 COMPLETED 时各自触发一次 summary。
