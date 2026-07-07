# metadata.md / version 文件 模板 / 状态枚举 / 目录约定

> v2 重构后的模板定义。metadata.md 是子需求的唯一状态源；`docs/version/{版本号}` 是版本级聚合视图。所有 `req` / `version` 命令写或读这些文件时参考本文件。

---

## §0. ID 解析规则

子需求 ID 完整格式：`{域}/{父需求名}#{子需求名}`

**按最后一个 `#` 拆分**：
- `#` 之前 = 域/父需求路径（含 `/`，多段路径整体保留）
- `#` 之后 = 子需求名（单段）

伪代码：
```
parseSubReqId(id) {
  idx = id.lastIndexOf('#')
  if idx == -1 {
    error "子需求 ID 必须含 '#'（按最后一个 '#' 拆分父/子）"
  }
  parent = id.substring(0, idx)
  child  = id.substring(idx + 1)
  return { parent, child }
}
```

ID → 路径映射：父路径保留 `/`，子名段独立成目录。`#` 仅作为 ID 分隔符，不出现在文件路径中。

**映射示例**：
| 子需求 ID | metadata.md 路径 |
|-----------|------------------|
| `payment/支付渠道重构#alipay` | `docs/discuss/payment/支付渠道重构/.task/alipay/metadata.md` |
| `order/订单取消优化#子需求1` | `docs/discuss/order/订单取消优化/.task/子需求1/metadata.md` |
| `a/b/c#x` | `docs/discuss/a/b/c/.task/x/metadata.md` |

**边界**：ID 段含 `#`（如 `order/退款#子项#1`）时按**最后一个** `#` 拆分，前段 `order/退款#子项` 整体视为父路径（虽含 `#` 仍非法字符，但解析规则固定：按最后一个 `#`）。

---

## §1. metadata.md 模板（8 字段）

子需求目录：`docs/discuss/{域}/{父需求名}/.task/{子需求名}/metadata.md`

**字段严格 8 项**，解析器只识别这 8 字段，其他字段忽略（AC11）。`versionBinding` 类型为 `string`（单一版本号），非数组。

```markdown
# 子需求元数据

## 基本信息
- subReqId: {域}/{父需求名}#{子需求名}        # 完整 ID（含 #）
- parentReqId: {域}/{父需求名}                # 父需求 ID（不含 # 和子名）
- versionBinding: {版本号 | ""}               # 当前绑定的版本号字符串；未绑定为空
- currentStage: {1|2|3|4|5}                   # 当前阶段编号
- currentState: {DISCUSSING|ANALYZING|PENDING_DESIGN_REVIEW|DEVELOPING|PENDING_PLAN_REVIEW|PENDING_CR_REVIEW|REVIEWING|COMPLETED}

## 时间戳
- createdAt: {ISO 8601 时间}                  # 子需求创建时间
- updatedAt: {ISO 8601 时间}                  # 最近一次字段更新时间

## 阶段产物引用
| 阶段 | 产物类型 | 路径（相对 metadata.md 所在目录） |
|------|---------|----------------------------------|
| 1 需求讨论 | 讨论文档 | docs/discuss/{域}/{父需求名}/.task/{子需求名}/discussion.md |
| 2 分析与设计 | 分析产物 | analysis/ |
| 2 分析与设计 | 设计文档 | design.md |
| 3 设计审核 | 审核记录 | design-consensus.md |
| 4 开发与逐任务审查 | 任务清单 | dev-tasks.md |
| 4 开发与逐任务审查 | 复杂任务 LLD | plans/ |
| 4 开发与逐任务审查 | CR 记录 | review/ |
| 4 开发与逐任务审查 | 已完成任务归档 | done/ |
| 5 收尾验收 | 验收报告 | acceptance.md |
| 5 收尾验收 | 交付清单 | change-manifest.md |
| 返工 | 返工单 | rework/R{n}-{根因}.md |
```

