# 命令处理逻辑

> **统一解析规则**：`next` / `approve` / `status` / `rework` 在确定作用目标（需求/里程碑）时，省略参数一律按「活动上下文」优先级解析
> **显式参数 > 活动指针 (`docs/.req-discuss/.workflow-active`) > 旧回退规则**（唯一进行中的自动选中；多个列出让选；无则提示 start）。显式传参不改变活动指针；要持久切换用 `use`。所有解析支持前缀/子串模糊匹配，唯一即定位，多个则列出让选。
>
> **里程碑「粘住」（关键，避免每步重复敲 `#`）**：活动指针应尽量带里程碑（`{需求ID}#里程碑`）。若指针**只有需求而该需求是多里程碑**：
> 1. `next`/`approve` 解析里程碑时——唯一进行中的里程碑 → 自动选中；多个 → 列出让选。
> 2. **解析出里程碑后，立即把它写回 `.workflow-active`（补成 `{需求ID}#里程碑`）使其粘住**，之后裸命令直接作用于该里程碑，**不再重复询问/输入 `#`**。
> 3. 切换到别的里程碑用 `/php-workflow use #{里程碑}`（只敲 `#`）；该里程碑 COMPLETED 后，指针自动改指剩余唯一在跑的里程碑（或提示重新 `use`）。
> 这样里程碑最多只需指定一次（甚至自动粘住），不是每个 `next` 都要带 `#`。`status` 解析不写回指针（它默认汇总展示）。

## `/php-workflow use [需求ID][#里程碑]`
设定活动上下文（粘性），之后裸命令默认作用于它。
1. 解析入参（支持前缀/子串模糊匹配）：
   - 传了 `需求ID[#里程碑]` → 解析为完整 ID；多里程碑需求建议带 `#里程碑`
   - 只传 `#里程碑`（无需求名）→ 沿用当前活动指针的需求，仅切换里程碑
   - 不传任何参数 → 显示当前活动上下文（不修改）
2. 校验解析结果存在（需求目录/里程碑存在）；匹配到多个则列出让用户选
3. 把完整 `{需求ID}[#里程碑]` 写入 `docs/.req-discuss/.workflow-active`（覆盖）
4. 回显：`当前活动: {需求ID}[#里程碑] — 阶段 {n}/5 {状态}`，并提示可直接 `/php-workflow next` / `approve` / `status`

> 切到别的需求/里程碑就再 `use` 一次；活动指针指向的目标 COMPLETED 后，由 `next`/`status` 提示重新 `use`（若只剩唯一进行中的，自动改指它）。

## `/php-workflow start {需求名}`
1. 询问用户需求所属的**业务域/模块**（从 `composer.json` 的 `autoload.psr-4` 或 `modules/` 目录读取本项目实际模块），或从需求描述中推断
2. 检查 `docs/.req-discuss/{域}/{需求名}.md` 是否已存在，存在则提示用户是否要基于已有讨论继续
3. 调用 `/req-discuss` skill，传入需求名作为讨论主题
4. 讨论完成并保存后，创建 `.task/progress.md`（模板见 templates.md），状态设为 `ANALYZING`
5. **把该需求设为活动上下文**（写入 `docs/.req-discuss/.workflow-active`）
6. 提示用户可用 `/php-workflow next` 进入分析与设计阶段（无需再带 ID）

**执行**：`/req-discuss "{需求名}：{用户提供的需求描述}"`

## `/php-workflow split [需求ID] {里程碑列表}`
把一个**已存在**的需求从单里程碑拆成多里程碑（仅大需求需要；普通需求不要拆）。
1. 解析需求 ID（省略时自动选中）。要求该需求阶段 1 讨论已完成（讨论文档存在）
2. 与用户确认里程碑划分：每个里程碑的名称、覆盖的模块、里程碑间依赖。例如 `alipay`（payment 中支付宝相关入口）、`wechat`（payment 中微信相关入口）
3. 识别**跨里程碑公共设计骨架**（如路由机制、数据一致性、共享事件级联）；若存在，建议抽出为 `design-foundation.md`，并作为各里程碑的前置依赖
4. 创建目录 `.task/milestones/{里程碑名}/`（各含 analysis/ done/ review/ 空目录占位）
5. 若需求已有单里程碑产出（analysis/ 等），按里程碑归位到对应 `milestones/{里程碑名}/`，公共部分留在 `.task/` 根
6. 重写 progress.md 为**多里程碑**结构（见 templates.md）
7. **把活动上下文设为应先做的里程碑**（有公共基础则指向它，写入 `docs/.req-discuss/.workflow-active`）
8. 提示用户后续用 `/php-workflow use #{里程碑}` 切换、`/php-workflow next` 推进（有依赖的里程碑须等前置就绪）

> 拆分是不可省的显式操作：未执行 split 的需求一律按单里程碑处理。已拆分的需求不支持自动合并回单里程碑（如需回退，手工整理目录后改 progress.md）。

## `/php-workflow approve [需求ID][#里程碑]`
确认当前所处的**人工检查点**。skill 有三个人工门，approve 按当前状态分发：

