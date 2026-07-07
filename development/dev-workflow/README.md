# Workflow — 伪多模块单体需求开发全流程编排（v2 版本制度 · 语言无关）

## 目标

创建通用的需求开发 / 版本管理流程，用来完成自动化编码

## 阅读路径

| 读者 | 先读 | 然后 |
|------|------|------|
| **人类（总览 / 评审）** | 本 README（设计理念 + 使用示例 + 产出物目录） | 必要时查 `references/` 对应文件 |
| **AI 主 agent（执行）** | `SKILL.md`（路由器 + 12 不变量 + 错误模板） | 按 SKILL.md 末尾索引按需读 `references/{commands,templates,stage-*}.md` |
| **v1 → v2 迁移** | 本 README 的「设计理念：版本 vs 里程碑」+「v1 → v2 目录变更」段 | 用 `req list` / `req show` 自查存量数据，按需归档 |

> **⚠️ v2 不兼容 v1；旧数据请自行清理**
>
> 本 skill 已从「里程碑（milestone）制度」重构为「版本（version）制度」。
> 旧 `docs/discuss/.workflow-active` 粘性指针、旧 `progress.md` 状态源、旧里程碑嵌套目录、旧 `use / split / start` 命令 —— 全部硬切换删除，无迁移脚本、无双轨共存、无适配层（spec C9/D11）。
>
> 存量 v1 数据（`docs/discuss/{域}/{需求名}/.task/progress.md`、`docs/discuss/{域}/{需求名}/.task/milestones/`、`docs/discuss/.workflow-active`）视为遗留，请用户自行清理或保留为只读历史。

状态机驱动的开发流程 skill。把「**父需求 → 子需求（5 阶段）→ 版本聚合**」串成一个统一入口，每个子需求由 `metadata.md` 记录状态，版本通过 `docs/version/{版本号}` 聚合跨域子需求；每次 `/dev-workflow next {子需求ID}` 显式指定推进对象，自动决定下一步调度哪个 agent、传什么参数。

面向伪多模块单体项目：代码都在同一仓库 `{module_root_glob}` 下，跨模块走 `{contract_type}` 通道（具体类型在项目 `CLAUDE.md` 的 `## 跨模块调用` 段声明），审查按模块路径过滤 diff，架构上下文取自 `docs/architecture/{module}/`（项目配置的自定义发现命令产出）。测试/语法校验等具体命令默认按项目 manifest 文件中声明的 `{test_cmd}` / `{lint_cmd}`，无项目级硬编码默认值。

---

## 设计理念：版本 vs 里程碑

v1 的「里程碑」是单父需求下的多个交付切片（嵌套目录 `milestones/{M}/`），v2 的「版本」是**跨父需求、跨业务域**的发布批次聚合容器（全局文件 `docs/version/{版本号}`）。两者核心差异：

| 维度 | 版本（v2，新） | 里程碑（v1，已废弃） |
|------|---------------|---------------------|
| **容器粒度** | 跨父需求聚合：版本可同时包含来自 `order/订单取消优化#子1` 和 `payment/支付渠道重构#alipay` 等不同域的子需求 | 单父需求内聚：里程碑 `{M}` 只能属于一个父需求 `docs/discuss/{域}/{父需求名}/.task/milestones/{M}/` |
| **状态文件** | metadata.md（子需求级，8 字段精简）—— 子需求唯一状态源 | progress.md（需求级 + 里程碑级 + 任务级三层字段）—— 多层混用 |
| **状态机** | 版本 5 态：`DRAFT → IN_PROGRESS → READY → RELEASED → ARCHIVED`（每态有显式转换命令 + 严格前置校验） | 无独立状态机：里程碑继承父需求状态，无独立推进命令 |
| **活动指针** | 无活动指针：所有命令必须显式传子需求 ID 或版本号；缺参时直接报错 + 列出可选项 | `.workflow-active` 粘性文件：一次 `use {需求}` 后可省略参数 |
| **既有数据兼容** | 硬切换无迁移：v1 progress.md / milestones/ 数据视为遗留，用户自行清理 | — |

**核心约束**：版本是聚合视图，子需求是执行单元。5 阶段流程在每个子需求上独立推进，版本只是「跨域子需求 → 一次发布批次」的打包容器。子需求 ↔ 版本 一对一绑定，全局唯一不可重复打包。

