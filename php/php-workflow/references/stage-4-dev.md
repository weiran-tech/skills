# 阶段 4：开发与逐任务审查（DEVELOPING）

> 执行阶段 4 / 处理 `/php-workflow approve` 的 plan 或 CR 分支前读本文件。产出物根路径见 templates.md。

**核心原则：每任务即审、CR 问题人工确认后才改写。编码是否并行由 Claude 自行判断；CR 人工门永远逐任务。** 任务 = dev-tasks.md 中一个可独立交付的工作项（通常一个模块的一组改动）。无独立分支，全部在当前 feature 分支推进。

### ★★ 子 agent 返回后通用协议（适用于 executor / code-reviewer / architect 等所有子 agent）

**每个子 agent 返回后，主 Agent 必须立刻完成以下四步，缺一不可，禁止静默结束本轮：**

1. **读产出**：读取子 agent 写出的产出文件（以文件为准，不以子 agent 返回文本为准）
2. **回写状态**：更新 metadata.md 任务状态行
3. **向用户输出结果摘要**：简述产出内容（编码改了什么 / CR 扫出几条 / plan 要点等）
4. **明确告知下一步**：用户该执行什么命令（`/php-workflow approve` / `/php-workflow next`），或主 Agent 将自动执行什么

**违反此协议的典型表现**：子 agent 跑完后只更新了 metadata.md 就结束、或只说"已完成"但不展示结果、或不告诉用户下一步该做什么。这些都是 BUG。

## 编码并行 vs 串行——由 Claude 判断

阶段 4 启动时，Claude 读取 dev-tasks.md 的任务依赖图，自行决定**编码**用并行还是串行，并把决策与理由记到 metadata.md。判断准则：

