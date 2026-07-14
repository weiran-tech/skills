# 阶段 4：开发与逐任务审查（DEVELOPING）

> 执行阶段 4 前读本文件。plan 细节见 `stage-4.1-plan.md`，CR 细节见 `stage-4.2-cr.md`。产出物根路径见 templates.md。

**工单目录基准**：`{讨论根目录}{域}/{需求名}/.task/`。本文件及 stage-4.1/4.2 中所有 `.task/` 路径（如 `.task/done/`、`.task/review/`、`.task/plans/`）均相对于此，**不是项目根目录下的 `.task/`**。agent prompt 中的 `.task/` 同理。

**核心原则：每任务即审、CR 问题人工确认后才改写。编码是否并行由 Claude 自行判断；CR 人工门永远逐任务。** 任务 = dev-tasks.md 中一个可独立交付的工作项（通常一个模块的一组改动）。无独立分支，全部在当前 feature 分支推进。

### ★★ 子 agent 返回后通用协议（适用于 executor / code-reviewer / architect 等所有子 agent）

**每个子 agent 返回后，主 Agent 必须立刻完成以下四步，缺一不可，禁止静默结束本轮：**

1. **读产出**：读取子 agent 写出的产出文件（以文件为准，不以子 agent 返回文本为准）
2. **回写状态**：更新 progress.md 任务状态行 + 里程碑进度表
3. **向用户输出结果摘要**：简述产出内容（编码改了什么 / CR 扫出几条 / plan 要点等）
4. **明确告知下一步**：用户该执行什么命令（`/devops-workflow approve` / `/devops-workflow next`），或主 Agent 将自动执行什么

**违反此协议的典型表现**：子 agent 跑完后只更新了 progress.md 就结束、或只说"已完成"但不展示结果、或不告诉用户下一步该做什么。这些都是 BUG。

## 编码并行 vs 串行——由 Claude 判断

阶段 4 启动时，Claude 读取 dev-tasks.md 的任务依赖图，自行决定**编码**用并行还是串行，并把决策与理由记到 progress.md。判断准则：

- **倾向并行**：存在 ≥2 个**互不依赖**、且**模块目录不重叠**（无文件冲突）的任务，并行能明显省时。并行时用 `team {N}:executor`，每个 executor 工作范围限定在自己的模块目录。
- **倾向串行**：任务之间有依赖链、共享同一模块/文件、任务很少或很小、或并行收益不明显。串行时用单个 `executor`，一次一个。
- **混合**：常见做法是按"波次"组织——同一波内**无依赖**的任务并行编码，波与波之间按依赖串行；有依赖的任务把前序产出（接口/Event 契约）注入 prompt。

> 决策只针对**编码**这一步。下面的 **CR 扫描 → 人工确认 → 改写** 始终**按任务逐个进行**：即使多个任务并行编码完成，CR 报告与人工裁决也是一个任务一份、一个任务一确认，绝不合并、绝不跳过人工门。并行只是让多个任务更快到达各自的 CR_SCANNED，不改变人工门的逐任务性质。

## 每个任务的闭环

```
TODO
 │ ⓪ 复杂度判断（三级：简单/普通/复杂，详见 automation.md + stage-4.1-plan.md）
 ├─ 简单 ──→ ① 编码 → ② DoD ──→ DONE（simple_task_skip_cr=true 时跳过 CR）
 ├─ 普通 ──→ ① 编码 → ② DoD → ③④⑤ CR 闭环 → ⑥ 复验 → DONE
 └─ 复杂 ──→ plan/LLD（architect/planner）
              ▼ PLANNING
              停 PENDING_PLAN_REVIEW ←人工确认门
              │ 人工 /devops-workflow approve
              ▼ PLAN_CONFIRMED
              → ① 编码 → ② DoD → ③④⑤ CR 闭环 → ⑥ 复验 → DONE
```

### ⓪ 复杂度判定（每个任务编码前必做）

Claude 基于 dev-tasks.md 任务描述 + design-consensus 改动范围判定，结果记录到 progress.md 任务行（`[简单]` / `[普通]` / `[复杂]`）。判定标准见 `automation.md「simple_task_skip_cr 协议」`。拿不准按普通处理。

### 简单任务快速通道（需 `simple_task_skip_cr=true`）

简单任务编码 + DoD 通过后：
1. **dev-tasks.md**：该任务下所有子项 `[ ]` 勾成 `[x]`
2. **写入** `.task/done/{范围标签}-{X.Y}.md`（改动摘要 + 测试结果）
3. **回写** progress.md：任务状态 → `DONE`
4. **向用户输出**：改动摘要 + 测试结果 + 明确标注「简单任务，跳过 CR」
5. 按 `auto_advance` 协议决定是否自动取下一个任务

> **简单任务不走 CR 扫描 / 人工裁决 / 改写 / 复验**，阶段 5 verifier 全局回归作为兜底。

### 普通/复杂任务闭环（不变）

