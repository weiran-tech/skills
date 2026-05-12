---
name: yunxiao-bug-stats
description: 获取云效项目中「线上故障」类型工作项的统计数据。使用分页优先模式，通过 advancedConditions 服务端过滤，直接取 pagination.total 提升性能，无需拉取全量数据。
---

# 云效线上故障统计

## 参数

| 参数              | 说明                                                      | 必填 | 默认值   |
| ----------------- | --------------------------------------------------------- | ---- | -------- |
| `organization_id` | 云效组织ID（从 CLAUDE.md 上下文中获取）                   | 否   | -        |
| `space_id`        | 云效项目ID                                                | 是   | -        |
| `range`           | 创建/关闭的日期范围，自然语言解析如 `"昨天"`、`"最近7天"` | 否   | 本月至今 |
| `labels`          | 标签筛选，逗号分隔的标签ID，如 `"labelId1,labelId2"`      | 否   | 不筛选   |

## 固定常量

以下 ID 为硬编码固定值，无需调用 API 动态获取：

**线上故障类型 ID**：`bba77181ef64f834248a0175`

**状态 ID**（用于 advancedConditions）：
| 状态   | ID       |
| ------ | -------- |
| 已关闭 | `100085` |

## advancedConditions 模板

使用 `advancedConditions` 组合查询条件，直接从服务端获取统计数量, **注意**：advancedConditions 是 json 字符串, 并非 json 对象

```json
// 按类型查询, 支持传入列表
{"conditionGroups":[[<condition1>, <condition2>]]}

// 组合 condition, 支持列表组合

// condition : 限定工作项类型为线上故障
{"fieldIdentifier":"workitemType","operator":"CONTAINS","value":["bba77181ef64f834248a0175"],"className":"workitemType","format":"list"}

// condition : 限定状态为未关闭（NOT IN 已关闭列表）
{"fieldIdentifier":"status","operator":"NOT_IN","value":["100085"],"className":"status","format":"list"}

// condition : 创建时间日期范围查询 (BETWEEN)
{"fieldIdentifier":"gmtCreate","operator":"BETWEEN","value":["<start_iso> 00:00:00"],"toValue":"<end_iso> 23:59:59","className":"dateTime","format":"input"}

// condition : 状态变更时间日期范围查询 (BETWEEN)
{"fieldIdentifier":"updateStatusAt","operator":"BETWEEN","value":["<start_iso> 00:00:00"],"toValue":"<end_iso> 23:59:59","className":"dateTime","format":"input"}

// condition : 标签筛选（多选 OR 逻辑）
{"fieldIdentifier":"labels","operator":"CONTAINS_ANY","value":["labelId1","labelId2"],"className":"labels","format":"list"}
```

## 功能

输出三个维度的线上故障统计 + 未解决清单：

1. **当前所有未解决的线上故障** - 状态非「已关闭」
2. **当前时间范围内创建的线上故障总数** - 按创建时间筛选
3. **当前时间范围内关闭的线上故障总数** - 状态为已关闭 且 状态更新时间在范围内
4. **未解决故障详细清单** - 按负责人分组展示，带 Emoji 标识

支持**标签筛选**：可多选标签，包含任意一个选中标签的故障即匹配。

---

## 工作流

### Step 0：交互式询问参数（单独调用时）

当用户直接调用 `/yunxiao-bug-stats` 且未提供参数时，使用 `AskUserQuestion` 交互式询问：

| 参数       | 说明     | 必填 | 默认值   | 询问方式                                                            |
| ---------- | -------- | ---- | -------- | ------------------------------------------------------------------- |
| `space_id` | 项目ID   | 是   | -        | 单选，先调用 `mcp__yunxiao__search_projects` 列出用户可见项目供选择 |
| `range`    | 日期范围 | 否   | 本月至今 | 接受自然语言，如 `"昨天"`、`"最近7天"`、`"2026-05-01 - 2026-05-11"` |

> 注意：如果用户已在对话中明确了参数（如 `/yunxiao-bug-stats space_id=xxx`），跳过对应询问。

### Step 1：解析日期范围

使用 `scripts/stats.py` 中的 `parse_days()` 函数解析日期范围：

```bash
uv run scripts/stats.py --parse-days "<range>"
```

返回格式：
```json
{"label": "5月", "start_iso": "2026-05-01", "end_iso": "2026-05-31"}
```

> Step 2-5 中的日期范围使用 `advancedConditions` 中的日期 BETWEEN 查询，无需使用 MCP 内置时间参数。

---

### Step 2：未解决线上故障数量

取服务端精确计数，`perPage: 1` 只取 `pagination.total`, 条件 : 线上故障类型 + 状态NOT_IN已关闭

