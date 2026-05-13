---
name: yunxiao-req-ai-review
description: AI 自动评审云效需求并生成评审意见。调用 yunxiao-req-review 技能执行标准化评审，支持参数调用：`/yunxiao-req-ai-review space_id=xxx`，无参数时交互式询问。
---

# 云效 AI 需求评审

## 技能依赖

本技能**必须调用 `yunxiao-req-review` 技能**执行标准化评审逻辑，不自行实现评审标准。

- **评审引擎**：`/yunxiao-req-review` - 提供12项评分标准、总分计算、评级判定
- **输出格式**：完整评审报告（评分明细、核心问题、改进优先级、总体评语）
- **集成方式**：从云效获取需求详情 → 组装评审内容 → 调用 yunxiao-req-review → 回写结果到云效

## 参数

| 参数              | 说明                                  | 必填                 | 默认值 | 示例 |
| ----------------- | ------------------------------------- | -------------------- | ------ | ---- |
| `organization_id` | 云效组织ID（从 CLAUDE.md 上下文获取） | 否                   | -      | -    |
| `space_id`        | 云效项目ID                            | 是（交互时自动获取） | -      | -    |
| `review_mode`     | 评审模式：`full` 完整评审 / `quick` 快速评审 | 否 | `full` | `quick` |

**调用方式：**
- 参数调用：`/yunxiao-req-ai-review space_id=2c0a78d7474abf949e37f28cca max_review=50 review_mode=full`
- 无参数调用：`/yunxiao-req-ai-review` → 交互式询问

**固定筛选条件（不可配置）：**
- 状态：待处理
- 迭代：未分配迭代

## 常量配置（组织级固定值，无需动态获取）

**状态常量**
| 状态     | ID                           |
| -------- | ---------------------------- |
| 待处理   | `100005`                     |
| 待评审   | `b6d1af1f9bd7ed8b3a79e27a11` |
| 评审驳回 | `62a829f0a33157f511cc6379a5` |
| 评审通过 | `bc5e4a3a72ef6f7c0ecdac11ee` |

**优先级常量**
| 优先级 | ID                           | 数量   |
| ------ | ---------------------------- | ------ |
| 紧急   | `f5a3e463cce0bef658ea9be69a` | 2 条   |
| 高     | `f4e494382a954d30b2ee1022a3` | 4 条   |
| 中     | `012ecf2e458fa055c529573824` | 145 条 |
| 低     | `8769fcec4b00aa281f2d1a4f76` | 5 条   |

**评级-状态映射表**（由 yunxiao-req-review 返回的评级决定云效状态）：
| yunxiao-req-review 评级 | 云效状态ID | 评审结论 |
| ----------------------- | ---------- | -------- |
| 优秀（90–100） | `bc5e4a3a72ef6f7c0ecdac11ee` | 评审通过 |
| 良好（75–89） | `b6d1af1f9bd7ed8b3a79e27a11` | 待人工评审 |
| 待改进（55–74） | `62a829f0a33157f511cc6379a5` | 评审驳回 |
| 不通过（0–54） | `62a829f0a33157f511cc6379a5` | 评审驳回 |

## advancedConditions 模板

使用 `advancedConditions` 组合查询条件，直接从服务端获取统计数量, **注意**：advancedConditions 的值是 json 字符串, 并非 json 对象

```json
// 组合条件：AND 关系写在同一个 conditionGroups 数组内
{"conditionGroups":[[
    {"fieldIdentifier":"sprint","..."},
    {"fieldIdentifier":"workitemType","..."},
    {"fieldIdentifier":"priority","..."}
]]}

// condition : 限定迭代为未分配迭代
{"fieldIdentifier":"sprint","operator":"CONTAINS","value":["EMPTY_VALUE"],"toValue":null,"className":"sprint","format":"list"}

// condition : 限定工作项类型为产品类需求和技术类需求, 硬编码即可
{"fieldIdentifier":"workitemType","operator":"CONTAINS","value":["9uy29901re573f561d69jn40","bca48ee2a0976d38f4802fae"],"toValue":null,"className":"workitemType","format":"list"}

// condition : 组合优先级查询
{"fieldIdentifier":"priority","operator":"CONTAINS","value":["<prio_id>"],"toValue":null,"className":"option","format":"list"}

// condition : 限定状态为待处理
{"fieldIdentifier":"status","operator":"CONTAINS","value":["100005"],"className":"status","format":"list"}
```

## 核心 MCP 工具速查表（减少思考时间）

**必须使用以下工具，不要思考工具名称，直接复制调用**：

