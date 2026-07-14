# 命令路由索引

> 执行任意 `/devops-workflow` 子命令前读本文件，按命令名跳转到对应 reference 文件。

> **统一解析规则**：`next` / `approve` / `status` / `rework` 在确定作用目标（需求/里程碑）时，省略参数一律按「活动上下文」优先级解析——**显式参数 > 活动指针 (`{讨论根目录}.workflow-active`) > 旧回退规则**（唯一进行中的自动选中；多个列出让选；无则提示 start）。显式传参不改变活动指针；要持久切换用 `use`。所有解析支持前缀/子串模糊匹配，唯一即定位，多个则列出让选。
>
> **里程碑「粘住」（关键，避免每步重复敲 `#`）**：活动指针应尽量带里程碑（`{需求ID}#里程碑`）。若指针**只有需求而该需求是多里程碑**：
> 1. `next`/`approve` 解析里程碑时——唯一进行中的里程碑 → 自动选中；多个 → 列出让选。
> 2. **解析出里程碑后，立即把它写回 `.workflow-active`（补成 `{需求ID}#里程碑`）使其粘住**，之后裸命令直接作用于该里程碑，**不再重复询问/输入 `#`**。
> 3. 切换到别的里程碑用 `/devops-workflow use #{里程碑}`（只敲 `#`）；该里程碑 COMPLETED 后，指针自动改指剩余唯一在跑的里程碑（或提示重新 `use`）。
> 这样里程碑最多只需指定一次（甚至自动粘住），不是每个 `next` 都要带 `#`。`status` 解析不写回指针（它默认汇总展示）。

---

## `/devops-workflow use [需求ID][#里程碑]`
设定活动上下文（粘性），之后裸命令默认作用于它。
1. 解析入参（支持前缀/子串模糊匹配）：
   - 传了 `需求ID[#里程碑]` → 解析为完整 ID；多里程碑需求建议带 `#里程碑`
   - 只传 `#里程碑`（无需求名）→ 沿用当前活动指针的需求，仅切换里程碑
   - 不传任何参数 → 显示当前活动上下文（不修改）
2. 校验解析结果存在（需求目录/里程碑存在）；匹配到多个则列出让用户选
3. 把完整 `{需求ID}[#里程碑]` 写入 `{讨论根目录}.workflow-active`（覆盖）
4. 回显：`当前活动: {需求ID}[#里程碑] — 阶段 {n}/5 {状态}`，并提示可直接 `/devops-workflow next` / `approve` / `status`

> 切到别的需求/里程碑就再 `use` 一次；活动指针指向的目标 COMPLETED 后，由 `next`/`status` 提示重新 `use`（若只剩唯一进行中的，自动改指它）。

## `/devops-workflow start {需求名}`
初始化需求目录 → 放入参考文档 → 调用 `/devops-discuss` 讨论 → 创建 progress.md → 设为活动上下文。**详见 `stages/stage-1-discuss.md`。**

## `/devops-workflow split [需求ID] {里程碑列表}`
把一个**已存在**的需求从单里程碑拆成多里程碑（仅大需求需要；普通需求不要拆）。
1. 解析需求 ID（省略时自动选中）。要求该需求阶段 1 讨论已完成（讨论文档存在）
2. 与用户确认里程碑划分：每个里程碑的名称、覆盖的模块、里程碑间依赖。例如 `alipay`（payment 中支付宝相关入口）、`wechat`（payment 中微信相关入口）
3. 识别**跨里程碑公共设计骨架**（如路由机制、数据一致性、共享事件级联）；若存在，建议抽出为 `design-foundation.md`，并作为各里程碑的前置依赖
4. 创建目录 `.task/milestones/{里程碑名}/`（各含 analysis/ done/ review/ 空目录占位）
5. 若需求已有单里程碑产出（analysis/ 等），按里程碑归位到对应 `milestones/{里程碑名}/`，公共部分留在 `.task/` 根
6. 重写 progress.md 为**多里程碑**结构（见 `templates.md`）
7. **把活动上下文设为应先做的里程碑**（有公共基础则指向它，写入 `{讨论根目录}.workflow-active`）
8. 提示用户后续用 `/devops-workflow use #{里程碑}` 切换、`/devops-workflow next` 推进（有依赖的里程碑须等前置就绪）

