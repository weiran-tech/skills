# 阶段 4：CR 扫描与裁决（PENDING_CR_REVIEW）

> 编码完成后进入 CR 扫描时读本文件。CR 门永远逐任务，不合并、不跳过。

**工单目录基准**：`{讨论根目录}{域}/{需求名}/.task/`。本文件中所有 `.task/` 路径均相对于此。

## ③ CR 扫描（编码完成后，单 code-reviewer，与编码不共享上下文）
**注意：code-reviewer 只产出问题清单，绝不直接改代码、绝不下达修复指令。**
```
code-reviewer "
审查任务 [{模块名} · {任务标题}] 在当前分支上的实际代码变更：
1. 执行 git diff <默认分支>...HEAD -- {任务工作范围目录} 获取该任务的变更内容
2. 读取 .task/done/{模块名}.md 与 .task/design-consensus.md 了解任务意图与契约
3. 读取 docs/{模块名}/ 了解该模块既有契约与业务规则
4. 基于实际变更审查：与设计/任务一致性、逻辑正确性、单测覆盖、跨模块契约一致性、是否符合 CLAUDE.md 与 .claude/rules/
5. 把问题写入 .task/review/{模块名}-{X.Y}.md，**严格按照下方示例格式**输出（逐字段对齐，不要自创格式）：

   ## 问题清单

   ### [1] 严重度: MAJOR — 实现与设计不一致：终态使用 STATUS_CANCEL 而非 STATUS_EXPIRE

   - 文件: `{实际文件路径}:{行号}`
   - 问题: 设计共识 §2.3 约定超时终态为 STATUS_EXPIRE，但实际代码使用了 STATUS_CANCEL，导致与退款回调的状态判断冲突。
   - 建议: 将 STATUS_CANCEL 改为 STATUS_EXPIRE，并同步更新对应单测断言。
   - 裁决: PENDING

   ### [2] 严重度: MINOR — 日志缺少关键字段

   - 文件: `{实际文件路径}:{行号}`
   - 问题: 异常分支的日志输出未包含关键业务标识，线上排查时无法关联到具体业务。
   - 建议: 在日志 context 中追加关键业务字段。
   - 裁决: PENDING

   末尾留一个『人工裁决』区，等待人工填写。不要给出『已修复』或自动修改任何代码。

审查必须基于实际代码变更，不做脱离代码的通用检查。
写入 review 文件必须使用 Write 工具，禁止用 Bash heredoc/echo 写文件。
Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"
```

### ★ CR 子 agent 返回后，主 Agent 必须立刻执行以下动作（缺一不可，禁止静默结束本轮）

> **这是最容易"卡住"的地方**——子 agent 跑完 ≠ 流程推进。子 agent 一返回，主 Agent 就要主动读报告、回写状态、把摘要和下一步指令打给用户。

1. **读取** code-reviewer 写出的报告 `.task/review/{范围标签}-{X.Y}.md`（子 agent 的返回文本不算数，以报告文件为准）
2. **回写** progress.md：把该任务状态置 `CR_SCANNED`
3. **按 `auto_cr_minor` 协议分流**（读取 `.workflow-config`，不存在视为 false）：

   **A. `auto_cr_minor=true` 时自动分流：**
   - **零问题**：自动置 CR_CONFIRMED，输出「CR 通过，无问题项，自动确认」→ 直接进入复验⑥
   - **全部 MINOR**：全部自动裁决为 ACCEPTED，在 review 文件中标注「auto_cr_minor: ACCEPTED」，自动置 CR_CONFIRMED，输出「auto_cr_minor: {N} 个 MINOR 问题已自动 ACCEPTED」→ 自动派 executor 改写⑤ → 复验⑥
   - **含 MAJOR**：进入人工门（走下方 B 流程）

   **B. `auto_cr_minor=false`（默认）或含 MAJOR 问题时：**
   - 回写需求/里程碑状态为 `PENDING_CR_REVIEW`
   - **向用户输出**（无论有无问题都必须输出，不许停在这一步不吭声）：
     - **有问题**：逐条列出 `#编号 [严重度] 文件:行 — 一句话问题`，然后明确提示：
       ```
       请逐条裁决每个问题：ACCEPTED（要改）/ REJECTED（不改）/ MODIFIED（改法调整）
       裁决完成后执行 /devops-workflow approve 推进
       ```
     - **零问题（PASSED）**：输出「CR 通过，无问题项，无需裁决」，然后明确提示：
       ```
       执行 /devops-workflow approve 确认并进入复验/勾选
       ```
   - **停在 PENDING_CR_REVIEW 等待用户**，不自动进入改写

