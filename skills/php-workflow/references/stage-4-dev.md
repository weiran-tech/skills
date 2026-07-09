# 阶段 4：开发与逐任务审查（DEVELOPING）

> 执行阶段 4 / 处理 `/php-workflow approve` 的 plan 或 CR 分支前读本文件。产出物根路径见 templates.md。

**核心原则：每任务即审、CR 问题人工确认后才改写。编码是否并行由 Claude 自行判断；CR 人工门永远逐任务。** 任务 = dev-tasks.md 中一个可独立交付的工作项（通常一个模块的一组改动）。无独立分支，全部在当前 feature 分支推进。

### ★★ 子 agent 返回后通用协议（适用于 executor / code-reviewer / architect 等所有子 agent）

**每个子 agent 返回后，主 Agent 必须立刻完成以下四步，缺一不可，禁止静默结束本轮：**

1. **读产出**：读取子 agent 写出的产出文件（以文件为准，不以子 agent 返回文本为准）
2. **回写状态**：更新 progress.md 任务状态行 + 里程碑进度表
3. **向用户输出结果摘要**：简述产出内容（编码改了什么 / CR 扫出几条 / plan 要点等）
4. **明确告知下一步**：用户该执行什么命令（`/php-workflow approve` / `/php-workflow next`），或主 Agent 将自动执行什么

**违反此协议的典型表现**：子 agent 跑完后只更新了 progress.md 就结束、或只说"已完成"但不展示结果、或不告诉用户下一步该做什么。这些都是 BUG。

## 编码并行 vs 串行——由 Claude 判断

阶段 4 启动时，Claude 读取 dev-tasks.md 的任务依赖图，自行决定**编码**用并行还是串行，并把决策与理由记到 progress.md。判断准则：

- **倾向并行**：存在 ≥2 个**互不依赖**、且**模块目录不重叠**（无文件冲突）的任务，并行能明显省时。并行时用 `team {N}:executor`，每个 executor 工作范围限定在自己的模块目录。
- **倾向串行**：任务之间有依赖链、共享同一模块/文件、任务很少或很小、或并行收益不明显。串行时用单个 `executor`，一次一个。
- **混合**：常见做法是按"波次"组织——同一波内**无依赖**的任务并行编码，波与波之间按依赖串行；有依赖的任务把前序产出（接口/Event 契约）注入 prompt。

> 决策只针对**编码**这一步。下面的 **CR 扫描 → 人工确认 → 改写** 始终**按任务逐个进行**：即使多个任务并行编码完成，CR 报告与人工裁决也是一个任务一份、一个任务一确认，绝不合并、绝不跳过人工门。并行只是让多个任务更快到达各自的 CR_SCANNED，不改变人工门的逐任务性质。

## 编码前是否出 plan（任务级详细设计）——按复杂度判断

每个任务编码前，按 dev-tasks 标注的复杂度（或 Claude 自行评估）决定：

- **简单任务**：design-consensus 的实现要点已够开工 → 直接编码，不出 plan。
- **复杂任务**：编码前先产出**任务级详细设计（plan/LLD）**，人工确认后再编码。判断复杂的信号：跨多文件/多层、涉及核心交易或资金链路、改动既有关键流程、有并发/一致性/迁移风险、设计有未决项。
- 拿不准时按复杂处理（出 plan 比返工便宜）。

plan 是**编码前的设计评审门**：把"方向错"挡在写代码之前，比事后 CR 便宜。plan 由 `architect`/`planner` 产出（只读、不写业务代码），人工 `/php-workflow approve` 确认后才编码。

## 每个任务的闭环（含可选 plan 门）

