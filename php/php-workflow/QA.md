# php-workflow 分析报告

> 仅读取分析报告。基于 `php/php-workflow/` 当前文件状态。

---

## 1. 完整处理流程图

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 1 需求讨论   /php-workflow start {需求名}                            │
│   ├─ 询问业务域（从 composer autoload/modules 推断）                       │
│   ├─ 检查 docs/.req-discuss/{域}/{需求名}.md 是否存在                     │
│   ├─ 调用 /req-discuss skill 多轮对话                                      │
│   └─ 创建 .task/progress.md（状态 = DISCUSSING → ANALYZING）              │
│ 状态: DISCUSSING                                                          │
└────────────────────────────────────┬────────────────────────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 2 分析与设计   /php-workflow next   → state = ANALYZING              │
│   ├─ 步骤 1: 受影响模块独立分析（并行 analyst → analysis/{模块}.md）       │
│   │    优先复用 docs/{模块}/{overview,business,contracts,flows}.md         │
│   └─ 步骤 2: ralph 汇总设计 → design-consensus.md + dev-tasks.md          │
│        校验 cross-module.md 事件链；冲突则写 conflicts.md 标 BLOCKED        │
│ 产出: design-consensus (6项必含清单) / dev-tasks (复杂度标注)              │
│ 状态: PENDING_DESIGN_REVIEW                                                │
└────────────────────────────────────┬────────────────────────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ★ 阶段 3 设计审核门（人工门）  /php-workflow approve                       │
│   清单 6 项逐项核对（契约/边界/决策理由/验收/未决项/实现要点）              │
│   ├─ 通过 → design-consensus 追加 "## 设计确认: APPROVED" → DEVELOPING    │
│   └─ 打回 → 阶段 2 补充（next 重跑）                                       │
└────────────────────────────────────┬────────────────────────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 4 开发与逐任务审查  /php-workflow next → state = DEVELOPING          │
│   Claude 判断: 编码并行 vs 串行（按依赖图/目录重叠，按波次组织）            │
│   ┌──── 每个任务独立闭环 ──────────────────────────────────────────┐      │
│   │ TODO                                                            │      │
│   │  ⓪ 复杂度判断                                                    │      │
│   │  ├ 简单 ──────────────────────────────────┐                     │      │
│   │  └ 复杂 → plan/LLD (architect/planner)   │                     │      │
│   │           ▼ PLANNING                       │                     │      │
│   │     ★ PENDING_PLAN_REVIEW (人工)            │                     │      │
│   │           ▼ PLAN_CONFIRMED                 │                     │      │
│   │  ① 编码 executor（对照 plan/design） ←────┘                     │      │
│   │     ▼ CODING                                                    │      │
│   │  ② DoD: phpunit 绿 + php -l 通过                                │      │
│   │  ③ CR 扫描 code-reviewer (只读，只产清单)                       │      │
│   │     ▼ CR_SCANNED                                                │      │
│   │  ★ PENDING_CR_REVIEW (人工逐条裁决 ACCEPTED/REJECTED/MODIFIED)  │      │
│   │     ▼ CR_CONFIRMED                                              │      │
│   │  ⑤ 改写 executor（只改已采纳项）                                 │      │
│   │     ▼ REWRITING                                                 │      │
│   │  ⑥ 复验 + 三处回写（progress/dev-tasks/done）                    │      │
│   │     ▼ VERIFYING → DONE                                          │      │
│   └──────────────────────────────────────────────────────────────────┘      │
│ 全部 DONE → 进入阶段 5                                                      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 5 收尾验收  /php-workflow next → state = REVIEWING                  │
│   verifier 独立验收：                                                       │
│   ├─ 全量 phpunit 绿                                                       │
│   ├─ php -l 全部通过（phpstan 默认不卡）                                    │
│   ├─ 跨模块契约闭合（design-consensus × cross-module.md）                  │
│   ├─ 迁移可用性                                                            │
│   └─ 写入 acceptance.md                                                    │
│  状态: COMPLETED                                                          │
└────────────────────────────────────┬────────────────────────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ /php-workflow summary → change-manifest.md (DDL/Job·MQ/API)             │
│ 可选 → release-docs 生成上线配置说明                                       │
└─────────────────────────────────────────────────────────────────────────┘

