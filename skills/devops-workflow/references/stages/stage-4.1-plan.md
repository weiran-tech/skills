# 阶段 4：复杂任务 plan（PENDING_PLAN_REVIEW）

> 复杂任务编码前出 plan 时读本文件。简单任务跳过本文件直接编码。

**工单目录基准**：`{讨论根目录}{域}/{需求名}/.task/`。本文件中所有 `.task/` 路径均相对于此。

## 复杂度与 plan 的关系

每个任务编码前，按 dev-tasks 标注的复杂度（或 Claude 自行评估）判定为三级之一（判定标准见 `automation.md「simple_task_skip_cr 协议」`）：

- **简单任务**：直接编码，不出 plan，不走 CR（需 `simple_task_skip_cr=true`）。
- **普通任务**：直接编码，不出 plan，走完整 CR 闭环。
- **复杂任务**：编码前先产出**任务级详细设计（plan/LLD）**，人工确认后再编码。判断复杂的信号：跨多范围/多层、涉及核心交易或资金链路、改动既有关键流程、有并发/一致性/迁移风险、设计有未决项。
- 拿不准时按普通处理（出 plan 比返工便宜，但不必对简单改动过度设计）。

plan 是**编码前的设计评审门**：把"方向错"挡在写代码之前，比事后 CR 便宜。plan 由 `architect`/`planner` 产出（只读、不写业务代码），人工 `/devops-workflow approve` 确认后才编码。

## ⓪ 复杂任务出 plan（architect/planner，只读）
```
architect "
为任务 [{模块名} · {任务标题}] 产出任务级详细设计（LLD），写入 .task/{...}/plans/{模块名}-{X.Y}.md。

**第一步：读代码建立现状认知**
1. 读 design-consensus.md 获取契约/边界/决策
2. 读 docs/{模块名}/ 获取模块架构文档
3. 如 {讨论根目录}{域}/{需求名}/docs/ 下有参考文档，读取作为需求背景
4. 读取任务涉及的现有代码文件，定位到具体类、方法、行号，理解当前实现

**第二步：产出 LLD，必含以下内容**

## 1. 改动文件清单（逐文件列出）
对每个要修改或新建的文件，列出：
- 文件路径：具体到项目实际路径（如 `modules/{模块}/src/Action/XxxAction.php` 或 `{service}-domain/src/main/java/.../XxxService.java`）
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
1. **确认文件已落盘**：检查 `.task/{...}/plans/{范围标签}-{X.Y}.md` 是否存在且有内容。如果 architect 只在对话中输出了 plan 但没写文件，主 Agent **必须手动将 plan 内容写入该文件**
2. **回写** progress.md：把该任务状态置 `PLANNING`
3. **按 `auto_plan_check` 协议分流**（读取 `.workflow-config`，不存在视为 false）：

   **A. `auto_plan_check=true` 时自动校验：**
   - 派 `critic` agent 校验 plan 必含项齐全性（改动文件清单 / 改动步骤 / 类与方法签名 / 测试用例清单 / 集成点 — 对照上方 LLD 模板）
   - **齐全（PASS）**：自动置 PLAN_CONFIRMED，向用户输出「auto_plan_check: plan 齐全性校验通过，已自动确认」+ plan 摘要 → 直接进入编码
   - **缺项（FAIL）**：打回 architect 重出 plan（最多重试 1 次），仍缺项则回写 `PENDING_PLAN_REVIEW`，走下方 B 流程

   **B. `auto_plan_check=false`（默认）或自动校验未通过时：**
   - 回写 progress.md 状态为 `PENDING_PLAN_REVIEW`
   - **向用户输出 plan 摘要**：列出改动文件清单（**仅文件名，不含路径** + 操作[新建/修改] + 一句话说明）、关键改动步骤、数据模型变更、测试用例清单
   - **明确告知**：
     ```
     plan 已保存到 .task/plans/{文件名}
     请审阅后执行 /devops-workflow approve 确认，或指出需要调整的地方
     ```

plan 不达标（缺项/方向问题）→ 打回重出，不进编码。确认后置 **PLAN_CONFIRMED** 再编码。

### ★ plan 确认后同步 design-consensus（防止设计漂移）
plan approve 后、编码开始前，主 Agent **必须检查** plan 是否调整了 design-consensus 中约定的内容（接口签名、数据模型、事件契约、跨模块调用等）。如果有调整：
1. 在 design-consensus.md 末尾追加 `## Plan 同步 [{X.Y} {模块名} · {任务标题}]`，记录调整项（原契约 → 新契约 + 调整原因）
2. 向用户输出同步摘要：「plan 对 design-consensus 的以下契约做了调整：{列表}，已同步回 design-consensus.md」

> **为什么要同步**：design-consensus 是阶段 5 验收的基线文档。如果 plan 调整了设计但不回写，验收时 verifier 会对照过期的契约检查代码，产生误报或漏检。

**⚠️ 人工门审批铁律（适用于所有人工门）：只有用户显式输入 `/devops-workflow approve` 才算审批通过。用户的任何其他消息——包括对设计的讨论、补充要求、确认某个细节正确、甚至说"没问题"——都不等于 approve。绝不推断审批意图。用户讨论 plan 内容时，应将其视为反馈并据此调整 plan，然后继续等待 `/devops-workflow approve`。**