**A. 阶段 3 设计审核（PENDING_DESIGN_REVIEW）** — 详见 stage-3-review.md
1. 解析需求 ID / `#里程碑`，定位 `design-consensus.md`
2. 确认状态为 PENDING_DESIGN_REVIEW，且阶段 3 审核清单逐项通过（有缺项先打回阶段 2，不 approve）
3. 在 design-consensus.md 末尾追加 `## 设计确认: APPROVED`
4. 更新状态为 DEVELOPING
5. 提示用户用 `/php-workflow next [#里程碑]` 进入开发阶段

**B. 阶段 4 任务 plan 确认（PENDING_PLAN_REVIEW，仅复杂任务）** — 详见 stage-4-dev.md
1. 定位当前任务的 plan `.task/{...}/plans/{任务序号}-{模块名}.md`
2. 确认 plan 必含项齐全（签名/字段/时序/边界/测试用例/迁移）；缺项或方向问题 → 打回重出，不 approve
3. 在 plan 末尾追加 `## 设计确认: APPROVED`，任务状态置 PLAN_CONFIRMED
4. 提示用户用 `/php-workflow next` 开始该任务编码（对照已确认 plan）

**C. 阶段 4 CR 问题人工确认（PENDING_CR_REVIEW）** — 详见 stage-4-dev.md
1. 定位当前正在审查的任务及其 CR 报告 `.task/review/{模块名}-{任务序号}.md`
2. **零问题分支**：报告判 PASSED 无问题项 → 跳过裁决，任务置 CR_CONFIRMED，直接进第 4 步复验
3. 有问题：确认人工裁决已填写（每条 ACCEPTED / REJECTED / MODIFIED）；若仍有 PENDING 的问题，提示用户先完成裁决，不推进。锁定裁决，任务置 CR_CONFIRMED
4. 复验与改写：
   - 有 ACCEPTED/MODIFIED 项 → 执行改写⑤（只改已采纳项）→ 复验⑥
   - 零问题 / 全部 REJECTED（无可改）→ 跳过改写⑤，直接复验⑥（重跑 phpunit + php -l 确认绿）
5. 复验通过 → 任务置 DONE，按⑥强制回写 progress.md + dev-tasks.md
6. 提示用户用 `/php-workflow next` 继续下一个任务（或若全部 DONE，进入阶段 5）

## `/php-workflow next [需求ID][#里程碑]`
1. 解析需求 ID
2. **多里程碑**：解析 `#里程碑`（省略时自动选中/列出选择）；读取该里程碑的当前阶段和状态。**单里程碑**：直接读需求级阶段与状态
3. 根据状态分发到对应阶段的执行逻辑（阶段逻辑作用范围 = 选中的里程碑；单里程碑则 = 整个需求）——阶段细节见 stage-{2..5}-*.md
4. **阶段 4 内**：首次进入时先按依赖图决定编码并行/串行（记入 progress.md）；推进当前未 DONE 任务——**复杂任务先出 plan 停在 PENDING_PLAN_REVIEW** 等 approve，确认后再编码；简单任务直接编码 → DoD → CR 扫描后**逐任务停在 PENDING_CR_REVIEW**，呈现该任务问题清单、提示用户裁决并 `/php-workflow approve`；不自动改写。多任务并行时按到达顺序逐个呈现各自的 plan / CR 门
5. 如果当前是 PENDING_DESIGN_REVIEW / PENDING_PLAN_REVIEW / PENDING_CR_REVIEW，提示用户先 `/php-workflow approve`（不重复执行已停住的人工门）
6. **依赖校验（多里程碑）**：若选中里程碑声明了前置依赖，且前置里程碑尚未到达约定阶段（如公共骨架未定稿），提示阻塞、不推进

## `/php-workflow status [需求ID][#里程碑]`
- **不指定需求 ID 且有活动上下文**：顶部高亮显示当前活动（`▶ 活动: {需求ID}[#里程碑]`），并展示其详细进度
- **不指定需求 ID 且无活动上下文**：扫描 `docs/.req-discuss/` 下所有 `.task/progress.md`，汇总显示
- **指定需求 ID、不带 `#里程碑`**：单里程碑显示该需求详细进度；多里程碑显示完整里程碑进度表
- **指定 `#里程碑`**：只显示该里程碑的阶段记录与任务清单

**输出格式（单里程碑）**：
```
需求开发进度

  order/订单取消优化
  阶段 3/5 — 设计审核（待审核）
  影响模块: order, payment
```
**输出格式（多里程碑，带活动高亮）**：
```
▶ 活动: payment/支付渠道重构#alipay

需求开发进度  payment/支付渠道重构  [多里程碑]

  里程碑 alipay ◀   阶段 4/5 — 开发与逐任务审查（进行中）  任务 2/5   模块: payment, order
  里程碑 wechat     阶段 2/5 — 分析与设计（进行中）        任务 0/4   模块: payment, order  依赖: 公共基础
```

## `/php-workflow list`
扫描 `docs/.req-discuss/` 下所有 `.task/progress.md`，只显示**未完成**的需求（状态不是 COMPLETED）。多里程碑需求在条目下附各里程碑一行简况。

## `/php-workflow rework [需求ID][#里程碑]`
设计/实现缺陷返工 —— **详见 rework.md**。

## `/php-workflow summary [需求ID][#里程碑]`
产出里程碑交付清单（DDL / 新增 Job·MQ / API 接口清单），给 DBA 与前端 —— **详见 summary.md**。建议阶段 5 验收通过后执行。
