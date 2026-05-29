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

| 参数              | 说明                                         | 必填                 | 默认值 | 示例    |
| ----------------- | -------------------------------------------- | -------------------- | ------ | ------- |
| `organization_id` | 云效组织ID（从 CLAUDE.md 上下文获取）        | 否                   | -      | -       |
| `space_id`        | 云效项目ID                                   | 是（交互时自动获取） | -      | -       |
| `review_mode`     | 评审模式：`full` 完整评审 / `quick` 快速评审 | 否                   | `full` | `quick` |

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
| yunxiao-req-review 评级 | 云效状态ID                   | 评审结论   |
| ----------------------- | ---------------------------- | ---------- |
| 优秀（90–100）          | `bc5e4a3a72ef6f7c0ecdac11ee` | 评审通过   |
| 良好（75–89）           | `b6d1af1f9bd7ed8b3a79e27a11` | 待人工评审 |
| 待改进（55–74）         | `62a829f0a33157f511cc6379a5` | 评审驳回   |
| 不通过（0–54）          | `62a829f0a33157f511cc6379a5` | 评审驳回   |

**自定义字段ID**
| 字段名称 | ID                           |
| -------- | ---------------------------- |
| 评审结论 | `92184debbf0f0d558444fa9019` |

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

| 工具名称                                 | 用途              | 必填参数                                                                              |
| ---------------------------------------- | ----------------- | ------------------------------------------------------------------------------------- |
| `mcp__yunxiao__search_projects`          | 获取项目列表      | 无参数                                                                                |
| `mcp__yunxiao__search_workitems`         | 搜索需求列表      | `organizationId`, `spaceId`, `spaceType`, `category`, `perPage`, `advancedConditions` |
| `mcp__yunxiao__get_work_item`            | 获取单条需求详情  | `organizationId`, `workItemId`                                                        |
| `mcp__yunxiao__create_work_item_comment` | 给需求添加评论    | `organizationId`, `workItemId`, `content`                                             |
| `mcp__yunxiao__update_work_item`         | 更新需求状态/字段 | `organizationId`, `workItemId`, `updateWorkItemFields`                                |

## 完整工作流

### Phase 1：选择项目（仅当未指定 space_id 时）

调用 `mcp__yunxiao__search_projects` 获取项目列表，**直接以序号列表展示**供用户选择：

**交互规则**：
- 输出纯文本序号列表，每行一个项目（序号 + 项目名称）
- 用户直接回复对应数字即可（无需使用 AskUserQuestion 工具）

**示例输出**：
```
请选择要评审的项目（回复数字）：
1. 聚单云
2. 客诉工单
3. 氪金平台
```

**实现要点**：
- 直接展示，无需分组、无需导航选项
- 用户回复数字即完成选择，一步到位
- 最多展示 20 个项目，超出时提示过滤方式

### Phase 2：筛选待评审需求

**Step 2.1 — 获取优先级分组统计（并发调用）**

使用 `perPage=1` 只获取总数，**并发调用 4 次**同时获取各优先级数量，减少等待时间。

查询条件：
- 状态：待处理
- 迭代：未分配迭代

```
mcp__yunxiao__search_workitems(
    organizationId, spaceId, category: Req, perPage: 1, includeDetails: false,
    advancedConditions: '{"conditionGroups":[[{"fieldIdentifier":"sprint","operator":"CONTAINS","value":["EMPTY_VALUE"],"toValue":null,"className":"sprint","format":"list"},{"fieldIdentifier":"status","operator":"CONTAINS","value":["100005"],"className":"status","format":"list"},{"fieldIdentifier":"workitemType","operator":"CONTAINS","value":["9uy29901re573f561d69jn40","bca48ee2a0976d38f4802fae"],"toValue":null,"className":"workitemType","format":"list"},{"fieldIdentifier":"priority","operator":"CONTAINS","value":["<prio_id>"],"toValue":null,"className":"option","format":"list"}]]}'
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

**Step 2.2 — 确认评审范围（简洁选择）**

展示当前筛选条件摘要：
```
当前筛选条件：
- 状态：待处理
- 迭代：未分配迭代
- 总计：N 条待评审需求
```

直接以序号方式询问评审范围：
```
请选择评审范围（回复数字）：
1. 紧急+高（优先评审高优先级）
2. 全部（按优先级降序）
3. 仅中+低（先处理积压）

