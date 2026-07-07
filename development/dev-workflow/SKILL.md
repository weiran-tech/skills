---
name: dev-workflow
description: 伪多模块单体项目的需求开发全流程编排。状态机驱动，从项目 manifest + CLAUDE.md 运行时发现语言/测试/契约，跨模块走 {contract_type} 通道。当用户说 "workflow"、"开发流程"、"需求流程"、"模块开发流程" 时触发。
---

# Workflow — 单体多模块需求开发全流程编排

v2 版本制度（替代 v1 里程碑制度）。状态机驱动的流程 skill：5 个开发阶段在**子需求级**独立推进，跨域发布通过**版本**聚合。本文件是**路由器 + 常驻安全规则**；各步骤的执行细节按需读取 `references/`（见末尾索引）。

面向伪多模块单体项目：代码同仓 `{module_root_glob}`，跨模块走 `{contract_type}` 通道，审查按模块路径过滤 diff（`git diff <默认分支>...HEAD -- {module_root_glob}`），架构上下文来自 `docs/workflow/{module}/`（{discovery_cmd} 产出）。测试/校验等具体命令默认按当前项目工具链（`{test_cmd}` / `{lint_cmd}`），可按项目配置替换。

## 总体流程

```
1 需求讨论 → 2 分析与设计 →[★阶段3 设计审核门]→ 4 开发与逐任务审查 → 5 收尾验收 → COMPLETED
  (req create) (next: analyst+ralph)  (approve)    (next: 逐任务闭环)      (next: verifier)
                                                        │
  阶段4 逐任务闭环：⓪复杂度判断 →[★复杂任务 plan 门]→ ①编码 → ②DoD → ③CR扫描 →[★CR人工门]→ ⑤改写 → ⑥复验+回写 → DONE
  ※ 阶段 4/5 发现设计/需求层缺陷 → /dev-workflow rework 按根因层级回退 + 依赖级联重做
```

三道人工门（均由 `/dev-workflow approve` 按状态分发）：**阶段3 设计审核** / **阶段4 复杂任务 plan** / **阶段4 CR 问题裁决**。

子需求 = 5 阶段流程的最小执行单元；版本 = 跨域发布批次的聚合视图（多个子需求打包成一个版本发布）。

## 命令速查

所有命令必须**显式传参**（子需求 ID 或版本号），无任何隐式解析或粘性指针。

### req 子命令族（子需求管理，4 个）

```
/dev-workflow req create {域}/{父需求名}                    # 创建父需求（单子需求场景）
/dev-workflow req show {子需求ID}                          # 查看子需求详情（metadata.md + 阶段产物）
/dev-workflow req list                                    # 列出所有子需求（含状态/版本绑定）
/dev-workflow req split {域}/{父需求名}                    # 把大需求拆成多个子需求（交互式向导）
```

### version 子命令族（版本管理，8 个）

```
/dev-workflow version create {版本号}                      # 创建版本（4 步流程：建空 DRAFT → 扫描未绑定 → 交互多选 → 回写 metadata.md.versionBinding）
/dev-workflow version show {版本号}                        # 查看版本详情（含聚合子需求状态）
/dev-workflow version list                                # 列出所有版本（含状态/子需求数）
/dev-workflow version add-sub {版本号} {子需求ID}          # 向版本添加子需求（仅 DRAFT 状态可执行）
/dev-workflow version start {版本号}                       # DRAFT → IN_PROGRESS（前置：至少 1 个子需求）
/dev-workflow version ready {版本号}                       # IN_PROGRESS → READY（前置：所有子需求 COMPLETED）
/dev-workflow version close {版本号}                       # READY → RELEASED（人工确认发布）
/dev-workflow version archive {版本号}                     # RELEASED → ARCHIVED（永久封存，禁止再修改）
```

### 流程推进（7 个保留）

```
/dev-workflow next {子需求ID}                             # 执行下一阶段 / 下一个任务
/dev-workflow approve {子需求ID}                          # 确认当前人工门（阶段3设计 / 阶段4 plan / 阶段4 CR）
/dev-workflow status {子需求ID}                           # 查看进度（省略=列出所有进行中子需求）
/dev-workflow rework {子需求ID}                           # 设计/实现缺陷返工（按根因层级回退 + 依赖级联重做）
/dev-workflow summary {版本号}                            # 产出交付清单（DDL / Job·MQ / API）给 DBA 与前端（按版本聚合）
/dev-workflow summary --merge {V1} {V2} ...               # 多版本合并清单（写 docs/version/.merged/change-manifest-{Y}-{M}-{D}.md）
/dev-workflow discovery refresh                            # 清空 §7 缓存，重跑 §1 发现（CLAUDE.md 修改后 / 新增模块后触发）
```