```
TODO
 │ ⓪ 复杂度判断
 ├─ 简单 ─────────────────────────────────┐
 └─ 复杂 → 出 plan/LLD（architect/planner） │
          ▼ PLANNING                        │
          停 PENDING_PLAN_REVIEW ←人工确认门  │
          │ 人工 /php-workflow approve           │
          ▼ PLAN_CONFIRMED                   │
 ┌────────────────────────────────────────┘
 │ ① 编码（executor；简单任务对照 design-consensus，复杂任务对照已确认 plan；并行/串行由 Claude 判断）
 ▼ CODING
 │ ② DoD 自检：phpunit 绿 + php -l 语法校验通过
 │ ③ CR 扫描（单个 code-reviewer，只读，产出问题清单，不改代码）
 ▼ CR_SCANNED  ←—— 停在这里，进入【人工确认门】，状态 PENDING_CR_REVIEW（逐任务，不合并）
 │ ④ 人工逐条裁决问题（采纳 / 忽略 / 修改），裁决写回 CR 报告
 ▼ CR_CONFIRMED  ←—— 由 /php-workflow approve 确认后推进
 │ ⑤ 改写（单个 executor）：只修复「已采纳」的问题
 ▼ REWRITING
 │ ⑥ 复验：phpunit + php -l 绿，且已采纳问题确已修复
 ▼ VERIFYING → DONE（勾选 + 回写）
```

### ⓪ 复杂任务出 plan（编码前，architect/planner，只读）
```
architect "
为任务 [{模块名} · {任务标题}] 产出任务级详细设计（LLD），写入 .task/{...}/plans/{模块名}-{X.Y}.md。

**第一步：读代码建立现状认知**
1. 读 design-consensus.md 获取契约/边界/决策
2. 读 docs/workflow/{模块名}/ 获取模块架构文档
3. 如 docs/discuss/{需求ID}/docs/ 下有参考文档，读取作为需求背景
4. 读取任务涉及的现有代码文件，定位到具体类、方法、行号，理解当前实现

**第二步：产出 LLD，必含以下内容**

## 1. 改动文件清单（逐文件列出）
对每个要修改或新建的文件，列出：
- 文件路径：`modules/{模块}/src/Action/XxxAction.php`
- 操作：新建 / 修改
- 改动说明：在第 N 行的 `methodName()` 方法中，插入 xxx / 新增方法 `yyy()`
- 改动原因：对应 design-consensus 的哪条契约/决策

## 2. 改动步骤序列（按执行顺序）
逐步描述 executor 应该怎么改，每步包含：
- Step N：在 `具体文件路径` 的 `具体方法/位置`，做什么改动
- 步骤之间的依赖关系（先改 A 才能改 B）

## 3. 类与方法签名
新增/修改的类和方法，精确到参数名、类型、返回类型

## 4. 数据模型变更
如有迁移：表名、字段名、类型、索引、默认值、迁移文件路径

## 5. 集成点
与现有代码的接入位置（在哪个 Action/Service/Event 的哪一行接入），引用现有代码的实际方法名

## 6. 测试用例清单
用例名 + 覆盖点 + 测试文件路径

## 7. 错误与边界处理

## 8. 迁移/回滚（如涉及）

只做设计，不写业务代码。Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"
```
### ★ architect/planner 返回后，主 Agent 必须立刻执行以下动作（缺一不可，禁止静默结束本轮）
1. **确认文件已落盘**：检查 `.task/{...}/plans/{模块名}-{X.Y}.md` 是否存在且有内容。如果 architect 只在对话中输出了 plan 但没写文件，主 Agent **必须手动将 plan 内容写入该文件**
2. **回写** progress.md：把该任务状态置 `PLANNING` → `PENDING_PLAN_REVIEW`
3. **向用户输出 plan 摘要**：列出改动文件清单（**仅文件名，不含路径** + 操作[新建/修改] + 一句话说明）、关键改动步骤、数据模型变更、测试用例清单
4. **明确告知**：
   ```
   plan 已保存到 .task/plans/{文件名}
   请审阅后执行 /php-workflow approve 确认，或指出需要调整的地方
   ```

