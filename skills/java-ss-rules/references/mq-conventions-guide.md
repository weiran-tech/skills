# mq-conventions.md 生成指南

mq-conventions.md 包含通用 MQ 规范和项目特有 MQ 信息。通用部分固定输出，项目特有部分优先从 docs 提取。

**数据来源优先级**：`docs/contracts.md` > 代码扫描。docs 存在时不做代码扫描。

## frontmatter

```yaml
---
description: MQ 消费者和生产者的开发规范、命名约定、幂等要求
globs:
  - "{消费者实际路径}/**"
  - "{MQ 常量类路径}/*MqConstant*"
  - "{EventHandler 路径}/*EventHandler*"
---
```

**globs 必须从项目信息中提取实际路径**，不能写死。例如：
- 消费者在 `adapter/event/listener/` → globs 写 `**/adapter/event/listener/**`
- 消费者在 `adapter/consumer/` → globs 写 `**/adapter/consumer/**`

globs 路径来源：
- **docs 存在时**：从 `docs/contracts.md` 的"消费的 MQ 事件"表格中的监听器类提取包路径
- **docs 不存在时**：grep `@RocketMQMessageListener` 提取消费者包路径

## 信息获取

### 从 docs/contracts.md 提取（优先）

如果 `docs/contracts.md` 存在，从中提取以下项目特有信息：

- **消费者包路径**：从"消费的 MQ 事件"表格的"监听器类"列提取包路径模式
- **ConsumerGroup 命名规则**：从"ConsumerGroup"列推断命名模式（如 `consumer_group_{service}_{业务标识}`）
- **事件发布入口类**：从"发布的 MQ 事件"表格的"发布类"列提取
- **Tag 命名约定**：从"Tag"列推断命名模式
- **高扇出 tag**：从"消费的 MQ 事件"中统计同一 tag 被多个监听器消费的情况；或从 `docs/flows.md` 的事件级联链路识别
- **常量类位置**：从 `docs/overview.md` 的模块结构中推断 domain 模块的 constants 包路径

### 从代码扫描提取（回退）

仅当 `docs/contracts.md` 不存在时执行：

- grep `@RocketMQMessageListener` 提取消费者包路径和 consumerGroup
- grep MQ 常量类（TOPIC_/TAG_）
- grep `syncSend`/`asyncSend` 提取发布入口
- 统计高扇出 tag（5+ 消费者）

## 文档结构

### 第一部分：新增消费者（通用 + 项目特有）

**通用内容（固定输出）：**

类模板结构（@Component + @Slf4j + @AllArgsConstructor + @RocketMQMessageListener + implements RocketMQListener<MessageExt>），onMessage 方法的标准流程（日志 → 反序列化 → 幂等检查 → 委托业务处理）。

**项目特有内容（从 docs 或扫描填充）：**

- 消费者文件位置：消费者包路径
- 注解中的常量引用：MQ 常量类名（如 `MqConstant.TOPIC_XXX`）
- ConsumerGroup 命名规则：推断的命名模式
- 顺序消费 vs 并发消费：如果 contracts.md 中有标注或扫描到有 `ConsumeMode.ORDERLY`，说明使用场景

### 第二部分：新增事件发布（通用 + 项目特有）

**通用内容（固定输出）：**

发布方式模板（syncSend / syncSendDeliverTimeMills）。

**项目特有内容（从 docs 或扫描填充）：**

- 事件发布入口类：EventHandler 类名
- Tag 命名约定：推断的命名模式
- 常量类位置：实际的 MQ 常量类名和所在模块

### 第三部分：幂等约定（通用，固定输出）

以下内容所有项目完全一致，直接输出：

```
所有 MQ 消费者必须实现幂等。推荐做法:

1. **状态判断幂等**: 消费前检查业务实体当前状态，已处理则跳过
2. **唯一键幂等**: 通过数据库唯一索引防止重复写入
3. **延迟消息幂等**: 延迟消息发出后不可撤销，消费时必须检查当前状态是否仍然需要处理

禁止依赖 RocketMQ 的 msgId 做幂等（集群模式下不保证唯一）。
```

### 第四部分：修改现有事件的注意事项（项目特有）

列出高扇出 tag（从 docs 或扫描结果获取），提醒修改这些 tag 的消息体属于破坏性变更。

引导先查看 `docs/contracts.md` 确认所有消费方。