---

## 五阶段主流程（在子需求级独立执行）

```
  阶段1 需求讨论     req create {父需求名} → req split {父需求名}    启动子需求
     │ (产出 docs/discuss/{域}/{父需求名}/.task/{子需求名}/discussion.md)
     ▼
  阶段2 分析与设计   next {子需求ID}  → analyst 逐模块分析 + ralph 汇总设计
     │ (产出 analysis/、design.md)
     ▼
 ┌──────────────────────────────────────────┐
 │ 阶段3 设计审核门  ★人工★  PENDING_DESIGN_REVIEW │
 │   approve {子需求ID}                       │
 └──────────────────────────────────────────┘
     ▼
  阶段4 开发与逐任务审查  next {子需求ID}   （详见 references/stage-4-dev.md）
     │
     ▼
  阶段5 收尾验收        next {子需求ID}   → verifier 全量回归 + 一致性把关
     │ (产出 acceptance.md)
     ▼
  COMPLETED ──→ summary {版本号}  → 交付清单 change-manifest.md（DDL / Job·MQ / API，给 DBA 与前端）

  ※ 阶段5 后如发现设计/需求层缺陷 → rework {子需求ID} 回退（要求版本状态 ∈ {DRAFT, IN_PROGRESS, READY}；RELEASED / ARCHIVED 报错）
```

```
阶段4 任务级闭环（每个任务独立走完，子需求级 metadata.md 为唯一状态源）

  TODO
   │ ⓪ 复杂度判断（Claude）
   ├─ 简单 ─────────────────────────────────────────────┐
   └─ 复杂 → 出 plan/LLD (architect/planner，只读)        │
            ▼ PLANNING                                    │
         ┌────────────────────────────────────────┐      │
         │ plan 人工门 ★人工★ PENDING_PLAN_REVIEW      │      │
         │   approve {子需求ID}                          │      │
         └────────────────────────────────────────┘      │
            ▼ PLAN_CONFIRMED                              │
   ┌───────────────────────────────────────────────────┘
   │ ① 编码 (executor，简单对照 design.md / 复杂对照已确认 plan)
   ▼ CODING
   │ ② DoD：{test_cmd} 绿 + {lint_cmd} 语法校验通过
   │ ③ CR 扫描 (code-reviewer，只读，只产出编号问题清单，不改代码)
   ▼ CR_SCANNED
         ┌────────────────────────────────────────┐
         │ CR 问题人工门 ★人工★ PENDING_CR_REVIEW      │  ← 逐条裁决 ACCEPTED/REJECTED/MODIFIED
         │   approve {子需求ID}                          │      │
         └────────────────────────────────────────┘
   ▼ CR_CONFIRMED
   │ ⑤ 改写 (executor，只改已采纳项)
   ▼ REWRITING
   │ ⑥ 复验 + 进度回写（强制）：{test_cmd} 绿 + {lint_cmd} 通过 → 回写 metadata.md 任务状态行 + 子需求目录 dev-tasks.md
   ▼ VERIFYING → DONE
```

> **CR 黑盒治理**：code-reviewer 只产出问题清单，绝不自动改代码。问题必须经人逐条裁决后，才由另一个 executor 对「已采纳」项改写。
> **进度回写是阻塞步骤**：每次状态流转都即时写回子需求 `metadata.md` 的 `currentStage` / `currentState` 字段；不回写不得推进下一个任务。
> **并行约束**：两个无依赖、目录不重叠的子需求可同时进入 CODING；CR 门永远逐子需求串行。

---

## 版本制度

版本是「跨父需求、跨业务域的子需求聚合容器」，标识一次发布批次。

- **状态机 5 态**：`DRAFT → IN_PROGRESS → READY → RELEASED → ARCHIVED`，每态转换由专门命令触发（`version start / ready / close / archive`）。
- **状态文件**：`docs/version/{版本号}`（全局，无扩展名），含 9 字段；不缓存子需求状态（实时从各 metadata.md 聚合）。
- **子需求绑定**：一对一绑定；`metadata.md.versionBinding` 为单值字符串；同一子需求不可重复打包到多个版本。
- **ARCHIVED 永久封存**：状态机终点，无 unarchive 命令；任何修改类命令一律拒绝。

### 版本创建流程（4 步）

