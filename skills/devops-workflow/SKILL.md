---
name: devops-workflow
description: 单体多模块项目的需求开发全流程编排。状态机驱动，自动调度 discuss、arch-analyzer、team、code-reviewer 等 skill/agent，串联需求讨论到代码审查的 5 个阶段。当用户说 "devops-workflow"、"开发流程"、"需求流程"、"模块开发流程" 时触发。
---

# DevOps Workflow — 单体多模块需求开发全流程编排

## 目录约定

> 修改顶级目录时只改这里，全文及 reference 文件中的路径同步全局替换即可。

- **{讨论根目录}** = `docs/discuss/` — 需求讨论、设计、任务工单的存放根目录

状态机驱动的流程 skill：5 个开发阶段串成统一入口，按 `progress.md` 的当前状态决定下一步调度什么 agent。本文件是**路由器 + 常驻安全规则**；各步骤的执行细节按需读取 `references/`（见末尾索引）。

面向单体项目（PHP 多模块 / Java DDD 多模块 / 单模块等）：代码同仓，审查按任务工作范围过滤 diff（`git diff <默认分支>...HEAD -- {工作范围目录}`），架构上下文来自项目文档目录（arch-analyzer 产出）。测试/校验命令由项目 `.claude/rules/` 中的规则定义（如 `unit-test-conventions.md`），workflow 不硬编码具体命令和目录结构。

## 总体流程

```
1 需求讨论 → 2 分析与设计 →[★阶段3 设计审核门]→ 4 开发与逐任务审查 → 5 收尾验收 →[★阶段5 验收确认门]→ COMPLETED
  (start)     (next: analyst+ralph)  (approve)    (next: 逐任务闭环)      (next: verifier)    (approve)
                                                        │
  阶段4 逐任务闭环：⓪复杂度判断（简单/普通/复杂）
    简单（skip_cr=true）：①编码 → ②DoD → DONE
    普通：①编码 → ②DoD → ③CR扫描 →[★CR人工门(+同步design)]→ ⑤改写 → ⑥复验+回写 → DONE
    复杂：[★plan门(+同步design)]→ ①编码 → ②DoD → ③CR扫描 →[★CR人工门(+同步design)]→ ⑤改写 → ⑥复验+回写 → DONE
  ※ 阶段 4/5 发现设计/需求层缺陷 → /devops-workflow rework 按根因层级回退 + 依赖级联重做
```

四道人工门（均由 `/devops-workflow approve` 按状态分发）：**阶段3 设计审核** / **阶段4 复杂任务 plan** / **阶段4 CR 问题裁决** / **阶段5 验收问题裁决**。

## 命令速查

```
/devops-workflow use [需求ID][#里程碑]        # 设定活动上下文，之后裸命令默认作用于它（粘性，推荐）
/devops-workflow start {需求名}              # 创建需求，进入阶段 1 讨论
/devops-workflow next [需求ID]               # 执行下一阶段 / 下一个任务（省略=活动上下文）
/devops-workflow approve [需求ID]            # 确认当前人工门（阶段3设计 / 阶段4 plan / 阶段4 CR）
/devops-workflow status [需求ID]             # 查看进度（省略=活动上下文+高亮；无活动则全部）
/devops-workflow list                        # 列出未完成的需求
/devops-workflow split [需求ID] {里程碑列表}  # 把大需求拆成多个里程碑（仅大需求需要）
/devops-workflow rework [需求ID]             # 设计/实现缺陷返工：按根因层级回退并级联重做
/devops-workflow followup {已完成需求ID} [新需求名]  # 基于已完成需求发起新需求（继承设计上下文）
/devops-workflow summary [需求ID]            # 产出交付清单（DDL / Job·MQ / API）给 DBA 与前端
/devops-workflow config                      # 查看/初始化/更新 .workflow-config 配置（缺失项自动补全）
```

- **需求 ID** = `{YYYY-MM-DD}-{域}-{需求名}`（如 `2026-09-12-order-订单取消优化`）
- **`#里程碑`** 仅多里程碑需求需要（如 `2026-09-12-payment-支付渠道重构#alipay`）；未 `split` 的需求是单里程碑，无需 `#`
- `followup` 用于需求 COMPLETED 后追加功能/优化：创建新需求，自动继承父需求的设计文档作为参考
- 命令的详细处理逻辑见 `references/commands.md`

### 流程配置（.workflow-config）

`{讨论根目录}.workflow-config` 控制流程行为（项目级，所有需求共享）。不存在则全部走手动，向后兼容。

```
auto_advance=true       # 阶段/任务完成后自动推进，不等 /devops-workflow next
auto_accept_pass=true   # 验收零问题自动 COMPLETED，不停门
```

各配置项的完整协议定义见 `references/automation.md`。各 stage 文件统一引用该协议，不重复定义。

### 强制前置（每个子命令执行前必须做）