plan 不达标（缺项/方向问题）→ 打回重出，不进编码。确认后置 **PLAN_CONFIRMED** 再编码。

### ★ plan 确认后同步 design-consensus（防止设计漂移）
plan approve 后、编码开始前，主 Agent **必须检查** plan 是否调整了 design-consensus 中约定的内容（接口签名、数据模型、事件契约、跨模块调用等）。如果有调整：
1. 在 design-consensus.md 末尾追加 `## Plan 同步 [{X.Y} {模块名} · {任务标题}]`，记录调整项（原契约 → 新契约 + 调整原因）
2. 向用户输出同步摘要：「plan 对 design-consensus 的以下契约做了调整：{列表}，已同步回 design-consensus.md」

> **为什么要同步**：design-consensus 是阶段 5 验收的基线文档。如果 plan 调整了设计但不回写，验收时 verifier 会对照过期的契约检查代码，产生误报或漏检。

**⚠️ 人工门审批铁律（适用于所有人工门）：只有用户显式输入 `/php-workflow approve` 才算审批通过。用户的任何其他消息——包括对设计的讨论、补充要求、确认某个细节正确、甚至说"没问题"——都不等于 approve。绝不推断审批意图。用户讨论 plan 内容时，应将其视为反馈并据此调整 plan，然后继续等待 `/php-workflow approve`。**

### ① 编码（并行示例：同波无依赖任务用 team；串行则换成单个 executor）
```
# 并行（同一波内互不依赖、模块目录不重叠的任务）
/oh-my-claudecode:team {N}:executor "
本波任务（互不依赖，按模块目录隔离、互不重叠）：
{对本波每个任务生成一行}
- {模块名} executor: 工作范围限定在 modules/{模块名}/
  任务: {从 dev-tasks.md 提取}
  {复杂任务：注入已确认的 plan 路径 .task/{...}/plans/{模块名}-{X.Y}.md，严格对照实现；简单任务：对照 design-consensus 实现要点}
  {若依赖前序波次，注入 .task/done/{前序模块}.md 中的接口/Event 契约}
  DoD: 写代码 + 写单测 + vendor/bin/phpunit modules/{模块名}/tests 绿 + 对改动文件执行 php -l 语法校验通过
  完成后：① 把本任务在 dev-tasks.md 中已完成的子项 [ ] 勾成 [x]；② 写入 .task/done/{模块名}.md（改动摘要、对外接口/Event 契约、phpunit 与 php -l 结果）

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
   - phpunit / php -l 执行结果
   - 发现的问题（如旧文件未清理等）
5. **明确告知**：「编码完成，现在进入 CR 扫描」，然后**立刻启动** code-reviewer（不等用户操作）

编码完成后，**逐任务**进入 CR 扫描；多个并行任务各自生成独立 CR 报告，依次过人工门。

### ③ CR 扫描（编码完成后，单 code-reviewer，与编码不共享上下文）
**注意：code-reviewer 只产出问题清单，绝不直接改代码、绝不下达修复指令。**
```
code-reviewer "
审查任务 [{模块名} · {任务标题}] 在当前分支上的实际代码变更：
1. 执行 git diff <默认分支>...HEAD -- modules/{模块名} 获取该模块变更内容
2. 读取 .task/done/{模块名}.md 与 .task/design-consensus.md 了解任务意图与契约
3. 读取 docs/{模块名}/ 了解该模块既有契约与业务规则
4. 基于实际变更审查：与设计/任务一致性、逻辑正确性、单测覆盖、跨模块契约一致性、是否符合 CLAUDE.md 与 .claude/rules/
5. 把问题写入 .task/review/{模块名}-{X.Y}.md，**严格按照下方示例格式**输出（逐字段对齐，不要自创格式）：

   ## 问题清单

   ### [1] 严重度: MAJOR — 实现与设计不一致：终态使用 STATUS_CANCEL 而非 STATUS_EXPIRE

   - 文件: `modules/middleman/src/Action/TradeCallback/MiddlemanTradeCallbackHandler.php:L309`
   - 问题: 设计共识 §2.3 约定超时终态为 STATUS_EXPIRE，但实际代码 L309 使用了 STATUS_CANCEL，导致与退款回调的状态判断冲突。
   - 建议: 将 L309 的 STATUS_CANCEL 改为 STATUS_EXPIRE，并同步更新对应单测断言。
   - 裁决: PENDING

   ### [2] 严重度: MINOR — 日志缺少 tradeNo 字段

   - 文件: `modules/middleman/src/Action/TradeCallback/MiddlemanTradeCallbackHandler.php:L245`
   - 问题: 异常分支的日志输出未包含 tradeNo，线上排查时无法关联到具体交易。
   - 建议: 在 L245 的 log context 中追加 `'tradeNo' => $order->trade_no`。
   - 裁决: PENDING

   末尾留一个『人工裁决』区，等待人工填写。不要给出『已修复』或自动修改任何代码。

