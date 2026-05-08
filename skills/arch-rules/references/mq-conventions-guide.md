# mq-conventions.md 生成指南

mq-conventions.md 包含通用 MQ 规范和项目特有 MQ 信息。通用部分固定输出，项目特有部分从代码扫描填充。

## frontmatter

```yaml
---
description: MQ 消费者和生产者的开发规范、命名约定、幂等要求
globs:
  - "{扫描到的消费者实际路径}/**"
  - "{扫描到的 MQ 常量类路径}/*MqConstant*"
  - "{扫描到的 EventHandler 路径}/*EventHandler*"
---
```

**globs 必须从第一步扫描结果中提取实际路径**，不能写死。例如：
- 消费者在 `adapter/event/listener/` → globs 写 `**/adapter/event/listener/**`
- 消费者在 `adapter/consumer/` → globs 写 `**/adapter/consumer/**`

## 文档结构

### 第一部分：新增消费者（通用 + 项目特有）

**通用内容（固定输出）：**

类模板结构（@Component + @Slf4j + @AllArgsConstructor + @RocketMQMessageListener + implements RocketMQListener<MessageExt>），onMessage 方法的标准流程（日志 → 反序列化 → 幂等检查 → 委托业务处理）。

**项目特有内容（扫描填充）：**

- 消费者文件位置：从扫描结果获取实际的消费者包路径
- 注解中的常量引用：从扫描到的 MQ 常量类名填充（如 `MqConstant.TOPIC_XXX`）
- ConsumerGroup 命名规则：从扫描到的 consumerGroup 常量推断命名模式（如 `consumer_group_{service}_{业务标识}`）
- 顺序消费 vs 并发消费：如果扫描到有 `ConsumeMode.ORDERLY` 的消费者，说明使用场景

### 第二部分：新增事件发布（通用 + 项目特有）

**通用内容（固定输出）：**

发布方式模板（syncSend / syncSendDeliverTimeMills）。

**项目特有内容（扫描填充）：**

- 事件发布入口类：从扫描到的 EventHandler 类名填充
- Tag 命名约定：从扫描到的 tag 常量推断命名模式
- 常量类位置：填充实际的 MQ 常量类名和所在模块

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

从扫描结果中，列出消费者数量 >= 5 的 tag 作为高扇出 tag，提醒修改这些 tag 的消息体属于破坏性变更。

如果项目有 `docs/contracts.md`，引导先查看该文件确认所有消费方。
