# 阶段 5：收尾验收（REVIEWING）+ 异常处理

> 执行阶段 5 收尾验收、或处理 BLOCKED / 阶段回退 / 中断恢复时读本文件。

**工单目录基准**：`{讨论根目录}{域}/{需求名}/.task/`。本文件中所有 `.task/` 路径均相对于此。

## 阶段 5：收尾验收

逐任务审查已在阶段 4 完成，本阶段只做**全局回归与一致性把关**，由独立 verifier 执行（不与编码共享上下文）。

**执行**：
```
verifier "
对需求 {域}/{需求名} 做收尾验收（只读，不改任何代码）：
1. 确认 progress.md 任务清单全部已勾选、各任务审查结论均为 PASSED
2. 全量回归：按项目 .claude/rules/ 中定义的测试命令执行全量单测通过
3. 对本次变更涉及的文件按项目规则执行语法/编译检查全部通过（静态分析是否纳入验收由项目规则决定）
4. 跨模块一致性：对照 .task/design-consensus.md（注意参考其返工修订和 plan 同步记录，以最新契约为准）与 docs/cross-module.md，校验 Event/Listener、Service 调用契约闭合
5. 迁移检查：如涉及数据库迁移文件，确认迁移与回滚可用
6. 结果写入 {讨论根目录}{域}/{需求名}/.task/acceptance/acceptance.md，**严格按以下格式**：

   ## 验收结果: {PASSED | FAILED}

   ## 检查项
   - [x/✗] progress.md 任务清单全部 DONE
   - [x/✗] 全量单测通过（附执行输出摘要）
   - [x/✗] 语法/编译检查通过
   - [x/✗] 跨模块契约闭合
   - [x/✗] 迁移可用（无迁移则标 N/A）

   ## 问题清单（PASSED 时留空）
   ### [1] 严重度: {MAJOR|MINOR} — {一句话标题}
   - 关联任务: {X.Y}
   - 文件: {路径:行号}
   - 问题: {具体描述}
   - 建议修复: {修复方向}

   不要修改任何代码文件，只产出报告。

写入验收报告必须使用 Write 工具，禁止用 Bash heredoc/echo 写文件。
Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"
```

**★ verifier 返回后，主 Agent 必须立刻执行以下动作（缺一不可，禁止静默结束本轮）**：
1. **读取** verifier 写出的 `{讨论根目录}{域}/{需求名}/.task/acceptance/acceptance.md`（以报告文件为准，不以 verifier 返回文本为准）
2. **回写** progress.md 并更新里程碑进度表
3. **按结果分支处理**：

**A. 验收通过（PASSED，无问题项）**：

读取 `{讨论根目录}.workflow-config` 的 `auto_accept_pass` 配置（不存在或未配置视为 false）：

- **auto_accept_pass=true**：直接回写 progress.md 阶段 5 状态为 COMPLETED，不停门
- **auto_accept_pass=false（默认）**：回写 progress.md 阶段 5 状态为 COMPLETED（零问题无需裁决，但仍输出确认提示）

两种模式均输出：逐项列 `单测 ✓ / 语法检查 ✓ / 跨模块契约 ✓ / 迁移 ✓`，输出「收尾验收通过，需求/里程碑 COMPLETED」+ 完成摘要（见下方流程完成输出）
- 多里程碑提示用 `/devops-workflow use #{下一个里程碑}` 推进或全部完成

> 按 automation.md「auto_summary 协议」处理：auto_summary=true 时自动执行 `/devops-workflow summary` 产出交付清单，否则提示用户可手动执行 `/devops-workflow summary`。

**B. 验收不通过（FAILED，有问题项）→ 按 `auto_accept_fix` 协议分流**：

读取 `.workflow-config` 的 `auto_accept_fix`（不存在视为 false）：

**B1. `auto_accept_fix=true` 且问题均为实现级（非 design-level）时 → 自动修复循环**：
- 向用户输出问题清单 + 标注「auto_accept_fix: 自动修复第 {round}/2 轮」
- 将所有问题视为 ACCEPTED，按关联任务分组派 executor 修复
- 修复后重新启动 verifier 做全局回归
- 循环最多 2 轮（可配置 `auto_accept_fix_max=N`）
- **通过** → COMPLETED，按 automation.md「auto_summary 协议」处理
- **超限仍 FAILED** → 回写 `PENDING_ACCEPT_REVIEW`，走下方 B2 人工门

**B2. `auto_accept_fix=false`（默认）或含 design-level 问题或自动修复超限时 → 人工确认门**：
- 回写 progress.md 阶段 5 状态为 **PENDING_ACCEPT_REVIEW**
- **向用户输出问题清单**，逐条列出 `#编号 [严重度] 关联任务 文件:行 — 一句话问题 — 建议修复`
- **明确提示**：
  ```
  验收发现 {N} 个问题，请逐条审阅：
  - 确认问题属实的标注 ACCEPTED
  - 不需要修复的标注 REJECTED（附理由）
  - 修复方式需调整的标注 MODIFIED（附说明）
  - 如果问题属于设计/需求层缺陷，建议使用 /devops-workflow rework

  裁决完成后执行 /devops-workflow approve 推进修复
  ```
