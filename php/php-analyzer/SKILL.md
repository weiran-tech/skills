---
name: php-analyzer
description: 分析 PHP/Laravel 伪多模块项目的服务架构。当用户说 "php-analyzer"、"分析服务架构"、"分析PHP架构"、"PHP模块分析"、"分析模块"、"analyze php architecture" 时触发。也适用于：用户想了解 PHP 模块功能边界、整理事件/监听器契约、为 AI 工具准备上下文文档、分析业务执行流程影响范围、或更新已有的模块架构文档。支持按模块单独分析以节约成本。
---

# PHP Arch Analyzer

分析当前 PHP/Laravel 伪多模块项目代码，**按模块逐个分析**，每个模块生成四份文档。每份文档服务于不同的读者和场景：

| 文件 | 作用 | 参考指南 |
|------|------|---------|
| `docs/{service-name}/overview.md` | 模块名片：职责、目录结构、技术栈、依赖 | `references/overview-md.md` |
| `docs/{service-name}/business.md` | 业务规则：为什么这么处理 | `references/business-md.md` |
| `docs/{service-name}/contracts.md` | 对外契约：承诺了什么 | `references/contracts-md.md` |
| `docs/{service-name}/flows.md` | 执行链路：怎么流转 | `references/flows-md.md` |

另外生成一份跨模块关联文档：

| 文件 | 作用 |
|------|------|
| `docs/cross-module.md` | 模块间依赖关系、事件级联、共享模型引用 |

### 文档间职责边界（必须遵守）

每份文档只回答一个问题，禁止交叉：

- **overview.md** → 事实（是什么、有什么、依赖谁）
- **business.md** → 规则（为什么这么处理），禁止出现具体事件类名和执行流程步骤
- **contracts.md** → 契约（唯一契约源），禁止展开完整业务流程
- **flows.md** → 链路（怎么流转），禁止展开业务规则细节

文档间只做单向引用，不复制内容：
- business.md 提到事件时：写"相关事件见 contracts.md"
- flows.md 提到规则时：写"该规则见 business.md"
- contracts.md 提到用途时：一句话说明，不展开流程

## 执行模式

### 模式一：单模块分析（默认 / 节约成本）

用户指定某个模块名（如 `account`、`user`），只分析该模块，生成 `docs/{service-name}/` 下四份文档。

### 模式二：全量分析

用户明确要求"全量分析"或"分析所有模块"时，按模块逐个执行，每完成一个模块输出进度，最后生成 `docs/cross-module.md`。

### 模式三：跨模块关联分析

用户要求"跨模块分析"或"模块关联"时，基于已有的各模块文档，生成或更新 `docs/cross-module.md`。

## 第一步：识别模块清单

- 读取 `composer.json` 的 `autoload.psr-4` 获取模块命名空间映射
- 扫描 `modules/` 目录获取所有模块名
- 列出模块清单，让用户选择要分析的模块（除非用户已指定）

## 第二步：并行扫描目标模块

在生成任何文档之前，先建立对模块的全面认知。以下扫描并行执行：

**目录结构：**
- 扫描模块根目录 `modules/{service-name}/` 的目录层级（src、resources、configurations、tests）
- 识别模块内部分层：Action、Models、Events、Listeners、Jobs、Http、Classes、Commands、Hooks

**路由扫描：**
- 读取 `src/Http/Routes/` 下所有路由文件（api_v1.php、web.php、backend.php 等）
- 记录每条路由：HTTP 方法、URI、Controller/Request 类、中间件
- 区分路由类型：api（外部接口）、backend（管理后台）、web（前端页面）

**模型扫描：**
- 读取 `src/Models/` 下所有 Eloquent 模型
- 记录：表名、关联关系（hasMany/belongsTo/morphTo 等）、Scope、Accessor/Mutator
- 扫描 `Models/Dao/` 下的 DAO 类，记录封装的查询方法
- 扫描 `Models/Filters/` 下的过滤器
- 扫描 `Models/Resources/` 下的 API Resource 转换器
- 扫描 `Models/Policies/` 下的授权策略

