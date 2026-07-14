# config：初始化/合并流程配置

> 处理 `/devops-workflow config` 时读本文件。

初始化或合并 `.workflow-config` 配置文件。**直接执行，无需人工确认**——合并完成后输出变更摘要。

## 完整配置模板

所有已知配置项及默认值：

```
# 流程推进
auto_advance=false              # 阶段/任务完成后自动推进

# 复杂度与 CR
simple_task_skip_cr=false       # 简单任务跳过 CR 门
auto_cr_minor=false             # CR MINOR 问题自动 ACCEPTED

# Plan
auto_plan_check=false           # critic agent 自动校验 plan 齐全性

# 验收
auto_accept_pass=false          # 验收零问题自动 COMPLETED
auto_accept_fix=false           # 验收失败自动修复+重跑验收
auto_accept_fix_max=2           # 自动修复最大轮次
```

## `/devops-workflow config`

1. 读取 `{讨论根目录}.workflow-config`
2. **不存在** → 用完整配置模板创建文件（默认值均为 false / 2），输出「已创建 .workflow-config，全部为默认值」
3. **已存在** → 合并逻辑：
   - 解析文件中每行的 `key=value`（忽略注释行和空行），记录用户已设置的值
   - 以完整配置模板为基准，逐项合并：**已有的 key 保留用户设置的 value，缺失的 key 补入默认值**
   - **整体回写**文件（按模板的分组和顺序重新生成，包含分组注释）
4. **直接输出变更摘要**（不询问是否补全）：
   - 无缺失项 → 「.workflow-config 已是最新，无需更新」
   - 有缺失项 → 列出新增了哪些配置项及其默认值

**输出格式**（有变更时）：
```
.workflow-config 已更新，新增 3 项配置（默认值）：

  + auto_accept_pass    = false   验收零问题自动 COMPLETED
  + auto_accept_fix     = false   验收失败自动修复+重跑验收
  + auto_accept_fix_max = 2       自动修复最大轮次

已保留的用户配置：
  auto_advance        = true
  simple_task_skip_cr = true
  auto_cr_minor       = true
  auto_plan_check     = true
```

> 用户可手动编辑 `.workflow-config` 调整值，`/devops-workflow config` 只补缺不改已有。新增配置项（如版本升级引入）会在下次执行时自动合并。

> 各配置项的行为协议详见 `automation.md`。