审查必须基于实际代码变更，不做脱离代码的通用检查。
Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"
```

### ★ CR 子 agent 返回后，主 Agent 必须立刻执行以下动作（缺一不可，禁止静默结束本轮）

> **这是最容易"卡住"的地方**——子 agent 跑完 ≠ 流程推进。子 agent 一返回，主 Agent 就要主动读报告、回写状态、把摘要和下一步指令打给用户。

1. **读取** code-reviewer 写出的报告 `.task/review/{模块名}-{X.Y}.md`（子 agent 的返回文本不算数，以报告文件为准）
2. **回写** progress.md：把该任务状态置 `CR_SCANNED`，需求/里程碑状态置 `PENDING_CR_REVIEW`
3. **向用户输出**（无论有无问题都必须输出，不许停在这一步不吭声）：
   - **有问题**：逐条列出 `#编号 [严重度] 文件:行 — 一句话问题`，然后明确提示：
     ```
     请逐条裁决每个问题：ACCEPTED（要改）/ REJECTED（不改）/ MODIFIED（改法调整）
     裁决完成后执行 /php-workflow approve 推进
     ```
   - **零问题（PASSED）**：输出「CR 通过，无问题项，无需裁决」，然后明确提示：
     ```
     执行 /php-workflow approve 确认并进入复验/勾选
     ```
4. **停在 PENDING_CR_REVIEW 等待用户**，不自动进入改写

**自检：如果你的输出中没有包含 `/php-workflow approve` 这个字符串，说明你漏了第 3 步，立刻补上。**

### ④ 人工确认门（PENDING_CR_REVIEW）
- 用户逐条裁决每个问题：`ACCEPTED`（要改）/ `REJECTED`（不改，附理由）/ `MODIFIED`（改法调整，附说明）
- 裁决方式二选一：直接在 `.task/review/{模块名}-{X.Y}.md` 的『人工裁决』区标注，或口头告知由主 Agent 回填
- 全部裁决完成后，用户执行 `/php-workflow approve`（多里程碑加 `#里程碑`）锁定裁决；主 Agent 据此把任务状态置 **CR_CONFIRMED**
- **零问题 / 全部 REJECTED**（无需改写）→ `approve` 直接跳过改写⑤，进入复验⑥与勾选
- **⚠️ 只有用户显式输入 `/php-workflow approve` 才算裁决锁定。** 用户口头说裁决结果（如"1 接受 2 拒绝"）是在提供裁决信息，主 Agent 应回填到 review 文件，但**不得自动推进到改写**，必须等 `/php-workflow approve`。

