# followup：基于已完成需求发起新需求

> 处理 `/devops-workflow followup` 时读本文件。

基于已完成需求发起新需求——用于需求交付后追加功能、做优化、或处理遗留项。新需求独立走完整 5 阶段流程，但自动继承父需求的设计上下文作为参考。

## `/devops-workflow followup {已完成需求ID} [新需求名]`

1. **解析父需求 ID**（支持模糊匹配）。校验其 progress.md 状态为 **COMPLETED**；非 COMPLETED 则拒绝并提示：
   - 进行中的需求 → 用 `/devops-workflow next` 继续推进
   - 有设计/实现缺陷 → 用 `/devops-workflow rework`
2. 询问用户**新需求名**（未提供时）和**业务域**（默认沿用父需求的域）
3. **初始化新需求目录**：`{讨论根目录}{域}/{新需求名}/`
   - 创建 `docs/` 目录
   - **自动复制父需求的关键产出物到 `docs/parent/`**：
     - `design-consensus.md` → `docs/parent/design-consensus.md`（设计契约参考）
     - `change-manifest.md` → `docs/parent/change-manifest.md`（交付清单参考，如存在）
     - 多里程碑时额外复制 `design-foundation.md`（如存在）
   - 提示用户可在 `docs/` 放入新的参考文档
4. 创建 `.task/progress.md`（使用标准模板），**新增 `parent` 字段**：
   ```
   - 父需求: {域}/{父需求名}（已完成，设计参考见 docs/parent/）
   ```
   状态设为 `DISCUSSING`（而非直接 ANALYZING，因为需要先讨论增量变更）
5. 用户确认参考文档后，调用 `/devops-discuss` skill。**在 prompt 中附加上下文**：
   ```
   本需求基于已完成需求「{父需求名}」发起。
   父需求的设计契约见 docs/parent/design-consensus.md，交付清单见 docs/parent/change-manifest.md。
   讨论重点聚焦增量变更——新增/优化了什么、与父需求设计的差异点、是否需要调整已有契约。
   ```
6. **设为活动上下文**（写入 `{讨论根目录}.workflow-active`）
7. 提示用户讨论完成后 `/devops-workflow next` 进入分析与设计

**输出格式**：
```
已基于「{父需求名}」(COMPLETED) 创建后续需求:
  需求ID: {域}/{新需求名}
  父需求: {域}/{父需求名}
  设计参考: docs/parent/design-consensus.md

请将新的参考文档放入 docs/ 目录，放好后回复确认进入讨论。
```

> **与 `/devops-workflow start` 的区别**：`start` 从零开始，无父需求上下文；`followup` 自动继承设计产出物、讨论聚焦增量、progress.md 记录关联关系。后续阶段 2 分析时 analyst 会同时参考父需求设计和新讨论结论。