**字段填充时机**：
- `subReqId` / `parentReqId` / `createdAt`：由 `req split` 创建子需求时一次性写入
- `versionBinding`：由 `version create` 交互式流程回写；解绑由 `version close` 后保留作为历史
- `currentStage` / `currentState`：由 `next` / `approve` / `rework` 命令推进时更新
- `updatedAt`：任何字段变更时同步刷新
- `阶段产物引用`：阶段 2 进入时填入 `analysis/ design.md`；阶段 3 通过时填入 `design-consensus.md`；阶段 4 起始填入 `dev-tasks.md`；阶段 5 完成填入 `acceptance.md change-manifest.md`

**示例**（填充后）：
```markdown
# 子需求元数据

## 基本信息
- subReqId: payment/支付渠道重构#alipay
- parentReqId: payment/支付渠道重构
- versionBinding: v1.0
- currentStage: 4
- currentState: DEVELOPING

## 时间戳
- createdAt: 2026-07-06T10:00:00+08:00
- updatedAt: 2026-07-06T14:30:00+08:00

## 阶段产物引用
| 阶段 | 产物类型 | 路径（相对 metadata.md 所在目录） |
|------|---------|----------------------------------|
| 1 需求讨论 | 讨论文档 | docs/discuss/payment/支付渠道重构/.task/alipay/discussion.md |
| 2 分析与设计 | 分析产物 | analysis/ |
| 2 分析与设计 | 设计文档 | design.md |
| 3 设计审核 | 审核记录 | design-consensus.md |
| 4 开发与逐任务审查 | 任务清单 | dev-tasks.md |
```

---

## §2. version 文件模板（9 字段）

版本文件路径：`docs/version/{版本号}`（**无扩展名**，全局资源，不在 `docs/discuss/` 下）

**字段严格 9 项**（AC12）。`subRequirements` 是数组，每个元素为完整子需求 ID（含 `#`）。

```markdown
# 版本：{版本号}

## 基本信息
- versionNumber: {版本号}                     # 与文件名一致
- status: {DRAFT|IN_PROGRESS|READY|RELEASED|ARCHIVED}
- createdAt: {ISO 8601 时间}                  # 版本创建时间
- releasedAt: {ISO 8601 时间 | ""}            # RELEASED 时填入；其他为空
- archivedAt: {ISO 8601 时间 | ""}            # ARCHIVED 时填入；其他为空
- owner: {责任人}                             # 版本负责人（人/团队）

## 描述
{description}                                # 版本的发布主题描述

## 子需求列表
subRequirements:
- {域}/{父需求名}#{子需求名1}
- {域}/{父需求名}#{子需求名2}
- ...

## 阶段记录
| 子需求 ID | 当前阶段 | 当前状态 | 阶段记录链接 |
|-----------|---------|---------|------------|
| {完整 ID} | {1-5} | {状态枚举} | {子需求目录相对路径} |
```

**字段填充时机**：
- `versionNumber` / `status=DRAFT` / `createdAt` / `owner` / `description`：`version create` 建空 DRAFT 文件时写入
- `subRequirements[]`：`version create` 交互式多选完成后写入；后续通过 `version add-sub` 增量追加（DRAFT 状态下）
- `releasedAt`：`version close`（READY → RELEASED）触发时填入
- `archivedAt`：`version archive`（RELEASED → ARCHIVED）触发时填入
- `阶段记录` 表：实时聚合各子需求 metadata.md 的 `currentStage` / `currentState`，**不缓存子需求状态值**（version 文件不持有子需求状态权威，状态权威仍在 metadata.md）

