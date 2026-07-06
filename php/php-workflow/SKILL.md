---
name: php-workflow
description: 伪多模块单体项目的需求开发全流程编排。状态机驱动，自动调度 php-analyzer、team、code-reviewer 等 skill/agent，串联需求讨论到代码审查的 5 个阶段。当用户说 "workflow"、"开发流程"、"需求流程"、"模块开发流程" 时触发。
---

# Workflow — 单体多模块需求开发全流程编排

状态机驱动的流程 skill：5 个开发阶段串成统一入口，按 `progress.md` 的当前状态决定下一步调度什么 agent。本文件是**路由器 + 常驻安全规则**；各步骤的执行细节按需读取 `references/`（见末尾索引）。

面向伪多模块单体项目：代码同仓 `modules/{模块}`，跨模块走 Events/Listeners + Service，审查按模块路径过滤 diff（`git diff <默认分支>...HEAD -- modules/{模块}`），架构上下文来自 `docs/workflow/{module}/`（php-analyzer 产出）。测试/校验等具体命令默认按 PHP 工具链（phpunit / php -l），可按项目配置替换。

## 总体流程

```
1 需求讨论 → 2 分析与设计 →[★阶段3 设计审核门]→ 4 开发与逐任务审查 → 5 收尾验收 → COMPLETED
  (start)     (next: analyst+ralph)  (approve)    (next: 逐任务闭环)      (next: verifier)
                                                        │
  阶段4 逐任务闭环：⓪复杂度判断 →[★复杂任务 plan 门]→ ①编码 → ②DoD → ③CR扫描 →[★CR人工门]→ ⑤改写 → ⑥复验+回写 → DONE
  ※ 阶段 4/5 发现设计/需求层缺陷 → /php-workflow rework 按根因层级回退 + 依赖级联重做
```

三道人工门（均由 `/php-workflow approve` 按状态分发）：**阶段3 设计审核** / **阶段4 复杂任务 plan** / **阶段4 CR 问题裁决**。

## 命令速查

```
/php-workflow use [需求ID][#里程碑]        # 设定活动上下文，之后裸命令默认作用于它（粘性，推荐）
/php-workflow start {需求名}              # 创建需求，进入阶段 1 讨论
/php-workflow next [需求ID]               # 执行下一阶段 / 下一个任务（省略=活动上下文）
/php-workflow approve [需求ID]            # 确认当前人工门（阶段3设计 / 阶段4 plan / 阶段4 CR）
/php-workflow status [需求ID]             # 查看进度（省略=活动上下文+高亮；无活动则全部）
/php-workflow list                        # 列出未完成的需求
/php-workflow split [需求ID] {里程碑列表}  # 把大需求拆成多个里程碑（仅大需求需要）
/php-workflow rework [需求ID]             # 设计/实现缺陷返工：按根因层级回退并级联重做
/php-workflow summary [需求ID]            # 产出交付清单（DDL / Job·MQ / API）给 DBA 与前端
```

- **需求 ID** = `{域}/{需求名}`（如 `order/订单取消优化`），与 `docs/discuss/` 目录一致
- **`#里程碑`** 仅多里程碑需求需要（如 `payment/支付渠道重构#alipay`）；未 `split` 的需求是单里程碑，无需 `#`
- 命令的详细处理逻辑见 `references/commands.md`

### 活动上下文（避免每步重复输入长 ID）

像 git 当前分支：`/php-workflow use` 选一次"当前在搞哪个需求/里程碑"，之后 `next/approve/status/rework` 省略参数即默认作用于它。
- 活动指针存于 `docs/discuss/.workflow-active`（单行 `{需求ID}[#里程碑]`，全局唯一，**便捷指针非状态源**）
- 解析优先级：**显式参数 > 活动指针 > 旧回退**（唯一在跑自动选/多个列出）；支持前缀子串模糊匹配（`trade#共` 即定位）
- **里程碑粘住**：多里程碑下，里程碑只需指定一次（`use trade#共享基础`）；指针只有需求时，首次 `next` 解析出里程碑会写回指针粘住，之后裸命令不必再带 `#`。切里程碑用 `use #{里程碑}`。详见 commands.md
- `start`/`split` 会自动设活动指针；显式传 ID 可临时操作别的需求而不动指针

## 项目约定

- **单体仓库**：默认已在项目仓库根目录。产出物存于 `docs/discuss/{域}/{需求名}/.task/`（目录结构见 `references/templates.md`）
- **模块路径** `modules/{模块名}/`；模块清单从 `composer.json` 的 `autoload.psr-4` 或 `ls modules/` 获取
- **架构文档** `docs/workflow/{模块名}/`（overview/business/contracts/flows）+ `docs/workflow/cross-module.md`，由 `php-analyzer` 产出；缺失则先提示跑 php-analyzer
- **验收基线（强制）**：`vendor/bin/phpunit modules/{模块}/tests` 单测绿 + 改动文件 `php -l` 语法校验通过
- **phpstan 默认不纳入 DoD/验收**：存量项目历史告警多、收益低；仅项目有干净基线时才可选开启
- **单仓库单分支**：所有模块共用一条 feature 分支，无独立分支/PR；具体命令按项目配置

