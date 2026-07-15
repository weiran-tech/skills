---
name: fe-workflow
description: 前端项目功能开发流水线总控。串联需求分析→技术设计(含自审)→编码→验证(Lint/Test/QA+CR)→E2E 的完整流程，流水线按分支归档（docs/pipeline/{分支名}/{流水线名}/），一个分支可有多条流水线，一条流水线可容纳多个功能（多份需求+设计，汇总报告），支持从任意步骤开始、断点恢复、--until 只出设计、--start 批量执行已审核功能（适合白天出设计晚上跑）。当用户说 "fe-workflow"、"开始流水线"、"完整开发"、"前端开发流程"、"走流程"、"pipeline" 时触发。
---

# FE Workflow — 前端功能开发流水线（总控）

串联完整的前端功能开发流程，每步完成后等待确认再进入下一步。
**流水线不执行任何 git 操作（commit/push/PR），仅做分析和代码生成**，只在功能完成时输出 files_changed 分组 + 建议 commit message，由用户自行提交。

本文件是总控路由 + 硬性规则；各步骤的执行细节按需读取 `references/`（见末尾索引）。**执行某步骤/子命令前必须先读对应 reference 文件**，凭记忆执行易漏步。

## 核心模型：流水线按分支归档，一个分支下可有多条流水线

- **分支目录**：`docs/pipeline/{branch-name}/`，branch-name 取当前分支名去 `feature/` 前缀。一个分支的所有流水线都必须创建在该分支目录下
- **流水线**：分支目录下的子文件夹，一个分支可有多条（如主功能一条、顺路的独立需求另开一条）
- **功能（feature）对齐需求**：流水线内每个功能一份独立的「需求+设计」文档 `spec-{n}-{feat-name}.md`，编号自动递增
- **汇总报告**：verify-report.md / e2e-report.md 每条流水线各一份，**按功能分章节**，更新时只覆盖对应功能的章节

```
docs/pipeline/{branch-name}/          ← 分支目录（分支名去 feature/ 前缀）
├── {pipeline-name-1}/                ← 流水线目录（一个分支可有多条）
│   ├── progress.yaml                 ← 状态权威源（features 数组，管所有功能）
│   ├── spec-1-coupon-list.md         ← 需求+设计合一，每功能一份
│   ├── spec-2-coupon-export.md
│   ├── verify-report.md              ← 汇总一份，按功能分章节
│   ├── e2e-report.md
│   └── start-report.md               ← 批量执行总结（--start 产出）
└── {pipeline-name-2}/
```

**需求与设计合并产出一份 spec**：requirement 写「基本信息 + 一、需求」，design 在同一文件追加「二、设计 + 自审修订」。full 模式下这两步**连续执行、中间不暂停**，design 完成后展示合并摘要，**只审核一次**。

**每步暂停时的交互格式**：

```
是否继续 Step N（步骤名）？
  y — 继续
  s — 跳过此步骤
```

## Input

`/fe-workflow [pipeline-name] [--feat=<id|name>] [--from=<step>] [--until=<step>] [--mode=full|lite] [--auto] [--start] [需求描述]`

- `pipeline-name`: 流水线名称（可选）。用户显式指定优先；不指定则默认取分支名（去 `feature/` 前缀）
- `--feat=<id|name>`: 定位流水线内的某个功能，用于恢复/重跑
- `--from=<step>`: 从指定步骤开始（自动断点恢复时不需要）
- `--until=<step>`: 执行到指定步骤（含人工审核）后结束。典型用法 `--until=design`：白天只出需求+设计，审核通过置 `design_approved: true` 结束
- `--mode=full|lite`: 流水线模式（默认按需求类型自动建议，按功能各自记录）
- `--auto`: 单功能全自动，跳过所有中间确认（门控自动决策）
- `--start`: 批量执行流水线内所有已审核设计（`design_approved: true`）且未实现的功能，严格串行，产出 start-report.md

可用步骤：`requirement` → `design` → `implement` → `verify` → `e2e`

**独立子命令**（不占用流水线步骤）：

- `/fe-workflow api-sync [模块]` — 真实接口就绪后替换 mock
- `/fe-workflow release` — 发布后文档收尾
- `/fe-workflow pr` — CR 结论汇总 + 按功能 commit 引导 + PR 创建（仅在用户明确要求时执行 git 操作）