**示例**（v1.0 含跨域子需求）：
```markdown
# 版本：v1.0

## 基本信息
- versionNumber: v1.0
- status: IN_PROGRESS
- createdAt: 2026-07-06T09:00:00+08:00
- releasedAt:
- archivedAt:
- owner: 支付平台组

## 描述
2024 Q1 发布批次：订单取消优化 + 支付宝渠道重构

## 子需求列表
subRequirements:
- order/订单取消优化#子需求1
- order/订单取消优化#子需求2
- payment/支付渠道重构#alipay
- payment/支付渠道重构#wechat

## 阶段记录
| 子需求 ID | 当前阶段 | 当前状态 | 阶段记录链接 |
|-----------|---------|---------|------------|
| order/订单取消优化#子需求1 | 5 | REVIEWING | docs/discuss/order/订单取消优化/.task/子需求1/metadata.md |
| order/订单取消优化#子需求2 | 4 | DEVELOPING | docs/discuss/order/订单取消优化/.task/子需求2/metadata.md |
| payment/支付渠道重构#alipay | 4 | DEVELOPING | docs/discuss/payment/支付渠道重构/.task/alipay/metadata.md |
| payment/支付渠道重构#wechat | 3 | PENDING_DESIGN_REVIEW | docs/discuss/payment/支付渠道重构/.task/wechat/metadata.md |
```

---

## §3. 状态枚举

### 子需求状态（写 metadata.md.currentState）

8 个状态值（任务描述中常称"7 态"，但实际枚举 8 项含 COMPLETED；AC4 校验字段合法）：

| 状态 | 含义 | 阶段 |
|------|------|------|
| `DISCUSSING` | 阶段 1 需求讨论中 | 1 |
| `ANALYZING` | 阶段 2 分析与设计中 | 2 |
| `PENDING_DESIGN_REVIEW` | 阶段 3 待设计审核 | 3 |
| `DEVELOPING` | 阶段 4 开发与逐任务审查 | 4 |
| `PENDING_PLAN_REVIEW` | 阶段 4 复杂任务 LLD 待审核（DEVELOPING 内子态） | 4 |
| `PENDING_CR_REVIEW` | 阶段 4 CR 扫描完成待人工确认（DEVELOPING 内子态） | 4 |
| `REVIEWING` | 阶段 5 收尾验收 | 5 |
| `COMPLETED` | 全部阶段完成 | - |

**状态流转**：
```
DISCUSSING
  ↓ next
ANALYZING
  ↓ next（设计文档就绪）
PENDING_DESIGN_REVIEW
  ↓ approve（设计审核通过）
DEVELOPING
  ↓ 复杂任务出现 → PENDING_PLAN_REVIEW → approve → DEVELOPING
  ↓ CR 扫描完成 → PENDING_CR_REVIEW → approve → DEVELOPING
  ↓ 全部任务 DONE
REVIEWING
  ↓ approve（验收通过）
COMPLETED
```

**`rework` 重置**：`COMPLETED → ANALYZING`（要求版本状态 ∈ {DRAFT, IN_PROGRESS, READY}；RELEASED / ARCHIVED 报错）。

### 版本状态机（写 `docs/version/{版本号}.status`）

5 态标准机（AC14）：

| 状态 | 含义 | 进入命令 | 前置条件 |
|------|------|---------|---------|
| `DRAFT` | 已创建，子需求已选但都未进入阶段 4 | `version create` | 无 |
| `IN_PROGRESS` | 至少一个子需求进入阶段 4 | `version start` | status=DRAFT 且 ≥1 个子需求 |
| `READY` | 所有子需求阶段 5 验收通过 | `version ready` | status=IN_PROGRESS 且所有子需求 currentState=COMPLETED |
| `RELEASED` | 已发布 | `version close` | status=READY |
| `ARCHIVED` | 永久封存（状态机终点） | `version archive` | status=RELEASED |

**状态流转**：
```
DRAFT ──version start──> IN_PROGRESS ──version ready──> READY ──version close──> RELEASED ──version archive──> ARCHIVED
                                                                                                                       ↑
                                                                                                              永久封存（不可逆）
```

**校验规则**（AC15）：每个状态转换检查「当前 status」+「子需求状态聚合」；不满足前置条件立即报错，错误信息含「字段名 / 原因 / 建议修复」（三段式：`[字段 {X} {当前值}] {原因}。建议: {修复}`）。