## Agent 权限与职责分离

| 阶段                         | 执行方式                                        | 权限                   |
| ---------------------------- | ----------------------------------------------- | ---------------------- |
| 2 模块分析                   | `php-analyzer` 或 `analyst`                     | 只读                   |
| 4 任务详细设计（仅复杂任务） | `architect` / `planner`                         | 只读（只设计不写码）   |
| 4 编码                       | `executor`（并行 `team`/串行单个，Claude 判断） | 读写                   |
| 4 CR 扫描（逐任务）          | 单个 `code-reviewer`                            | 只读（只产清单不改码） |
| 4 改写（逐任务）             | 单个 `executor`                                 | 读写（只改已采纳项）   |
| 5 收尾验收                   | `verifier`                                      | 只读                   |

人工门：阶段3 设计审核、阶段4 plan 确认、阶段4 CR 裁决。

---

## 关键不变量（必须遵守，不随阶段文件加载与否而改变）

1. **子 agent 返回 ≠ 流程推进（防卡死）**：每次子 agent（analyst/architect/code-reviewer/executor/verifier）返回后，主 Agent **必须立刻**：① 读取其产出文件（不以子 agent 的返回文本为准）→ ② 回写 progress.md 对应状态 → ③ 向用户输出结果摘要 + **明确的下一步指令**（该 approve 还是 next）。**绝不允许因为"子 agent 说完了"就静默结束本轮而不给提示。** 尤其 CR 扫描、plan 产出这两个停在人工门前的步骤。
2. **CR 问题人工门**：code-reviewer 只产出问题清单，**绝不直接改代码**；扫出的问题必须经人工逐条裁决（ACCEPTED/REJECTED/MODIFIED）并 `/php-workflow approve` 后，才由另一个 executor 对已采纳项改写。零问题（PASSED）也要输出"无需裁决，执行 approve"，不许静默卡住。
3. **编码与审查分两轮**：编码、CR、改写各自独立 agent，CR 与编码不共享上下文，禁止同上下文自审。
4. **进度即时回写（阻塞步骤）**：任务每次状态流转（含中间态 CODING/CR_SCANNED/CR_CONFIRMED/REWRITING/DONE）都必须即时写回 progress.md 任务状态行 + 里程碑进度表计数，并把 dev-tasks.md 对应子项 `[ ]→[x]`；回写未完成不得推进下一个任务。`progress.md` 是状态权威源，与 dev-tasks.md 勾选须一致。
5. **设计分两层**：design-consensus = 共识/契约层（必含清单，阶段3 清单式审核，缺项打回）；复杂任务的实现细节走任务级 plan/LLD（阶段4 编码前出，人工 approve 后才编码）。简单任务只用 design-consensus，不出 plan。
6. **未决项不许悬空**：design-consensus 的 `待确认/TODO` 必须登记成表并有处置，不许默默漏进编码。
7. **设计/需求层缺陷走 rework**，不要硬塞进 CR 改写：CR 改写只解决"设计对、改当前任务小问题"；牵动设计或多任务用 `/php-workflow rework`，依赖扩散自动算下游 + 人工确认，未受影响的 DONE 保留。
8. **里程碑默认单个**：只有大需求才 `split`；跨模块交互一律通过 Service/Events，禁止直接访问他模块 Model/Repository。
9. **中断恢复**：流程可在任意阶段中断，下次 `/php-workflow next` 从 progress.md 记录的当前阶段恢复。
10. **所有 agent prompt 必须含 Bash 静态分析约束**：禁止 for/while/if/case/here-doc/嵌套 `$()`。产出物只落项目内 `.task/`，禁止写 home 或仓库外。

---

## references 索引（按需读取，别一次性全载）

| 当你要做                                                                       | 先读                           |
| ------------------------------------------------------------------------------ | ------------------------------ |
| 写/更新 progress.md、初始化任务目录、查状态枚举                                | `references/templates.md`      |
| 执行任意 `/php-workflow` 子命令的详细逻辑                                      | `references/commands.md`       |
| 执行**阶段 2** 分析与设计（analyst/ralph prompts + design-consensus 必含清单） | `references/stage-2-design.md` |
| 执行**阶段 3** 设计审核清单门                                                  | `references/stage-3-review.md` |
| 执行**阶段 4** 开发（复杂度/并行判断 + plan/编码/CR/改写 全部 prompts）        | `references/stage-4-dev.md`    |
| 执行**阶段 5** 收尾验收 + 异常处理（BLOCKED/回退/中断恢复）                    | `references/stage-5-accept.md` |
| 执行 `/php-workflow rework` 返工                                               | `references/rework.md`         |
| 执行 `/php-workflow summary` 产出交付清单（DDL/Job·MQ/API）                    | `references/summary.md`        |

> **执行某阶段/命令前，必须先读对应 reference 文件**再行动——尤其阶段 4，prompts 和人工门的精确措辞都在 `stage-4-dev.md`，凭记忆执行易漏步、易卡死。人看的总览与示例见同目录 `README.md`。
