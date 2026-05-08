---
name: arch-aggregate
description: 聚合 arch-docs 下所有服务文档，生成整体项目视图，包括业务场景、跨服务业务流程、服务速查、MQ事件全景图和变更影响分析。当用户说 "arch-aggregate"、"聚合架构文档"、"生成整体文档"、"汇总服务文档"、"aggregate arch docs" 时触发。
---

# Arch Aggregate

读取 `services/` 下所有服务的文档，聚合生成整体项目视图。

**目标读者**：开发、产品经理  
**核心原则**：聚焦业务场景和流程，技术实现细节不出现在聚合文档中

输出结构：
```
aggregate/
├── business-scenarios.md   # 核心业务场景
├── business-flows/         # 每个场景的跨服务业务流程
│   └── {场景名}.md
├── service-map.md          # 服务职责速查
├── event-topology.md       # MQ 事件全景图
└── impacts.md              # 变更影响决策工具
```

源材料：`services/{服务名}/` 下的 overview.md、business.md、flows.md、contracts.md

文档模板：`references/templates.md`

---

## 第一步：增量变更检测（基于内容哈希）

通过 Python 脚本对比文件内容的 SHA-1 哈希值检测变更，避免文件时间戳不可靠的问题。

### 清单文件

`aggregate/.manifest.json` 以 JSON 格式存储上次聚合时每个服务每个文件的 SHA-1 哈希：

```json
{
  "kjs-trade": {
    "overview.md": "f7d0dd47...",
    "business.md": "a1b2c3d4...",
    "flows.md": "e5f6a7b8...",
    "contracts.md": "eb6a1dd8..."
  }
}
```

### 检测脚本

本 skill 目录下的 `check-changes.py`，自动扫描 `services/{服务名}/` 下所有 `*.md` 文件（不限定固定文件列表）。

运行时从项目根目录执行，三个子命令：

| 子命令 | 用途 |
|--------|------|
| `detect` | 输出变更详情（默认） |
| `list` | 仅输出变更服务名，每行一个 |
| `save` | 将当前哈希写入清单文件 |

### 检测规则

- `aggregate/.manifest.json` 不存在 → **全量首次运行**
- 服务的四个文件哈希均与清单一致 → **跳过该服务**
- 服务的任一文件哈希不一致（包括新增/删除文件）→ **需重新分析**
- 用户指定服务名（如 `arch-aggregate kjs-trade kjs_product`）→ 只分析指定服务，不做哈希检测
- 用户要求"全量聚合"→ 跳过检测，分析所有服务

### 输出变更检测结果

```
变更检测（基于内容哈希）：
  ✓ kjs-trade — 内容有变更，需重新分析
  ✓ kjs_product — 内容有变更，需重新分析
  - kjs-kf — 内容无变更，跳过
  ...
```

---

## 第二步：读取变更服务文档

对有变更的服务，**并行读取**每个服务下的四个标准文件。

记录每个服务的：
- 服务名与一句话职责
- 业务场景覆盖范围
- 涉及的用户角色（买家、卖家、客服、系统自动）
- 跨服务的调用/触发关系

contracts.md 仅用于提取"产生的事件"列构建事件级联链路，其余技术契约细节不出现在聚合文档中。

---

## 第三步：增量更新原则

写文件前先检查是否已存在：

- **不存在**：直接生成完整内容
- **已存在**：读取现有内容，保留手动补充的业务背景和说明，只更新与变更服务相关的部分，新增内容追加不覆盖

手动补充的内容优先级高于自动生成内容。

---

## 第四步：生成 business-scenarios.md

**文件路径**：`aggregate/business-scenarios.md`

列出所有核心业务场景。写作要求：
- 每个场景一句话说清楚：**是什么、谁参与、目的是什么**
- 语言面向产品/新人，不出现技术术语
- 从服务文档中提炼场景，合并同类项

场景分两类：
- **有独立流程文档的场景**：标注详细流程链接
- **无独立流程文档的场景**：归入底部表格，指向主服务文档

格式见 `references/templates.md`。

---

## 第五步：生成 business-flows/{场景名}.md

**文件路径**：`aggregate/business-flows/{场景名}.md`

### 筛选原则

**生成 flow 的条件**（必须同时满足）：
1. 涉及 3 个以上服务的协作（状态流转或事件驱动，非简单查询）
2. 存在多步骤有序推进
3. 改动后影响面广，需多团队协同评估

不满足条件的场景列入 `business-scenarios.md` 表格，不单独生成 flow。

### 写作要求

- 用户视角为主，明确标注系统自动节点
- 主流程步骤编号连续，体现先后顺序
- 不描述技术实现（不出现 MQ、Topic、Feign、Redis 等）
- 关键状态变化必须标注
- 异常分支单独列出，不混入主流程

格式见 `references/templates.md`。

---

## 第六步：生成 service-map.md

**文件路径**：`aggregate/service-map.md`

服务速查索引。写作要求：
- 职责描述用产品语言，去掉技术词汇
- 按业务相关性分组（交易类、通知类、基础类等）

格式见 `references/templates.md`。

---

## 第七步：生成 event-topology.md

**文件路径**：`aggregate/event-topology.md`

MQ 事件全景图，从所有服务 `contracts.md` 中提取事件发布/消费关系。

**数据提取规则**：
- 从"消费的 MQ 事件"表格提取：Topic、Tag、消费方、业务动作
- 从"发布的 MQ 事件"表格提取：Topic、Tag、发布方、触发时机、已知消费方
- 按 Topic 分组，列出所有 Tag 的发布方和消费方
- 识别 2 层以上级联链路（A → B → C），单独列出

**增量更新**：某个服务的 contracts.md 有变更时，只更新该服务相关的 Topic/Tag 行。

格式见 `references/templates.md`。

---

## 第八步：生成 impacts.md

**文件路径**：`aggregate/impacts.md`

变更影响决策工具，两个维度组织：
- **按业务流程**：每条流程上的可变更点及其影响
- **按服务**：每个服务的可变更点及其影响扩散

每条影响精确到：修改了什么 → 影响哪条流程 → 影响哪些服务 → 影响哪个状态。

重点关注：
- 跨服务调用链
- 共用的业务规则
- 状态机流转点
- 边界说明中的"不负责事项"

格式见 `references/templates.md`。

---

## 第九步：更新哈希清单并输出结果

运行本 skill 目录下的 `check-changes.py save`，将当前哈希写入清单文件。

输出模板：

```
✅ arch-aggregate 完成

变更检测（基于内容哈希）：
  分析服务：{有变更的服务列表}
  跳过服务：{无变更的服务列表}

生成/更新的文件：
  ✓ business-scenarios.md（{N} 个场景）
  ✓ business-flows/{场景名}.md × {N}
  ✓ service-map.md
  ✓ event-topology.md
  ✓ impacts.md

待人工补充：
  - {列出从服务文档中无法推断、需要产品/业务确认的内容}
```