> **总命令数（AC3 修订）**：**19 启用**（4 req + 8 version + 7 保留） + 3 删除（use / split / start）。`summary --merge` 与 `discovery refresh` 的详细逻辑见 `references/commands.md` §C。

### 已删除命令（v1 → v2 迁移指南）

- `use {ID}` → **已废弃**：删除粘性活动指针，每次操作必须显式传 ID
- `start {需求名}` → **改为**：`req create {域}/{父需求名}` + `req split {域}/{父需求名}`（向导式创建子需求）
- `split {ID} {里程碑列表}` → **改为**：`req split {域}/{父需求名}`（交互式向导逐个询问子需求 名/描述/模块影响）

- **子需求 ID** = `{域}/{父需求名}#{子需求名}`（如 `payment/支付渠道重构#alipay`），与目录 `docs/discuss/{域}/{父需求名}/.task/{子需求名}/` 一致
- **版本号**：任意非空字符串（如 `v1.0` / `v1.0-rc1` / `2024Q1`），仅做去重检查，不做 SemVer 校验
- 命令的详细处理逻辑见 `references/commands.md`

## 项目约定

- **单体仓库**：默认已在项目仓库根目录。子需求产出物存于 `docs/discuss/{域}/{父需求名}/.task/{子需求名}/`（目录结构见 `references/templates.md`）
- **版本文件存于** `docs/version/{版本号}`（全局资源，跨父需求、跨业务域）
- **模块路径** `{module_root_glob}/`；模块清单从项目 `manifest file` + `CLAUDE.md` 运行时声明获取
- **架构文档** `docs/workflow/{模块名}/`（overview/business/contracts/flows）+ `docs/workflow/cross-module.md`，由 `{discovery_cmd}` 产出；缺失则先提示跑 `{discovery_cmd}`
- **验收基线（强制）**：`{test_cmd} {module_root_glob}/{模块}/tests` 单测绿 + 改动文件 `{lint_cmd}` 语法校验通过
- **静态分析默认不纳入 DoD/验收**：存量项目历史告警多、收益低；仅项目有干净基线时才可选开启
- **单仓库单分支**：所有模块共用一条 feature 分支，无独立分支/PR；具体命令按项目配置

## Agent 权限与职责分离

| 阶段                         | 执行方式                                        | 权限                   |
| ---------------------------- | ----------------------------------------------- | ---------------------- |
| 2 模块分析                   | `{discovery_cmd}` 或 `analyst`                  | 只读                   |
| 4 任务详细设计（仅复杂任务） | `architect` / `planner`                         | 只读（只设计不写码）   |
| 4 编码                       | `executor`（并行 `team`/串行单个，Claude 判断） | 读写                   |
| 4 CR 扫描（逐任务）          | 单个 `code-reviewer`                            | 只读（只产清单不改码） |
| 4 改写（逐任务）             | 单个 `executor`                                 | 读写（只改已采纳项）   |
| 5 收尾验收                   | `verifier`                                      | 只读                   |

人工门：阶段3 设计审核、阶段4 plan 确认、阶段4 CR 裁决。

---

## 关键不变量（必须遵守，不随阶段文件加载与否而改变）