请选择评审数量（回复数字）：
1. 默认10条
2. 全部
3. 自定义（请输入数量）
```

获取用户确认后，使用最终组合条件（状态 + 迭代 + 优先级）拉取需求数据（按优先级降序排序）。进入 Phase 3 前，**必须明确：search_workitems 仅用于获取需求 ID 列表，实际评审内容必须通过 mcp__yunxiao__get_work_item 逐条获取完整详情**。

### Phase 3：调用 yunxiao-req-review 逐条评审

**⚠️ 关键强制要求：必须逐条评审，不得批量处理；必须调用 get_work_item 获取完整详情，绝对不能使用 search_workitems 返回的列表数据（列表数据不包含完整的 description 字段）**

对每一条待评审需求，告知用户"正在评审第 N/M 条：[标题]"，然后依次执行：

**Step 3.1 — 获取需求详情并组装评审内容**

**🔴 强制要求：必须调用 mcp__yunxiao__get_work_item 获取单条需求的完整详情**，search_workitems 返回的列表数据 description 字段不完整（可能为空或截断），直接使用会导致评审结果失真。

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
- 参与人：{participants_list}
- 附件：{attachments_list}
"""
```

**评审结论字段ID：`92184debbf0f0d558444fa9019`**

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

| yunxiao-req-review 评级 | 云效状态ID                   | 处理方式               |
| ----------------------- | ---------------------------- | ---------------------- |
| 优秀（90–100）          | `bc5e4a3a72ef6f7c0ecdac11ee` | 评审通过，写简评       |
| 良好（75–89）           | `b6d1af1f9bd7ed8b3a79e27a11` | 待人工评审，写完整报告 |
| 待改进（55–74）         | `62a829f0a33157f511cc6379a5` | 评审驳回，写完整报告   |
| 不通过（0–54）          | `62a829f0a33157f511cc6379a5` | 评审驳回，写完整报告   |

**特殊边界处理**：需求描述为空或极简短的，直接标记"评审驳回"，评论内容注明"[AI] 需求描述为空 / 过于简略，无法进行评审"。

**Step 3.4 — 生成评论内容（来自 yunxiao-req-review 输出）**

yunxiao-req-review 返回的评审报告为 Markdown 格式（包含 `###`、`**`、`---`、`|` 等符号）。**云效 API 不支持 Markdown 特殊符号，提交时会返回 400 错误**（错误信息："评论失败，请检查是否存在特殊符号或者表情符号"）。因此必须在发布评论前将 Markdown 转换为 HTML 富文本或纯文本格式。

**转换流程（二选一）**：

**方案 A — Markdown 转 HTML（推荐）**：
将 Markdown 格式的评审报告通过 HTML 转换后发布，例如：
- `### xxx` → `<h3>xxx</h3>`
- `**text**` → `<strong>text</strong>`
- `- item` → `<li>item</li>`
- `---` → `<hr>`
- Markdown 表格 → HTML `<table>`
- `>` 引用 → `<blockquote>`

**方案 B — 纯文本降级（最简单可靠）**：
如果无法执行 Markdown 转 HTML，则使用纯文本降级策略：
1. 移除所有 Markdown 标记符号：`#`、`*`、`_`、`~`、`\`
2. 移除表格分隔符 `|` 和 `-`（用空格替代）
3. 移除列表符号 `-` / `*`（用 `1.` / `2.` 序号替代或缩进空格）
4. 移除水平线 `---` / `***`（用空行替代）
5. 保留中文括号【】()、冒号:、缩进空格、换行等云效兼容字符
6. 执行特殊符号清洗（同下）

**特殊符号清洗规则**（所有方案都必须执行）：
- 移除 emoji 范围 `\U00010000-\U0010ffff`
- 移除特殊装饰符号（━、─、■、●、◆、★☆、♦、♠、♣、♥、❤、❌、✅、⚠️、📋、🤖 等）
- 移除连续空行（合并为单个空行）

**评论内容结构模板**：
```
AI 自动化评审报告

总分: {XX}/100 | 评级: {优秀/良好/待改进/不通过}

[此处为 yunxiao-req-review 返回的完整评审报告，已转为 HTML 或纯文本]

AI 评审仅供参考,最终结论以人工评审为准
```

**Step 3.5 — 回写云效（三个子步骤全部必执行）**

对每一条需求，以下三个操作缺一不可，按顺序依次执行：

#### 子步骤 1：发布评论

先执行清洗逻辑：
```python
def clean_comment_content(content):
    import re
    content = re.sub(r'[\U00010000-\U0010ffff]', '', content)
    content = re.sub(r'[━─■●◆★☆♦♠♣♥❤❌✅⚠️📋🤖]', '', content)
    content = re.sub(r'\n\s*\n', '\n\n', content)
    return content.strip()
