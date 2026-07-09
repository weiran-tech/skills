# 阶段 3：设计审核（PENDING_DESIGN_REVIEW）

> 执行阶段 3 / 处理 `/workflow approve` 的设计审核分支前读本文件。

**清单式人工审核门，不是橡皮图章。** approve 前必须逐项核对 design-consensus 的必含清单，任一项缺失/过浅 → 打回阶段 2 补充，不得 approve。

**审核清单（主 Agent 先自查并把结论附在提示里，再交人工确认）**：
- [ ] 对外契约齐全（接口/Event/Listener/跨模块调用）
- [ ] 模块边界清晰（谁该改、谁不该改）
- [ ] 关键机制决策有"为什么"（不是只有结论）
- [ ] 验收标准可执行
- [ ] 未决项已登记成表，且每条有处置方式（不许有悬空 TODO）
- [ ] 简单任务的实现要点足以直接开工；复杂任务已在 dev-tasks 标记 `复杂`（编码前出 plan）

提示内容：
```
分析与设计已完成，等待人工审核（清单式）。

设计文档: docs/discuss/{需求ID}/.task/design-consensus.md
任务拆分: docs/discuss/{需求ID}/.task/dev-tasks.md
{如有冲突} 冲突记录: docs/discuss/{需求ID}/.task/conflicts.md

主 Agent 自查结论: {逐项 ✓/✗ + 缺项说明}
未决项: {N 条，处置摘要}
复杂任务: {列出将在阶段 4 出 plan 的任务}

操作: 逐项核对后执行 /workflow approve；若有缺项，先让其补充再审
```

**⚠️ 只有用户显式输入 `/workflow approve` 才算审批通过。** 用户对设计的讨论、补充要求、确认某个细节正确、甚至说"没问题"，都不等于 approve。收到非 approve 消息时，视为反馈并据此调整设计，然后继续等待 `/workflow approve`。

**approve 通过后**：在 design-consensus.md 末尾追加 `## 设计确认: APPROVED`，状态置 DEVELOPING，提示用户 `/workflow next` 进入阶段 4（见 stage-4-dev.md）。
