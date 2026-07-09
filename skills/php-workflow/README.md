# Workflow — PHP 单体多模块需求开发全流程编排

状态机驱动的开发流程 skill。把"需求讨论 → 分析设计 → 开发 → 审查 → 验收"串成一个统一入口，用 `progress.md` 记录状态，每次 `/workflow next` 自动决定下一步调度哪个 agent、传什么参数。

面向伪多模块单体项目：代码都在同一仓库 `modules/{模块}` 下，跨模块走 Events/Listeners + Service，审查按模块路径过滤 diff，架构上下文取自 `docs/workflow/{module}/`（php-analyzer 产出）。测试/校验等具体命令默认按 PHP 工具链（phpunit / php -l），可按项目配置替换。

---

## 设计理念

| 原则 | 含义 |
|------|------|
| **状态机单一数据源** | `progress.md` 是唯一状态源；每次状态变化即时回写（阻塞步骤） |
| **四道人工门** | 设计审核（阶段3）、复杂任务 plan（阶段4）、CR 问题裁决（阶段4）、验收问题裁决（阶段5）——关键决策必须人确认 |
| **设计分两层** | design-consensus = 共识/契约层（小需求够用）；复杂任务再出任务级 plan/LLD |
| **编码与审查分离** | 编码、CR、改写各自独立 agent，不共享上下文，禁止自审 |
| **编码并行由 Claude 判断** | 互不依赖、目录不重叠的任务可并行；CR 门永远逐任务 |
| **设计错可回退** | rework 通道按根因层级（实现/设计/需求）回退 + 依赖级联重做 |

---

## 五阶段 + 四人工门 主流程

```
  阶段1 需求讨论        /workflow start  → /devops-discuss 多轮对话
     │ (产出 docs/discuss/{需求ID}.md)
     ▼
  阶段2 分析与设计      /workflow next   → analyst 逐模块分析 + ralph 汇总设计
     │ (产出 analysis/、design-consensus.md[必含清单]、dev-tasks.md)
     ▼
 ┌──────────────────────────────────────────┐
 │ 阶段3 设计审核门  ★人工★  PENDING_DESIGN_REVIEW │  ← 清单式审核，缺项打回阶段2
 │   /workflow approve                        │
 └──────────────────────────────────────────┘
     ▼
  阶段4 开发与逐任务审查  /workflow next  （见下方"任务级闭环"）
     │
     ▼
  阶段5 收尾验收        /workflow next   → verifier 全量回归 + 一致性把关（只读，不改代码）
     │ (产出 acceptance/acceptance.md 问题清单)
     ├─ 通过（无问题）→ COMPLETED
     ▼ 有问题
 ┌──────────────────────────────────────────┐
 │ 阶段5 验收确认门 ★人工★ PENDING_ACCEPT_REVIEW │  ← 逐条裁决 ACCEPTED/REJECTED/MODIFIED
 │   /workflow approve                        │
 └──────────────────────────────────────────┘
     ▼
  ACCEPT_FIXING → executor 修复已采纳项 → 重跑收尾验收
     ▼
  COMPLETED ──→ /workflow summary  → 交付清单 change-manifest.md（DDL / Job·MQ / API，给 DBA 与前端）

  ※ 阶段4/5 若发现设计/需求层缺陷 → /workflow rework 回退重做
```

---

## 阶段4 任务级闭环（每个任务独立走完）

