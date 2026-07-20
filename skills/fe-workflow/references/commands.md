# commands — 入口分流 / Preamble / 断点恢复 / decisions / --auto / --start

## 1. 初始化与入口分流

### 1.1 名称解析

运行 `git branch --show-current`：

- **branch-name（硬性）**：分支名去 `feature/` 前缀直接使用（`feature/3.5-wx` → `3.5-wx`），不自行起名
- **pipeline-name 优先级（硬性）**：① 用户显式指定 > ② 默认与 branch-name 相同（此时目录为 `docs/pipeline/{branch-name}/{branch-name}/`）。不要自行起 kebab-case 名称
- 在 master/main/develop 上且未指定名称 → 询问用户，并建议先创建功能分支（不自动执行）

### 1.2 入口分流

检查 `docs/pipeline/{branch-name}/{pipeline-name}/`：

**A. 目录不存在 → 新建流水线**：创建目录，初始化 progress.yaml（features 数组，首个功能 `id: 1`）。功能名：用户在需求描述中给出则使用，否则暂用纯编号（`spec-{n}.md`），requirement 完成后根据需求内容补 kebab-case 短名，重命名 spec 文件并同步 progress.yaml。

**B. 目录已存在 → 读取 progress.yaml，按意图分流**：
- 带**新的需求描述** → 新增功能：features 追加一项，`id` 取当前最大值 +1，新建 spec，从 requirement 开始
- 带 `--feat=<id|name>` → 定位该功能，进入断点恢复（第 4 节）
- 什么都没带 → 扫描分支目录 `docs/pipeline/{branch-name}/` 下所有流水线：只有一条时直接进功能看板（单功能未完成直接自动恢复）；多条时先列流水线清单让用户选
- 带 `--start` → 批量执行模式（第 6 节）

## 2. Preamble — 每步执行前的上下文注入

每个步骤执行前必须运行，结果结构化输出后再执行步骤：

1. **读取进度**：progress.yaml → 当前功能（id/name/spec/mode）、当前步骤、前序步骤状态、**同流水线其他功能概览**（名称 + 进度 + files_changed）、历史 decisions（当前功能全部 + 其他功能中与本功能相关的）
2. **加载 Memory**（若环境支持）：搜索 project 类型（本项目历史功能记录）与 feedback 类型（用户偏好），最多 3 条，避免上下文过载
3. **加载前序产出摘要**（只取片段，不全文读取大文件）：

| 当前步骤 | 加载内容 |
|---------|---------|
| design | spec「一、需求」的需求背景 + 功能描述 |
| implement | spec「二、设计」的改动文件清单 + 页面组件设计 |
| verify | spec 需求+设计摘要 + 本功能 files_changed |
| e2e | 需求的用户操作流程 + 设计的路由和页面结构 + files_changed |

4. **输出格式**：

```
=== Preamble: {step-name} ===
流水线：{pipeline-name}（分支 {branch}）
当前功能：#2 coupon-export（full 模式）
前序状态：requirement ✅ → design ✅（已审核）
同流水线其他功能：#1 coupon-list（已完成，改动 3 个文件）
关键决策：
- [#1/design] 选择方案B：新建组件
相关经验（Memory）：{如有}
前序产出要点：{...}
===
```

## 3. 步骤执行的统一封装

- 每步执行前：Preamble → progress.yaml 该功能该步 `status: in-progress`
- 每步执行后：`status: done` + updated 时间戳
- **`--until=<step>`**：目标步骤执行并完成人工审核后流水线**结束**（不再询问下一步）；`--until=design` 时审核通过即置 `design_approved: true`，提示"设计已就绪，可继续添加下一个需求，或晚上用 --start 批量执行"
- **每功能完成**（最后一步 done/skipped）：输出 files_changed 列表 + 建议 commit message（建议按功能单独 commit，方便回滚）；流水线内还有未完成功能 → 展示看板询问是否继续；全部完成 → 提示可用 `/fe-workflow pr`

## 4. 断点恢复（多功能看板）

progress.yaml 已存在且未带新需求描述时自动执行（不需要 `--from`）：

1. **读取进度**：确定每个功能每步 status
2. **验证产出文件**（防进度文件失真）：requirement/design → 对应 spec 文件存在，且 design 需额外包含「二、设计」章节（两步共用一个文件，仅文件存在不够）；verify/e2e → 汇总报告中存在本功能章节；不存在 → 该步改回 `pending`
3. **确定继续位置**：带 `--feat` → 定位该功能第一个 `pending` 且所有 depends 均为 done/skipped 的步骤；只有一个未完成功能 → 自动定位；多个 → 看板选择；用户显式 `--from` → 以用户指定为准（跳过自动检测）
4. **看板格式**：

