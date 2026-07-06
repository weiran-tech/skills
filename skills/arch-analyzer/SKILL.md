---
name: arch-analyzer
description: 分析 Java 微服务项目（多模块 Maven/Gradle 结构）的服务架构。当用户说 "arch-analyzer"、"分析服务架构"、"生成服务文档"、"架构分析"、"文档化服务"、"analyze service architecture" 时触发。也适用于：用户想了解微服务功能边界、整理 MQ 事件契约、为 AI 工具准备上下文文档、分析业务执行流程影响范围、或更新已有的服务架构文档。
---

# Arch Analyzer

分析当前 Java 微服务项目代码，生成四份文档。每份文档服务于不同的读者和场景：

| 文件 | 作用 | 参考指南 |
|------|------|---------|
| `docs/workflow/overview.md` | 服务名片：职责、模块、技术栈、依赖 | `references/overview-md.md` |
| `docs/workflow/business.md` | 业务规则：为什么这么处理 | `references/business-md.md` |
| `docs/workflow/contracts.md` | 对外契约：承诺了什么 | `references/contracts-md.md` |
| `docs/workflow/flows.md` | 执行链路：怎么流转 | `references/flows-md.md` |

### 文档间职责边界（必须遵守）

每份文档只回答一个问题，禁止交叉：

- **overview.md** → 事实（是什么、有什么、依赖谁）
- **business.md** → 规则（为什么这么处理），禁止出现具体 MQ tag 名和执行流程步骤
- **contracts.md** → 契约（唯一契约源），禁止展开完整业务流程
- **flows.md** → 链路（怎么流转），禁止展开业务规则细节

文档间只做单向引用，不复制内容：
- business.md 提到事件时：写"相关事件见 contracts.md"
- flows.md 提到规则时：写"该规则见 business.md"
- contracts.md 提到用途时：一句话说明，不展开流程

## 第一步：并行扫描项目

在生成任何文档之前，先建立对项目的全面认知。以下扫描并行执行：

**模块结构：**
- 读取根目录 `pom.xml` / `build.gradle`，获取 `<modules>` 列表
- 读取 `application.yml` / `bootstrap.yml` 获取 `spring.application.name`

**MQ 消费方扫描：**
- 搜索 `@RocketMQMessageListener`、`@KafkaListener`、`@RabbitListener`
- 读取每个监听器类，记录：topic、tag/consumerGroup、消费后调用的 Service 方法
- **事件级联追踪**：对每个监听器，沿调用链（Consumer → Service → Repository/DomainService）向下追踪，检查是否有 `syncSend`、`asyncSend`、`syncSendDeliverTimeMills`、`convertAndSend` 等 MQ 发布调用。记录该 Consumer 处理过程中产生的所有下游事件（topic:tag）。这是构建完整事件级联链路的关键步骤

**MQ 发布方扫描：**
- 搜索 `syncSend`、`asyncSend`、`sendDelayLevel`、`syncSendDeliverTimeMills`、`convertAndSend`
- 记录每处发布的：topic、tag、触发该发布的业务方法

**Feign 接口扫描：**
- 搜索 `@FeignClient`，区分本服务暴露的（`*-api` 模块）和调用外部的（`*-infrastructure` 模块）

**业务逻辑扫描：**
- 读取 `*-core` / `*-domain` / `*-application` 模块下的 `@Service` 类
- 查找状态枚举（含 `Status`、`State`）、路由/分发逻辑（Router、Dispatcher、Strategy、Handler）、`@Scheduled` 定时任务

## 第二步：增量更新原则

写文件前先检查是否已存在：

- **不存在**：直接生成完整内容
- **已存在**：读取现有内容，保留手动补充的部分（业务背景、决策原因等），只更新可从代码推断的表格和列表，追加新发现的内容

手动补充的内容比代码扫描结果更有价值，不要覆盖。

## 第三步：逐份生成文档

按以下顺序生成，每份文档读取对应的 reference 文件获取详细规则和模板：

1. **docs/workflow/overview.md** → 读取 `references/overview-md.md`
2. **docs/workflow/business.md** → 读取 `references/business-md.md`
3. **docs/workflow/contracts.md** → 读取 `references/contracts-md.md`
4. **docs/workflow/flows.md** → 读取 `references/flows-md.md`

如果用户只要求生成某一份文档，只读取对应的 reference 文件即可。

## 第四步：完成摘要

输出简短摘要：
- 扫描结果：模块数、MQ 监听器数、发布点数、Feign 接口数
- 标注了"待确认"的字段（信息不足处）
- 保留了哪些已有内容（增量更新时）

## 第五步：自动触发 arch-publish

文档生成完成后，**无需用户额外指令**，立即执行 `arch-publish` skill，将本次生成的文档推送到 arch-docs。

按照 arch-publish skill 的完整流程执行，包括：确定 arch-docs 路径、确定服务名称、推送文档、更新索引。