**事件/监听器扫描：**
- 扫描 `src/Events/` 目录，记录所有事件类及其携带的数据
- 扫描 `src/Listeners/` 目录，记录每个监听器：监听的事件、执行的业务逻辑
- 检查 `ServiceProvider` 中的 `$listens` 属性或 `EventServiceProvider` 获取事件-监听器绑定
- **事件级联追踪**：对每个监听器，沿调用链（Listener → Action/Service → Model）向下追踪，检查是否有 `event()` 调用或 Job dispatch。记录该 Listener 处理过程中产生的所有下游事件/任务

**队列任务扫描：**
- 扫描 `src/Jobs/` 目录，记录每个 Job：队列名、延迟配置、执行的业务逻辑
- 追踪 Job 的 dispatch 来源（哪些 Action/Listener 触发了这个 Job）

**Action 层扫描：**
- 读取 `src/Action/` 下的 Action 类（业务逻辑层）
- 记录每个 Action 的公开方法、调用的 Model/Event/Job
- 识别核心业务操作入口

**命令行扫描：**
- 读取 `src/Commands/` 下的 Artisan 命令
- 记录命令签名、调度频率（如果有）、业务动作

**跨模块引用扫描：**
- 在当前模块代码中 grep 其他模块的命名空间引用（如 `use User\Models\Store`）
- 记录：引用方类 → 被引用模块 → 被引用类 → 引用场景

**HTTP 请求层扫描：**
- 读取 `src/Http/Request/` 下的请求处理类（按 Api/Backend/Web 分组）
- 识别请求验证规则、响应格式
- 扫描 `src/Http/Middlewares/` 下的中间件
- 扫描 `src/Http/Traits/` 下的复用 Trait

**Hooks 扫描：**
- 读取 `src/Hooks/` 下的 Hook 类（框架扩展点）
- 记录 Hook 注册的功能：菜单、权限、设置项等

## 第三步：增量更新原则

写文件前先检查是否已存在：

- **不存在**：直接生成完整内容
- **已存在**：读取现有内容，保留手动补充的部分（业务背景、决策原因等），只更新可从代码推断的表格和列表，追加新发现的内容

手动补充的内容比代码扫描结果更有价值，不要覆盖。

## 第四步：逐份生成文档

按以下顺序生成，每份文档读取对应的 reference 文件获取详细规则和模板：

1. **docs/{service-name}/overview.md** → 读取 `references/overview-md.md`
2. **docs/{service-name}/business.md** → 读取 `references/business-md.md`
3. **docs/{service-name}/contracts.md** → 读取 `references/contracts-md.md`
4. **docs/{service-name}/flows.md** → 读取 `references/flows-md.md`

如果用户只要求生成某一份文档，只读取对应的 reference 文件即可。

## 第五步：完成摘要

输出简短摘要：
- 扫描结果：路由数、模型数、事件数、监听器数、Job 数、Action 数、命令数
- 跨模块引用数量和方向
- 标注了"待确认"的字段（信息不足处）
- 保留了哪些已有内容（增量更新时）

## 第六步：跨模块关联（可选）

如果是全量分析或用户要求，生成 `docs/cross-module.md`：

```markdown
# 跨模块关联分析

## 模块依赖矩阵
| 模块 | 依赖的模块 | 被依赖的模块 |
|------|-----------|-------------|

## 事件级联链路
{从事件发布 → 监听 → 下游事件/Job 的完整级联}

## 共享模型引用
{哪些模块直接引用了其他模块的 Model}

## 跨模块 Action 调用
{哪些模块调用了其他模块的 Action}
```

## 注意事项

- 本项目是 Laravel 伪多模块结构，所有模块在同一个 Laravel 应用中运行，共享数据库
- 模块间可以直接 `use` 其他模块的类，这是跨模块耦合的主要形式
- `vendor` 目录是项目依赖包，不需要分析
- 每个模块的 `ServiceProvider` 是模块入口，注册路由、事件、命令等
- Action 层等同于 Java 项目中的 Service 层