1. **读取** `{讨论根目录}.workflow-active`（`cat` 或 Read）→ 若文件存在且非空，将其内容设为当前活动上下文
2. 若文件不存在且命令需要需求 ID → 走旧回退规则（唯一进行中自动选中；多个列出让选；无则提示 `start`）
3. **禁止跳过此步骤**——不得在未读取该文件的情况下声称"没有活跃的 workflow 流程"

### 活动上下文（避免每步重复输入长 ID）

像 git 当前分支：`/devops-workflow use` 选一次"当前在搞哪个需求/里程碑"，之后 `next/approve/status/rework` 省略参数即默认作用于它。
- 活动指针存于 `{讨论根目录}.workflow-active`（单行 `{需求ID}[#里程碑]`，全局唯一，**便捷指针非状态源**）
- 解析优先级：**显式参数 > 活动指针 > 旧回退**（唯一在跑自动选/多个列出）；支持前缀子串模糊匹配（`trade#共` 即定位）
- **里程碑粘住**：多里程碑下，里程碑只需指定一次（`use trade#共享基础`）；指针只有需求时，首次 `next` 解析出里程碑会写回指针粘住，之后裸命令不必再带 `#`。切里程碑用 `use #{里程碑}`。详见 commands.md
- `start`/`split` 会自动设活动指针；显式传 ID 可临时操作别的需求而不动指针

## 任务编号与产出物命名（强制）

任务统一使用 **`X.Y`** 格式编号（X=任务组, Y=组内子任务，从 1 起始）。禁止 T1、0.1、波次1、T5R 等非标格式。

编号在阶段 2 产出 dev-tasks.md 时确定，全流程所有产出物文件名必须引用同一编号：

| 产出物 | 文件名 |
|--------|--------|
| progress.md 任务行 | `{X.Y} {模块名} · {任务标题}` |
| plan | `.task/plans/{模块名}-{X.Y}.md` |
| done 报告 | `.task/done/{模块名}-{X.Y}.md` |
| CR 报告 | `.task/review/{模块名}-{X.Y}.md` |

## 项目约定

- **单体仓库**：默认已在项目仓库根目录。产出物存于 `{讨论根目录}{域}/{需求名}/.task/`（目录结构见 `references/templates.md`）
- **需求级参考文档**：`{讨论根目录}{域}/{需求名}/docs/`，用户在 `/devops-workflow start` 时放入（业务说明、接口文档、原始需求材料等），阶段 2 分析和阶段 4 编码时 agent 会读取
- **项目规则前置（强制）**：workflow 启动前，项目必须已有 `.claude/rules/` 目录（由 `arch-rules` 生成）。如果缺失，提示用户先执行 `arch-rules` 生成项目规则，不允许在无规则的项目上跑 workflow
- **工作范围**：每个任务在 dev-tasks.md 中标注工作范围目录（一个或多个），由阶段 2 analyst 确定。executor / code-reviewer / verifier 均以此为工作边界，不假设特定目录结构
- **架构文档** `docs/{模块名}/`（overview/business/contracts/flows）+ `docs/cross-module.md`（或 `docs/cross-service-guide.md`），由 `arch-analyzer` 产出；缺失则先提示跑 arch-analyzer
- **验收基线（强制）**：按项目 `.claude/rules/` 中定义的测试命令执行模块级单测通过 + 按项目规则执行语法/编译检查通过
- **静态分析**：是否纳入 DoD/验收由项目 `.claude/rules/` 决定，workflow 不强制
- **单仓库单分支**：所有模块共用一条 feature 分支，无独立分支/PR；具体命令按项目配置

## Agent 权限与职责分离

| 阶段 | 执行方式 | 权限 |
|------|---------|------|
| 2 模块分析 | `arch-analyzer` 或 `analyst` | 只读 |
| 4 任务详细设计（仅复杂任务） | `architect` / `planner` | 只读（只设计不写码）|
| 4 编码 | `executor`（并行 `team`/串行单个，Claude 判断） | 读写 |
| 4 CR 扫描（逐任务） | 单个 `code-reviewer` | 只读（只产清单不改码）|
| 4 改写（逐任务） | 单个 `executor` | 读写（只改已采纳项）|
| 5 收尾验收 | `verifier` | 只读 |

人工门：阶段3 设计审核、阶段4 plan 确认、阶段4 CR 裁决、阶段5 验收问题裁决。

---

## 关键不变量（必须遵守，不随阶段文件加载与否而改变）

