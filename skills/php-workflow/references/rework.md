# rework：子需求返工通道（v2 版本制度）

**返工通道**：当任意阶段（通常阶段 4/5 人工审核）发现设计或实现缺陷，需要回退重做时使用。处理"局部改写补不了、必须回到设计甚至需求层"的情况。

v2 重构后，返工按**子需求**粒度执行（spec C10），不再涉及 v1 的里程碑维度。所有版本（version）状态门禁约束来自 `commands.md §C rework` 段，本文件展开返工具体执行步骤。

---

## `/php-workflow rework {子需求ID}`

### 处理步骤

1. **解析子需求 ID**：格式 `{service-name}}/{父需求名}#{子需求名}`（按最后一个 `#` 拆分；解析规则见 `templates.md §0`）。缺参 → 报错 + 列出可 rework 的子需求（详见 `commands.md §C rework`）。

2. **校验子需求存在**：`docs/discuss/{service-name}}/{父需求名}/.task/{子需求名}/metadata.md` 必须存在；不存在报错 `[字段 subReqId {X}] 子需求不存在`。

3. **校验子需求状态**：读 `metadata.md.currentState`，要求 `== COMPLETED`
   - 非 COMPLETED → 报错：`[字段 currentState {X}] rework 要求 COMPLETED 状态。建议：用 /php-workflow next {X} 推进到 COMPLETED 后再 rework`

4. **强门禁 — 版本状态校验**（AC19/D22，**先于返工单写入**）：

   | 版本状态 | 门禁结果 | 错误信息 / 下一步 |
   |---------|---------|------------------|
   | `DRAFT` | 通过 | 允许 rework |
   | `IN_PROGRESS` | 通过 | 允许 rework |
   | `READY` | 通过 | 允许 rework |
   | `RELEASED` | **拒绝** | `[字段 versionStatus RELEASED] 版本已发布，禁止 rework。建议：如需修复请新建子需求并 /php-workflow version add-sub 加入新版本` |
   | `ARCHIVED` | **拒绝** | `[字段 versionStatus] 版本已归档，禁止 rework。建议：版本已永久封存，需修复请新建版本` |

   - 校验来源：读 `metadata.md.versionBinding` → 读 `docs/version/{版本号}.status`
   - DRAFT 状态下子需求 COMPLETED 是异常态（如出现，按"理论不应存在"报错，提示检查 metadata.md）

5. **与用户确认缺陷描述与根因层级**（实现级 / 设计级 / 需求级），自动获取当前日期 `{YYYY-MM-DD}`

6. **查找返工轮次 R{N}**：扫描 `docs/discuss/{service-name}}/{父需求名}/.task/{子需求名}/rework/` 目录，取最大 `R{n}-` 编号 +1；首次返工 R1

7. **写返工单文件**：`docs/discuss/{service-name}}/{父需求名}/.task/{子需求名}/rework/R{N}-{YYYY-MM-DD}.md`
   - 内容含：返工轮次、日期、根因层级、缺陷描述、初判受影响任务/模块、依赖扩散结果

8. **依赖扩散（自动算 + 人工确认）**：
   - 读 `docs/discuss/{service-name}}/{父需求名}/.task/{子需求名}/dev-tasks.md` 依赖图
   - 找出"依赖被改设计 / 被改任务"的下游子需求（跨子需求依赖）
   - 连同初判受影响任务一起**列给用户确认**（可增删）
   - 确认后才把这些子需求/任务置 TODO 并标 `(返工R{N})`
   - **未被勾选的 DONE 任务保留，不重复劳动**

9. **回写 metadata.md**：
   - `currentState: COMPLETED → ANALYZING`
   - `currentStage: 5 → 2`
   - `updatedAt: {当前 ISO 8601}`
   - 任务清单区追加"返工 R{N}"标记
   - 阶段产物引用表追加新返工单路径

10. **之后用 `/php-workflow next {子需求ID}` 正常推进重跑**——设计级先过阶段 3 重审，复杂任务重出 plan，再 code → CR → 收尾验收

---

## 按根因层级决定回退深度（action 改为子需求级）

| 根因层级 | 含义 | 回退动作 | 重跑范围（子需求级） |
|---------|------|---------|---------------------|
| **实现级** | 设计对、代码错 | 不动 design-consensus.md；当前子需求 `currentState: COMPLETED → ANALYZING` | 受影响任务回 TODO → 重 code → 重 CR（**仅当前子需求范围内**，不级联） |
| **设计级** | design-consensus.md 错 | 在 `design-consensus.md` 末尾追加 `## 返工修订 R{N}：{原因}`；当前子需求 `currentState: COMPLETED → ANALYZING` + 退回至阶段 2（ANALYZING）；阶段 3 重审 | **当前子需求** + **依赖被改设计的下游子需求** 级联回 ANALYZING；受影响任务回 TODO（复杂任务重出 plan）→ 重 code → 重 CR |
| **需求级** | 需求/理解本身错 | 回阶段 1：当前子需求 `currentState → DISCUSSING`；走 `/req-discuss`（**注意：v2 不再依赖 req-discuss skill**，改用本 skill 阶段 1 入口 + 阶段 2-5 重跑） | 视讨论结论确定；当前子需求 + 全部依赖该需求的子需求 级联回 DISCUSSING |