| 工具名称                                       | 用途                 | 必填参数                                                                              |
| ---------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------- |
| `mcp__yunxiao__search_projects`                | 获取项目列表         | 无参数                                                                                |
| `mcp__yunxiao__search_workitems`               | 搜索需求列表         | `organizationId`, `spaceId`, `spaceType`, `category`, `perPage`, `advancedConditions` |
| `mcp__yunxiao__get_work_item`                  | 获取单条需求详情     | `organizationId`, `workItemId`                                                        |
| `mcp__yunxiao__create_work_item_comment`       | 给需求添加评论       | `organizationId`, `workItemId`, `content`                                             |
| `mcp__yunxiao__update_work_item`               | 更新需求状态/字段    | `organizationId`, `workItemId`, `updateWorkItemFields`                                |
| `mcp__yunxiao__get_workitem_type_field_config` | 获取需求类型字段配置 | `organizationId`, `workItemTypeId`                                                    |

---

## 完整工作流

### Phase 1：选择项目（仅当未指定 space_id 时）

调用 `mcp__yunxiao__search_projects` 获取项目列表，展示给用户选择：

以表格形式展示，只显示序号和项目名称，不显示项目ID：

| 序号 | 项目名称 |
| ---- | -------- |
| 1    | xxx项目  |
| 2    | xxx项目  |

让用户通过输入序号来选择项目。

### Phase 2：筛选待评审需求

**Step 2.1 — 获取优先级分组统计（并发调用）**

使用 `perPage=1` 只获取总数，**并发调用 4 次**同时获取各优先级数量，减少等待时间。

查询条件 : 
- 状态：待处理
- 迭代：未分配迭代

```
mcp__yunxiao__search_workitems(
    organizationId, spaceId, category: Bug, perPage: 1, includeDetails: false,
    advancedConditions: '...'
)
# 并发获取每个优先级的数量（4 次 MCP 同时调用，perPage=1 只取总数）
# 每个优先级使用相同 advancedConditions，仅替换 <prio_id> 为对应优先级ID
# 所有请求完成后聚合结果：priority_name → pagination.total
```

展示优先级统计表格：
| 优先级   | 数量  |
| -------- | ----- |
| 紧急     | N     |
| 高       | N     |
| 中       | N     |
| 低       | N     |
| **总计** | **N** |

---

**Step 2.2 — 确认评审范围（AskUserQuestion 交互式选择）**

调用 `AskUserQuestion` 工具让用户选择：

| 问题                 | 类型 | 选项                                       |
| -------------------- | ---- | ------------------------------------------ |
| 选择评审的优先级范围 | 多选 | 紧急、高、中、低、全部                     |
| 选择评审数量         | 单选 | 默认 10 条（优先级降序）、全部、自定义数量 |

获取用户确认后，拉取对应范围内的需求数据（按优先级降序排序）进入 Phase 3 逐条评审。

---

### Phase 3：调用 yunxiao-req-review 逐条评审

对每一条待评审需求，告知用户"正在评审第 N/M 条：[标题]"，然后依次执行：

**Step 3.1 — 获取需求详情并组装评审内容**

调用 `mcp__yunxiao__get_work_item` 获取完整需求详情：

```python
mcp__yunxiao__get_work_item(
  organizationId="<organization_id>",
  workItemId="<workitem_id>"
)
```

提取完整信息并组装评审内容字符串：
```python
requirement_content = f"""
# 需求标题：{subject}

## 需求描述
{description or '无描述'}

## 基本信息
- 需求类型：{workitem_type_name}
- 优先级：{priority_name}
- 负责人：{assigned_to_name}
- 创建人：{creator_name}

## 关联信息
- 标签：{labels_list}
- 参与人：{participants_list}
- 附件：{attachments_list}
"""
```

同时提取：
- customFieldValues 中的"评审结论"字段ID

**Step 3.2 — 调用 yunxiao-req-review 技能执行评审**

**必须调用 Skill 工具执行评审，不得自行评审**：

```python
# 完整评审模式（默认）
Skill(skill="yunxiao-req-review", args=f"requirement_title='{subject}' requirement_content='{requirement_content}' output_format='full'")

# 快速评审模式（review_mode=quick）
Skill(skill="yunxiao-req-review", args=f"requirement_title='{subject}' requirement_content='{requirement_content}' mode='quick'")
```

**评审返回内容包含**（完整模式）：
- 总分（0–100）
- 评级（优秀/良好/待改进/不通过）
- 评分明细表
- 核心问题列表
- 改进优先级表
- 总体评语

**Step 3.3 — 根据评级确定处理方式**

对照评级-状态映射表：

| yunxiao-req-review 评级 | 云效状态ID | 处理方式 |
| ----------------------- | ---------- | -------- |
| 优秀（90–100） | `bc5e4a3a72ef6f7c0ecdac11ee` | 评审通过，写简评 |
| 良好（75–89） | `b6d1af1f9bd7ed8b3a79e27a11` | 待人工评审，写完整报告 |
| 待改进（55–74） | `62a829f0a33157f511cc6379a5` | 评审驳回，写完整报告 |
| 不通过（0–54） | `62a829f0a33157f511cc6379a5` | 评审驳回，写完整报告 |

