# 阶段 5：收尾验收（REVIEWING）+ 异常处理

> 执行阶段 5 收尾验收、或处理 BLOCKED / 阶段回退 / 中断恢复时读本文件。

## 阶段 5：收尾验收

逐任务审查已在阶段 4 完成，本阶段只做**全局回归与一致性把关**，由独立 verifier 执行（不与编码共享上下文）。

**执行**：
```
verifier "
对需求 {域}/{需求名} 做收尾验收（只读，不改任何代码）：
1. 确认 progress.md 任务清单全部已勾选、各任务审查结论均为 PASSED
2. 全量回归：vendor/bin/phpunit 全绿
3. 对本次变更涉及的文件执行 php -l 语法校验全部通过（phpstan 默认不纳入验收）
4. 跨模块一致性：对照 .task/design-consensus.md（注意参考其返工修订和 plan 同步记录，以最新契约为准）与 docs/cross-module.md，校验 Event/Listener、Service 调用契约闭合
5. 迁移检查：如涉及 modules/*/resources/migrations，确认迁移与回滚可用
6. 结果写入 docs/discuss/{需求ID}/.task/acceptance/acceptance.md，**严格按以下格式**：

   ## 验收结果: {PASSED | FAILED}

   ## 检查项
   - [x/✗] progress.md 任务清单全部 DONE
   - [x/✗] phpunit 全绿（附执行输出摘要）
   - [x/✗] php -l 语法校验通过
   - [x/✗] 跨模块契约闭合
   - [x/✗] 迁移可用（无迁移则标 N/A）

   ## 问题清单（PASSED 时留空）
   ### [1] 严重度: {MAJOR|MINOR} — {一句话标题}
   - 关联任务: {X.Y}
   - 文件: {路径:行号}
   - 问题: {具体描述}
   - 建议修复: {修复方向}

   不要修改任何代码文件，只产出报告。

Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"
```

**★ verifier 返回后，主 Agent 必须立刻执行以下动作（缺一不可，禁止静默结束本轮）**：
1. **读取** verifier 写出的 `docs/discuss/{需求ID}/.task/acceptance/acceptance.md`（以报告文件为准，不以 verifier 返回文本为准）
2. **回写** progress.md 并更新里程碑进度表
3. **按结果分支处理**：

**A. 验收通过（PASSED，无问题项）**：
- 回写 progress.md 阶段 5 状态为 COMPLETED
- 向用户输出：逐项列 `phpunit ✓ / php -l ✓ / 跨模块契约 ✓ / 迁移 ✓`，输出「收尾验收通过，需求/里程碑 COMPLETED」+ 完成摘要（见下方流程完成输出）
- 多里程碑提示用 `/workflow use #{下一个里程碑}` 推进或全部完成
- 提示用户可执行 `/workflow summary` 产出交付清单

**B. 验收不通过（FAILED，有问题项）→ 进入人工确认门**：
- 回写 progress.md 阶段 5 状态为 **PENDING_ACCEPT_REVIEW**
- **向用户输出问题清单**，逐条列出 `#编号 [严重度] 关联任务 文件:行 — 一句话问题 — 建议修复`
- **明确提示**：
  ```
  验收发现 {N} 个问题，请逐条审阅：
  - 确认问题属实的标注 ACCEPTED
  - 不需要修复的标注 REJECTED（附理由）
  - 修复方式需调整的标注 MODIFIED（附说明）
  - 如果问题属于设计/需求层缺陷，建议使用 /workflow rework

  裁决完成后执行 /workflow approve 推进修复
  ```
- **停在 PENDING_ACCEPT_REVIEW 等待用户**，绝不自动派 executor 修复

**C. 验收发现设计错 / 多任务受牵连** → 在问题清单中标注，提示用户使用 `/workflow rework`（设计级，见 rework.md）

4. 不许停在"verifier 已完成"而不给结果与下一步