```
TODO
 │ ⓪ 复杂度判断（Claude）
 ├─ 简单 ─────────────────────────────────────────────┐
 └─ 复杂 → 出 plan/LLD (architect/planner，只读)         │
          ▼ PLANNING                                    │
       ┌────────────────────────────────────────┐      │
       │ plan 人工门 ★人工★ PENDING_PLAN_REVIEW      │      │
       │   /workflow approve                      │      │
       └────────────────────────────────────────┘      │
          ▼ PLAN_CONFIRMED                              │
 ┌───────────────────────────────────────────────────┘
 │ ① 编码 (executor，简单对照 design-consensus / 复杂对照已确认 plan)
 ▼ CODING
 │ ② DoD：phpunit 绿 + php -l 语法校验通过
 │ ③ CR 扫描 (code-reviewer，只读，只产出编号问题清单，不改代码)
 ▼ CR_SCANNED
       ┌────────────────────────────────────────┐
       │ CR 问题人工门 ★人工★ PENDING_CR_REVIEW      │  ← 逐条裁决 ACCEPTED/REJECTED/MODIFIED
       │   /workflow approve                      │
       └────────────────────────────────────────┘
 ▼ CR_CONFIRMED
 │ ⑤ 改写 (executor，只改已采纳项)
 ▼ REWRITING
 │ ⑥ 复验 + 进度回写（强制）：phpunit 绿 + php -l 通过 → 回写 progress.md + dev-tasks.md
 ▼ VERIFYING → DONE
```

> **CR 黑盒治理**：code-reviewer 只产出问题清单，绝不自动改代码。问题必须经人逐条裁决后，才由另一个 executor 对"已采纳"项改写。
> **进度回写是阻塞步骤**：每次状态流转都即时写回 `progress.md` 任务状态行 + 里程碑进度表计数，并同步 `dev-tasks.md` 子项勾选；不回写不得推进下一个任务。

---

## 里程碑（默认单里程碑）

- **默认**：一个需求 = 一个里程碑，整套 5 阶段直接在需求层跑，无需关心里程碑。
- **大需求**：用 `/workflow split` 按交付切片拆成多个里程碑（如按渠道/子系统/上线批次拆分）。拆分后每个里程碑独立跑阶段 2→5，公共设计骨架（`design-foundation.md`）须先于各里程碑定稿；用 `#里程碑` 选择符分别推进。

---

## rework 返工通道

开发+CR 完成后，人工审核发现设计/实现有根本性问题时用。按根因层级决定回退深度：

| 根因层级 | 含义 | 回退动作 | 重跑范围 |
|---------|------|---------|---------|
| 实现级 | 设计对、代码错 | 不动 design-consensus | 受影响任务回 TODO → 重 code → 重 CR |
| **设计级** | design-consensus 错 | 标返工修订 → 退回阶段2修订 → 阶段3重审 | 受影响任务 **+ 依赖该设计的下游任务**级联回 TODO（复杂任务重出 plan）|
| 需求级 | 需求本身错 | 回阶段1 重新 devops-discuss | 视讨论结论，可能整体重来 |

依赖扩散：自动从 dev-tasks 依赖图算出下游受影响任务，**列给人工确认**后才标重做；未受影响的 DONE 任务保留。

> 边界：只改当前任务能解决 → 用 CR 改写；牵动设计或别的任务 → 用 rework。

---

## 命令速查

| 命令 | 作用 |
|------|------|
| `/workflow use [需求ID][#里程碑]` | **设定活动上下文（粘性）**，之后裸命令默认作用于它 |
| `/workflow start {需求名}` | 创建需求，进入阶段1讨论（自动设为活动）|
| `/workflow next [需求ID][#里程碑]` | 推进到下一阶段 / 下一个任务（省略=活动上下文）|
| `/workflow approve [需求ID][#里程碑]` | 确认当前人工门（设计审核 / plan / CR 裁决 / 验收问题裁决，按状态自动分发）|
| `/workflow status [需求ID][#里程碑]` | 查看进度（省略=活动上下文+高亮；无活动则全部）|
| `/workflow list` | 列出未完成的需求 |
| `/workflow split [需求ID] {里程碑列表}` | 大需求拆里程碑 |
| `/workflow followup {已完成需求ID} [新需求名]` | 基于已完成需求发起新需求（继承设计上下文） |
| `/workflow rework [需求ID][#里程碑]` | 设计/实现缺陷返工 |
| `/workflow summary [需求ID][#里程碑]` | 产出交付清单（DDL / Job·MQ / API）给 DBA 与前端，验收通过后执行 |