> 拆分是不可省的显式操作：未执行 split 的需求一律按单里程碑处理。已拆分的需求不支持自动合并回单里程碑（如需回退，手工整理目录后改 progress.md）。

## `/devops-workflow next [需求ID][#里程碑]`
1. 解析需求 ID
2. **多里程碑**：解析 `#里程碑`（省略时自动选中/列出选择）；读取该里程碑的当前阶段和状态。**单里程碑**：直接读需求级阶段与状态
3. 根据状态分发到对应阶段的执行逻辑——**详见 `stages/stage-{2..5}-*.md`**
4. **阶段 4 内**：首次进入时先按依赖图决定编码并行/串行（记入 progress.md）；推进当前未 DONE 任务——**复杂任务先出 plan 停在 PENDING_PLAN_REVIEW** 等 approve，确认后再编码；简单任务直接编码 → DoD → CR 扫描后**逐任务停在 PENDING_CR_REVIEW**，呈现该任务问题清单、提示用户裁决并 `/devops-workflow approve`；不自动改写。多任务并行时按到达顺序逐个呈现各自的 plan / CR 门
5. 如果当前是 PENDING_*_REVIEW，提示用户先 `/devops-workflow approve`
6. **依赖校验（多里程碑）**：若选中里程碑声明了前置依赖，且前置里程碑尚未到达约定阶段，提示阻塞、不推进

> **auto_advance 模式**：详见 `automation.md`「auto_advance 协议」。

## `/devops-workflow approve [需求ID][#里程碑]`
确认当前所处的**人工检查点**。按当前状态分发：

| 状态 | 人工门 | 详见 |
|------|--------|------|
| PENDING_DESIGN_REVIEW | 阶段 3 设计审核 | `stages/stage-3-review.md` |
| PENDING_PLAN_REVIEW | 阶段 4 复杂任务 plan 确认 | `stages/stage-4.1-plan.md` |
| PENDING_CR_REVIEW | 阶段 4 CR 问题裁决 | `stages/stage-4.2-cr.md` |
| PENDING_ACCEPT_REVIEW | 阶段 5 验收问题裁决 | `stages/stage-5-accept.md` |

各门的详细步骤（校验、裁决、同步 design-consensus、改写、复验）见对应 stage 文件。

## `/devops-workflow status [需求ID][#里程碑]`
- **不指定需求 ID 且有活动上下文**：顶部高亮显示当前活动（`▶ 活动: {需求ID}[#里程碑]`），并展示其详细进度
- **不指定需求 ID 且无活动上下文**：扫描 `{讨论根目录}` 下所有 `.task/progress.md`，汇总显示
- **指定需求 ID、不带 `#里程碑`**：单里程碑显示该需求详细进度；多里程碑显示完整里程碑进度表
- **指定 `#里程碑`**：只显示该里程碑的阶段记录与任务清单

## `/devops-workflow list`
扫描 `{讨论根目录}` 下所有 `.task/progress.md`，只显示**未完成**的需求（状态不是 COMPLETED）。多里程碑需求在条目下附各里程碑一行简况。

## `/devops-workflow rework [需求ID][#里程碑]`
设计/实现缺陷返工 —— **详见 `commands/rework.md`**。

## `/devops-workflow followup {已完成需求ID} [新需求名]`
基于已完成需求发起新需求（继承设计上下文）—— **详见 `commands/followup.md`**。

## `/devops-workflow config`
初始化/合并 `.workflow-config` 配置（自动补缺，不停确认）—— **详见 `commands/config.md`**。

## `/devops-workflow summary [需求ID][#里程碑]`
产出交付清单（DDL / Job·MQ / API）—— **详见 `commands/summary.md`**。建议阶段 5 验收通过后执行。