> 与 CR 扫描同理：**子 agent 跑完 ≠ 流程推进**。verifier 一返回，主 Agent 就要读 acceptance.md、回写状态、把验收结论和下一步打给用户。**verifier 只产出问题清单，绝不直接改代码——与 code-reviewer 同理。**

### ★ 验收人工确认门（PENDING_ACCEPT_REVIEW）

与阶段 4 CR 人工门机制相同：
- 用户逐条裁决每个问题：`ACCEPTED`（要改）/ `REJECTED`（不改，附理由）/ `MODIFIED`（改法调整，附说明）
- 裁决方式：直接在 `acceptance.md` 问题清单标注，或口头告知由主 Agent 回填
- 全部裁决完成后，用户执行 `/workflow approve`
- **⚠️ 只有用户显式输入 `/workflow approve` 才算裁决锁定。** 用户口头说裁决结果是在提供裁决信息，主 Agent 应回填到 acceptance.md，但不得自动推进到修复

### ★ approve 后修复（ACCEPT_FIXING）

`/workflow approve` 确认后：
- **零问题 / 全部 REJECTED**（无需修复）→ 直接置 COMPLETED
- **有 ACCEPTED/MODIFIED 项** → 按关联任务分组，对每个受影响任务派单独 executor 修复（只改已采纳项），修复后重跑收尾验收（重新走本阶段完整流程）

```
executor "
按验收裁决修复任务 [{模块名} · {任务标题}]，工作范围 modules/{模块名}/：
只处理 .task/acceptance/acceptance.md 中裁决为 ACCEPTED / MODIFIED 且关联本任务的问题（REJECTED 的不动）。
逐条修复后在该问题下标注『已修复』并简述改动。
修复后重跑 vendor/bin/phpunit modules/{模块名}/tests 与对改动文件 php -l 确认通过。
遵守 CLAUDE.md 架构规则。Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"
```

修复完成后，**必须重新走收尾验收**（再次启动 verifier），确认问题已修复且无新回归。

**流程完成输出**：
```
需求 [{域}/{需求名}] 已完成自动化流程

讨论文档: docs/discuss/{需求ID}.md
设计文档: docs/discuss/{需求ID}/.task/design-consensus.md
逐任务审查: docs/discuss/{需求ID}/.task/review/
收尾验收: docs/discuss/{需求ID}/.task/acceptance/acceptance.md
影响模块: {模块列表}

后续人工操作：迁移（如有 migrations）、测试验收、上线发布
```

---

## 异常处理

### BLOCKED 状态
阶段 2 汇总设计时如果发现接口冲突，progress.md 会标记为 BLOCKED。
- `/workflow status` 会显示 BLOCKED 原因
- 用户解决冲突后，执行 `/workflow next` 重新触发阶段 2

### 阶段回退
- 阶段 3 设计审核不通过（清单有缺项）→ `/workflow next` 重新触发阶段 2 补充设计后再审
- 阶段 4 复杂任务 plan 不达标 → 打回 architect/planner 重出 plan，确认后才编码；不影响其他任务
- 阶段 4 CR 人工裁决后改写/复验不达标 → 在同一任务内重跑改写⑤+复验⑥，直至已采纳问题修复且 phpunit 绿 + php -l 通过；该任务不 DONE 不影响其他任务
- **阶段 4/5 发现设计或需求层缺陷（局部改写补不了）→ `/workflow rework`**：按根因层级回退（实现/设计/需求），级联重做受影响任务，详见 rework.md
- 阶段 5 收尾验收发现**单任务实现问题** → 退回对应任务，重走该任务 CR 扫描→人工确认→改写闭环后再重跑收尾验收；发现**设计错** → 用 `/workflow rework`（设计级）

### 中断恢复
流程可以在任意阶段中断。下次执行 `/workflow next` 时，从 progress.md 记录的当前阶段恢复（多里程碑下从选中里程碑的当前阶段恢复）。