**自检：如果走人工门路径，你的输出中没有包含 `/devops-workflow approve` 这个字符串，说明你漏了提示，立刻补上。**

## ④ 人工确认门（PENDING_CR_REVIEW）
- 用户逐条裁决每个问题：`ACCEPTED`（要改）/ `REJECTED`（不改，附理由）/ `MODIFIED`（改法调整，附说明）
- 裁决方式二选一：直接在 `.task/review/{范围标签}-{X.Y}.md` 的『人工裁决』区标注，或口头告知由主 Agent 回填
- 全部裁决完成后，用户执行 `/devops-workflow approve`（多里程碑加 `#里程碑`）锁定裁决；主 Agent 据此把任务状态置 **CR_CONFIRMED**
- **零问题 / 全部 REJECTED**（无需改写）→ `approve` 直接跳过改写⑤，进入复验⑥与勾选
- **⚠️ 只有用户显式输入 `/devops-workflow approve` 才算裁决锁定。** 用户口头说裁决结果（如"1 接受 2 拒绝"）是在提供裁决信息，主 Agent 应回填到 review 文件，但**不得自动推进到改写**，必须等 `/devops-workflow approve`。
- `auto_cr_minor=true` 自动裁决的结果，用户可通过 `/devops-workflow rework` 推翻。

### ★ CR 裁决后同步 design-consensus（防止设计漂移）
CR approve 后、改写开始前，主 Agent **必须检查**裁决为 MODIFIED 的问题是否涉及 design-consensus 层面的契约变更（接口签名、状态码、事件名、数据模型等）。如果有：
1. 在 design-consensus.md 末尾追加 `## CR 同步 [{X.Y} {模块名} · {任务标题}]`，记录变更项（原契约 → 新契约 + 变更原因，引用 CR 问题编号）
2. 向用户输出同步摘要：「CR 裁决的以下 MODIFIED 项调整了 design-consensus 契约：{列表}，已同步回 design-consensus.md」

> 仅 MODIFIED 项需要检查；ACCEPTED 项是"设计对、改小问题"，不影响契约层。

## ⑤ 改写（仅改已采纳项，单 executor）
```
executor "
按已确认的审查裁决修复任务 [{范围标签} · {任务标题}]，工作范围限定在该任务的工作范围目录（见 dev-tasks.md）：
只处理 .task/review/{模块名}-{X.Y}.md 中裁决为 ACCEPTED / MODIFIED 的问题（REJECTED 的不动）。
逐条修复后在该问题下标注『已修复』并简述改动。
修复后按项目 .claude/rules/ 中定义的测试命令重跑模块级单测，并按项目规则执行语法/编译检查确认通过，把 dev-tasks.md 中剩余已完成子项 [ ] 勾成 [x]。
遵守 CLAUDE.md 架构规则。Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"
```

## ⑥ 复验与进度回写（强制，做完才算 DONE，缺一不可）

确认已采纳问题均已修复、模块级单测通过 + 语法/编译检查通过后：
1. **dev-tasks.md（第一优先）**：确认该任务下所有子项 `[ ]` 均已勾成 `[x]`（漏勾的由主 Agent 补勾）
2. **progress.md 任务清单**：任务状态 → `DONE`，`[ ]` → `[x]`
3. **progress.md 里程碑进度表**：任务进度计数 +1

> **回写是阻塞步骤**：未完成回写不得开始下一个任务。

### 回写完成后——自动流转

> 按 automation.md「auto_advance 协议」处理：auto_advance=true 时自动取下一个 TODO 任务或自动进入阶段 5 验收，否则提示 `/devops-workflow next`。
