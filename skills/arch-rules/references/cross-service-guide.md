# cross-service-guide.md 生成指南

cross-service-guide.md 是 Teammate agent 进入本仓库时的操作手册。包含改动前必读、常见改动的操作步骤、完成后的汇报格式。

## frontmatter

```yaml
---
description: 跨服务改动指南，Teammate agent 进入本仓库前必读
globs:
  - "**/event/listener/**"
  - "**/acl/**"
  - "**/api/**"
---
```

globs 限定在跨服务交互的代码路径。只有操作 MQ 消费者、ACL 调用、RPC 接口定义时才加载，避免日常单服务开发时浪费 token。文件中引用的 docs/ 文档不会自动加载，只是文字指引。

## 文档结构

### 第一部分：改动前必读

列出 docs/ 目录下实际存在的文件，说明什么时候需要看。只列存在的文件：

| 文档 | 什么时候看 |
|------|-----------|
| `docs/contracts.md` | 新增/修改 MQ 事件或 RPC 接口前（避免 tag 冲突、消息体不兼容） |
| `docs/flows.md` | 评估改动的下游影响范围时 |
| `docs/business.md` | 实现业务逻辑前（理解状态机和业务规则） |
| `docs/overview.md` | 初次进入本仓库时 |

如果 docs/ 目录不存在，此部分改为提醒阅读 CLAUDE.md 和 .claude/rules/ 下的规则文件。

### 第二部分：改动类型清单（清单 + 引用，不重复正文）

用表格列出四种改动类型，每种只写简要步骤摘要，详细规范引用对应的 rules 文件：

| 改动类型 | 操作步骤摘要 | 详细规范 |
|---------|------------|---------|
| 新增 MQ 消费者 | 常量注册 → 创建 Consumer → 委托业务层 → 幂等 → 编译 | 见 `mq-conventions.md` |
| 新增 MQ 事件发布 | Tag 常量注册 → 发布逻辑 → 更新 contracts.md → 编译 | 见 `mq-conventions.md` |
| 暴露新 RPC 接口 | api 模块定义 → application 模块实现 → 编译 | 见 `rpc-conventions.md` |
| 对接外部 RPC | pom 加依赖 → RpcConfig → Client 封装 → 编译 | 见 `rpc-conventions.md` |

末尾附上项目的编译命令（从扫描结果填充 adapter 模块名）。

**禁止展开 MQ/RPC 的具体操作细节**，那些内容已经在对应的 conventions 文件中维护。

### 第三部分：完成后的汇报格式（通用，固定输出）

以下格式所有项目完全一致：

```
## 改动摘要
- 服务: {service-name}
- 改动类型: [新增消费者 / 新增事件发布 / 新增 RPC / ...]

## MQ 契约（如有）
- Topic: xxx
- Tag: xxx
- ConsumerGroup: xxx
- 消息体字段: { field1: Type, field2: Type }

## RPC 契约（如有）
- 接口: XxxRpcService.methodName
- 入参: XxxReqDTO { field1: Type }
- 出参: XxxRespDTO { field1: Type }

## 编译结果
- mvn compile: PASS / FAIL
- mvn test: PASS / FAIL（如有失败列出失败用例）

## 影响范围
- 新增文件: [列表]
- 修改文件: [列表]
```

这个格式是跨服务开发流程中 Lead 做汇总校验的依据，所有服务必须统一。
