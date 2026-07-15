# Step 5 — E2E 端到端测试（e2e）

生成 Playwright E2E 测试，在真实浏览器中验证页面交互，保存关键步骤截图。full 模式执行，lite 模式跳过。

**两种调用方式**：

- **流水线内**（Step 5）：前置检查本功能 implement 为 done
- **独立调用**（`/fe-workflow e2e [doc-path] [--yunxiao <ID>]`，不依赖流水线）：跳过前置检查，直接按下方模式判定表确定用例来源（给了 doc-path → 模式 B；给了 --yunxiao → 模式 C；都没给 → 自动发现文档或兜底）；截图目录用 `tests/e2e/results/screenshots/{feat-name 或页面名}/` 一级结构；报告直接输出到对话（带 `--feat` 定位到流水线功能时才写 e2e-report 章节）

## 1. 环境检测

```bash
cd tests/e2e && npx playwright test --list 2>&1
```

失败（Playwright 未安装/Chromium 缺失）→ 流水线内标记 `skipped`，记录 decision，输出"E2E 环境未就绪，跳过"继续；用户单独跑本步时则按 `references/e2e-setup.md` 引导完成一次性接入（安装、config 模板、配置矩阵都在那里）。

> dev server 不需要手动检测：`playwright.config.ts` 已配置 `webServer` 时 Playwright 自动启动。

## 2. 确定测试依据（三模式自动判定）

| 优先级 | 条件 | 模式 | 用例来源 |
|--------|------|------|----------|
| ① | 命令带 `--yunxiao <目录ID\|用例ID>`，或 config.yaml 配置了 `e2e_testcase_repo` 且用户要求用例驱动 | **C 测试用例驱动** | 云效用例库 |
| ② | 命令传入 `[doc-path]` | **B 现有文档驱动** | 指定文档 |
| ③ | 本功能 spec 存在 | **A 需求+设计驱动** | spec（需求的操作流程 + 设计的路由/页面结构） |
| ④ | 自动发现到现有文档 | **B 现有文档驱动** | 见发现顺序 |
| ⑤ | 都没有 | 兜底 | `git diff --name-only master` + 源码 |

**模式 C：云效用例读取（Yunxiao MCP）**

前置：云效 MCP 已配置；用例库/目录 ID 从 `docs/pipeline/config.yaml` 的 `e2e_testcase_repo` / `e2e_testcase_directory` 读取（未配置且用户未提供 → 用 `list_test_repos` 按名字查询确认）。读取链路：

1. `get_current_organization_info` → `organizationId`
2. `list_test_repos({organizationId, name})` → 定位 `testRepoId`（默认页只返回前几个，按 name 过滤更稳）
3. `list_testcase_directories({organizationId, testRepoId})` → 目录树取 `directoryId`
4. `search_testcases({organizationId, testRepoId, directoryId, page, perPage})` — **`directoryId` 必填**
5. `get_testcase(...)` → `preCondition` + `testSteps.content[]{step, expected}`

逐条映射：`step` → Playwright action，`expected` → assert，`preCondition` → `beforeEach`；一条用例一个 `test()`。用例标题带分流前缀（`[✅P0]`/`[🧩P1]`/`[⬜P2]`）时直接据此分流。

**模式 B 自动发现顺序**（命中即用，多个则合并）：
1. `docs/**/*测试要点*.md`、`docs/**/*test*.md` — 已是用例表（操作/预期结果），最优来源
2. `docs/**/modules/{页面目录}/*.md`、`docs/**/{feat-name}/*.md` — 模块/功能文档
3. `docs/**/{feat-name}*.md`

**统一提取**（各模式一致，源代码始终作为补充依据）：页面路由（**以项目路由配置文件为准**，文件路径 ≠ URL）、用户操作流程、预期结果（toast/跳转/数据变化）、接口依赖（需等待的 API）。