```
流水线恢复：3.40-batch（分支 feature/3.40-batch）
#1 coupon-list    ✅✅✅✅✅  已完成（3 个文件，建议已 commit）
#2 coupon-export  ✅✅🔄⏳⏳  implement 待执行 ← 设计已审核
#3 coupon-stats   ✅🔄⏳⏳⏳  design 待执行
（步骤顺序：requirement / design / implement / verify / e2e）

继续哪个功能？（输入编号 / 功能名 / "新增" 添加新需求）
```

5. **加载历史决策**：展示所选功能的 decisions 记录，帮助恢复上下文

## 5. decisions 记录与 Memory 写入

**decisions 记录时机**（自动追加，必须带 feature 字段，格式见 `templates.md`）：
- 用户确认排除某个场景 / 选择了特定方案 / 后端接口待确认的 mock 决策 / 用户跳过某步骤的原因 / 跨功能文件冲突的执行顺序约定

**Memory 写入**（若环境支持）：某功能全部步骤完成（最后一步 done/skipped）时写入——project 类型（功能名、流水线/分支、涉及模块、完成日期）+ feedback 类型（该功能开发中用户的关键反馈和偏好）。按功能粒度写一次，中途中断不写；不写临时性信息（代码细节、文件路径）。

## 6. `--start` 批量执行模式

"白天出设计、晚上跑实现"的昼夜工作流：

1. **筛选**：读取分支目录下各流水线的 progress.yaml（多条时先让用户选择，或显式指定 pipeline-name），筛选满足以下条件的功能：`design_approved: true`（lite 模式下 requirement 为 done）、implement 为 `pending`、不含 `blocked`。结果为空 → 提示"没有已审核待实现的功能"并结束；开跑前输出执行清单（功能列表 + 顺序）
2. **严格串行（硬性）**：一个功能完整跑完 implement → verify → e2e，再开始下一个，**禁止交叉执行**（否则 verify 会把多个功能的改动混在一起分析）。执行顺序：decisions 中有跨功能顺序约定的按约定，否则按功能 id 升序。门控规则沿用 `--auto`；**编码规范 skill 调用规则不变**——每个功能的 implement 前必须实际调用 Skill tool
3. **失败不阻塞整晚**：某功能 implement 失败或 verify 有无法自动修复的阻塞问题 → 标记 `blocked`（原因记入 decisions），**继续下一个功能**，不中断整批
4. **产出 start-report.md**（模板见 `templates.md`）：执行概览 + 逐功能 commit 建议（files_changed 分组 + 建议 commit message），是早上人工按功能逐个 commit 的依据

## 7. `--auto` 全自动模式

- 不暂停、不等待确认，所有步骤连续执行；作用于**单个功能**（批量执行多个功能用 `--start`）
- **⚠️ 同样必须通过 Skill tool 加载项目编码规范 skill，不可跳过**
- 默认走 full 模式，除非用户显式 `--mode=lite`
- 质量门控自动决策：verify 阶段 lint error 自动 `--fix`、测试失败自动修复（轮数按 config.yaml 的 `auto_fix_rounds`，默认 2）；e2e 失败自动修复同轮数，仍失败标 skipped 继续；设计自审问题自动修订，不暂停
- 仍然生成 spec 等产出文档、仍然更新 progress.yaml（保证可追溯与断点恢复）
- 前置检查失败不直接报错，提示并建议补充执行
- 结束后输出简要总结：files_changed 列表 + 建议 commit message
- 触发：`/fe-workflow --auto <需求描述>`，或用户说"全自动"、"自动跑"、"不用确认"

## 8. 独立子命令路由

| 命令 | 转到 |
|------|------|
| `/fe-workflow api-sync [模块]` | `references/commands/api-sync.md` |
| `/fe-workflow release [--feat=<id\|name>]` | `references/commands/release.md` |
| `/fe-workflow pr` | `references/commands/pr.md` |
| `/fe-workflow verify` | `references/stages/stage-4-verify.md`（按其「独立调用」分支执行） |
| `/fe-workflow e2e [doc-path] [--yunxiao <ID>]` | `references/stages/stage-5-e2e.md`（按其「独立调用」分支执行） |

**独立步骤入口规则**：`verify` / `e2e` 独立命令**不走 1.2 入口分流**，不要求流水线目录存在；直接读对应 stage 文件按"独立调用"分支执行。若当前分支恰好有流水线且能定位到对应功能（用户带了 `--feat`），则关联该功能——结果写入汇总报告对应章节；否则结果直接输出到对话，不创建流水线目录。
