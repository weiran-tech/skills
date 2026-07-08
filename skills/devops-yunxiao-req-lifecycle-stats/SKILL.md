---
name: devops-yunxiao-req-lifecycle-stats
description: 获取云效项目中需求生命周期统计。统计未评审需求、本月创建/关闭需求、已评审待计划需求的数量与清单，按产品类/技术类分类。当用户需要"需求统计"、"需求概览"、"评审统计"、"需求分类统计"时使用此技能
---

# 云效需求生命周期统计

## 参数

| 参数              | 说明                                                        | 必填 | 默认值                       |
| ----------------- | ----------------------------------------------------------- | ---- | ---------------------------- |
| `space_id`        | 云效项目ID                                                  | 否   | `cbf6b94fbf645e67ec6626fac1` |
| `organization_id` | 云效组织ID（可选：从上下文中获取）                          | 否   | -                            |
| `range`           | 创建/关闭的日期范围，自然语言解析如 `"昨天"`、`"最近7天"`    | 否   | 本月至今                     |

## 功能

输出四个维度的需求统计，每项均区分 **产品类需求** 和 **技术类需求**：

1. **当前所有未评审的需求** — 状态为「待处理」且无评审结论或评审结论为空
2. **当前时间范围内创建的需求总数** — 按创建时间筛选
3. **当前时间范围内关闭的需求总数** — 状态阶段为已完成/已取消 且状态更新时间在范围内
4. **已评审但待计划的需求** — 有评审结论且为"通过"/"拒绝"，但状态仍为「待处理」

输出清单：
- 第 4 项附带详细清单（ID / 标题 / 负责人 / 优先级 / 创建时间 / 链接）

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

> **注意**: MCP 的 `createdAfter`/`updatedAfter`/`createdBefore`/`updatedBefore` 参数格式均为 `YYYY-MM-DD`。

使用 `mcp__yunxiao__list_work_item_types` 获取两种类型 ID：
- 名称包含"产品" → product_type_id
- 名称包含"技术" → technical_type_id

### Step 1：获取未评审需求数量（拉一页，遍历分类计数）

对每种类型调用 search_workitems 获取一页数据，遍历检查评审结论后计数：

```
mcp__yunxiao__search_workitems(
    organizationId, spaceId, category: Req,
    workitemType: <type_id>, perPage: 200, includeDetails: true
)
→ 遍历第一页 items，统计无评审结论的数量
→ 若 pagination.total <= 200（一页覆盖全部），结果为精确值；否则注明"仅基于前200条估算"
```

### Step 2：获取创建于范围内数量（直接用分页 total，不拉 items）

对每种类型调用一次，用 perPage=1 + includeDetails=false 只取分页信息：

```
mcp__yunxiao__search_workitems(
    organizationId, spaceId, category: Req,
    workitemType: <type_id>,
    createdAfter: "<start_iso>",
    createdBefore: "<end_iso>",
    perPage: 1, includeDetails: false
)
→ pagination.total 即为该类型在该范围内的创建总数
```

重复上述调用获取另一种类型的数据。共需 **2 次 MCP 调用**。

### Step 3：获取关闭于范围内数量（直接用分页 total，不拉 items）

因 statusStage 不支持 OR 逻辑，对每种类型分两次调用（completed + cancelled），将 pagination.total 相加：

```
# 类型A - 已完成（已完成对应 statusStage "4"）
mcp__yunxiao__search_workitems(
    organizationId, spaceId, category: Req,
    workitemType: <type_a_id>, statusStage: "4",
    updatedAfter: "<start_iso>", updatedBefore: "<end_iso>",
    perPage: 1, includeDetails: false
)

# 类型A - 已取消（已取消对应 statusStage "5"）
mcp__yunxiao__search_workitems(... statusStage: "5" ...)
→ 两次 pagination.total 相加 = 类型A本月关闭数
```

共需 **4 次 MCP 调用**（产品-完成、产品-取消、技术-完成、技术-取消）。

### Step 4：获取已评审待计划清单（需拉取明细）

调用 search_workitems 拉取待处理需求：

```
mcp__yunxiao__search_workitems(
    organizationId, spaceId, category: Req,
    perPage: 200, includeDetails: true
)
→ 遍历 items，筛选条件：有评审结论 且 状态未关闭
→ 收集符合要求的 item 详情
```

若 total > 200，则仅展示第一页内的已评审待计划清单，并在报告中注明。

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

stats.py 检测 `_counts` 存在时进入**分页优先模式**，直接使用该字段作为 counts 来源，不遍历 items 计数。`_items` 仅用于生成已评审待计划清单。

### Step 6：生成报告

按照下方「输出格式」生成最终报告。工作项链接格式：

```
https://devops.aliyun.com/organization/<organization_id>/work/workitems/<identifier>
```

## 输出格式

ALWAYS use this exact markdown table format:

```
## 需求生命周期统计

| 统计项                               | 数量  |
| ------------------------------------ | ----- |
| **未评审需求总数**                   | **N** |
| └ 产品类需求                         | N     |
| └ 技术类需求                         | N     |
| **`{range}`创建需求总数**            | **N** |
| └ 产品类需求                         | N     |
| └ 技术类需求                         | N     |
| **`{range}`关闭需求总数**            | **N** |
| └ 产品类需求                         | N     |
| └ 技术类需求                         | N     |

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