```

然后调用工具：
```
mcp__yunxiao__create_work_item_comment(
  organizationId="<organization_id>",
  workItemId="<workitem_id>",
  content="<已转为 HTML 或纯文本的评审报告>"
)
```

评论失败处理：先清洗后重试一次；仍失败则记录标注，继续执行后续子步骤，不中断流程。

#### 子步骤 2：合并更新工作项状态 + 评审结论字段（性能优化：1 次调用完成 2 项操作）

**注意：此步骤已将原"子步骤 2 状态更新"和"子步骤 3 自定义字段更新"合并为单次 API 调用，性能提升 33%**

```
mcp__yunxiao__update_work_item(
  organizationId="<organization_id>",
  workItemId="<workitem_id>",
  updateWorkItemFields={
    "status": "<mapped_status_id>",
    "customFieldValues": {
      "92184debbf0f0d558444fa9019": "[AI] {评级}：总分 {XX}/100"
    }
  }
)
```

**要求**：
- 每个需求都必须写入评审结论自定义字段数据，无论评级高低
- 仅当自定义字段 `"92184debbf0f0d558444fa9019"` 在该项目中不存在时，才回退到只更新状态的独立调用
- 即使跳过自定义字段，也必须记录说明，不得无故省略

**如果任一子步骤失败**：不中断整个评审流程，在 Phase 4 汇总报告中注明哪些操作的哪些环节回写失败。

### Phase 4：汇总报告

所有需求评审完毕后输出统计报告，按 yunxiao-req-review 的评级分类（输出时不使用 emoji，保持纯文本格式）：

```
AI 需求评审完成
-------------------------
筛选条件：
- 状态：待处理 | 迭代：未分配迭代

统计结果：
总计评审：{N} 条
优秀（90–100）：{N} 条 → 评审通过
良好（75–89）：{N} 条 → 待人工评审
待改进（55–74）：{N} 条 → 评审驳回
不通过（0–54）：{N} 条 → 评审驳回

平均得分：{XX.X} 分
```

-------------------------
评审驳回清单（需重提）：
- [需求标题]({云效链接}) → {XX}分 · 核心问题：{简要}

待人工评审清单（需补充完善）：
- [需求标题]({云效链接}) → {XX}分 · 主要缺失：{简要}

评审通过清单（可推进）：
- [需求标题]({云效链接}) → {XX}分
```

**云效链接格式规范**：
```
https://yunxiao.aliyun.com/org/{organization_id}/project/{space_id}/workitem/{workitem_id}
```

示例：
```
https://yunxiao.aliyun.com/org/62ac9a6364c8a06be2d5db5d/project/2c0a78d7474abf949e37f28cca/workitem/ABC123456
```

## 注意事项

### 核心原则
- **禁止自行评审**：必须调用 `yunxiao-req-review` 技能执行评审，不得自行判断或评分
- **透传评审结果**：评审报告内容直接来自 yunxiao-req-review 的输出，不得修改评分或评级
- **必须获取完整详情**：必须调用 `mcp__yunxiao__get_work_item` 获取单条需求的完整详情，**绝对不能使用 search_workitems 返回的列表数据**（列表的 description 字段不完整，会导致评审失真）

### 技术细节
- **状态ID校准**：如更新状态失败，先用 `mcp__yunxiao__get_work_item` 查一条状态为"评审驳回"/"待评审"的需求，确认其 statusIdentifier
- **评审边界**：需求描述为空或极简短的，直接标记"评审驳回"并注明"[AI] 需求描述为空 / 过于简略，无法进行评审"，跳过 yunxiao-req-review 调用
- **评论去重**：如果工作项已有 🤖 开头的 AI 评论，追加新评论时标注"(第2次评审)"
- **评审结论自定义字段必写**：每个需求都必须写入 `92184debbf0f0d558444fa9019` 字段的评审结论数据，不可因评级高低而跳过。状态更新与自定义字段更新已合并为单次 API 调用以提升性能。仅当该项目确实不存在此自定义字段时才回退到独立更新，并记录说明
- **Markdown 转 HTML 必填**：yunxiao-req-review 输出的 Markdown 格式内容不能直接提交到云效 API（会返回 400 错误），必须先转换为 HTML 富文本或使用纯文本降级策略
- **限速保护**：每次更新间隔 1-2 秒，避免触发 API 限流
- **评论失败处理**：如果评论工具调用失败，先清洗后重试一次；仍失败则继续执行状态更新和自定义字段更新，不中断整个评审流程，最后在汇总报告中标注哪些需求评论失败

### 与 yunxiao-req-review 集成说明
1. 本技能仅负责云效数据读写和流程编排，**评审逻辑完全委托**给 yunxiao-req-review
2. yunxiao-req-review 负责评分标准、评级判定、报告格式化
3. 两个技能解耦，未来评审标准更新只需修改 yunxiao-req-review 一处即可