**关键约束**：
- 三个层级的 action 都基于**子需求**粒度执行；不存在"里程碑级返工"（v1 概念已废弃）
- 设计级 / 需求级的级联仅作用于**当前版本内**已绑定到同版本的下游子需求（version 文件 `subRequirements[]` 范围内）
- 跨版本的下游子需求（不在当前版本）需用户在新版本中独立处理

---

## 依赖扩散详解（AC19 + 步骤 8）

依赖扩散的目标：当返工当前子需求时，自动找出**所有**可能受影响的子需求，避免下游返工漏掉。

### 数据来源

子需求依赖图存于 `docs/discuss/{service-name}}/{父需求名}/.task/{子需求名}/dev-tasks.md`，含两类：
1. **任务级依赖**（当前子需求内）：任务 A 依赖任务 B
2. **子需求级依赖**（跨子需求）：子需求 X 依赖子需求 Y 的产物（如 Y 的 API、Y 的 DDL）

### 扩散算法

```
impact_set = {当前子需求}
queue = [当前子需求]
while queue 非空:
  sub_req = queue.pop()
  # 在 version.subRequirements[] 范围内查找下游
  for each sub_req' in version.subRequirements[]:
    if sub_req' 依赖 sub_req (dev-tasks.md 子需求级依赖图):
      impact_set.add(sub_req')
      queue.push(sub_req')
# 输出：影响集合 + 各自依赖路径
return impact_set
```

### 人工确认流程

```
依赖扩散结果（自动算出，依赖 dev-tasks.md）:

  受影响子需求（依赖当前返工子需求）:
    [1] payment/支付渠道重构#wechat
        依赖路径: 依赖 alipay 的 API POST /api/payment/alipay/refund
    [2] order/订单取消优化#子1
        依赖路径: 依赖 alipay 的 DDL ALTER TABLE payment_order ...

  [确认以上子需求都级联返工？可输入编号删减] (y/n/<编号列表>)
  > y
  ✓ 已确认 2 个下游子需求级联返工 R{N}
```

- 用户可输入编号列表删减（如 `> 2` 移除第 2 个）
- 用户输入 `n` 取消返工（不写返工单）
- 未被勾选的下游子需求保持当前状态，不重复劳动

---

## 返工单文件模板

路径：`docs/discuss/{service-name}}/{父需求名}/.task/{子需求名}/rework/R{N}-{YYYY-MM-DD}.md`

```markdown
# 返工单 R{N}

**子需求**: {service-name}}/{父需求名}#{子需求名}
**日期**: {YYYY-MM-DD}
**根因层级**: {实现级 | 设计级 | 需求级}
**版本绑定**: {版本号}（状态: {DRAFT | IN_PROGRESS | READY}）

## 缺陷描述
{详细描述缺陷；含重现步骤、影响范围}

## 初判受影响任务/模块
- 任务清单: {dev-tasks.md 中受影响的任务名}
- 模块影响: {涉及的代码模块}

## 依赖扩散结果
{列出经人工确认的下游子需求（含依赖路径）}

## 回退动作
{按根因层级展开：实现级 / 设计级 / 需求级 具体回退步骤}

## 重跑计划
{重 code → 重 CR → 收尾验收的时间安排}
```

---

## 错误信息规范

rework 命令错误信息统一三段式（AC18/D21）：

| 错误场景 | 错误信息 |
|---------|---------|
| 子需求不存在 | `[字段 subReqId {X}] 子需求不存在。建议：用 /php-workflow req show {父需求ID} 查看` |
| 非 COMPLETED 状态 | `[字段 currentState {X}] rework 要求 COMPLETED 状态。建议：用 /php-workflow next {X} 推进到 COMPLETED 后再 rework` |
| 版本已发布 | `[字段 versionStatus RELEASED] 版本已发布，禁止 rework。建议：如需修复请新建子需求并 /php-workflow version add-sub 加入新版本` |
| 版本已归档 | `[字段 versionStatus] 版本已归档，禁止 rework。建议：版本已永久封存，需修复请新建版本` |
| 缺参 | `[字段 subReqId] 缺失。建议：/php-workflow rework {service-name}}/{父需求名}#{子需求名}` |

---

## 与阶段 4 CR 改写的区别

| 维度 | CR 改写 | rework |
|------|--------|--------|
| 触发时机 | 阶段 4 CR 扫描发现问题 | 阶段 4/5 任意阶段人工审核 |
| 范围 | 任务内循环（小问题） | 跨任务/跨子需求级联（设计/需求层错） |
| 状态机变化 | 不回退状态 | `COMPLETED → ANALYZING`（或 `DISCUSSING`） |
| 产物 | review/CR 改写记录 | rework/R{N}-*.md 返工单 |
| 拿不准选哪个 | 只改当前任务能解决 → 用 CR 改写 | 牵动设计或别的子需求 → 用 rework |

rework 是**显式人工触发**，不自动判定"要返工"。

---

## 验收（AC19）

对 RELEASED 版本的子需求执行 rework → 报错：

```
[字段 versionStatus RELEASED] 版本已发布，禁止 rework。建议：如需修复请新建子需求并 /php-workflow version add-sub 加入新版本
```

对 ARCHIVED 版本的子需求执行 rework → 报错：

```
[字段 versionStatus] 版本已归档，禁止 rework。建议：版本已永久封存，需修复请新建版本
```