> 开始生成前，**回显本次判定的模式与用例来源**，让覆盖范围对用户透明。

## 3. 用例分流（必做，尤其模式 B/C）

并非每条用例都能自动 E2E。先逐条打标，**只为「✅ 可 E2E」生成用例**，其余记入报告说明原因，**禁止把不可自动化的用例硬写成会误报的脆弱断言**：

| 标签 | 判定 | 处理 |
|------|------|------|
| ✅ 可 E2E | 页面加载/路由跳转/表单提交/列表搜索/可见 UI 断言 | 生成 `test()` |
| 🔒 需登录 | 访问受登录态保护的页面 | 有 token fixture 则生成；否则 skipped，标注"需测试 token" |
| 🧩 需 mock | JSBridge/原生能力/三方回调 | 不生成，记入报告 |
| ⬜ 不可 E2E | KeepAlive 缓存、IndexedDB、SSR 请求参数等白盒断言 | 不生成，建议改用单测 |

测试重点按需求类型：新页面（加载+主流程+关键交互截图）/ 功能扩展（新路径+原功能不受影响）/ 表单弹窗（开-填-提-关全流程）/ 列表搜索（加载/搜索/分页/空数据）。

## 4. 生成测试文件

位置 `tests/e2e/specs/{feat-name}.spec.ts`；截图目录 `tests/e2e/results/screenshots/{pipeline-name}/{feat-name}/`（`path.resolve(__dirname, '../results/screenshots/...')` 绝对路径拼接）。

**编写规则**：
- 选择器优先级：`getByRole` > `getByText` > `getByPlaceholder` > `getByTestId` > CSS 选择器（最后手段）；禁止脆弱 XPath
- 等待策略：`waitForLoadState('networkidle')` / `waitForResponse` / `expect(locator).toBeVisible()` / `waitForURL`；**禁止 `waitForTimeout`**
- 截图：每个用例关键步骤必截（加载后/操作前/结果态/异常态），命名 `{用例名}-{序号}-{描述}.png`，`fullPage: true`
- H5 注意：Vant Toast 出现即截图+断言（很快消失）；Popup 等 transition 完成再截图；下拉/上滑用 `page.touchscreen`；操作 input 前先滚动到可视区域
- MWP 接口 mock：用网关 URL（如 `**/h5/{apiKey}/1.0`）精确拦截，不打真实短信/账号

## 5. 执行与自动修复

```bash
cd tests/e2e && npx playwright test specs/{feat-name}.spec.ts 2>&1
```

失败用例逐个诊断（读取失败截图）：

| 错误信息 | 类型 | 处理 |
|---------|------|------|
| `Timeout waiting for locator` | 选择器/时序 | 修复测试代码 |
| 断言不等 / `waitForURL timeout` | 可能是功能 bug | 记入报告，不改源码 |
| `Element is not visible` | 元素遮挡 | 检查 z-index / v-if |
| `ERR_CONNECTION_REFUSED` | 服务未启动 | 提示启动 dev server |

测试代码问题修复后重跑，最多重试 3 轮（`--auto`/`--start` 下按 config.yaml `auto_fix_rounds`）；功能 Bug 记录到报告并附截图，等待人工确认。

## 6. 报告与收尾

写入 `e2e-report.md` 本功能章节（模板见 `templates.md`）。全部通过 → 本功能完成；有失败（修复轮次用尽）→ 暂停提示"E2E 发现 {N} 个失败用例，可能是页面交互 bug，请检查截图后继续"。

## Guardrails

- 生成前必须回显驱动模式与用例来源
- **必做用例分流**；需登录用例无 token 时记 skipped
- 每个用例必须包含截图，绝对路径拼接，目录按 `{pipeline-name}/{feat-name}` 隔离
- 失败优先修测试代码，不随意修改源代码；最多重试 3 轮不无限循环
- 模式 C：`search_testcases` 必须带 `directoryId`；优先按用例标题前缀分流
