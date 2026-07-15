# E2E 环境接入（新项目一次性配置）

stage-5 环境检测失败、或项目首次接入 E2E 时，按本文完成一次性配置。日常执行规则见 `stages/stage-5-e2e.md`。

## 1. 目录约定

```
tests/e2e/
├── package.json            # 子工程独立管理 Playwright 依赖
├── playwright.config.ts
├── specs/                  # 测试文件 {feat-name}.spec.ts
├── results/                # 执行产物（截图/录像/trace）
└── report/                 # HTML/JSON 报告
```

## 2. 一次性安装

子工程用项目自身的包管理器（npm / pnpm / yarn 任一）：

```bash
cd tests/e2e
npm install                        # 安装 Playwright
npx playwright install chromium    # 安装浏览器内核
```

> ⚠️ **版本对齐坑**：Playwright 每个版本绑定特定浏览器 build。新装/升级 `@playwright/test` 后**必须重跑** `npx playwright install chromium`，否则报 `Executable doesn't exist at .../chromium_headless_shell-XXXX`。
> 多进程并发安装出现 `__dirlock` 锁错误 → `rm -rf ~/Library/Caches/ms-playwright/__dirlock` 后重装。

**验证**：`cd tests/e2e && npx playwright test --list` 能列出用例即就绪。

## 3. playwright.config.ts 通用模板

各项目结构一致，**只需改 4 处**（`baseURL` / `webServer.command` / `timeout` / 设备）：

```typescript
import { defineConfig, devices } from '@playwright/test'
import path from 'path'

const projectRoot = path.resolve(__dirname, '../../')

export default defineConfig({
    testDir: './specs',
    outputDir: path.join(projectRoot, 'tests/e2e/results'),
    reporter: [
        ['html', { outputFolder: path.join(projectRoot, 'tests/e2e/report'), open: 'never' }],
        ['json', { outputFile: path.join(projectRoot, 'tests/e2e/report/results.json') }],
        ['list'],
    ],
    use: {
        baseURL: 'http://localhost:<PORT>',   // ← 改：项目 dev 端口
        screenshot: 'off',                     // 手动截图由测试代码控制
        video: 'retain-on-failure',
        trace: 'on-first-retry',
    },
    projects: [
        { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },  // ← 改：H5 用移动设备，PC 用 Desktop Chrome
    ],
    webServer: {
        command: '<DEV_COMMAND>',              // ← 改：项目 dev 启动命令
        url: 'http://localhost:<PORT>',        // ← 改：同 baseURL
        reuseExistingServer: true,             // 已启动则复用，未启动则自动拉起
        timeout: <TIMEOUT>,                    // ← 改：SPA 60s，SSR 建议 120s
        cwd: projectRoot,
    },
})
```

## 4. 项目配置矩阵（参考值，以项目实际配置为准）

| 项目类型 | dev 命令来源 | 设备 | webServer timeout |
|---------|-------------|------|-------------------|
| Vue 3 + Vite（H5） | package.json 的 dev/start 脚本 | Pixel 5 | 60s |
| Nuxt 3（H5，SSR） | 同上 | Pixel 5 | **120s**（SSR 冷启慢，给足） |
| Vue 3 + Vite（PC 后台） | 同上 | Desktop Chrome | 60s |

端口以项目 `vite.config.ts` / `nuxt.config.ts` 为准。

## 5. 关键配置说明

| 配置项 | 推荐值 | 说明 |
|--------|--------|------|
| `screenshot` | `'off'` | 不自动截图，由测试代码 `page.screenshot()` 手动控制时机 |
| `video` | `'retain-on-failure'` | 仅失败保留录像 |
| `trace` | `'on-first-retry'` | 重试保留 trace，`npx playwright show-trace` 可回放 |
| `webServer.reuseExistingServer` | `true` | 本地已开 dev 则复用，未开自动拉起 |
| `webServer.cwd` | 项目根目录 | 确保 dev 命令在正确位置执行 |

## 6. 可选：Playwright MCP

```bash
claude mcp add playwright -s user -- npx @playwright/mcp@latest
```
