# 阶段 5：收尾验收（REVIEWING → COMPLETED）+ 异常处理

> 执行阶段 5 收尾验收、或处理 BLOCKED / 阶段回退 / 中断恢复时读本文件。
>
> **作用域：子需求级（AC8）** — 本阶段的所有验收、产物、状态变更均在子需求上独立推进。版本只是跨域聚合视图，版本级聚合在阶段 5 完成后由 `summary {版本号}` 命令产出。

## 阶段 5：收尾验收

逐任务审查已在阶段 4 完成，本阶段只做**子需求级全局回归与一致性把关**，由独立 verifier 执行（不与编码共享上下文）。

**执行**：
```
verifier "
对子需求 {域}/{父需求名}#{子需求名} 做收尾验收：
1. 确认 metadata.md 任务清单全部已勾选、各任务审查结论均为 PASSED
2. 全量回归：{test_cmd} 全绿
3. 对本次变更涉及的文件执行 {lint_cmd} 语法校验全部通过（{static_analysis_cmd} 默认不纳入验收）
4. 跨模块一致性：对照 docs/discuss/{域}/{父需求名}/.task/{子需求名}/design-consensus.md 与 docs/architecture/cross-module.md，校验 {contract_type} 契约闭合
5. 迁移检查：如涉及 {module_root_glob}/*/resources/migrations，确认迁移与回滚可用
6. 结果写入 docs/discuss/{域}/{父需求名}/.task/{子需求名}/acceptance.md

执行约束见 SKILL.md 不变量 12：所有 Bash 命令必须可静态分析，禁止 for/while/if/case/here-doc/嵌套 $()。"
```

**★ verifier 返回后，主 Agent 必须立刻执行以下动作（缺一不可，禁止静默结束本轮）**：
1. **读取** verifier 写出的 `docs/discuss/{域}/{父需求名}/.task/{子需求名}/acceptance.md`（以报告文件为准，不以 verifier 返回文本为准）
2. **回写** metadata.md：阶段 5 状态置 通过 → COMPLETED / 不通过 → 标注问题
3. **版本聚合（仅当验收通过时执行）**：若 metadata.md.versionBinding 非空（该子需求已绑定版本号），则回写 `docs/version/{版本号}` 的 stageRecord 字段，**追加一行**：
   ```
   {子需求ID}: COMPLETED at {ISO 时间}
   ```
   追加前先读取现有 stageRecord 完整内容；保留所有既有行不变；在末尾追加新行；原子写回（写临时文件 → mv 替换）
4. **向用户输出验收结果摘要**（无论通过与否都必须输出，不许跑完不吭声）：
   - 通过：逐项列 `{test_cmd} ✓ / {lint_cmd} ✓ / 跨模块契约 ✓ / 迁移 ✓`，输出「子需求 {子需求ID} 收尾验收通过 → COMPLETED + 版本 {版本号} stageRecord 已聚合」+ 完成摘要（见下方流程完成输出）；版本下其他子需求可独立推进
   - 不通过：列出失败项（哪条回归红/哪个契约不闭合），并明确下一步——单任务实现问题走子需求级任务回退、设计错走 `/dev-workflow rework`
5. 不许停在"verifier 已完成"而不给结果与下一步

> 与 CR 扫描同理：**子 agent 跑完 ≠ 流程推进**。verifier 一返回，主 Agent 就要读 acceptance.md、回写 metadata.md、执行版本聚合（如适用）、把验收结论和下一步打给用户。

- 验收通过 → 更新 metadata.md.currentState = COMPLETED；执行版本聚合（如该子需求已绑定版本）；输出完成摘要，并**提示用户可执行 `/dev-workflow summary {版本号}` 产出版本级交付清单**（DDL/Job·MQ/API，见 summary.md）。summary 由用户主动触发，不在阶段 5 流程内自动跑
- 验收发现**单任务实现问题** → 退回对应子需求任务 executor 修复，修复后重走该任务的逐任务审查（阶段 4），再重跑收尾验收
- 验收发现**设计错 / 多任务受牵连** → `/dev-workflow rework`（见 rework.md）；**前置门禁（AC19）**：版本状态 ∈ {DRAFT, IN_PROGRESS, READY} 才允许；RELEASED / ARCHIVED 一律报错"版本已发布，禁止 rework"

**流程完成输出**（子需求级）：
```
子需求 [{域}/{父需求名}#{子需求名}] 已完成自动化流程

父需求讨论: docs/discuss/{域}/{父需求名}.md
设计文档: docs/discuss/{域}/{父需求名}/.task/{子需求名}/design-consensus.md
状态源: docs/discuss/{域}/{父需求名}/.task/{子需求名}/metadata.md
逐任务审查: docs/discuss/{域}/{父需求名}/.task/{子需求名}/review/
收尾验收: docs/discuss/{域}/{父需求名}/.task/{子需求名}/acceptance.md
绑定版本: {版本号}（stageRecord 已聚合该子需求行）
影响模块: {模块列表}

版本级聚合交付清单（DDL/Job·MQ/API）需执行 `/dev-workflow summary {版本号}` 产出。

后续人工操作：迁移（如有 migrations）、测试验收、上线发布
```

---

## 异常处理

### BLOCKED 状态
阶段 2 汇总设计时如果发现接口冲突，metadata.md 会标记为 BLOCKED。
- `/dev-workflow status {子需求ID}` 会显示 BLOCKED 原因
- 用户解决冲突后，执行 `/dev-workflow next {子需求ID}` 重新触发阶段 2

### 阶段回退
- 阶段 3 设计审核不通过（清单有缺项）→ `/dev-workflow next {子需求ID}` 重新触发阶段 2 补充设计后再审
- 阶段 4 复杂任务 plan 不达标 → 打回 architect/planner 重出 plan，确认后才编码；不影响其他任务
- 阶段 4 CR 人工裁决后改写/复验不达标 → 在同一任务内重跑改写⑤+复验⑥，直至已采纳问题修复且 `{test_cmd}` 绿 + `{lint_cmd}` 通过；该任务不 DONE 不影响其他任务
- **阶段 4/5 发现设计或需求层缺陷（局部改写补不了）→ `/dev-workflow rework {子需求ID}`**：按根因层级回退（实现/设计/需求），级联重做受影响任务，详见 rework.md
  - **AC19 严格门**：版本状态 = RELEASED 或 ARCHIVED 时，rework 立即报错「[字段 version.status] {版本号} 已 {RELEASED|ARCHIVED}。建议：建新版本或新子需求」；仅 DRAFT / IN_PROGRESS / READY 可 rework
- 阶段 5 收尾验收发现**单任务实现问题** → 退回对应子需求任务，重走该任务 CR 扫描→人工确认→改写闭环后再重跑收尾验收；发现**设计错** → 用 `/dev-workflow rework {子需求ID}`（同样受 AC19 版本状态门禁约束）

### 中断恢复
流程可以在任意阶段中断。下次执行 `/dev-workflow next {子需求ID}` 时，从 metadata.md 记录的 currentStage / currentState 恢复。**必须显式传子需求 ID**（spec D8：无活动指针）；缺参时主 Agent 报错并列出所有 currentState ∈ {ANALYZING, DEVELOPING, REVIEWING} 的子需求供选择。