旁路通道:
  /php-workflow rework [需求ID][#里程碑]
    ├─ 实现级: 不动 design-consensus, 受影响任务回 TODO
    ├─ 设计级: 追加 "返工修订 R{N}", 退回阶段 2 重审, 下游任务级联重做
    └─ 需求级: 回阶段 1 重新 /req-discuss
```

---

## 2. 产出物路径、文件作用、流程状态机

### 2.1 文档作用清单

| 路径 | 作用 | 何时读 |
|---|---|---|
| `php/php-workflow/SKILL.md` | 路由器 + 常驻安全规则（10 条不变量）| **永远先读** |
| `php/php-workflow/README.md` | 用户总览、流程图、使用示例（三场景）| 用户查阅 |
| `php/php-workflow/references/commands.md` | `use/start/split/next/approve/status/list/rework/summary` 子命令详细逻辑 | 处理任意 `/php-workflow` 命令前 |
| `php/php-workflow/references/templates.md` | progress.md 模板（单/多里程碑）、状态枚举、目录约定 | 写/更新 progress.md、初始化任务目录时 |
| `php/php-workflow/references/stage-2-design.md` | 阶段 2 prompts（analyst/ralph） | 执行 `next` 进入分析时 |
| `php/php-workflow/references/stage-3-review.md` | 阶段 3 审核清单 + 自查结论模板 | 处理 `approve` 设计审核分支时 |
| `php/php-workflow/references/stage-4-dev.md` | 阶段 4 prompts（architect/executor/code-reviewer/改写）+ 子 agent 返回协议 | 阶段 4 全程 |
| `php/php-workflow/references/stage-5-accept.md` | 阶段 5 verifier prompt + 异常处理（BLOCKED/回退/中断恢复）| `next` 进入验收时 |
| `php/php-workflow/references/rework.md` | rework 根因层级与重跑规则 | 处理 `rework` 命令时 |
| `php/php-workflow/references/summary.md` | summary 命令 writer prompt + change-manifest 模板 | 处理 `summary` 命令时 |

### 2.2 产出物路径表

```
docs/.req-discuss/
├── .workflow-active                              # 活动上下文指针（单行 {需求ID}[#里程碑]）
├── {域}/{需求名}/
│   ├── {需求名}.md                               # 阶段1 讨论文档
│   └── .task/
│       ├── progress.md                           # ★唯一状态源
│       ├── analysis/{模块}.md                    # 阶段2 模块分析
│       ├── design-consensus.md                   # 阶段2 共识/契约层
│       ├── dev-tasks.md                          # 阶段2 任务拆分
│       ├── plans/{序号}-{模块}.md                # 阶段4 复杂任务 LLD
│       ├── done/{模块}.md                        # 阶段4 任务完成报告
│       ├── review/{模块}-{序号}.md               # 阶段4 CR 报告 + 人工裁决
│       ├── rework/R{N}-{date}.md                 # 返工单
│       ├── acceptance.md                         # 阶段5 验收报告
│       └── change-manifest.md                    # summary 交付清单
└── milestones/{里程碑}/                          # 多里程碑模式
    └── {上述 .task 子集}
```

### 2.3 状态机

**需求/里程碑级**：
```
DISCUSSING ─→ ANALYZING ─→ PENDING_DESIGN_REVIEW
                                  │ approve
                                  ▼
                              DEVELOPING ─→ PENDING_PLAN_REVIEW ─→ (复杂任务 plan 门)
                                  │              │ approve
                                  │              ▼
                              PENDING_CR_REVIEW   PLAN_CONFIRMED → (回到 DEVELOPING 流)
                                  │ approve
                                  ▼
                              REVIEWING ─→ COMPLETED
```

**任务级**：
```
TODO ─→ PLANNING* ─→ PENDING_PLAN_REVIEW ─→ PLAN_CONFIRMED
                                                  │
                                                  ▼
                                              CODING ─→ CR_SCANNED
                                                          │ (PENDING_CR_REVIEW 在里程碑级)
                                                          ▼
                                                     CR_CONFIRMED ─→ REWRITING ─→ VERIFYING ─→ DONE
       * 简单任务跳过 PLANNING
```

**特殊态**：`BLOCKED`（阶段 2 冲突）、`IN_PROGRESS`（多里程碑需求级）。

---

## 3. 冗余项（可整合的重复内容）

### 3.1 文档结构层面
1. **流程图重复 3 处**：`SKILL.md`（总体）+ `README.md`（详细）+ 各 stage-*.md（局部）。`README.md` 与 `SKILL.md` 的总体流程图信息量高度重叠，仅呈现形式不同。
2. **"Bash 静态分析约束"在每条 agent prompt 里都重复**：`stage-2-design.md`（analyst/ralph ×2）、`stage-4-dev.md`（architect/executor/code-reviewer/executor/改写 ×4）、`stage-5-accept.md`（verifier）、`summary.md`（writer）。共重复 ~8 次。
3. **"子 agent 返回后必须执行的动作"四步协议在 stage-4-dev.md 里写了 4 次**（architect 返回、executor 编码返回、CR 返回、verifier 返回虽在 stage-5），属于同一协议反复粘贴。
4. **"设计分两层"原则**在 `SKILL.md`、`README.md`、`stage-2-design.md`、`stage-4-dev.md` 至少 4 处提及。
5. **状态枚举在 3 处定义**：`SKILL.md`（不变量 1）、`templates.md`（状态枚举章节）、`stage-4-dev.md`（任务级状态行）。
6. **活动指针与里程碑"粘住"规则**：`SKILL.md`、`commands.md` 头部、`README.md` 命令速查区 3 处。

### 3.2 命令/路径层面
7. **"docs/.req-discuss/{域}/{需求名}/..." 这个根路径在 8 个文件里反复出现**（每处 stage 都重写一次完整路径）。可考虑用相对路径 `.task/{...}` + 一处总约定，agent prompt 真正执行时再展开。
8. **三道人工门清单**（设计审核 / plan 门 / CR 门）的"停在等用户"提示在 `commands.md`、`stage-3-review.md`、`stage-4-dev.md` 重复描述。
9. **DoD 定义**（`phpunit 绿 + php -l 通过 + CR + 改写 + 复验`）：`SKILL.md`、`templates.md` DoD 说明、`stage-4-dev.md` 复验节、`stage-5-accept.md` 验收项，至少 4 处。

### 3.3 提示语层面
10. **"子 agent 跑完 ≠ 流程推进"** 这个警告语在 `SKILL.md`（不变量 1）、`stage-4-dev.md`（CR 节标题）、`stage-5-accept.md` 至少 3 次以相近措辞出现。
11. **"不许静默结束本轮"** 类的话术在 stage-4-dev.md 中每个子 agent 返回协议都重复。
12. **`/php-workflow use` 行为说明**在 `SKILL.md`（活动上下文章节）、`README.md`（命令速查表）、`commands.md`（use 完整逻辑）3 处，详略不一。

---

## 4. 改进项

### 4.1 结构层面
1. **SKILL.md 瘦身**：当前承担"路由器 + 安全规则 + 流程图 + 命令速查 + 不变量 + 索引"六重职责。建议把"流程图"与"命令速查"完整版移到 `README.md`，SKILL.md 只保留路由器 + 10 条不变量 + references 索引。预计可减 40-50%。
2. **抽取"agent prompt 公共前缀"模板**：把"模块边界 + 复杂度判断 + Bash 静态分析约束 + 产出物路径 + 读完产出文件后回写"做成共享模板/变量，stage-*.md 里只写每个 agent 独有的部分（任务描述、必含清单、审查维度）。
3. **统一状态枚举表到 `templates.md`**：把 `SKILL.md` 与 `stage-4-dev.md` 里的状态枚举都集中到 `templates.md`，并在那里加"状态转换矩阵"图，让所有引用变成 `详见 templates.md §状态枚举`。

### 4.2 内容层面
4. **根路径变量化**：在 SKILL.md 顶部定义 `产出物根 = docs/.req-discuss/{域}/{需求名}/.task/`，所有 stage-*.md 引用时用 `$ROOT/plans/...` 形式，主 Agent 实际拼装时再展开。好处是路径集中修改不出错。
5. **"子 agent 返回后四步协议"做成可复用片段**：在 `templates.md` 或新文件 `agent-protocol.md` 定义，主 Agent 在每个子 agent 收尾处直接引用，而不是每个 stage 重写一次。
6. **"Bash 静态分析约束"提到 SKILL.md 的不变量**，stage-*.md 里只在 prompt 头部以"参见 SKILL.md 不变量 N"形式引用，节省大量重复。
7. **加一份"中断恢复速查"**：当前 `stage-5-accept.md` 只一句话，但中断恢复实际涉及 5 个阶段 + 多里程碑 + 活动指针 + rework 残留态，可能在真实使用中频繁出错。

### 4.3 流程层面
8. **阶段 4 并行判断缺少"何时显式询问用户"约定**：`stage-4-dev.md` 说"由 Claude 判断"，但没说明若判断可能影响数小时编码结果时是否要先和用户确认。补一条"判断成本估算 > N 行代码 / N 个文件时先告知用户再决"的规则。
9. **rework 缺少"级联任务过滤"**：`rework.md` 步骤 4 说"自动算出下游任务，列给人工确认"，但没说下游任务是否包含"已完成但不影响最终产物的辅助任务"（如日志、注释更新）。需要明确"依赖图反向遍历"的口径。
10. **summary 与 release-docs 的衔接**：`summary.md` 末尾说"两者不重复"，但没说同一份 change-manifest 是否需要二次 review。建议在 change-manifest 落盘后由 user 选择要不要喂 release-docs，而不是主 Agent 自动判断。
11. **CR 零问题分支的"跳过裁决"提示强度不足**：`commands.md` C 段说"零问题 → 跳过裁决，置 CR_CONFIRMED"，但 `stage-4-dev.md` 又写"零问题（PASSED）也要输出"无需裁决，执行 approve"，不许静默卡住"。这两处表达略有差异，合并为统一措辞。
12. **缺失"已 DONE 需求/归档"机制**：当前没有 `archive` 或 `close` 命令，COMPLETED 的需求会一直留在 `docs/.req-discuss/` 下。`/php-workflow list` 还能看到吗？需要明确归档/隐藏规则。

### 4.4 可读性层面
13. **"★" 符号密度过高**：`stage-4-dev.md` 里"★★"出现 3 次，"★"出现 12+ 次。建议用文字标签（`[强制]`/`[易卡死]`/`[关键]`）替代星号。
14. **`阶段 4 内/5 内` 这种嵌套**在 `stage-4-dev.md` 出现了 4+ 次，括号式中文不易扫读。可拆成"阶段 4.1/4.2/4.3"子编号。
15. **示例缺中文一致性**：`README.md` 示例一里用 `订单取消优化`、`支付渠道重构#alipay` 等非常具体，但 `commands.md` 用 `{需求名}` 占位符。建议 commands.md 也补一个最小可跑的"订单取消"示例，降低首次使用门槛。

---

## 一句话总结

**架构是好的**（状态机 + 三道人工门 + 任务级闭环 + rework 通道，闭环完整），**冗余主要在文档层**（agent prompt 公共前缀、状态枚举、根路径、子 agent 协议 4 类内容反复粘贴）。**最大改进收益**是把 `templates.md` 升级为"状态枚举 + 路径约定 + agent 公共协议 + 子 agent 返回四步"的总约定源，让 `SKILL.md` 瘦身到 30% 体量、`stage-*.md` 里所有 agent prompt 通过模板插值复用公共部分。
