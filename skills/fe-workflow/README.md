# fe-workflow — 前端功能开发流水线

一条命令走完前端功能开发全流程，每一步产出可追溯的文档，全程零 git 操作——代码提交始终由你掌控。

```
需求描述 ──▶ ① 需求分析 ──▶ ② 技术设计(含自审) ──▶ ③ 编码 ──▶ ④ 验证 ──▶ ⑤ E2E ──▶ 完成
              写 spec        追加设计+自动审查      规范强制    Lint/Test    真实浏览器    输出 files_changed
              「一、需求」    ★人工审核(唯一必停)    前置加载    QA+CR       执行+截图     + 建议 commit
                                                              ★有问题才停
```

两道门：**设计审核**（每个功能一次，需求+设计连续生成后合并审核）、**验证问题裁决**（零问题自动通过，不打断节奏）。

## 它解决什么问题

| 痛点 | fe-workflow 的答案 |
|------|-------------------|
| 需求口头传达，做完对不上 | 每个功能一份 spec（需求+设计合一），先审后写码 |
| AI 写码不守项目规范 | 编码前**强制**加载项目编码规范 skill（阻断式，全自动模式也不豁免） |
| 自己写的代码自己审，走过场 | 验证内置 CR：独立子代理（全新上下文、只读）出问题清单，编码与审查隔离 |
| 一个分支好几个功能，改动混在一起 | 按功能记录 files_changed，验证/E2E/commit 都按功能隔离 |
| 白天开会没时间盯执行 | 昼夜工作流：白天只出设计并审核，晚上批量自动执行，早上看报告逐功能 commit |
| 会话中断/隔天继续，上下文丢失 | progress.yaml 状态权威源 + 多功能看板，随时断点恢复 |

## 整体流程详解

### 步骤与产物

| 步骤 | 做什么 | 产物 | 停不停 |
|------|--------|------|--------|
| ① requirement | 文字/截图/文档 → 结构化需求；功能扩展类强制影响面分析（grep 全部引用） | spec「一、需求」 | 不停，直接进 ② |
| ② design | 组件/路由/Service/权限设计 + 5 维度自审自动修订 + 跨功能文件冲突预检 | spec「二、设计」+ 自审记录 | ★ 停：需求+设计合并审核一次 |
| ③ implement | 强制加载项目编码规范 skill 后编码；接口未就绪走 mock 并标注 | 源代码 + files_changed 回写 | 停：确认后进 ④ |
| ④ verify | Lint（白名单安全修复）→ 核心函数单测 → QA+CR（独立子代理，A/B/C 三级问题清单） | verify-report 本功能章节 | ★ 有 C 类阻塞项才停 |
| ⑤ e2e | 三种驱动（spec / 现有文档 / 云效用例）生成 Playwright 测试，真实浏览器执行+截图 | e2e-report 章节 + 截图 | 失败修 3 轮仍败才停 |

**full 模式** 5 步全跑（新功能）；**lite 模式** ①③④ 三步（小改动/Bug 修复），按功能独立选择。

### 产物归档（按分支组织）

```
docs/pipeline/{分支名}/{流水线名}/
├── progress.yaml            # 状态权威源：每功能每步的进度、决策记录、files_changed
├── spec-1-coupon-list.md    # 每个功能一份需求+设计文档
├── spec-2-coupon-export.md
├── verify-report.md         # 汇总报告，按功能分章节
├── e2e-report.md
└── start-report.md          # 批量执行总结
```

一个分支可以有多条流水线，一条流水线装多个功能——需求追加进来自动编号，互不干扰。

### 典型一天（昼夜工作流）

```
白天  /fe-workflow --until=design 优惠券列表页...     → 审核设计 → 通过
      /fe-workflow --until=design 优惠券导出功能...   → 审核设计 → 通过
      （冲突预检自动提示：两功能都改 CouponList.vue，#1 先做）

晚上  /fe-workflow --start
      → 按顺序串行执行 #1、#2 的 编码→验证→E2E，失败的标 blocked 不堵后面

早上  看 start-report.md → 按报告的 files_changed 分组逐功能 commit → /fe-workflow pr
```

## 命令速查

```
/fe-workflow <需求描述>                    # 新功能进流水线（追加需求自动编号）
/fe-workflow --until=design <需求描述>     # 只出需求+设计（白天用）
/fe-workflow --start                       # 批量执行已审核功能（晚上用）
/fe-workflow --auto <需求描述>             # 单功能全自动，不暂停
/fe-workflow --mode=lite <描述>            # 小改动 3 步精简流程
/fe-workflow                               # 看板 / 断点恢复
/fe-workflow --feat=2 --from=verify        # 定位某功能重跑某步

# 独立入口（不依赖流水线，存量代码/页面直接用）
/fe-workflow verify                        # 验证当前分支改动（git diff 兜底）
/fe-workflow e2e [doc-path] [--yunxiao <ID>]  # 按文档/云效用例直接跑 E2E

# 子命令
/fe-workflow api-sync                      # 真实接口就绪后替换 mock
/fe-workflow release                       # 发布后增量更新项目功能文档
/fe-workflow pr                            # 提交前汇总 + 按功能 commit 引导 + 建 PR
```

## 前置要求

| 项 | 说明 |
|----|------|
| 编码规范 skill（必需） | 项目对应的编码规范 skill，在项目 CLAUDE.md / `docs/pipeline/config.yaml` 登记（后台管理项目可直接用 `fe-backend-page` + `fe-kr36-ui-guide`） |
| Playwright（可选） | E2E 用；新项目接入见 `references/e2e-setup.md`（安装 + config 模板） |
| Apifox MCP（可选） | 接口定义来源；未配置自动走 mock 流程 |
| 云效 MCP（可选） | E2E 用例驱动模式；用例库 ID 配在 `docs/pipeline/config.yaml` |

## 目录结构

```
fe-workflow/
├── SKILL.md                     # 总控路由 + 硬性规则（Guardrails）
└── references/                  # 按需加载，不占常驻上下文
    ├── templates.md             # progress.yaml / spec / 报告模板
    ├── commands.md              # 入口分流、Preamble、断点恢复、--auto/--start 规则
    ├── e2e-setup.md             # 新项目 E2E 一次性接入
    ├── stages/stage-1~5-*.md    # 各步骤执行细节
    └── commands/                # api-sync / release / pr 子命令
```
