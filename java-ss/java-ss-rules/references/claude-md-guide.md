# CLAUDE.md 生成指南

CLAUDE.md 是项目的核心规则文件，启动时始终加载。保持精简（<100 行），只放项目特有信息和索引。

通用的架构规则、设计原则、编码标准已拆到 `.claude/rules/architecture.md`，CLAUDE.md 中不再重复。

## 输出模板

CLAUDE.md 是纯入口文件，不持有任何事实内容或编码规则。只包含三部分：项目一句话、文档阅读顺序、规则文件索引。

```markdown
{服务一句话职责描述，从 overview.md 或 spring.application.name + 核心 Service 类推断}

## 文档阅读顺序

| 顺序 | 文档 | 什么时候看 |
|------|------|-----------|
| 1 | [docs/{service-name}/overview.md](docs/{service-name}/overview.md) | 初次进入：服务职责、模块结构、技术栈、上下游依赖 |
| 2 | [docs/{service-name}/business.md](docs/{service-name}/business.md) | 实现业务逻辑前：状态机、业务规则 |
| 3 | [docs/{service-name}/contracts.md](docs/{service-name}/contracts.md) | 改 MQ/RPC 前：事件契约全表、接口依赖 |
| 4 | [docs/{service-name}/flows.md](docs/{service-name}/flows.md) | 评估影响范围：执行流程、事件级联链路 |

{只列出 docs/ 下实际存在的文件}

## 规则文件（.claude/rules/）

### 始终加载

| 文件 | 内容 |
|------|------|
| `architecture.md` | DDD 分层约束、设计原则、编码标准、完成检查清单 |
| `package-map.md` | 关键包路径速查表 |

### 按需加载（globs 匹配时自动加载）

| 文件 | 内容 |
|------|------|
| `mq-conventions.md` | MQ 消费者/生产者开发模板、幂等约定 |
| `rpc-conventions.md` | RPC 接口暴露和调用模板、本项目 RPC 框架约定 |
| `build-and-test.md` | 构建编译测试命令 |
```

**关键原则**：
- Tech Stack 和 Modules 由 `docs/{service-name}/overview.md` 持有，CLAUDE.md 不重复
- RPC 框架约定（注解、URL 模式等）由 `rpc-conventions.md` 持有
- 架构规则和编码标准由 `architecture.md` 持有

## 增量更新规则

- CLAUDE.md 不持有事实内容（Tech Stack、Modules）和编码规则（Architecture、Design Rules）
- 已有的 CLAUDE.md 如果包含这些内容，迁移到对应文件后从 CLAUDE.md 中移除
- 禁止删除已有的自定义章节（如果不属于上述迁移范围）
