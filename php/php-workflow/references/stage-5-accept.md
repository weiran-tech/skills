# 阶段 5：收尾验收（REVIEWING）+ 异常处理

> 执行阶段 5 收尾验收、或处理 BLOCKED / 阶段回退 / 中断恢复时读本文件。

## 阶段 5：收尾验收

逐任务审查已在阶段 4 完成，本阶段只做**全局回归与一致性把关**，由独立 verifier 执行（不与编码共享上下文）。

**执行**：
```
verifier "
对需求 {域}/{需求名} 做收尾验收：
1. 确认 progress.md 任务清单全部已勾选、各任务审查结论均为 PASSED
2. 全量回归：vendor/bin/phpunit 全绿
3. 对本次变更涉及的文件执行 php -l 语法校验全部通过（phpstan 默认不纳入验收）
4. 跨模块一致性：对照 .task/design-consensus.md 与 docs/cross-module.md，校验 Event/Listener、Service 调用契约闭合
5. 迁移检查：如涉及 modules/*/resources/migrations，确认迁移与回滚可用
6. 结果写入 docs/.req-discuss/{域}/{需求名}/.task/acceptance.md

Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"
```

**★ verifier 返回后，主 Agent 必须立刻执行以下动作（缺一不可，禁止静默结束本轮）**：
1. **读取** verifier 写出的 `docs/.req-discuss/{域}/{需求名}/.task/acceptance.md`（以报告文件为准，不以 verifier 返回文本为准）
2. **回写** progress.md：阶段 5 状态置 通过 → COMPLETED / 不通过 → 标注问题；并更新里程碑进度表
3. **向用户输出验收结果摘要**（无论通过与否都必须输出，不许跑完不吭声）：
   - 通过：逐项列 `phpunit ✓ / php -l ✓ / 跨模块契约 ✓ / 迁移 ✓`，输出「收尾验收通过，需求/里程碑 COMPLETED」+ 完成摘要（见下方流程完成输出）；多里程碑提示用 `/php-workflow use #{下一个里程碑}` 推进或全部完成
   - 不通过：列出失败项（哪条回归红/哪个契约不闭合），并明确下一步——单任务实现问题走任务回退、设计错走 `/php-workflow rework`
4. 不许停在"verifier 已完成"而不给结果与下一步

> 与 CR 扫描同理：**子 agent 跑完 ≠ 流程推进**。verifier 一返回，主 Agent 就要读 acceptance.md、回写状态、把验收结论和下一步打给用户。

- 验收通过 → 更新 progress.md 为 COMPLETED（多里程碑下为该里程碑 COMPLETED；全部里程碑 COMPLETED 时需求才 COMPLETED），输出完成摘要，并**提示用户可执行 `/php-workflow summary` 产出交付清单**（DDL/Job·MQ/API，见 summary.md）
- 验收发现**单任务实现问题** → 退回对应任务 executor 修复，修复后重走该任务的逐任务审查，再重跑收尾验收
- 验收发现**设计错 / 多任务受牵连** → `/php-workflow rework`（设计级，见 rework.md）：design-consensus 退回阶段 2 修订 → 阶段 3 重审 → 受影响任务及下游级联回 TODO 重跑

**流程完成输出**：
```
需求 [{域}/{需求名}] 已完成自动化流程

讨论文档: docs/.req-discuss/{域}/{需求名}.md
设计文档: docs/.req-discuss/{域}/{需求名}/.task/design-consensus.md
逐任务审查: docs/.req-discuss/{域}/{需求名}/.task/review/
收尾验收: docs/.req-discuss/{域}/{需求名}/.task/acceptance.md
影响模块: {模块列表}

后续人工操作：迁移（如有 migrations）、测试验收、上线发布
```

---

## 异常处理

### BLOCKED 状态
阶段 2 汇总设计时如果发现接口冲突，progress.md 会标记为 BLOCKED。
- `/php-workflow status` 会显示 BLOCKED 原因
- 用户解决冲突后，执行 `/php-workflow next` 重新触发阶段 2

### 阶段回退
- 阶段 3 设计审核不通过（清单有缺项）→ `/php-workflow next` 重新触发阶段 2 补充设计后再审
- 阶段 4 复杂任务 plan 不达标 → 打回 architect/planner 重出 plan，确认后才编码；不影响其他任务
- 阶段 4 CR 人工裁决后改写/复验不达标 → 在同一任务内重跑改写⑤+复验⑥，直至已采纳问题修复且 phpunit 绿 + php -l 通过；该任务不 DONE 不影响其他任务
- **阶段 4/5 发现设计或需求层缺陷（局部改写补不了）→ `/php-workflow rework`**：按根因层级回退（实现/设计/需求），级联重做受影响任务，详见 rework.md
- 阶段 5 收尾验收发现**单任务实现问题** → 退回对应任务，重走该任务 CR 扫描→人工确认→改写闭环后再重跑收尾验收；发现**设计错** → 用 `/php-workflow rework`（设计级）

### 中断恢复
流程可以在任意阶段中断。下次执行 `/php-workflow next` 时，从 progress.md 记录的当前阶段恢复（多里程碑下从选中里程碑的当前阶段恢复）。
