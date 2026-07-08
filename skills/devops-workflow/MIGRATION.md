# 迁移指南：php-workflow → dev-workflow

本文档记录从 `php/php-workflow/`（v2 版本制度）向 `devops-workflow/`（通用化版本）的一般化迁移。所有 PHP/Composer/PSR-4 细节已剥离，仅保留状态机、命令速查与 12 条不变量；运行时通过项目 `composer.json`（或等价 manifest 文件）+ `CLAUDE.md` 重新发现语言/测试/契约工具链。

## What was kept（保留项）

下列核心机制完全保留，仅替换占位符：

| 类别         | 保留内容                                                                                                                                                                                                              |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 状态机       | 子需求 5 阶段流程（1 需求讨论 → 2 分析与设计 → 3 设计审核 → 4 开发与逐任务审查 → 5 收尾验收）                                                                                                                         |
| 子需求级闭环 | 阶段4 逐任务闭环：复杂度判断 → plan 门 → 编码 → DoD → CR 扫描 → CR 人工门 → 改写 → 复验回写                                                                                                                           |
| 状态机 5 态  | 版本状态机 `DRAFT / IN_PROGRESS / READY / RELEASED / ARCHIVED`                                                                                                                                                        |
| 命令集合     | 4 个 `req` 子命令 + 8 个 `version` 子命令 + 5 个保留推进命令（next/approve/status/rework/summary）                                                                                                                    |
| Schema       | `metadata.md`、`version` 文件、目录结构 `docs/discuss/{service-name}/{父需求名}/.task/{子需求名}/`                                                                                                                              |
| 三道人工门   | 阶段3 设计审核 / 阶段4 plan 确认 / 阶段4 CR 裁决（均由 `/devops-workflow approve` 分发）                                                                                                                              |
| 12 不变量    | 子 agent 返回 ≠ 流程推进、CR 问题人工门、编码审查分两轮、进度即时回写、设计分两层、未决项不许悬空、设计/需求层缺陷走 rework、子需求默认单个、无活动指针、版本状态机 5 态、metadata.md 单源、agent prompt 静态分析约束 |

## What was removed（移除项）

下列 PHP/Composer 绑定项已全部移除，由占位符替代：

| 移除的原文                                        | 通用化替换                                           | 出现位置               |
| ------------------------------------------------- | ---------------------------------------------------- | ---------------------- |
| `phpunit`                                         | `{test_cmd}`                                         | 验收基线               |
| `php -l`                                          | `{lint_cmd}`                                         | 验收基线               |
| `vendor/bin/phpunit modules/{service-name}/tests` | `{test_cmd} {module_root_glob}/{service-name}/tests` | 验收基线               |
| `php-analyzer`                                    | `{discovery_cmd}`                                    | 模块分析、架构文档产出 |
| `composer.json`（作为模块清单来源）               | `manifest file`（通用概念）                          | 模块路径约定           |
| `composer.json` 的 `autoload.psr-4`               | 删除                                                 | 模块清单发现路径       |
| `Service/Events/Listeners` 跨模块机制             | `{contract_type}` 通道                               | 跨模块交互             |
| `docs/workflow/{service-name}/` 架构文档目录      | `docs/workflow/{service-name}/`                      | 架构上下文来源         |
| `phpstan` 默认 DoD                                | "静态分析" 通用占位                                  | 验收基线               |
| `docs/discuss/.workflow-active` 粘性指针          | 删除（未引用）                                       | 活动指针约定           |
| `modules/{service-name}` 模块根                   | `{module_root_glob}`                                 | 模块路径约定           |

## What was redirected（重定向项）

| 原引用                                   | 新引用                                    | 说明                                     |
| ---------------------------------------- | ----------------------------------------- | ---------------------------------------- |
| `/php-workflow {子命令}`                 | `/devops-workflow {子命令}`               | 所有命令路径重定向                       |
| `php-workflow`（作为 skill 名）          | `dev-workflow`（作为 skill 名）           | 仅在 `MIGRATION.md` 与原项目历史语境保留 |
| `composer.json` 模块清单发现             | `manifest file` + `CLAUDE.md` 运行时声明  | 从硬编码 PSR-4 推断改为运行时项目自声明  |
| `php-analyzer` 架构文档产出              | `{discovery_cmd}` 由项目 `CLAUDE.md` 指定 | 不再硬编码 PHP 分析器                    |
| `docs/workflow/{service-name}/` 架构文档 | `docs/workflow/{service-name}/`           | 命名从"工作流产物"改为"架构产物"         |
| `Service/Events/Listeners` 跨模块机制    | `{contract_type}` 通道（按语言而异）      | 不再限定具体实现名                       |

## Compatibility stance（兼容性立场）

- **`php/php-workflow/` 是只读历史参考**：原 skill 保留在原位置、保留原内容，**不会被修改、不会被删除、不会被别名指向 `dev-workflow`**。
- **不创建符号链接**：`/devops-workflow/` 与 `php/php-workflow/` 之间不存在任何 `symlink`、共享目录或共享状态文件。
- **不创建别名**：CLI 层面不会注册 `php-workflow → dev-workflow` 别名；两个 skill 独立存在。
- **状态文件互不相通**：`docs/discuss/`、`docs/version/` 目录结构与命名约定相同，但子需求 ID、版本号、metadata.md 内容不会跨 skill 共享。
- **不维护向后兼容层**：用户从 `php-workflow` 迁到 `dev-workflow` 时，不会自动迁移任何既有子需求/版本；如需保留历史，按"新 skill + 原项目目录"双轨运行。

## Migration path for existing users（迁移路径）

对于已经使用 `php/php-workflow/` 的项目（如有）：

1. **新需求/新项目**：直接使用 `/devops-workflow` 命令。新 skill 通过 `CLAUDE.md` 声明运行时工具链（`{test_cmd}` / `{lint_cmd}` / `{discovery_cmd}` / `{contract_type}` / `{module_root_glob}`）。
2. **存量进行中项目**：保留 `php/php-workflow/` 使用方式不变——`original php-workflow` 仍可正常调用，是合法的 legacy skill。
3. **混合运行**：同一仓库内允许"旧项目用 php-workflow、新模块用 dev-workflow"；两个 skill 通过不同的命令前缀区分（`/php-workflow` vs `/devops-workflow`）。
4. **回滚**：如新 skill 在某项目上不可用，回退到 `original php-workflow` 即可，无需修改项目目录结构。
5. **配置迁移**：原 `composer.json autoload psr-4` 不需要迁移——新 skill 不再读取 PSR-4 作为模块清单来源，改由 `CLAUDE.md` 显式声明。

## 校验

通用化迁移的强制验收点：

- `SKILL.md` 中**无**任何 `php` / `composer` / `psr-4` / `Service/Events/Listeners` 字面子串。
- `MIGRATION.md` 包含字面子串 `original php-workflow`（用于 grep 测试）。
- `SKILL.md` 列出全部 17 个启用命令（4 + 8 + 5）。
- 12 不变量完整保留；不变量 8 同时包含"跨模块交互一律通过 `{contract_type}` 通道"与"禁止直接访问他模块实现细节"两个半句。