```
1. 建空 DRAFT 文档  → version create {版本号}  写入 9 字段初始值
2. 扫描未绑定子需求  → 自动扫描 metadata.md.versionBinding 为空的子需求
3. 交互多选         → 用户用编号多选要纳入的子需求
4. 回写 metadata    → 对每个选中子需求写 metadata.md.versionBinding = {版本号}
```

### 版本状态推进

```
DRAFT ──version start──> IN_PROGRESS ──version ready──> READY ──version close──> RELEASED ──version archive──> ARCHIVED
                                                                                                            ↑
                                                                                                   永久封存（不可逆）
```

每个状态转换都有严格前置条件（AC15），不满足立即报错，错误信息三段式 `[字段 {X} {当前值}] {原因}。建议: {修复}`。

---

## 命令速查

> 所有命令**必须显式传参**（子需求 ID 或版本号）。缺参统一行为：报错 + 列出可选项（AC16）。

### `req` 命令族（4 个）

| 命令 | 必传参数 | 作用 | 替代的 v1 命令 |
|------|---------|------|--------------|
| `/dev-workflow req create` | `{域}/{父需求名}` | 创建父需求目录骨架 | 替代 `start` |
| `/dev-workflow req show` | `{域}/{父需求名}` | 显示父需求详情 + 子需求清单 | — |
| `/dev-workflow req list` | （无） | 列出所有父需求 | — |
| `/dev-workflow req split` | `{域}/{父需求名}` | 交互式向导逐个创建子需求 | 替代 `split` |

### `version` 命令族（8 个）

| 命令 | 必传参数 | 作用 |
|------|---------|------|
| `/dev-workflow version create` | `{版本号}` | 交互式建版本（4 步：DRAFT 文件 → 扫描 → 多选 → 回写 metadata） |
| `/dev-workflow version show` | `{版本号}` | 显示版本详情 + 子需求状态聚合 |
| `/dev-workflow version list` | （无） | 列出所有版本 |
| `/dev-workflow version add-sub` | `{版本号} {子需求ID}` | DRAFT 版本增量加子需求 |
| `/dev-workflow version start` | `{版本号}` | DRAFT → IN_PROGRESS（须 ≥1 子需求且 ≥1 子需求已推进） |
| `/dev-workflow version ready` | `{版本号}` | IN_PROGRESS → READY（须全部子需求 COMPLETED） |
| `/dev-workflow version close` | `{版本号}` | READY → RELEASED（发布，写 releasedAt） |
| `/dev-workflow version archive` | `{版本号}` | RELEASED → ARCHIVED（永久封存） |

### 保留命令（7 个）

| 命令 | 必传参数 | 作用 |
|------|---------|------|
| `/dev-workflow next` | `{子需求ID}` | 推进子需求到下一阶段（缺参报错 + 列可选项） |
| `/dev-workflow approve` | `{子需求ID}` | 确认子需求当前人工门（设计审核 / plan / CR 裁决，按状态自动分发） |
| `/dev-workflow status` | `[子需求ID \| 版本号]` | 显示进度（缺参扫描 + 汇总） |
| `/dev-workflow rework` | `{子需求ID}` | 子需求从 COMPLETED 回退到 ANALYZING（强门禁：版本非 RELEASED/ARCHIVED） |
| `/dev-workflow summary` | `{版本号}` | 输出版本聚合 DDL / Job·MQ / API 清单（给 DBA / 运维 / 前端） |
| `/dev-workflow summary --merge` | `{V1} {V2} ...` | 多版本合并清单（写 `docs/version/.merged/change-manifest-{Y}-{M}-{D}.md`；仅在用户显式传 `--merge` 时启用） |
| `/dev-workflow discovery refresh` | （无） | 清空 DiscoveryContext 缓存，重跑 manifest + CLAUDE.md 发现流程（CLAUDE.md 修改后 / 新增模块后触发） |

**总命令数**：**19 启用**（4 req + 8 version + 7 保留）+ 3 删除（见下）。`summary --merge` 与 `discovery refresh` 的详细逻辑见 `references/commands.md` §C。

### ID 格式

- **父需求 ID** = `{域}/{父需求名}`（如 `order/订单取消优化`）
- **子需求 ID** = `{域}/{父需求名}#{子需求名}`（如 `payment/支付渠道重构#alipay`）
- 按**最后一个 `#`** 拆分：`#` 之前 = 父路径，之后 = 子名