```
mcp__yunxiao__search_workitems(
    organizationId, spaceId, category: Bug, perPage: 1, includeDetails: false,
    advancedConditions: '...'
)
→ pagination.total = 未解决线上故障总数
```

**共 1 次 MCP 调用**

### Step 3：范围内创建的线上故障数量

对线上故障类型 + 创建时间范围过滤，取 `pagination.total`, 条件 : 线上故障类型 + 创建时间范围

```
mcp__yunxiao__search_workitems(
    organizationId, spaceId: '<space_id>', category: Bug, perPage: 1, includeDetails: false,
    advancedConditions: '...'
)
→ pagination.total = 范围内创建的线上故障总数
```

**共 1 次 MCP 调用**

### Step 4：范围内关闭的线上故障数量

线上故障类型 + 状态为已关闭 + 状态更新时间在范围内，取 `pagination.total`, 条件 : 线上故障类型 + 状态为已关闭 + 状态更新时间在范围内

```
mcp__yunxiao__search_workitems(
    organizationId, spaceId: '<space_id>', category: Bug, perPage: 1, includeDetails: false,
    advancedConditions: '...'
)
→ pagination.total = 范围内关闭的线上故障总数
```

**共 1 次 MCP 调用**

### Step 5：未解决线上故障明细清单

拉取一页数据用于展示清单（最多 200 条，超过则注明展示限制）, 条件 : 线上故障类型 + 状态NOT_IN已关闭

```
mcp__yunxiao__search_workitems(
    organizationId, spaceId: '<space_id>', category: Bug,
    perPage: 200, includeDetails: true,
    advancedConditions: '...'
)
```

若 `total > 200`，仅展示第一页内的清单并注明范围限制。

**共 1 次 MCP 调用**

---

### Step 6：组装数据并运行统计分析

将 Step 2-5 的结果组装为 JSON 写入临时文件：

```json
{
  "_counts": {
    "total": N,
    "unresolved": N,
    "created": N,
    "closed": N
  },
  "_items": [未解决故障明细列表]
}
```

调用 stats.py：

```bash
uv run scripts/stats.py <json-file> "<label>" <organization_id>
```

stats.py 检测到 `_counts` 存在时进入**分页优先模式**，直接使用该字段作为统计来源。

---

## 输出格式

ALWAYS use this exact markdown table format：

```
## 线上故障统计

| 统计项                      | 数量  |
| --------------------------- | ----- |
| **当前所有未解决线上故障**  | **N** |
| **`{label}`创建的线上故障** | **N** |
| **`{label}`关闭的线上故障** | **N** |

## 未解决故障清单（按负责人分组）

### 👤 负责人A（X 个故障）

| 优先级 | 严重程度 | 状态     | 编号 | 标题 | 创建时间         | 链接        |
| ------ | -------- | -------- | ---- | ---- | ---------------- | ----------- |
| 🟡 中   | ⚠️ 一般   | 🔧 处理中 | xxx  | xxx  | 2026-05-12 10:30 | [查看](...) |

### ❌ 未分配（X 个故障）

| 优先级 | 严重程度 | 状态     | 编号 | 标题 | 创建时间         | 链接        |
| ------ | -------- | -------- | ---- | ---- | ---------------- | ----------- |
| 🔴 紧急 | 💥 致命   | ❓ 待确认 | xxx  | xxx  | 2026-05-12 10:30 | [查看](...) |

## 状态统计摘要

| 状态     | 数量 |
| -------- | ---- |
| 🔧 处理中 | X    |
| ❓ 待确认 | X    |

## 优先级统计摘要

| 优先级 | 数量 |
| ------ | ---- |
| 🔴 紧急 | X    |
| 🟠 高   | X    |
| 🟡 中   | X    |
```

### Emoji 说明

| 类型         | 标识 | 值            |
| ------------ | ---- | ------------- |
| **优先级**   | 🔴    | 紧急/最高     |
|              | 🟠    | 高/较高       |
|              | 🟡    | 中/普通       |
|              | 🟢    | 低/较低       |
| **严重程度** | 💥    | 致命          |
|              | 🔥    | 严重          |
|              | ⚠️    | 一般          |
|              | 📝    | 轻微          |
| **状态**     | ❓    | 待确认        |
|              | 📋    | 待处理        |
|              | 🔧    | 处理中/进行中 |
|              | ✅    | 已修复/已解决 |
|              | ⏸️    | 挂起中/暂停   |
|              | 🔒    | 已关闭        |
|              | 💻    | 开发中        |
|              | 🧪    | 测试中        |
|              | 🔍    | 验证中        |
|              | 🚀    | 发布中        |