**独立步骤入口**（不依赖流水线，可对未走流水线的代码/页面直接执行）：

- `/fe-workflow verify` — 独立验证当前分支改动，范围兜底 `git diff --name-only master`
- `/fe-workflow e2e [doc-path] [--yunxiao <目录ID|用例ID>]` — 独立跑 E2E（模式 B 文档驱动 / 模式 C 云效用例驱动，适合存量页面）

**流水线模式（按功能独立选择）**

| 模式 | 适用场景 | 执行步骤 |
|------|---------|---------|
| **full** | 新功能（需要新页面/新路由） | 全部 5 步 |
| **lite** | 功能扩展/Bug修复/小改动 | requirement → implement → verify（design/e2e 跳过）|

## 步骤总览

```
1 requirement → 2 design(含自审) → [需求+设计合并审核] → 3 implement → 4 verify → [有问题才暂停] → 5 e2e
   (需求分析)     (连续执行不暂停)                          (编码规范      (Lint/Test/QA+CR
                                                            skill 前置)     四合一)
```

| 步骤 | 要点 | 权限 |
|------|------|------|
| 1 requirement | 结构化需求写入 spec，建议 full/lite 模式 | 写 spec |
| 2 design | 设计+自审+跨功能文件冲突预检；审核通过置 `design_approved: true` | 写 spec，只设计不写码 |
| 3 implement | **编码规范 skill 前置调用（阻断）**；完成必须回写 files_changed | 读写代码 |
| 4 verify | Lint（白名单自动修复）→ Test（核心函数单测）→ **QA+CR（独立子代理，只读 diff+spec，只产问题清单不改码）**；零阻塞问题自动通过，有问题暂停等用户逐条确认后修复 | 见左 |
| 5 e2e | 三种驱动模式（A spec / B 现有文档 / C 云效用例），失败自动修复后仍失败则暂停提示 | 写测试+截图 |

**verify 内置 CR 的隔离规则**：QA+CR 环节必须派独立子代理（全新上下文），编码与审查不共享上下文，禁止同上下文自审；子代理返回后主流程必须读其产出清单 → 回写 progress.yaml → 输出摘要和下一步提示，不得静默结束。

## 配置（config.yaml，可选）

`docs/pipeline/config.yaml`（项目级，所有流水线共享），不存在则全部走默认：

```yaml
coding_standard_skill:      # 项目编码规范 skill 名（优先级最高，见下方映射表）
e2e_testcase_repo:          # E2E 模式C：云效测试用例库 ID（不配置则仅 A/B 模式）
e2e_testcase_directory:     # E2E 模式C：用例目录 ID
auto_fix_rounds: 2          # --auto/--start 下 verify・e2e 失败自动修复轮数
```

## 项目约定

- **branch-name（硬性）**：分支名去 `feature/` 前缀直接使用，不自行起名；在 master/main/develop 上未指定名称则询问用户并建议先开功能分支
- **目录规则（硬性）**：流水线一律两级结构 `docs/pipeline/{branch-name}/{pipeline-name}/`，禁止在 `docs/pipeline/` 一级直建
- **编码规范前置（强制·阻断）**：implement 前必须通过 Skill tool 实际调用项目编码规范 skill，**调用返回前禁止编写任何业务代码**。解析顺序：config.yaml 的 `coding_standard_skill` > 项目 CLAUDE.md 声明 > 按项目特征自动匹配：

| 项目类型 | 规范 skill |
|---------|-----------|
| 后台管理（如 backend-kejinshou） | `fe-backend-page`（组件 API 另见 `fe-kr36-ui-guide`） |
| 其他前端项目 | 在项目 CLAUDE.md 或 config.yaml 登记（推荐把规范 skill 放项目仓库 `.claude/skills/`，clone 即用）；未登记则提示用户补充，不得凭猜测编码 |

- **接口获取**：项目配置了 Apifox MCP 时优先取真实接口定义；否则走 mock 并在代码中标注，接口就绪后 `/fe-workflow api-sync` 替换
- **验收基线**：Lint/Test 按项目 package.json scripts 实际存在的命令执行（缺失时降级或跳过并说明），不硬编码命令