### 已删除命令（3 个）的迁移指南

v1 旧命令已硬切换删除；执行会立即报错并给出迁移指南。

| v1 命令 | 状态 | 迁移到 |
|--------|------|--------|
| `/dev-workflow use {需求ID}[#里程碑]` | ❌ 已删除 | **直接传子需求 ID** 给 `next / approve / status / rework`。v2 无活动指针，每次命令必须显式传参 |
| `/dev-workflow split {需求ID} {里程碑列表}` | ❌ 已删除 | **`/dev-workflow req split {父需求ID}`** —— 启动交互式向导逐个创建子需求。旧版里程碑嵌套目录已废弃，子需求同级扁平化 |
| `/dev-workflow start {需求名}` | ❌ 已删除 | **`/dev-workflow req create {域}/{父需求名}`** —— 创建父需求后，用 `req split` 进入子需求创建向导 |

---

## 使用示例

### 示例一：单子需求（最常见）

订单取消优化 —— 单父需求、单子需求、无版本管理诉求（也走版本，但只含一个子需求）。

```bash
# 1. 创建父需求（domain=order）
/dev-workflow req create order/订单取消优化
#   → 创建 docs/discuss/order/订单取消优化/.task/parent.md
#   → 提示：下一步用 req split 创建子需求

# 2. 交互式向导创建子需求（输入子需求名 / 描述 / 模块影响，逐个创建）
/dev-workflow req split order/订单取消优化
#   → 向导询问：子需求名 > 描述 > 模块影响
#   → 创建 docs/discuss/order/订单取消优化/.task/订单取消逻辑/metadata.md（8 字段）
#   → 提示：下一步用 version create 绑定版本

# 3. 创建版本并选入子需求（4 步流程）
/dev-workflow version create v1.0
#   → 步骤1：建空 DRAFT 文档 docs/version/v1.0（9 字段，status=DRAFT）
#   → 步骤2：扫描未绑定子需求 → 列出 order/订单取消优化#订单取消逻辑（DISCUSSING）
#   → 步骤3：交互多选（输入编号）→ 选中 1 个子需求
#   → 步骤4：回写子需求 metadata.md.versionBinding = "v1.0"

# 4. 启动版本
/dev-workflow version start v1.0
#   → 校验：DRAFT + ≥1 子需求 + ≥1 子需求已推进
#   → 状态：v1.0: DRAFT → IN_PROGRESS

# 5. 阶段 2：分析与设计（显式传子需求 ID）
/dev-workflow next order/订单取消优化#订单取消逻辑
#   → 调度 analyst + ralph 产出 analysis/、design.md
#   → 状态：metadata.md.currentState: DISCUSSING → ANALYZING → PENDING_DESIGN_REVIEW

# 6. 阶段 3：设计审核（人工门）
/dev-workflow approve order/订单取消优化#订单取消逻辑
#   → 逐项核对 design.md 必含清单
#   → 状态：metadata.md.currentState: PENDING_DESIGN_REVIEW → DEVELOPING

# 7. 阶段 4：开发与逐任务审查（多次 next 推进任务）
/dev-workflow next order/订单取消优化#订单取消逻辑
#   → 任务 1 编码完成、CR 扫出问题，停在 PENDING_CR_REVIEW
#   → 人工裁决：#1 ACCEPTED、#2 REJECTED、#3 MODIFIED
/dev-workflow approve order/订单取消优化#订单取消逻辑
#   → 改写 #1/#3，复验绿，任务 1 置 DONE
/dev-workflow next order/订单取消优化#订单取消逻辑   # 推进任务 2 … 直到全部 DONE

# 8. 阶段 5：收尾验收
/dev-workflow next order/订单取消优化#订单取消逻辑
#   → verifier 全量 {test_cmd} + {lint_cmd} + 跨模块一致性
#   → 状态：metadata.md.currentState: REVIEWING → COMPLETED
```