- **停在 PENDING_ACCEPT_REVIEW 等待用户**，绝不自动派 executor 修复

**C. 验收发现设计错 / 多任务受牵连** → 不进入自动修复循环（即使 `auto_accept_fix=true`），在问题清单中标注 design-level，提示用户使用 `/devops-workflow rework`（设计级，见 rework.md）

4. 不许停在"verifier 已完成"而不给结果与下一步

> 与 CR 扫描同理：**子 agent 跑完 ≠ 流程推进**。verifier 一返回，主 Agent 就要读 acceptance.md、回写状态、把验收结论和下一步打给用户。**verifier 只产出问题清单，绝不直接改代码——与 code-reviewer 同理。**

### ★ 验收人工确认门（PENDING_ACCEPT_REVIEW）

与阶段 4 CR 人工门机制相同：
- 用户逐条裁决每个问题：`ACCEPTED`（要改）/ `REJECTED`（不改，附理由）/ `MODIFIED`（改法调整，附说明）
- 裁决方式：直接在 `acceptance.md` 问题清单标注，或口头告知由主 Agent 回填
- 全部裁决完成后，用户执行 `/devops-workflow approve`
- **⚠️ 只有用户显式输入 `/devops-workflow approve` 才算裁决锁定。** 用户口头说裁决结果是在提供裁决信息，主 Agent 应回填到 acceptance.md，但不得自动推进到修复

### ★ approve 后修复（ACCEPT_FIXING）

`/devops-workflow approve` 确认后：
- **零问题 / 全部 REJECTED**（无需修复）→ 直接置 COMPLETED，按 automation.md「auto_summary 协议」处理
- **有 ACCEPTED/MODIFIED 项** → 按关联任务分组，对每个受影响任务派单独 executor 修复（只改已采纳项），修复后重跑收尾验收（重新走本阶段完整流程）

```
executor "
按验收裁决修复任务 [{范围标签} · {任务标题}]，工作范围限定在该任务的工作范围目录（见 dev-tasks.md）：
只处理 .task/acceptance/acceptance.md 中裁决为 ACCEPTED / MODIFIED 且关联本任务的问题（REJECTED 的不动）。
逐条修复后在该问题下标注『已修复』并简述改动。
修复后按项目 .claude/rules/ 中定义的测试命令重跑模块级单测，并按项目规则执行语法/编译检查确认通过。
遵守 CLAUDE.md 架构规则。Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"
```

修复完成后，**必须重新走收尾验收**（再次启动 verifier），确认问题已修复且无新回归。

**流程完成输出**：
```
需求 [{域}/{需求名}] 已完成自动化流程

讨论文档: {讨论根目录}{域}/{需求名}/discussion.md
设计文档: {讨论根目录}{域}/{需求名}/.task/design-consensus.md
逐任务审查: {讨论根目录}{域}/{需求名}/.task/review/
收尾验收: {讨论根目录}{域}/{需求名}/.task/acceptance/acceptance.md
影响模块: {模块列表}

后续人工操作：迁移（如有 migrations）、测试验收、上线发布
```

---

## 异常处理

### BLOCKED 状态
阶段 2 汇总设计时如果发现接口冲突，progress.md 会标记为 BLOCKED。
- `/devops-workflow status` 会显示 BLOCKED 原因
- 用户解决冲突后，执行 `/devops-workflow next` 重新触发阶段 2

### 阶段回退
- 阶段 3 设计审核不通过（清单有缺项）→ `/devops-workflow next` 重新触发阶段 2 补充设计后再审
- 阶段 4 复杂任务 plan 不达标 → 打回 architect/planner 重出 plan，确认后才编码；不影响其他任务
- 阶段 4 CR 人工裁决后改写/复验不达标 → 在同一任务内重跑改写⑤+复验⑥，直至已采纳问题修复且模块级单测通过 + 语法/编译检查通过；该任务不 DONE 不影响其他任务
- **阶段 4/5 发现设计或需求层缺陷（局部改写补不了）→ `/devops-workflow rework`**：按根因层级回退（实现/设计/需求），级联重做受影响任务，详见 rework.md
- 阶段 5 收尾验收发现**单任务实现问题** → 退回对应任务，重走该任务 CR 扫描→人工确认→改写闭环后再重跑收尾验收；发现**设计错** → 用 `/devops-workflow rework`（设计级）

### 中断恢复
流程可以在任意阶段中断。下次执行 `/devops-workflow next` 时，从 progress.md 记录的当前阶段恢复（多里程碑下从选中里程碑的当前阶段恢复）。