## Guardrails（硬性规则）

- **编码阶段必须通过 Skill tool 实际调用编码规范 skill**，每次编码都必须产生一次 Skill tool call，不可凭记忆替代；`--auto`/`--start` 同样不可跳过
- **流水线全程不执行任何 git 操作**；跳过的步骤标 `skipped` 而非 `done`
- **progress.yaml 是状态权威源**，每步前后更新（含 in-progress 中间态）；implement 完成必须回写 `files_changed`——它是功能间代码边界，verify/e2e 分析范围与 commit 分组都依赖它
- **写文档步骤（requirement/design）多功能可并行推进；写代码步骤（implement 及之后）同一时刻只允许一个功能**，冲突时提示先完成或标 blocked
- **`--start` 只执行 `design_approved: true` 的功能**（未经审核的设计不得夜间自动编码），严格串行——一个功能完整跑完 implement→verify→e2e 再开始下一个；单功能失败标 `blocked` 记原因，继续下一个，不中断整批
- **design 完成必须做跨功能文件冲突预检**：重叠文件标明执行顺序并记入 decisions
- **verify 的 QA+CR 必须派独立子代理**（全新上下文只读），问题清单经用户逐条确认后才修复已采纳项；子代理返回 ≠ 流程推进（读产物 → 回写 → 提示下一步）
- **汇总报告按功能章节化更新**，不整份重写
- **Preamble 每步执行前必须运行**：注入进度状态、历史 decisions、前序产出摘要（只取片段不读全文）、相关 Memory（若环境支持，最多 3 条）——细节见 `references/commands.md`
- 每步完成暂停等待确认（requirement→design 连续执行、verify 零问题自动通过除外），交互格式统一 `y — 继续 / s — 跳过`；用户随时可说"跳过"或"回退到{步骤}"

## 交互速查

| 场景 | 命令 |
|------|------|
| 新功能完整流水线 | `/fe-workflow [需求描述]` |
| 白天只出需求+设计 | `/fe-workflow --until=design <需求描述>` |
| 同流水线追加功能 | `/fe-workflow <新需求描述>`（编号自动 +1） |
| 晚上批量跑实现+验证 | `/fe-workflow --start` |
| 查看功能看板 / 断点恢复 | `/fe-workflow`（自动检测） |
| 定位某功能重跑 | `/fe-workflow --feat=2 --from=verify` |
| 小改动精简流程 | `/fe-workflow --mode=lite <描述>` |
| 单功能全自动 | `/fe-workflow --auto <描述>` |
| 接口同步 | `/fe-workflow api-sync` |
| 发布后收尾 | `/fe-workflow release` |
| CR 汇总 + PR | `/fe-workflow pr` |
| 独立验证当前分支改动 | `/fe-workflow verify` |
| 独立 E2E（存量页面/云效用例） | `/fe-workflow e2e [doc-path] [--yunxiao <ID>]` |

## references 索引（按需读取，别一次性全载）

| 当你要做 | 先读 |
|---------|------|
| 写/更新 progress.yaml、spec 模板、报告模板、状态枚举 | `references/templates.md` |
| 入口分流（新建/追加/断点恢复/看板）、Preamble、decisions、Memory、--auto/--start 详细规则 | `references/commands.md` |
| Step 1 需求分析 | `references/stages/stage-1-requirement.md` |
| Step 2 技术设计（含自审 + 冲突预检 + 合并审核） | `references/stages/stage-2-design.md` |
| Step 3 编码实现（规范前置 + 互斥检查 + files_changed 回写） | `references/stages/stage-3-implement.md` |
| Step 4 代码验证（Lint/Test/QA+CR + 问题确认交互） | `references/stages/stage-4-verify.md` |
| Step 5 E2E 测试（A/B/C 三种驱动模式） | `references/stages/stage-5-e2e.md` |
| 新项目 E2E 环境一次性接入（安装 + config 模板） | `references/e2e-setup.md` |
| `/fe-workflow api-sync` | `references/commands/api-sync.md` |
| `/fe-workflow release` | `references/commands/release.md` |
| `/fe-workflow pr` | `references/commands/pr.md` |