**特殊边界处理**：需求描述为空或极简短的，直接标记"评审驳回"，评论内容注明"[AI] 需求描述为空 / 过于简略，无法进行评审"。

**Step 3.4 — 生成评论内容（来自 yunxiao-req-review 输出）**

将 yunxiao-req-review 返回的评审报告直接作为评论内容，添加头部标识：

```
🤖 AI 自动化评审报告
━━━━━━━━━━━━━━━━━━━━━
【总分：{XX}/100】【评级：{优秀/良好/待改进/不通过}】
━━━━━━━━━━━━━━━━━━━━━

[此处直接插入 yunxiao-req-review 返回的完整评审报告]

━━━━━━━━━━━━━━━━━━━━━
⚠️ AI 评审仅供参考，最终结论以人工评审为准
```

**Step 3.5 — 回写云效**

**发布评论（必须执行，不要思考工具名称，直接调用）**：
```python
mcp__yunxiao__create_work_item_comment(
  organizationId="<organization_id>",
  workItemId="<workitem_id>",
  content="<完整评审报告>"
)
```

更新工作项状态（根据评级映射）：
```python
# 状态常量（直接使用，不要思考或查询）：
# 待处理 → 100005
# 待评审 → b6d1af1f9bd7ed8b3a79e27a11
# 评审驳回 → 62a829f0a33157f511cc6379a5
# 评审通过 → bc5e4a3a72ef6f7c0ecdac11ee

mcp__yunxiao__update_work_item(
  organizationId="<organization_id>",
  workItemId="<workitem_id>",
  updateWorkItemFields={
    "status": "<mapped_status_id>"
  }
)
```

更新"评审结论"自定义字段（如存在）：
```python
# 从需求详情的 customFieldValues 中找到"评审结论"的 fieldId
# 遍历 customFieldValues 数组，找到 fieldName == "评审结论" 的项
# 使用该项的 fieldId 作为 key 更新 customFieldValues
# 如果找不到，跳过更新，不要中断流程

mcp__yunxiao__update_work_item(
  organizationId="<organization_id>",
  workItemId="<workitem_id>",
  updateWorkItemFields={
    "customFieldValues": {
      "<review_conclusion_field_id>": f"[AI] {评级}：总分 {XX}/100"
    }
  }
)
```

**重要**：如果工具调用失败，不继续执行并告知用户。

---

### Phase 4：汇总报告

所有需求评审完毕后输出统计报告，按 yunxiao-req-review 的评级分类：

```
🤖 AI 需求评审完成
━━━━━━━━━━━━━━━━━━━━━
统计结果：
总计评审：{N} 条
优秀（90–100）：{N} 条 → 评审通过
良好（75–89）：{N} 条 → 待人工评审
待改进（55–74）：{N} 条 → 评审驳回
不通过（0–54）：{N} 条 → 评审驳回

平均得分：{XX.X} 分

━━━━━━━━━━━━━━━━━━━━━
⚠️ 评审驳回清单（需重提）：
- [需求标题](云效链接) → {XX}分 · 核心问题：{简要}

📋 待人工评审清单（需补充完善）：
- [需求标题](云效链接) → {XX}分 · 主要缺失：{简要}

✅ 评审通过清单（可推进）：
- [需求标题](云效链接) → {XX}分
```

---

## 注意事项

### 核心原则
- **禁止自行评审**：必须调用 `yunxiao-req-review` 技能执行评审，不得自行判断或评分
- **透传评审结果**：评审报告内容直接来自 yunxiao-req-review 的输出，不得修改评分或评级

### 技术细节
- **状态ID校准**：如更新状态失败，先用 `mcp__yunxiao__get_work_item` 查一条状态为"评审驳回"/"待评审"的需求，确认其 statusIdentifier
- **评审边界**：需求描述为空或极简短的，直接标记"评审驳回"并注明"[AI] 需求描述为空 / 过于简略，无法进行评审"，跳过 yunxiao-req-review 调用
- **评论去重**：如果工作项已有 🤖 开头的 AI 评论，追加新评论时标注"(第2次评审)"
- **自定义字段容错**："评审结论"字段可能不存在于某些项目，不存在时跳过更新，不要中断流程
- **限速保护**：每次更新间隔 1-2 秒，避免触发 API 限流
- **评论失败处理**：如果评论工具调用失败，继续执行状态更新，不要中断整个评审流程，最后在汇总报告中标注哪些需求评论失败

### 与 yunxiao-req-review 集成说明
1. 本技能仅负责云效数据读写和流程编排，**评审逻辑完全委托**给 yunxiao-req-review
2. yunxiao-req-review 负责评分标准、评级判定、报告格式化
3. 两个技能解耦，未来评审标准更新只需修改 yunxiao-req-review 一处即可
