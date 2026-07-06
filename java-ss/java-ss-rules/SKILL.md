---
name: java-ss-rules
description: 为 Java 独立服务项目生成标准化的 Claude Code 规则文件（CLAUDE.md + .claude/rules/）。 dd
---

# Java Standalone Service Rules

为当前 Java 独立服务项目生成标准化的 Claude Code 规则文件。

**定位**：只生成开发规范和操作指南，不分析业务逻辑和执行流程（业务分析由 java-ss-analyzer 负责）。 d

## 产出物

| 文件 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `CLAUDE.md` | 项目级 | 模板 + 扫描 | 纯入口导航（一句话职责 + 文档阅读顺序 + 规则索引），不持有事实内容或编码规则 |
| `.claude/rules/architecture.md` | 通用规则 | 模板直出 | DDD 分层约束 + 设计原则 + 编码标准 + Mapper XML 安全规范 + 完成检查清单 |
| `.claude/rules/unit-test-conventions.md` | 通用规则 | 模板直出 | 单元测试规范 + Maven 构建编译测试命令 |
| `.claude/rules/package-map.md` | 项目特有 | docs 或扫描 | 包路径速查表（无 globs，无条件加载） |
| `.claude/rules/mq-conventions.md` | 混合 | 模板 + docs/workflow/扫描 | MQ 开发模板 + 幂等约定 + 项目特有 tag/常量（globs 动态生成） |
| `.claude/rules/rpc-conventions.md` | 混合 | 模板 + docs/workflow/扫描 | 本项目 RPC 框架约定 + RPC 开发模板（globs 固定：api/rpc/acl） |

### 信息归属原则

每个文件只回答一个问题，零重复，文档间只做单向引用：

```
CLAUDE.md              → 纯入口（一句话 + 导航）
overview.md            → 事实（服务是什么、模块、技术栈、依赖）  ← arch-analyzer 生成
business.md            → 规则（为什么这么处理）                  ← arch-analyzer 生成
contracts.md           → 契约（承诺了什么）                      ← arch-analyzer 生成
flows.md               → 链路（怎么流转）                        ← arch-analyzer 生成
architecture.md        → 通用编码规则（DDD 约束、设计原则、Mapper XML 安全规范）
unit-test-conventions  → 单元测试规范 + 构建编译命令
package-map.md         → 速查（包路径在哪）
mq-conventions         → MQ 开发模板（怎么写消费者/生产者）
rpc-conventions        → RPC 开发模板 + 本项目 RPC 框架约定
```

## 执行流程

### 第一步：获取项目信息

优先从 `docs/workflow/` 目录获取，回退到代码扫描。

**模式 A：docs 存在（推荐）**

检查 `docs/workflow/` 目录是否包含 `overview.md`、`contracts.md`、`flows.md`。如果存在，直接读取：

- `docs/workflow/{service-name}/overview.md` → 项目名称、基础包名、模块列表、技术栈、上下游依赖
- `docs/workflow/{service-name}/contracts.md` → MQ 事件契约（topic/tag/consumerGroup）、RPC 接口列表、高扇出 tag
- `docs/workflow/{service-name}/flows.md` → 消费者包路径、事件发布入口类

仅补充读取 `pom.xml` 获取 `<modules>` 列表（用于 package-map 生成）。

**模式 B：docs 不存在（回退）**

并行执行代码扫描，建立项目认知：

- **项目结构**：读取根 `pom.xml` 获取 modules/artifactId/groupId；读取 `application.yml` 获取 spring.application.name；确定基础包名
- **模块职责**：识别 api/adapter/application/domain/infrastructure/common-* 角色；识别独立子域模块
- **MQ 扫描**：grep `@RocketMQMessageListener` 提取消费者包路径和 consumerGroup；grep MQ 常量类（TOPIC_/TAG_）；grep `syncSend`/`asyncSend` 提取发布入口；统计高扇出 tag（5+ 消费者）
- **RPC 扫描**：扫描 `*RpcService` 接口；grep RPC 实现注解（@Tesla/@DubboService）；grep `*RpcConfig`/@FeignClient；扫描 ACL Client
- **Controller 扫描**：grep `@RestController` 确定注解模式和 URL 约定

### 第二步：生成通用规则文件（模板直出）

读取 `templates/` 目录下的模板，直接写入目标项目：

1. **`.claude/rules/architecture.md`** ← 读取 `templates/architecture.md`，直接复制
2. **`.claude/rules/unit-test-conventions.md`** ← 读取 `templates/unit-test-conventions.md`，直接复制

这两个文件是全局统一标准，所有项目完全一致，不做任何定制。

### 第三步：生成项目特有规则文件（模板 + 扫描填充）

读取 `references/` 目录下的生成指南，结合第一步获取的项目信息生成：

1. **`.claude/rules/package-map.md`** ← 读取 `references/package-map-guide.md`
2. **`.claude/rules/mq-conventions.md`** ← 读取 `references/mq-conventions-guide.md`
3. **`.claude/rules/rpc-conventions.md`** ← 读取 `references/rpc-conventions-guide.md`

### 第三步补充：globs 动态生成

mq-conventions.md 的 frontmatter globs 必须从第一步获取的项目信息中提取实际路径，不能写死。例如：
- 消费者在 `adapter/event/listener/` → globs 写 `**/adapter/event/listener/**`
- 消费者在 `adapter/consumer/` → globs 写 `**/adapter/consumer/**`

architecture.md 和 package-map.md 不设 globs（无条件加载）。

### 第四步：生成 / 更新 CLAUDE.md

读取 `references/claude-md-guide.md`，结合第一步获取的项目信息生成或更新项目根目录的 CLAUDE.md。

CLAUDE.md 是纯入口导航文件，不持有任何事实内容（Tech Stack、Modules 由 overview.md 持有）或编码规则（由 architecture.md 持有）或 RPC 约定（由 rpc-conventions.md 持有）。

**增量更新原则**：
- CLAUDE.md 不存在 → 完整生成
- CLAUDE.md 已存在且包含 Tech Stack / Modules / Architecture 等内容 → 迁移到对应文件后从 CLAUDE.md 中移除，替换为纯导航格式
- 已有的 rules 文件 → 保留手动补充的内容，只更新可从代码推断的部分

### 第五步：完成摘要

输出简短摘要：
- 信息来源：docs 模式 / 代码扫描模式
- 项目名称、基础包名、模块数量
- 生成 / 更新了哪些文件
- 识别到的 MQ 常量类、消费者数量、高扇出 tag
- 识别到的 RPC 框架类型和接口数量
- 标注"待确认"的信息（无法确定的部分）
