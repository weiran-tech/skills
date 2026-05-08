---
name: arch-rules
description: 为 Java 微服务项目生成标准化的 Claude Code 规则文件（CLAUDE.md + .claude/rules/）。当用户说 "arch-rules"、"生成规则文件"、"初始化 claude rules"、"init rules"、"生成开发规范" 时触发。适用于：新项目初始化开发规范、统一团队 Claude Code 使用标准、为跨服务 Agent Teams 协作准备仓库级规则。
---

# Arch Rules

为当前 Java 微服务项目生成标准化的 Claude Code 规则文件。

**定位**：只生成开发规范和操作指南，不分析业务逻辑和执行流程（业务分析由 arch-analyzer 负责）。

## 产出物

| 文件 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `CLAUDE.md` | 项目级 | 模板 + 扫描 | 纯入口导航（一句话职责 + 文档阅读顺序 + 规则索引），不持有事实内容或编码规则 |
| `.claude/rules/architecture.md` | 通用规则 | 模板直出 | DDD 分层约束 + 设计原则 + 编码标准 + 完成检查清单 |
| `.claude/rules/build-and-test.md` | 通用规则 | 模板直出 | Maven 构建测试命令 |
| `.claude/rules/package-map.md` | 项目特有 | 代码扫描 | 包路径速查表（无 globs，无条件加载） |
| `.claude/rules/mq-conventions.md` | 混合 | 模板 + 扫描 | MQ 开发模板 + 幂等约定 + 项目特有 tag/常量（globs 从扫描结果动态生成） |
| `.claude/rules/rpc-conventions.md` | 混合 | 模板 + 扫描 | 本项目 RPC 框架约定 + RPC 开发模板（globs 固定：api/rpc/acl） |
| `.claude/rules/cross-service-guide.md` | 混合 | 模板 + 扫描 | 跨服务改动清单 + 引用，不重复 MQ/RPC 正文（globs 从扫描结果动态生成） |

### 信息归属原则

每个文件只回答一个问题，零重复，文档间只做单向引用：

```
CLAUDE.md        → 纯入口（一句话 + 导航）
overview.md      → 事实（服务是什么、模块、技术栈、依赖）  ← arch-analyzer 生成
business.md      → 规则（为什么这么处理）                  ← arch-analyzer 生成
contracts.md     → 契约（承诺了什么）                      ← arch-analyzer 生成
flows.md         → 链路（怎么流转）                        ← arch-analyzer 生成
architecture.md  → 通用编码规则（DDD 约束、设计原则）
package-map.md   → 速查（包路径在哪）
mq-conventions   → MQ 开发模板（怎么写消费者/生产者）
rpc-conventions  → RPC 开发模板 + 本项目 RPC 框架约定
cross-service    → 跨服务清单（做什么 → 引用去哪看）
build-and-test   → 构建命令
```

## 执行流程

### 第一步：扫描项目基础信息

并行执行以下扫描，建立项目认知：

**项目结构：**
- 读取根 `pom.xml`，获取 `<modules>` 列表、`<artifactId>`、`<groupId>`
- 读取 `application.yml` / `bootstrap.yml`，获取 `spring.application.name`
- 确定基础包名（从 groupId + artifactId 推断，或扫描 src 下的实际包结构）

**模块职责识别：**
- 识别各模块角色：api / adapter / application / domain / infrastructure / common-*
- 识别独立子域模块（有自己 domain + infrastructure 的模块）

**MQ 信息扫描：**
- 搜索 `@RocketMQMessageListener`，提取：消费者类所在包路径、consumerGroup 命名模式
- 搜索 MQ 常量类（包含 `TOPIC_` 或 `TAG_` 的 interface/class），记录类名和位置
- 搜索 `syncSend` / `asyncSend` / `syncSendDeliverTimeMills`，提取事件发布入口类
- 统计每个 tag 的消费者数量，识别高扇出 tag（5+ 消费者）

**RPC 信息扫描：**
- 扫描 api 模块中的 `*RpcService` 接口，确定接口定义位置
- 搜索 RPC 实现类的注解模式（`@Tesla` / `@DubboService` / `@Service` 等）
- 搜索 `*RpcConfig` 或 `@FeignClient`，确定外部 RPC 调用模式
- 搜索 ACL Client 类，确定外部调用的封装模式

**Controller 扫描：**
- 搜索 `@RestController`，确定 Controller 注解模式和 URL 约定

**docs 目录检查：**
- 检查 `docs/` 目录是否存在以及包含哪些文件

### 第二步：生成通用规则文件（模板直出）

读取 `templates/` 目录下的模板，直接写入目标项目：

1. **`.claude/rules/architecture.md`** ← 读取 `templates/architecture.md`，直接复制
2. **`.claude/rules/build-and-test.md`** ← 读取 `templates/build-and-test.md`，直接复制

这两个文件是全局统一标准，所有项目完全一致，不做任何定制。

### 第三步：生成项目特有规则文件（模板 + 扫描填充）

读取 `references/` 目录下的生成指南，结合第一步的扫描结果生成：

1. **`.claude/rules/package-map.md`** ← 读取 `references/package-map-guide.md`
2. **`.claude/rules/mq-conventions.md`** ← 读取 `references/mq-conventions-guide.md`
3. **`.claude/rules/rpc-conventions.md`** ← 读取 `references/rpc-conventions-guide.md`
4. **`.claude/rules/cross-service-guide.md`** ← 读取 `references/cross-service-guide.md`

### 第三步补充：globs 动态生成

mq-conventions.md 和 cross-service-guide.md 的 frontmatter globs 必须从第一步扫描结果中提取实际路径，不能写死。例如：
- 消费者在 `adapter/event/listener/` → globs 写 `**/adapter/event/listener/**`
- 消费者在 `adapter/consumer/` → globs 写 `**/adapter/consumer/**`

architecture.md 和 package-map.md 不设 globs（无条件加载）。

### 第四步：生成 / 更新 CLAUDE.md

读取 `references/claude-md-guide.md`，结合扫描结果生成或更新项目根目录的 CLAUDE.md。

CLAUDE.md 是纯入口导航文件，不持有任何事实内容（Tech Stack、Modules 由 overview.md 持有）或编码规则（由 architecture.md 持有）或 RPC 约定（由 rpc-conventions.md 持有）。

**增量更新原则**：
- CLAUDE.md 不存在 → 完整生成
- CLAUDE.md 已存在且包含 Tech Stack / Modules / Architecture 等内容 → 迁移到对应文件后从 CLAUDE.md 中移除，替换为纯导航格式
- 已有的 rules 文件 → 保留手动补充的内容，只更新可从代码推断的部分

### 第五步：完成摘要

输出简短摘要：
- 项目名称、基础包名、模块数量
- 生成 / 更新了哪些文件
- 识别到的 MQ 常量类、消费者数量、高扇出 tag
- 识别到的 RPC 框架类型和接口数量
- 标注"待确认"的信息（扫描无法确定的部分）