**示例一产物路径**：
```
docs/discuss/order/订单取消优化/
├── .task/
│   ├── parent.md
│   └── 订单取消逻辑/
│       ├── metadata.md              # 8 字段；currentState=COMPLETED; versionBinding=v1.0
│       ├── discussion.md            # 阶段 1 讨论文档
│       ├── analysis/                # 阶段 2 分析产物
│       ├── design.md                # 阶段 2 设计文档
│       ├── design-consensus.md      # 阶段 3 审核记录
│       ├── dev-tasks.md             # 阶段 4 任务清单
│       ├── plans/                   # 阶段 4 复杂任务 LLD
│       ├── review/                  # 阶段 4 CR 记录
│       ├── done/                    # 阶段 4 已完成任务归档
│       ├── acceptance.md            # 阶段 5 验收报告
│       └── change-manifest.md       # 阶段 5 交付清单
docs/version/v1.0                     # 9 字段；status=IN_PROGRESS；subRequirements=[order/订单取消优化#订单取消逻辑]
```

---

### 示例二：多子需求跨域版本

支付平台 v1.0 发布 —— 同时纳入 `order/订单取消优化#订单取消逻辑` 和 `payment/支付渠道重构#alipay`，跨域聚合到同一版本。

```bash
# 1. 先建两个父需求
/dev-workflow req create order/订单取消优化
/dev-workflow req create payment/支付渠道重构
#   → 各创建 docs/discuss/{order,payment}/{需求名}/.task/parent.md

# 2. 在各自父需求下用 req split 创建子需求
/dev-workflow req split order/订单取消优化
#   → 向导创建子需求 订单取消逻辑
/dev-workflow req split payment/支付渠道重构
#   → 向导创建子需求 alipay
#   → 向导创建子需求 wechat（同一版本可选；本例只选 alipay 演示）

# 3. 创建版本同时纳入两域子需求（关键演示：跨父 / 跨域）
/dev-workflow version create v1.0
#   → 步骤1：建空 DRAFT 文档 docs/version/v1.0
#   → 步骤2：扫描未绑定子需求（跨父需求聚合）:
#       [1] order/订单取消优化#订单取消逻辑   (DISCUSSING)
#       [2] payment/支付渠道重构#alipay       (DISCUSSING)
#       [3] payment/支付渠道重构#wechat       (DISCUSSING)
#   → 步骤3：交互多选（输入编号）> 1,2
#   → 步骤4：同时回写两个子需求 metadata.md.versionBinding = "v1.0"
#   → 校验：子需求归属唯一 → 通过；不重复打包

# 4. 启动版本
/dev-workflow version start v1.0
#   → 校验：DRAFT + ≥1 子需求
#   → 状态：v1.0: DRAFT → IN_PROGRESS

# 5. 两子需求并行推进阶段 2-5（互不依赖、目录不重叠时由 Claude 判断可并行）
#    子需求 A：order 域
/dev-workflow next order/订单取消优化#订单取消逻辑
#   → 阶段 2 设计 → PENDING_DESIGN_REVIEW
/dev-workflow approve order/订单取消优化#订单取消逻辑
#   → 阶段 3 通过 → DEVELOPING
#    ... 阶段 4、5 同示例一

#    子需求 B：payment 域（可与 A 并行编码）
/dev-workflow next payment/支付渠道重构#alipay
#   → 阶段 2 设计 → PENDING_DESIGN_REVIEW
/dev-workflow approve payment/支付渠道重构#alipay
#   → 阶段 3 通过 → DEVELOPING
#    ... 阶段 4、5 同示例一

# 6. 全员子需求 COMPLETED 后 → 版本推进
/dev-workflow version ready v1.0
#   → 校验：IN_PROGRESS + 所有子需求 currentState=COMPLETED
#   → 状态：v1.0: IN_PROGRESS → READY

/dev-workflow version close v1.0
#   → 二次确认：即将发布版本 v1.0
#   → 写 releasedAt
#   → 状态：v1.0: READY → RELEASED

# 7. 后续归档（不可逆，强警告）
/dev-workflow version archive v1.0
#   → 二次确认：归档后永久只读
#   → 写 archivedAt
#   → 状态：v1.0: RELEASED → ARCHIVED（永久封存）

# 8. 跨域聚合交付清单（按版本聚合）
/dev-workflow summary v1.0
#   → 输出两个子需求所有 DDL / Job·MQ / API
```

**示例二产物路径**：
```
docs/discuss/order/订单取消优化/.task/订单取消逻辑/metadata.md     # versionBinding: v1.0
docs/discuss/payment/支付渠道重构/.task/alipay/metadata.md         # versionBinding: v1.0
docs/discuss/payment/支付渠道重构/.task/wechat/metadata.md         # versionBinding: （空，未纳入 v1.0）
docs/version/v1.0                                                  # 9 字段；subRequirements=[order/...#订单取消逻辑, payment/...#alipay]
```