- **需求 ID** = `{YYYY-MM-DD}-{域}-{需求名}`（如 `2026-09-12-order-订单取消优化`），与 `docs/discuss/` 目录一致
- **`#里程碑`** 仅多里程碑需求需要（如 `2026-09-12-payment-支付渠道重构#alipay`）
- **活动上下文（推荐）**：`/workflow use` 选一次当前在搞的需求/里程碑（存于 `docs/discuss/.workflow-active`），之后 `next/approve/status/rework` 省略参数即默认指向它，不必每步重复敲长 ID
- 模糊匹配：`use` / 显式传参支持前缀子串（如 `trade#共` → `trade…#共享基础`），唯一即定位
- 省略且无活动上下文时：唯一进行中的自动选中，多个则列出让你选；显式传 ID 可临时操作别的需求而不改活动指针

---

## 使用示例

### 示例一：普通需求（单里程碑，最常见）

```bash
# 1. 起需求，进入讨论（devops-discuss 多轮对话厘清目标/影响）
/workflow start 订单取消优化
#   → 询问业务域=order，多轮讨论，产出 docs/discuss/2026-09-12-order-订单取消优化/discussion.md

# 2. 分析与设计（analyst 逐模块分析 + ralph 汇总出 design-consensus + dev-tasks）
/workflow next
#   → 状态停在 PENDING_DESIGN_REVIEW，给出设计审核清单自查结论

# 3. 设计审核门（你逐项核对 design-consensus 必含清单）
/workflow approve
#   → design-consensus 标 APPROVED，进入开发

# 4. 开发：逐任务闭环（简单任务直接编码→CR 扫描→停在 CR 门）
/workflow next
#   → 任务1 编码完成、CR 扫出 3 个问题，停在 PENDING_CR_REVIEW，呈现问题清单

#    你裁决：#1 ACCEPTED、#2 REJECTED(理由)、#3 MODIFIED(说明)
/workflow approve
#   → 只改 #1/#3，复验绿，任务1 置 DONE，回写 progress.md + dev-tasks.md

/workflow next       # 推进任务2…… 直到全部 DONE

# 5. 收尾验收（verifier 全量 phpunit + php -l + 跨模块一致性；phpstan 默认不卡）
/workflow next
#   → 通过则 COMPLETED
#   → 有问题则停在 PENDING_ACCEPT_REVIEW，呈现问题清单
#    你裁决：#1 ACCEPTED、#2 REJECTED(理由)
/workflow approve
#   → 只修已采纳项，修复后重跑验收
```

### 示例二：大需求（多里程碑 + 复杂任务 plan 门）

```bash
# 需求已讨论完，按交付切片拆里程碑
/workflow split payment/支付渠道重构 alipay,wechat
#   → 确认 alipay/wechat 划分 + 抽出 design-foundation.md（公共骨架，先定稿）

# 选一次活动上下文，之后裸命令默认作用于它（不必每步敲长 ID）
/workflow use payment/支付渠道重构#alipay     # 也可模糊：use payment#alipay

/workflow next        # 阶段2 分析设计 → PENDING_DESIGN_REVIEW
/workflow approve     # 设计审核通过

/workflow next        # 阶段4：某任务判为【复杂】→ architect 出 plan，停在 PENDING_PLAN_REVIEW
/workflow approve     # plan 确认 → 编码 → CR 扫描 → PENDING_CR_REVIEW …

# 切到另一个里程碑：只敲 #
/workflow use #wechat
/workflow next

# 看进度（省略=活动上下文高亮；status 全局进度表）
/workflow status
#   ▶ 活动: payment/支付渠道重构#wechat
#   里程碑 alipay     阶段 4/5 — 开发（进行中）  任务 2/6
#   里程碑 wechat ◀   阶段 3/5 — 设计审核（待审核）任务 0/9
```