1. **子 agent 返回 ≠ 流程推进（防卡死）**：每次子 agent（analyst/architect/code-reviewer/executor/verifier）返回后，主 Agent **必须立刻**：① 读取其产出文件（不以子 agent 的返回文本为准）→ ② 回写 metadata.md 对应状态 → ③ 向用户输出结果摘要 + **明确的下一步指令**（该 approve 还是 next）。**绝不允许因为"子 agent 说完了"就静默结束本轮而不给提示。** 尤其 CR 扫描、plan 产出这两个停在人工门前的步骤。
2. **CR 问题人工门**：code-reviewer 只产出问题清单，**绝不直接改代码**；扫出的问题必须经人工逐条裁决（ACCEPTED/REJECTED/MODIFIED）并 `/dev-workflow approve` 后，才由另一个 executor 对已采纳项改写。零问题（PASSED）也要输出"无需裁决，执行 approve"，不许静默卡住。
3. **编码与审查分两轮**：编码、CR、改写各自独立 agent，CR 与编码不共享上下文，禁止同上下文自审。
4. **进度即时回写（阻塞步骤）**：任务每次状态流转（含中间态 CODING/CR_SCANNED/CR_CONFIRMED/REWRITING/DONE）都必须即时写回 metadata.md 任务状态行 + 子需求进度表计数，并把 dev-tasks.md 对应子项 `[ ]→[x]`；回写未完成不得推进下一个任务。`metadata.md` 是子需求状态权威源，与 dev-tasks.md 勾选须一致。
5. **设计分两层**：design-consensus = 共识/契约层（必含清单，阶段3 清单式审核，缺项打回）；复杂任务的实现细节走任务级 plan/LLD（阶段4 编码前出，人工 approve 后才编码）。简单任务只用 design-consensus，不出 plan。
6. **未决项不许悬空**：design-consensus 的 `待确认/TODO` 必须登记成表并有处置，不许默默漏进编码。
7. **设计/需求层缺陷走 rework**，不要硬塞进 CR 改写：CR 改写只解决"设计对、改当前任务小问题"；牵动设计或多任务用 `/dev-workflow rework`，依赖扩散自动算下游 + 人工确认，未受影响的 DONE 保留。
8. **子需求默认单个**：只有大需求才 `req split`；跨模块交互一律通过 `{contract_type}` 通道，禁止直接访问他模块实现细节（具体实现细节按语言而异，统一表述为"直接调用对模块内部的实体"）。
9. **无活动指针**：所有命令必须显式传子需求 ID 或版本号，无任何隐式解析或粘性默认值。`next/approve/status/rework/summary` 缺参 → 报错 + 列出可选项。
10. **版本状态机 5 态**：版本状态 `DRAFT / IN_PROGRESS / READY / RELEASED / ARCHIVED`，全手动转换（`version start/ready/close/archive`），每个转换有严格前置校验。ARCHIVED 永久封存，禁止任何修改类命令；RELEASED 禁止 rework。
11. **metadata.md 单源**：子需求状态唯一权威源是 `docs/discuss/{域}/{父需求名}/.task/{子需求名}/metadata.md`；`docs/version/{版本号}` 不缓存子需求状态，只存子需求 ID 列表 + 聚合视图。子需求 ↔ 版本 一对一绑定（`metadata.md.versionBinding` 单一字符串）。
12. **所有 agent prompt 必须含 Bash 静态分析约束**：禁止 for/while/if/case/here-doc/嵌套 `$()`。产出物只落项目内 `.task/` 或 `docs/version/`，禁止写 home 或仓库外。

---

## references 索引（按需读取，别一次性全载）

| 当你要做                                                                       | 先读                              |
| ------------------------------------------------------------------------------ | --------------------------------- |
| 写/更新 metadata.md / version 文件、初始化目录、查状态枚举                    | `references/templates.md`         |
| 执行任意 `/dev-workflow` 子命令的详细逻辑（含 req/version/next/approve/summary/summary --merge/discovery refresh 等）   | `references/commands.md`          |
| 执行**阶段 2** 分析与设计（analyst/ralph prompts + design-consensus 必含清单） | `references/stage-2-design.md`    |
| 执行**阶段 3** 设计审核清单门                                                  | `references/stage-3-review.md`    |
| 执行**阶段 4** 开发（复杂度/并行判断 + plan/编码/CR/改写 全部 prompts）        | `references/stage-4-dev.md`       |
| 执行**阶段 5** 收尾验收 + 异常处理（BLOCKED/回退/中断恢复）                    | `references/stage-5-accept.md`    |
| 执行 `/dev-workflow rework` 返工                                               | `references/rework.md`            |
| 执行 `/dev-workflow summary` 产出交付清单（按版本聚合 DDL/Job·MQ/API）        | `references/summary.md`           |

> **执行某阶段/命令前，必须先读对应 reference 文件**再行动——尤其阶段 4，prompts 和人工门的精确措辞都在 `stage-4-dev.md`，凭记忆执行易漏步、易卡死。人看的总览与示例见同目录 `README.md`。

## 错误模板

所有错误输出统一使用三段式模板：

```
[字段 {X} {当前值}] {原因}。建议: {修复}
```

例如：
- `[字段 模块路径 {空}] 必填字段缺失。建议: 提供 modules 下的子目录名（如 "payment"）。`
- `[字段 版本状态 RELEASED] 不允许 rework。建议: 修改请新建版本或在 ARCHIVED 前回退至 DRAFT。`