### ★ CR 裁决后同步 design-consensus（防止设计漂移）
CR approve 后、改写开始前，主 Agent **必须检查**裁决为 MODIFIED 的问题是否涉及 design-consensus 层面的契约变更（接口签名、状态码、事件名、数据模型等）。如果有：
1. 在 design-consensus.md 末尾追加 `## CR 同步 [{X.Y} {模块名} · {任务标题}]`，记录变更项（原契约 → 新契约 + 变更原因，引用 CR 问题编号）
2. 向用户输出同步摘要：「CR 裁决的以下 MODIFIED 项调整了 design-consensus 契约：{列表}，已同步回 design-consensus.md」

> 仅 MODIFIED 项需要检查；ACCEPTED 项是"设计对、改小问题"，不影响契约层。

### ⑤ 改写（仅改已采纳项，单 executor）
```
executor "
按已确认的审查裁决修复任务 [{模块名} · {任务标题}]，工作范围 modules/{模块名}/：
只处理 .task/review/{模块名}-{X.Y}.md 中裁决为 ACCEPTED / MODIFIED 的问题（REJECTED 的不动）。
逐条修复后在该问题下标注『已修复』并简述改动。
修复后重跑 vendor/bin/phpunit modules/{模块名}/tests 与对改动文件 php -l 确认通过，并把 dev-tasks.md 中剩余已完成子项 [ ] 勾成 [x]。
遵守 CLAUDE.md 架构规则。Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"
```

### ★ ⑥ 复验与进度回写（强制，做完才算 DONE，缺一不可）
确认已采纳问题均已修复、phpunit 绿 + php -l 通过后，主 Agent **必须立刻**在进入下一个任务前完成以下三处回写：
1. **dev-tasks.md（第一优先）**：读取 dev-tasks.md，确认该任务下所有子项 `[ ]` 均已勾成 `[x]`（executor/改写 executor 漏勾的由主 Agent 补勾）。**这是最常遗漏的步骤，必须第一个做。**
2. **progress.md 任务清单**：把该任务状态行更新为 `DONE`，`[ ]` 勾成 `[x]`
3. **progress.md 里程碑进度表**：把该里程碑的「任务进度」计数 +1（如 `2/9 → 3/9`）；若该里程碑所有任务 DONE，再更新其阶段为「5 收尾验收」就绪

**自检：如果你只更新了 progress.md 而没有更新 dev-tasks.md，说明你漏了第 1 步，立刻补上。两个文件的状态必须一致。**

> **回写是阻塞步骤**：未完成上述三处回写，不得开始下一个任务/下一波。每个**中间状态**变化（CODING / CR_SCANNED / CR_CONFIRMED / REWRITING）也要即时写回 progress.md 任务状态行，保证 `/php-workflow status` 任何时刻反映真实进度。

## 关键规则
- **复杂任务编码前必须出 plan 并人工确认**：简单任务对照 design-consensus 直接编码；复杂任务先 architect/planner 出 LLD → 人工 approve → 才编码。拿不准按复杂处理
- **编码并行/串行由 Claude 判断**：并行仅限互不依赖、模块目录不重叠的任务；有依赖的按波次串行，前序产出（接口/Event 契约）注入后续 prompt
- **CR 门永远逐任务**：无论编码是否并行，CR 扫描、人工确认、改写都是一个任务一份、一个一个过，绝不合并、绝不跳过
- 编码、CR、改写各自独立 agent，CR 与编码不共享上下文
- **CR 问题不经人工确认，绝不改写**；code-reviewer 永远只产出清单，改写永远是另一个 executor 按人工采纳清单执行
- 被 REJECTED 的问题不得改动；被 MODIFIED 的按人工说明改
- **进度即时回写（强制）**：每次状态变化都立刻写回 progress.md 任务状态行 + 里程碑进度表计数，并同步 dev-tasks.md 子项勾选；回写未完成不得推进下一个任务。`progress.md` 是任务**状态**权威源，`dev-tasks.md` 勾选是**细粒度子项**清单，两者必须一致
- 全部任务 DONE 后更新 progress.md，输出开发汇总，等待 `/php-workflow next` 进入阶段 5 收尾验收（见 stage-5-accept.md）