---

### 示例三：rework 返工流程

阶段 5 验收时发现 design.md 方案有缺陷，需回退该子需求重新设计。

```bash
# 前提：子需求 A 处于 COMPLETED，版本 v1.0 处于 IN_PROGRESS
# 验收 review 发现 design.md 数据模型有缺陷，需重新设计

# 1. 触发 rework（强门禁：版本必须 ∈ {DRAFT, IN_PROGRESS, READY}）
/dev-workflow rework order/订单取消优化#订单取消逻辑
#   → 校验：currentState=COMPLETED + 版本 v1.0 状态=IN_PROGRESS（通过门禁）
#   → 执行 rework（详见 references/rework.md）:
#     * 创建返工单 docs/discuss/order/订单取消优化/.task/订单取消逻辑/rework/R1-数据模型缺陷.md
#     * 状态：metadata.md.currentState: COMPLETED → ANALYZING
#     * 状态：metadata.md.currentStage: 5 → 2

# 2. 阶段 2 修订 design.md
/dev-workflow next order/订单取消优化#订单取消逻辑
#   → 修订 design.md（数据模型调整）
#   → 状态：ANALYZING → PENDING_DESIGN_REVIEW

# 3. 阶段 3 重审（人工门）
/dev-workflow approve order/订单取消优化#订单取消逻辑
#   → 逐项核对修订后的 design.md
#   → 状态：PENDING_DESIGN_REVIEW → DEVELOPING

# 4. 阶段 4 重做受影响任务
/dev-workflow next order/订单取消优化#订单取消逻辑
#   → 复杂任务重出 plan → PLAN_CONFIRMED → 编码 → CR
#   → 状态：DEVELOPING
/dev-workflow approve order/订单取消优化#订单取消逻辑   # CR 门裁决
/dev-workflow next order/订单取消优化#订单取消逻辑   # 推进到下一个任务
# ... 直至所有 DONE

# 5. 阶段 5 重验
/dev-workflow next order/订单取消优化#订单取消逻辑
#   → 全量回归通过 → COMPLETED

# 6. 重新推版本（v1.0 状态不变：仍是 IN_PROGRESS，其他子需求不受影响）
/dev-workflow version ready v1.0
#   → 校验：所有子需求 COMPLETED
#   → 状态：v1.0: IN_PROGRESS → READY

# 7. 后续 close / archive 同示例二
```

**版本门禁边界示例**（强门禁的拦截）：
```bash
# 如果 v1.0 已 RELEASED，rework 会立即报错
/dev-workflow rework order/订单取消优化#订单取消逻辑
#   → [字段 versionStatus RELEASED] 版本已发布，禁止 rework。建议：如需修复请新建子需求并 /dev-workflow version add-sub 加入新版本

# 如果 v1.0 已 ARCHIVED，rework 同样报错
/dev-workflow rework order/订单取消优化#订单取消逻辑
#   → [字段 versionStatus] 版本已永久封存，禁止 rework

# RELEASED / ARCHIVED 版本的任何修改类命令一律拒绝
#   如需修复：建新子需求 + 新版本（v1.1）→ version add-sub → 走完整流程
```

**示例三产物路径**：
```
docs/discuss/order/订单取消优化/.task/订单取消逻辑/
├── metadata.md                       # 8 字段；currentState=COMPLETED；versionBinding=v1.0；阶段产物引用追加 rework/R1-...
├── rework/
│   └── R1-数据模型缺陷.md             # 返工单
├── analysis/                          # 修订后的分析
├── design.md                          # 修订后的设计
├── design-consensus.md                # 阶段 3 重审记录
└── ...                                # 阶段 4-5 产物全部更新
docs/version/v1.0                      # 9 字段；状态保持 IN_PROGRESS → READY → RELEASED
```

---

## 产出物目录

