---
name: yunxiao-req-stats
description: 获取云效项目中需求评审结果统计
---

# 云效需求生命周期统计

## 参数

| 参数              | 说明                                                      | 必填 | 默认值   |
| ----------------- | --------------------------------------------------------- | ---- | -------- |
| `space_id`        | 云效项目ID                                                | 是   | -        |
| `organization_id` | 云效组织ID（可选：从上下文中获取）                        | 否   | -        |
| `range`           | 创建/关闭的日期范围，自然语言解析如 `"昨天"`、`"最近7天"` | 否   | 本月至今 |

## 固定常量

以下 ID 为硬编码固定值，无需调用 API 动态获取：

**<type_id>: 工作项类型 ID**
| 类型       | ID                         |
| ---------- | -------------------------- |
| 产品类需求 | `9uy29901re573f561d69jn40` |
| 技术类需求 | `bca48ee2a0976d38f4802fae` |

**<status_id> : 状态 ID（用于 advancedConditions）**
| 状态     | ID                           |
| -------- | ---------------------------- |
| 待处理   | `100005`                     |
| 待评审   | `b6d1af1f9bd7ed8b3a79e27a11` |
| 评审通过 | `bc5e4a3a72ef6f7c0ecdac11ee` |
| 评审驳回 | `62a829f0a33157f511cc6379a5` |
| 已完成   | `100014`                     |
| 已关闭   | `100085`                     |
| 已取消   | `141230`                     |



## advancedConditions 模板

仅仅使用 : advancedConditions 来组合查询状态和类型

```json
// 按类型查询, 支持传入列表
{"conditionGroups":[[{"fieldIdentifier":"workitemType","operator":"CONTAINS","value":["<type_id>"],"className":"workitemType","format":"list"}]]}

// 限定状态查询, 支持传入列表
{"conditionGroups":[[{"fieldIdentifier":"status","operator":"CONTAINS","value":["<status_id>"],"className":"status","format":"list"}]]}

// 同时限定类型+状态
{"conditionGroups":[[{"fieldIdentifier":"workitemType","operator":"CONTAINS","value":["<type_id>"],"className":"workitemType","format":"list"},{"fieldIdentifier":"status","operator":"CONTAINS","value":["<status_id>"],"className":"status","format":"list"}]]}

// gmtCreate 日期范围查询 (BETWEEN) — Step 2 使用
{"conditionGroups":[[{"fieldIdentifier":"workitemType","operator":"CONTAINS","value":["<type_id>"],"className":"workitemType","format":"list"},{"fieldIdentifier":"gmtCreate","operator":"BETWEEN","value":["<start_iso> 00:00:00"],"toValue":"<end_iso> 23:59:59","className":"dateTime","format":"input"}]]}

// gmtStatusChanged 日期范围查询 (BETWEEN) — Step 3 使用
{"conditionGroups":[[{"fieldIdentifier":"workitemType","operator":"CONTAINS","value":["<type_ids>"],"className":"workitemType","format":"list"},{"fieldIdentifier":"gmtStatusChanged","operator":"BETWEEN","value":["<start_iso> 00:00:00"],"toValue":"<end_iso> 23:59:59","className":"dateTime","format":"input"}]]}

// 多类型 + gmtCreate BETWEEN（产品类创建数）
{"conditionGroups":[[{"fieldIdentifier":"workitemType","operator":"CONTAINS","value":["9uy29901re573f561d69jn40"],"className":"workitemType","format":"list"},{"fieldIdentifier":"gmtCreate","operator":"BETWEEN","value":["2026-05-01 00:00:00"],"toValue":"2026-05-11 23:59:59","className":"dateTime","format":"input"}]]}

// 多类型 + gmtStatusChanged BETWEEN（关闭总数）
{"conditionGroups":[[{"fieldIdentifier":"workitemType","operator":"CONTAINS","value":["9uy29901re573f561d69jn40","bca48ee2a0976d38f4802fae"],"className":"workitemType","format":"list"},{"fieldIdentifier":"gmtStatusChanged","operator":"BETWEEN","value":["2026-05-01 00:00:00"],"toValue":"2026-05-11 23:59:59","className":"dateTime","format":"input"}]]}
```

## 功能

输出四个维度的需求统计，每项均区分 **产品类需求** 和 **技术类需求**：

1. **当前所有未评审的需求** — 状态为「待处理」
2. **当前所有待评审的需求** — 状态为「待评审」
3. **当前时间范围内创建的需求总数** — 按创建时间筛选
4. **当前时间范围内关闭的需求总数** — 状态阶段为已完成/已取消 且状态更新时间在范围内
5. **已评审但待计划的需求** — 状态是「评审通过」

第 4 项附带详细清单（ID / 标题 / 负责人 / 优先级 / 创建时间 / 链接）。

---

## 工作流

### Step 0：准备工作

使用 `scripts/stats.py` 中的 `parse_days()` 函数解析日期范围：

```bash
uv run scripts/stats.py --parse-days "<range>"
```

返回格式：
```json
{"label": "5月", "start_iso": "2026-05-01", "end_iso": "2026-05-31"}
```

> Step 2/3 中的日期范围使用 `advancedConditions` 中的 `gmtCreate` / `gmtStatusChanged` BETWEEN 查询，无需使用 MCP 内置时间参数。