---

## §4. 目录约定

### 子需求目录（扁平化，无 milestone 嵌套）

```
docs/discuss/{域}/{父需求名}/
└── .task/
    └── {子需求名}/
        ├── metadata.md              # 唯一状态源（8 字段）
        ├── discussion.md             # 阶段 1 讨论文档
        ├── analysis/                 # 阶段 2 分析产物
        ├── design.md                 # 阶段 2 设计文档
        ├── design-consensus.md       # 阶段 3 审核记录
        ├── dev-tasks.md              # 阶段 4 任务清单
        ├── plans/                    # 阶段 4 复杂任务 LLD
        ├── done/                     # 阶段 4 已完成任务归档
        ├── review/                   # 阶段 4 CR 记录
        ├── acceptance.md             # 阶段 5 验收报告
        ├── change-manifest.md        # 阶段 5 交付清单
        └── rework/                   # 返工单（R{n}-{根因}.md）
```

**对比 v1**：v1 多里程碑模式有 `milestones/{M}/` 子目录；v2 取消该层级，子需求与父需求同级扁平化（spec C3）。

### 版本目录（全局，与子需求目录平级）

```
docs/
├── discuss/                          # 子需求树（按域/父需求/子需求组织）
│   └── {域}/{父需求名}/.task/{子需求名}/...
└── version/                          # 版本聚合（全局，跨父需求/跨域）
    ├── v1.0                          # 无扩展名
    ├── v1.1
    └── v2.0
```

**对比 v1**：v1 没有 `docs/version/` 概念；v2 引入全局版本目录（spec C1/C4）。

### 模块路径约定

`{module_root_glob}` 由项目 `manifest file` + `CLAUDE.md` 运行时声明（详见 `discovery.md`）。例如项目约定 `modules` 目录为模块根，则 `{module_root_glob}` 解析为 `modules`，模块下子目录为具体模块名。

### 架构文档目录约定

```
docs/architecture/{模块名}/
├── overview.md          # 模块概览
├── business.md          # 业务说明
├── contracts.md         # 契约/接口约定
├── flows.md             # 关键流程
└── ...
docs/architecture/
└── cross-module.md      # 跨模块契约总览
```

**架构文档来源**：由 `{discovery_cmd}` 在项目初始化时产出；缺失时先提示用户跑 `{discovery_cmd}` 或手动补齐。

### 根路径速查

| 资源类型 | 根路径 |
|---------|--------|
| 子需求元数据 | `docs/discuss/{域}/{父需求名}/.task/{子需求名}/metadata.md` |
| 子需求阶段产物 | `docs/discuss/{域}/{父需求名}/.task/{子需求名}/{阶段产物}` |
| 版本文件 | `docs/version/{版本号}` |
| 模块根 | `{module_root_glob}/{模块名}/`（由 manifest + CLAUDE.md 声明） |
| 模块架构 | `docs/architecture/{模块名}/` |
| （已删除）活动指针 | `docs/discuss/.workflow-active` ❌ 不再存在 |

---

## §5. 字段 schema 对照

| 文件 | 字段数 | 字段 | 类型 |
|------|--------|------|------|
| metadata.md | 8 | subReqId, parentReqId, versionBinding, currentStage, currentState, createdAt, updatedAt, 阶段产物引用 | string, string, string, int(1-5), enum, ISO 8601, ISO 8601, table |
| version 文件 | 9 | versionNumber, status, subRequirements[], createdAt, releasedAt, archivedAt, owner, description, stageRecord | string, enum, array[string], ISO 8601, ISO 8601, ISO 8601, string, string, table |

**约束**：
- metadata.md 解析器**只识别** 8 字段；写其他字段可保留但解析时忽略（AC11）
- version 文件解析器输出**完整** 9 字段对象；任何缺失字段报错（AC12）
- `versionBinding` 是 `string`（单值），不是 `string[]`；唯一性由 metadata.md 端保证，version 文件侧不重复校验（避免双源不一致）