```
docs/
├── discuss/                              # 子需求树（按域/父需求/子需求组织，扁平化）
│   └── {域}/{父需求名}/
│       └── .task/
│           ├── parent.md                 # 父需求摘要（req create 创建）
│           └── {子需求名}/
│               ├── metadata.md           # ★唯一状态源（8 字段：subReqId / parentReqId / versionBinding / currentStage / currentState / createdAt / updatedAt / 阶段产物引用）
│               ├── discussion.md         # 阶段 1 讨论文档
│               ├── analysis/             # 阶段 2 分析产物
│               ├── design.md             # 阶段 2 设计文档
│               ├── design-consensus.md   # 阶段 3 审核记录
│               ├── dev-tasks.md          # 阶段 4 任务清单
│               ├── plans/                # 阶段 4 复杂任务 LLD
│               ├── done/                 # 阶段 4 已完成任务归档
│               ├── review/               # 阶段 4 CR 记录
│               ├── acceptance.md         # 阶段 5 验收报告
│               ├── change-manifest.md    # 阶段 5 交付清单
│               └── rework/               # 返工单（R{n}-{原因}.md）
└── version/                              # 版本聚合（全局，跨父需求/跨域）
    ├── v1.0                              # 无扩展名；9 字段；不缓存子需求状态
    ├── v1.1
    └── v2.0
```

**v1 → v2 目录变更**：
- ❌ 删除 `docs/discuss/.workflow-active`（活动指针）
- ❌ 删除 `docs/discuss/{域}/{需求名}/.task/progress.md`（替换为各子需求 `metadata.md`）
- ❌ 删除 `docs/discuss/{域}/{需求名}/.task/milestones/{M}/` 嵌套（子需求同级扁平化）
- ✅ 新增 `docs/version/{版本号}` 全局版本文件

---

## 依赖与约定

- **依赖 skill/agent**：`dev-discuss`（阶段1）、`{discovery_cmd}`（架构文档发现）、`analyst`/`architect`/`planner`/`executor`/`code-reviewer`/`verifier`（OMC agents）、`team`（并行编码）、`ralph`（汇总设计）
- **测试/校验**：验收基线 = `{test_cmd} {module_root_glob}/...` 单测绿 + 改动文件 `{lint_cmd}` 语法校验。`{static_analysis_cmd}` 默认不纳入验收（存量项目历史告警多、收益低），项目有干净基线时再可选开启。具体命令按项目 manifest 文件配置
- **单仓库单分支**：所有模块共用一条 feature 分支，diff 用 `git diff <默认分支>...HEAD -- {module_root_glob}` 按目录隔离；**无独立分支/PR**
- **架构规则**：遵守项目 `CLAUDE.md` 与 `.claude/rules/` 的架构与编码规范
- **产出物只落项目内** `docs/discuss/{域}/{需求名}/.task/` 与 `docs/version/`，禁止写入 home 或仓库外
- **并发协作**：metadata.md 与 version 文件编辑**不依赖自动加锁**，协作时人工协调（spec 不承诺并发安全）
- **错误处理哲学**：严格失败 —— 任何校验失败立即停止；错误信息三段式 `[字段 {X} {当前值}] {原因}。建议: {修复}`

---

## 参考索引（references/）

> 以下文件由其他 worker 产出。本 README 只列出引用路径与定位，详见对应 reference。

| 你要做 | 先读 |
|--------|------|
| 了解上下文发现机制（manifest 文件 + CLAUDE.md → DiscoveryContext） | `references/discovery.md` |
| 写/更新 metadata.md、初始化任务目录、查状态枚举 | `references/templates.md` |
| 执行任意 `/dev-workflow` 子命令的详细逻辑 | `references/commands.md` |
| 执行**阶段 2** 分析与设计 | `references/stage-2-design.md` |
| 执行**阶段 3** 设计审核清单门 | `references/stage-3-review.md` |
| 执行**阶段 4** 开发（复杂度/并行 + plan/编码/CR/改写 全部 prompts） | `references/stage-4-dev.md` |
| 执行**阶段 5** 收尾验收 + 异常处理（BLOCKED / 回退 / 恢复） | `references/stage-5-accept.md` |
| 执行 `/dev-workflow rework` 返工 | `references/rework.md` |
| 执行 `/dev-workflow summary` 产出交付清单 | `references/summary.md` |
| 总览、设计理念、命令速查、使用示例 | `README.md`（本文件） |
| 路由器 + 常驻安全规则 | `SKILL.md` |

> **执行某阶段/命令前必须先读对应 reference 文件**再行动——尤其阶段 4，prompts 和人工门的精确措辞都在 `stage-4-dev.md`，凭记忆执行易漏步、易卡死。