## ① 编码（并行示例：同波无依赖任务用 team；串行则换成单个 executor）
```
# 并行（同一波内互不依赖、模块目录不重叠的任务）
/oh-my-claudecode:team {N}:executor "
本波任务（互不依赖，按模块目录隔离、互不重叠）：
{对本波每个任务生成一行}
- {范围标签} executor: 工作范围限定在该任务的工作范围目录（见 dev-tasks.md）
  任务: {从 dev-tasks.md 提取}
  {复杂任务：注入已确认的 plan 路径 .task/{...}/plans/{模块名}-{X.Y}.md，严格对照实现；简单任务：对照 design-consensus 实现要点}
  {若依赖前序波次，注入 .task/done/{前序模块}.md 中的接口/Event 契约}
  DoD: 写代码 + 写单测 + 按项目 .claude/rules/ 中定义的测试命令执行模块级单测通过 + 按项目规则执行语法/编译检查通过
  完成后：① 把本任务在 dev-tasks.md 中已完成的子项 [ ] 勾成 [x]；② 写入 .task/done/{模块名}.md（改动摘要、对外接口/Event 契约、测试与检查结果）

遵守项目 CLAUDE.md 与 .claude/rules/ 的架构与编码规范。
Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"

# 串行时：去掉 team，对单个任务起一个 executor，内容同上（仅一行任务）。
```

### ★ executor 编码返回后，主 Agent 必须立刻执行以下动作（缺一不可，禁止静默结束本轮）
1. **读取** executor 写出的完成报告 `.task/done/{模块名}.md`（以文件为准）
2. **同步 dev-tasks.md**：读取 dev-tasks.md，把该任务已完成的子项 `[ ]` 勾成 `[x]`（executor 漏勾的由主 Agent 补勾，**不可跳过**）
3. **回写** progress.md：把该任务状态置 `CODING`（如尚未置）
4. **向用户输出**：
   - 改动摘要（改了哪些文件/类、新增了什么）
   - 测试与语法/编译检查执行结果
   - 发现的问题（如旧文件未清理等）
5. **明确告知**：「编码完成，现在进入 CR 扫描」，然后**立刻启动** code-reviewer（不等用户操作）

**⚠️ 编码完成后必须进入 CR 扫描（stage-4.2-cr.md），这是不可跳过的必经步骤。** auto_advance 不在此处生效——auto_advance 的触发点是任务 DONE（⑥复验回写完成）之后，不是编码完成之后。编码 → CR → 裁决 → 改写 → 复验 → DONE 的完整闭环不可压缩。

编码完成后，**逐任务**进入 CR 扫描（详见 `stage-4.2-cr.md`）；多个并行任务各自生成独立 CR 报告，依次过人工门。

## ⑥ 复验与进度回写（强制，做完才算 DONE，缺一不可）
确认已采纳问题均已修复、模块级单测通过 + 语法/编译检查通过后，主 Agent **必须立刻**在进入下一个任务前完成以下三处回写：
1. **dev-tasks.md（第一优先）**：读取 dev-tasks.md，确认该任务下所有子项 `[ ]` 均已勾成 `[x]`（executor/改写 executor 漏勾的由主 Agent 补勾）。**这是最常遗漏的步骤，必须第一个做。**
2. **progress.md 任务清单**：把该任务状态行更新为 `DONE`，`[ ]` 勾成 `[x]`
3. **progress.md 里程碑进度表**：把该里程碑的「任务进度」计数 +1（如 `2/9 → 3/9`）；若该里程碑所有任务 DONE，再更新其阶段为「5 收尾验收」就绪

**自检：如果你只更新了 progress.md 而没有更新 dev-tasks.md，说明你漏了第 1 步，立刻补上。两个文件的状态必须一致。**

> **回写是阻塞步骤**：未完成上述三处回写，不得开始下一个任务/下一波。每个**中间状态**变化（CODING / CR_SCANNED / CR_CONFIRMED / REWRITING）也要即时写回 progress.md 任务状态行，保证 `/devops-workflow status` 任何时刻反映真实进度。

### 回写完成后——自动流转

> 按 automation.md「auto_advance 协议」处理：auto_advance=true 时自动取下一个 TODO 任务或自动进入阶段 5 验收，否则提示 `/devops-workflow next`。

## 关键规则
- **复杂任务编码前必须出 plan 并人工确认**：简单任务对照 design-consensus 直接编码；复杂任务先 architect/planner 出 LLD → 人工 approve → 才编码。拿不准按复杂处理（详见 `stage-4.1-plan.md`）
- **编码并行/串行由 Claude 判断**：并行仅限互不依赖、模块目录不重叠的任务；有依赖的按波次串行，前序产出（接口/Event 契约）注入后续 prompt
- **CR 门永远逐任务**：无论编码是否并行，CR 扫描、人工确认、改写都是一个任务一份、一个一个过，绝不合并、绝不跳过（详见 `stage-4.2-cr.md`）
- 编码、CR、改写各自独立 agent，CR 与编码不共享上下文
- **CR 问题不经人工确认，绝不改写**；code-reviewer 永远只产出清单，改写永远是另一个 executor 按人工采纳清单执行
- 被 REJECTED 的问题不得改动；被 MODIFIED 的按人工说明改
- **进度即时回写（强制）**：每次状态变化都立刻写回 progress.md 任务状态行 + 里程碑进度表计数，并同步 dev-tasks.md 子项勾选；回写未完成不得推进下一个任务。`progress.md` 是任务**状态**权威源，`dev-tasks.md` 勾选是**细粒度子项**清单，两者必须一致
- 全部任务 DONE 后：auto_advance=true 自动进阶段 5；否则提示 `/devops-workflow next`
