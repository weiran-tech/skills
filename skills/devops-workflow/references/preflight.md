# Preflight — 流程启动前置检查

执行 `/devops-workflow start` 时，按顺序逐项检查。任何 `blocking: true` 的检查项未通过，立即终止并输出错误提示和修复指引，不创建需求。其他子命令（`next`/`approve`/`status` 等）不执行 preflight。

## 检查清单

### 1. rules-dir — 项目规则目录

| 字段 | 值 |
|------|------|
| id | `rules-dir` |
| check | `.claude/rules/` 目录存在且包含至少一个 `.md` 文件 |
| blocking | true |
| error | 项目缺少 `.claude/rules/` 规则目录，workflow 无法确定测试命令和编码规范 |
| fix | 先执行 `arch-rules` skill 生成项目规则，再启动 workflow |

### 2. omc-active — OMC 插件已加载

| 字段 | 值 |
|------|------|
| id | `omc-active` |
| check | 当前会话的可用 agent types 中包含 `oh-my-claudecode:executor`（通过 system-reminder 中的 "Available agent types" 列表判断） |
| blocking | true |
| error | oh-my-claudecode 插件未加载，workflow 依赖的 agent（executor、architect、code-reviewer、verifier）不可用 |
| fix | 确认 oh-my-claudecode 插件已安装并启用（执行 `/oh-my-claudecode:omc-setup` 或检查 `.claude/plugins/` 配置） |

### 3. arch-docs — 架构文档存在

| 字段 | 值 |
|------|------|
| id | `arch-docs` |
| check | `docs/` 目录下存在至少一个模块的 `overview.md`（由 `arch-analyzer` 产出） |
| blocking | false |
| error | 未找到架构文档，阶段 2 分析时 agent 缺少架构上下文，设计质量可能下降 |
| fix | 建议先执行 `arch-analyzer` skill 生成架构文档；如确认不需要可继续 |

## 执行协议

1. **逐项顺序检查**：按编号 1→2→3… 依次执行
2. **blocking 项失败即终止**：输出该项的 `error` + `fix`，不继续后续检查，不执行命令
3. **non-blocking 项失败输出警告**：输出 `⚠ {error}`，继续执行
4. **全部通过后**：输出一行确认（如 `✓ preflight passed`），继续执行命令的正常逻辑
5. **仅 `start` 触发**：只有 `/devops-workflow start` 执行 preflight，其他子命令直接执行

## 扩展

新增检查项只需在"检查清单"中追加条目，保持同一表格结构（id / check / blocking / error / fix）。SKILL.md 无需修改。