### 示例三：需求完成后追加功能 → followup

```bash
# 订单取消优化已 COMPLETED，现在要基于它做"取消原因统计"
/workflow followup 2026-09-12-order-订单取消优化 取消原因统计
#   → 自动继承父需求设计文档到 docs/parent/
#   → 进入阶段 1 讨论，聚焦增量变更
#   → 讨论完成后 /workflow next 走标准 5 阶段流程
```

### 示例四：收尾验收发现设计错 → rework

```bash
# 阶段5 验收时发现 design-consensus 的方案有缺陷，多个已 DONE 任务受影响
/workflow rework 2026-07-09-payment-支付渠道重构#alipay
#   → 确认根因层级 = 设计级
#   → design-consensus 标 "## 返工修订 R1"，里程碑退回阶段2
#   → 自动算出依赖该设计的下游任务，列给你确认（可增删）
#   → 确认后这些任务回 TODO(标 返工R1)，未受影响的 DONE 保留
#   → progress.md 追加返工记录 R1

# 修订设计 → 重审 → 受影响任务级联重跑
/workflow next 2026-07-09-payment-支付渠道重构#alipay     # 阶段2 修订 design-consensus
/workflow approve 2026-07-09-payment-支付渠道重构#alipay  # 阶段3 重审通过
/workflow next 2026-07-09-payment-支付渠道重构#alipay     # 复杂任务重出 plan → 重 code → 重 CR
```

---

## 产出物目录

```
docs/discuss/
  .workflow-active               # 活动上下文指针（单行 {需求ID}[#里程碑]，便捷用，非状态源）
  {需求ID}/
  discussion.md                  # 阶段1 讨论文档
  docs/                          # 需求级参考文档（业务说明、接口文档、原始材料，用户手动放入）
  .task/
    progress.md                  # ★唯一状态源：阶段记录 + 任务清单/里程碑进度表 + 返工记录
    analysis/                    # 阶段2 逐模块分析
    design-consensus.md          # 阶段2 共识/契约层设计（必含清单）
    dev-tasks.md                 # 阶段2 任务拆分（标注 简单|复杂 + 依赖）
    plans/                       # 阶段4 复杂任务的 plan/LLD（简单任务无）
    done/                        # 阶段4 各任务完成标记（改动摘要、契约、测试结果）
    review/                      # 阶段4 各任务 CR 问题清单 + 人工裁决
    rework/                      # 返工单（缺陷返工时才有）
    acceptance/                  # 阶段5 验收报告目录
      acceptance.md              # 收尾验收报告
    change-manifest.md           # /workflow summary 交付清单（DDL/Job·MQ/API，给 DBA 与前端）
  # 多里程碑时，analysis/design-consensus/dev-tasks/plans/done/review/rework 下沉到
  # .task/milestones/{里程碑}/，design-foundation.md 留在 .task/ 根作公共骨架
```

---

## 依赖与约定

- **依赖 skill/agent**：`/devops-discuss`（阶段1）、`php-analyzer`（架构文档）、`analyst`/`architect`/`planner`/`executor`/`code-reviewer`/`verifier`（OMC agents）、`team`（并行编码）、`ralph`（汇总设计）
- **测试/校验**：验收基线 = `vendor/bin/phpunit modules/{模块}/tests` 单测绿 + 改动文件 `php -l` 语法校验。phpstan 默认不纳入验收（存量项目历史告警多、收益低），项目有干净基线时再可选开启。具体命令按项目配置
- **单仓库单分支**：所有模块共用一条 feature 分支，diff 用 `git diff <默认分支>...HEAD -- modules/{模块}` 按目录隔离；**无独立分支/PR**
- **架构规则**：遵守项目 `CLAUDE.md` 与 `.claude/rules/` 的架构与编码规范
- **产出物只落项目内** `docs/discuss/{需求ID}/.task/`，禁止写入 home 或仓库外