---

### Step 1：未评审需求数量

取待处理总数，服务端精确计数：

```
mcp__yunxiao__search_workitems(
    organizationId, spaceIdentifier, category: Req, perPage: 1, includeDetails: false,
    advancedConditions: '...'
)
→ pagination.total = 产品类待处理总数（≈ 未评审数上限）
```

重复获取技术类数据。**共 2 次 MCP 调用**。


### Step 2：创建于范围内数量

对每种类型各 1 次，取 pagination.total。**共 2 次**：

```
mcp__yunxiao__search_workitems(
    organizationId, spaceIdentifier: '<space_id>', category: Req,
    advancedConditions: '<advanced_conditions_json>',
    perPage: 1, includeDetails: false
)
→ pagination.total = 该产品类创建数
```

advancedConditions 中使用 gmtCreate BETWEEN 查询：

```json
{"conditionGroups":[[{"fieldIdentifier":"workitemType","operator":"CONTAINS","value":["<type_id>"],"className":"workitemType","format":"list"},{"fieldIdentifier":"gmtCreate","operator":"BETWEEN","value":["<start_iso> 00:00:00"],"toValue":"<end_iso> 23:59:59","className":"dateTime","format":"input"}]]}
```

示例：
```json
{"conditionGroups":[[{"fieldIdentifier":"workitemType","operator":"CONTAINS","value":["9uy29901re573f561d69jn40"],"className":"workitemType","format":"list"},{"fieldIdentifier":"gmtCreate","operator":"BETWEEN","value":["2026-05-01 00:00:00"],"toValue":"2026-05-11 23:59:59","className":"dateTime","format":"input"}]]}
```

---

### Step 3：关闭于范围内数量

将两种类型 + 两个 statusStage 合并，单次查询即可。

**推荐：一次查询拿到合计**（仅 1 次 MCP 调用）：

```
mcp__yunxiao__search_workitems(
    organizationId, spaceIdentifier: '<space_id>', category: Req,
    advancedConditions: '<advanced_conditions_json>',
    perPage: 1, includeDetails: false
)
→ pagination.total = 两类合计关闭总数
```

advancedConditions 中使用 gmtStatusChanged BETWEEN 查询：

```json
{"conditionGroups":[[{"fieldIdentifier":"workitemType","operator":"CONTAINS","value":["<type_ids>"],"className":"workitemType","format":"list"},{"fieldIdentifier":"gmtStatusChanged","operator":"BETWEEN","value":["<start_iso> 00:00:00"],"toValue":"<end_iso> 23:59:59","className":"dateTime","format":"input"}]]}
```

如需分类后的细分数值，则分两次调用（各传单个 type_id），共 2 次。

---

### Step 4：已评审待计划「评审通过」清单 + 数量

**Step 4a — 总量（分页优先）**：先查待处理总数：

```
mcp__yunxiao__search_workitems(
    organizationId, spaceIdentifier: '<space_id>', category: Req,
    perPage: 1, includeDetails: false,
    advancedConditions: '...'
)
→ pagination.total = 待处理总数（近似上限）
```

**Step 4b — 明细清单**：拉一页并本地筛选：

```
mcp__yunxiao__search_workitems(
    organizationId, spaceIdentifier: '<space_id>', category: Req,
    perPage: 200, includeDetails: true,
    advancedConditions: '...'
)
```

若 total > 200，仅展示第一页内的清单并注明范围限制。

---

### Step 5：组装数据并运行统计分析

将 Step 1-4 的结果组装为 JSON 写入临时文件：

```json
{
  "_counts": {
    "not_reviewed_product": N, "not_reviewed_technical": N,
    "created_product": N, "created_technical": N,
    "closed_product": N, "closed_technical": N
  },
  "_items": [已评审待计划的 item 列表],
  "items": []
}
```

调用 stats.py：

```bash
uv run scripts/stats.py <json-file> "<label>" <organization_id>
```

stats.py 检测 `_counts` 存在时进入**分页优先模式**，直接使用该字段作为 counts 来源。

---

### Step 6：生成报告

工作项链接格式：

```
https://devops.aliyun.com/organization/<organization_id>/work/workitems/<identifier>
```

## 输出格式

ALWAYS use this exact markdown table format:

```
## 需求生命周期统计

| 统计项                    | 数量  |
| ------------------------- | ----- |
| **未评审需求总数**        | **N** |
| └ 产品类需求              | N     |
| └ 技术类需求              | N     |
| **`{range}`创建需求总数** | **N** |
| └ 产品类需求              | N     |
| └ 技术类需求              | N     |
| **`{range}`关闭需求总数** | **N** |
| └ 产品类需求              | N     |
| └ 技术类需求              | N     |

## 已评审待计划需求

| 统计项               | 数量  |
| -------------------- | ----- |
| **已评审待计划总数** | **N** |
| └ 产品类需求         | N     |
| └ 技术类需求         | N     |

## 已评审待计划清单

| ID  | 标题 | 负责人 | 优先级 | 创建时间 | 评审结论 | 链接 |
| --- | ---- | ------ | ------ | -------- | -------- | ---- |
| xxx | xxx  | xxx    | xxx    | xxx      | xxx      | xxx  |
```