1. **子 agent 返回 ≠ 流程推进（防卡死）**：每次子 agent（analyst/architect/code-reviewer/executor/verifier）返回后，主 Agent **必须立刻**：① 读取其产出文件（不以子 agent 的返回文本为准）→ ② 回写 progress.md 对应状态 → ③ 向用户输出结果摘要 + **明确的下一步指令**（该 approve 还是 next）。**绝不允许因为"子 agent 说完了"就静默结束本轮而不给提示。** 尤其 CR 扫描、plan 产出这两个停在人工门前的步骤。
2. **审查/验收问题人工门**：code-reviewer 和 verifier 只产出问题清单，**绝不直接改代码**；扫出的问题必须经人工逐条裁决（ACCEPTED/REJECTED/MODIFIED）并 `/devops-workflow approve` 后，才由另一个 executor 对已采纳项改写。零问题（PASSED）也要输出"无需裁决，执行 approve"，不许静默卡住。阶段 5 验收同理：verifier 只读不写，问题清单经人工裁决后才修复。
3. **编码与审查分两轮**：编码、CR、改写各自独立 agent，CR 与编码不共享上下文，禁止同上下文自审。
4. **进度即时回写（阻塞步骤）**：任务每次状态流转（含中间态 CODING/CR_SCANNED/CR_CONFIRMED/REWRITING/DONE）都必须即时写回 progress.md 任务状态行 + 里程碑进度表计数，并把 dev-tasks.md 对应子项 `[ ]→[x]`；回写未完成不得推进下一个任务。`progress.md` 是状态权威源，与 dev-tasks.md 勾选须一致。
5. **设计分两层 + 三级复杂度**：design-consensus = 共识/契约层（必含清单，阶段3 清单式审核，缺项打回）；复杂任务的实现细节走任务级 plan/LLD（阶段4 编码前出，人工 approve 后才编码）。简单和普通任务只用 design-consensus，不出 plan。简单任务在 `simple_task_skip_cr=true` 时跳过 CR 门（详见 `automation.md`）。
6. **未决项不许悬空**：design-consensus 的 `待确认/TODO` 必须登记成表并有处置，不许默默漏进编码。
7. **设计/需求层缺陷走 rework**，不要硬塞进 CR 改写：CR 改写只解决"设计对、改当前任务小问题"；牵动设计或多任务用 `/devops-workflow rework`，依赖扩散自动算下游 + 人工确认，未受影响的 DONE 保留。
8. **里程碑默认单个**：只有大需求才 `split`；跨模块交互一律通过 Service/Events，禁止直接访问他模块 Model/Repository。
9. **中断恢复**：流程可在任意阶段中断，下次 `/devops-workflow next` 从 progress.md 记录的当前阶段恢复。
10. **所有 agent prompt 必须含 Bash 静态分析约束**：禁止 for/while/if/case/here-doc/嵌套 `$()`。产出物只落项目内 `.task/`，禁止写 home 或仓库外。
11. **人工门只认 `/devops-workflow approve`**：四道人工门（设计审核 / plan 确认 / CR 裁决 / 验收问题裁决）的审批**只有**用户显式输入 `/devops-workflow approve` 才算通过。用户的任何其他消息——包括讨论、补充要求、确认某个细节正确、甚至说"没问题"——都**不等于** approve，绝不推断审批意图。收到非 approve 消息时，视为反馈并据此调整产出，然后继续等待 `/devops-workflow approve`。
12. **design-consensus 同步（防设计漂移）**：阶段 4 中 plan 确认后和 CR 裁决 MODIFIED 后，如果调整了 design-consensus 层面的契约（接口签名/数据模型/事件契约等），**必须同步回写** design-consensus.md 并向用户输出同步摘要。不回写会导致阶段 5 验收对照过期契约检查，产生误报或漏检。

---

## references 索引（按需读取，别一次性全载）

| 当你要做 | 先读 |
|---------|------|
| 写/更新 progress.md、初始化任务目录、查状态枚举 | `references/templates.md` |
| 执行任意 `/devops-workflow` 子命令（路由入口） | `references/commands.md` |
| 自动化协议（auto_advance / auto_accept_pass 等） | `references/automation.md` |
| **阶段执行** | |
| 阶段 1 需求讨论（start + devops-discuss） | `references/stages/stage-1-discuss.md` |
| 阶段 2 分析与设计（analyst/ralph + design-consensus） | `references/stages/stage-2-design.md` |
| 阶段 3 设计审核清单门 | `references/stages/stage-3-review.md` |
| 阶段 4 开发（总则 + 并行判断 + 编码 + 复验回写） | `references/stages/stage-4.0-dev.md` |
| 阶段 4 复杂任务 plan（复杂度判断 + plan 产出 + 同步） | `references/stages/stage-4.1-plan.md` |
| 阶段 4 CR 扫描与裁决（CR + 人工门 + 同步 + 改写） | `references/stages/stage-4.2-cr.md` |
| 阶段 5 收尾验收 + 异常处理 | `references/stages/stage-5-accept.md` |
| **独立命令** | |
| `/devops-workflow rework` 返工 | `references/commands/rework.md` |
| `/devops-workflow followup` 基于已完成需求发起新需求 | `references/commands/followup.md` |
| `/devops-workflow config` 初始化/合并流程配置 | `references/commands/config.md` |
| `/devops-workflow summary` 产出交付清单（DDL/Job·MQ/API） | `references/commands/summary.md` |

> **执行某阶段/命令前，必须先读对应 reference 文件**再行动——尤其阶段 4，prompts 和人工门的精确措辞都在 `stages/stage-4.0-dev.md` / `stages/stage-4.1-plan.md` / `stages/stage-4.2-cr.md`，凭记忆执行易漏步、易卡死。
