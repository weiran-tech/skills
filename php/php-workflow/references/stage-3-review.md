# 阶段 3：设计审核（PENDING_DESIGN_REVIEW）

> 执行阶段 3 / 处理 `/php-workflow approve {子需求ID}` 的设计审核分支前读本文件。

**审核门在子需求级。** 5 阶段流程跑在每个子需求上，版本只是跨域聚合视图（spec C8/D10）。`approve` 必须显式传子需求 ID；不允许跳过审核或粘性活动指针（spec C6/D8）。

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

子需求 ID: {域}/{父需求名}#{子需求名}
设计文档: docs/discuss/{域}/{父需求名}/.task/{子需求名}/design-consensus.md
任务拆分: docs/discuss/{域}/{父需求名}/.task/{子需求名}/dev-tasks.md
{如有冲突} 冲突记录: docs/discuss/{域}/{父需求名}/.task/{子需求名}/conflicts.md

主 Agent 自查结论: {逐项 ✓/✗ + 缺项说明}
未决项: {N 条，处置摘要}
复杂任务: {列出将在阶段 4 出 plan 的任务}

操作: 逐项核对后执行 /php-workflow approve {子需求ID}；若有缺项，先让其补充再审
```

**approve 通过后**：在 `docs/discuss/{域}/{父需求名}/.task/{子需求名}/design-consensus.md` 末尾追加 `## 设计确认: APPROVED`，然后**回写 `metadata.md`**：
- `currentState`: `PENDING_DESIGN_REVIEW` → `DEVELOPING`
- `updatedAt`: 更新为当前时间（ISO 8601，例 `2026-07-06T14:30:00+08:00`）

**提示输出**：
```
设计审核通过。子需求 {子需求ID} 已进入 DEVELOPING 状态。

下一步: 执行 /php-workflow next {子需求ID} 进入阶段 4（开发与任务闭环）。
```

**缺参行为**：`/php-workflow approve` 无参时 → 立即停止并报错：
```
[字段 子需求ID] 必填，不能为空。建议：传入 /php-workflow approve {域}/{父需求名}#{子需求名}。
```

并在报错后扫描 `docs/discuss/{域}/{父需求名}/.task/{子需求名}/metadata.md` 列出所有 `currentState == PENDING_DESIGN_REVIEW` 的子需求作为可选项：
```
当前可审核的子需求：
- payment/支付渠道重构#alipay  (design-consensus: docs/discuss/payment/支付渠道重构/.task/alipay/design-consensus.md)
- order/订单取消优化#子需求1   (design-consensus: docs/discuss/order/订单取消优化/.task/子需求1/design-consensus.md)

请选择后执行：/php-workflow approve {子需求ID}
```