- **倾向并行**：存在 ≥2 个**互不依赖**、且**目录不重叠**（`modules/{模块}/` 不重叠，无文件冲突）的子需求，并行能明显省时。并行时用 `team {N}:executor`，每个 executor 工作范围限定在自己的子需求目录与对应模块。
- **倾向串行**：子需求之间有依赖链、共享同一模块/文件、子需求很少或很小、或并行收益不明显。串行时用单个 `executor`，一次一个。
- **混合**：常见做法是按"波次"组织——同一波内**互不依赖**的子需求并行编码（满足"互不依赖 + `modules/{模块}/` 不重叠"两个条件），波与波之间按依赖串行；有依赖的子需求把前序产出（接口/Event 契约）注入 prompt。

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
为子需求 [{域}/{父需求名}#{子需求名} · {任务标题}] 产出任务级详细设计（LLD），写入 docs/discuss/{域}/{父需求名}/.task/{子需求名}/plans/{任务序号}-{模块名}.md。
依据：design-consensus.md（契约/边界/决策）、docs/workflow/{模块名}/、相关现有代码。
必含：
1. 类与方法签名（精确到参数/返回类型）
2. 数据模型字段 + 类型（如有迁移，列字段/索引/默认值）
3. 调用时序 / 与现有代码的集成点（在哪些 Action/Service/Event 接入）
4. 错误与边界处理
5. 要写的测试用例清单（用例名 + 覆盖点）
6. 迁移/回滚（如涉及）
只做设计，不写业务代码。Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"
```
### ★ architect/planner 返回后，主 Agent 必须立刻执行以下动作（缺一不可，禁止静默结束本轮）
1. **确认文件已落盘**：检查 `docs/discuss/{域}/{父需求名}/.task/{子需求名}/plans/{任务序号}-{模块名}.md` 是否存在且有内容。如果 architect 只在对话中输出了 plan 但没写文件，主 Agent **必须手动将 plan 内容写入该文件**
2. **回写** metadata.md：把该任务状态置 `PLANNING` → `PENDING_PLAN_REVIEW`
3. **向用户输出 plan 摘要**：列出关键设计点（类/方法签名、数据模型、调用时序、测试用例清单）
4. **明确告知**：
   ```
   plan 已保存到 docs/discuss/{域}/{父需求名}/.task/{子需求名}/plans/{文件名}
   请审阅后执行 /php-workflow approve 确认，或指出需要调整的地方
   ```

plan 不达标（缺项/方向问题）→ 打回重出，不进编码。确认后置 **PLAN_CONFIRMED** 再编码。

### ① 编码（并行示例：同波无依赖子需求用 team；串行则换成单个 executor）
```
# 并行（同一波内互不依赖、modules/{模块}/ 不重叠的子需求）
/oh-my-claudecode:team {N}:executor "
本波任务（互不依赖，按子需求隔离、modules/{模块}/ 互不重叠）：
{对本波每个子需求生成一行}
- 子需求 [{域}/{父需求名}#{子需求名}] executor: 工作范围限定在 docs/discuss/{域}/{父需求名}/.task/{子需求名}/ 与 modules/{模块}/
  任务: {从 dev-tasks.md 提取}
  {复杂任务：注入已确认的 plan 路径 docs/discuss/{域}/{父需求名}/.task/{子需求名}/plans/{任务序号}-{模块名}.md，严格对照实现；简单任务：对照 design-consensus 实现要点}
  {若依赖前序波次，注入 docs/discuss/{域}/{父需求名}/.task/{子需求名}/done/{前序模块}.md 中的接口/Event 契约}
  DoD: 写代码 + 写单测 + vendor/bin/phpunit modules/{模块}/tests 绿 + 对改动文件执行 php -l 语法校验通过
  完成后：① 把本任务在 dev-tasks.md 中已完成的子项 [ ] 勾成 [x]；② 写入 docs/discuss/{域}/{父需求名}/.task/{子需求名}/done/{模块名}.md（改动摘要、对外接口/Event 契约、phpunit 与 php -l 结果）

遵守项目 CLAUDE.md 与 .claude/rules/ 的架构与编码规范。
Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"

# 串行时：去掉 team，对单个子需求起一个 executor，内容同上（仅一行任务）。
```

### ★ executor 编码返回后，主 Agent 必须立刻执行以下动作（缺一不可，禁止静默结束本轮）
1. **读取** executor 写出的完成报告 `docs/discuss/{域}/{父需求名}/.task/{子需求名}/done/{模块名}.md`（以文件为准）
2. **回写** metadata.md：把该子需求任务状态置 `CODING`（如尚未置）
3. **向用户输出**：
   - 改动摘要（改了哪些文件/类、新增了什么）
   - phpunit / php -l 执行结果
   - 发现的问题（如旧文件未清理等）
4. **明确告知**：「编码完成，现在进入 CR 扫描」，然后**立刻启动** code-reviewer（不等用户操作）

编码完成后，**逐任务**进入 CR 扫描；多个并行任务各自生成独立 CR 报告，依次过人工门。

### ③ CR 扫描（编码完成后，单 code-reviewer，与编码不共享上下文）
**注意：code-reviewer 只产出问题清单，绝不直接改代码、绝不下达修复指令。**
```
code-reviewer "
审查子需求 [{域}/{父需求名}#{子需求名} · {任务标题}] 在当前分支上的实际代码变更：
1. 执行 git diff <默认分支>...HEAD -- modules/{模块名} 获取该模块变更内容
2. 读取 docs/discuss/{域}/{父需求名}/.task/{子需求名}/done/{模块名}.md 与 .task/design-consensus.md 了解任务意图与契约
3. 读取 docs/workflow/{模块名}/ 了解该模块既有契约与业务规则
4. 基于实际变更审查：与设计/任务一致性、逻辑正确性、单测覆盖、跨模块契约一致性、是否符合 CLAUDE.md 与 .claude/rules/
5. 把问题整理成**编号清单**写入 docs/discuss/{域}/{父需求名}/.task/{子需求名}/review/{模块名}-{任务序号}.md，每条含：编号 / 严重度(critical|major|minor) / 文件:行 / 问题描述 / 建议改法 / 裁决:PENDING
   末尾留一个『人工裁决』区，等待人工填写。不要给出『已修复』或自动修改任何代码。

审查必须基于实际代码变更，不做脱离代码的通用检查。
Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"
```

### ★ CR 子 agent 返回后，主 Agent 必须立刻执行以下动作（缺一不可，禁止静默结束本轮）

> **这是最容易"卡住"的地方**——子 agent 跑完 ≠ 流程推进。子 agent 一返回，主 Agent 就要主动读报告、回写状态、把摘要和下一步指令打给用户。

1. **读取** code-reviewer 写出的报告 `docs/discuss/{域}/{父需求名}/.task/{子需求名}/review/{模块名}-{任务序号}.md`（子 agent 的返回文本不算数，以报告文件为准）
2. **回写** metadata.md：把该子需求任务状态置 `CR_SCANNED`，子需求状态置 `PENDING_CR_REVIEW`
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
- 裁决方式二选一：直接在 `docs/discuss/{域}/{父需求名}/.task/{子需求名}/review/{模块名}-{任务序号}.md` 的『人工裁决』区标注，或口头告知由主 Agent 回填
- 全部裁决完成后，用户执行 `/php-workflow approve`（多子需求加 `#子需求ID`）锁定裁决；主 Agent 据此把任务状态置 **CR_CONFIRMED**
- **零问题 / 全部 REJECTED**（无需改写）→ `approve` 直接跳过改写⑤，进入复验⑥与勾选

### ⑤ 改写（仅改已采纳项，单 executor）
```
executor "
按已确认的审查裁决修复子需求 [{域}/{父需求名}#{子需求名} · {任务标题}]，工作范围 modules/{模块名}/ 与 docs/discuss/{域}/{父需求名}/.task/{子需求名}/：
只处理 docs/discuss/{域}/{父需求名}/.task/{子需求名}/review/{模块名}-{任务序号}.md 中裁决为 ACCEPTED / MODIFIED 的问题（REJECTED 的不动）。
逐条修复后在该问题下标注『已修复』并简述改动。
修复后重跑 vendor/bin/phpunit modules/{模块名}/tests 与对改动文件 php -l 确认通过，并把 dev-tasks.md 中剩余已完成子项 [ ] 勾成 [x]。
遵守 CLAUDE.md 架构规则。Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"
```

### ⑥ 复验与进度回写（强制，做完才算 DONE）
确认已采纳问题均已修复、phpunit 绿 + php -l 通过后，主 Agent **必须**在进入下一个子需求/下一波之前完成回写：
1. **metadata.md 任务清单**：把该子需求任务状态行更新为 `DONE`，`[ ]` 勾成 `[x]`
2. **dev-tasks.md**：确认该任务下所有子项 `[ ]` 均已勾成 `[x]`（executor 漏勾的补勾）
3. **版本聚合视图（如适用）**：若该子需求所属版本中所有子需求均 DONE，更新 `docs/version/{版本号}` 阶段为「5 收尾验收」就绪

> **回写是阻塞步骤**：未完成上述回写，不得开始下一个子需求/下一波。每个**中间状态**变化（CODING / CR_SCANNED / CR_CONFIRMED / REWRITING）也要即时写回 metadata.md 任务状态行，保证 `/php-workflow status` 任何时刻反映真实进度。

## 关键规则
- **复杂任务编码前必须出 plan 并人工确认**：简单任务对照 design-consensus 直接编码；复杂任务先 architect/planner 出 LLD → 人工 approve → 才编码。拿不准按复杂处理。plan 维度按**子需求**划分，每个子需求独立出 plan 与评审
- **编码并行/串行由 Claude 判断**：并行仅限两个子需求同时进入 CODING（满足"互不依赖 + 目录不重叠（`modules/{模块}/` 不重叠）"）；有依赖的按波次串行，前序产出（接口/Event 契约）注入后续 prompt
- **CR 门永远逐任务**：无论编码是否并行，CR 扫描、人工确认、改写都是一个任务一份、一个一个过，绝不合并、绝不跳过
- 编码、CR、改写各自独立 agent，CR 与编码不共享上下文
- **CR 问题不经人工确认，绝不改写**；code-reviewer 永远只产出清单，改写永远是另一个 executor 按人工采纳清单执行
- 被 REJECTED 的问题不得改动；被 MODIFIED 的按人工说明改
- **进度即时回写（强制）**：每次状态变化都立刻写回 metadata.md 任务状态行，并同步 dev-tasks.md 子项勾选；回写未完成不得推进下一个任务。`metadata.md` 是子需求**状态**权威源，`dev-tasks.md` 勾选是**细粒度子项**清单，两者必须一致
- 全部子需求 DONE 后更新 metadata.md，输出开发汇总，等待 `/php-workflow next` 进入阶段 5 收尾验收（见 stage-5-accept.md）
