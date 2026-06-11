---
name: bun-analyzer
description: 分析 Bun 项目的架构
---

# Bun Analyzer

分析当前 Bun 项目代码，生成四份文档, 如果服务多个，每个服务对应四份文档。每份文档服务于不同的读者和场景：

| 文件                | 作用                               | 参考指南                     |
| ------------------- | ---------------------------------- | ---------------------------- |
| `docs/{service}/overview.md`  | 服务名片：职责、模块、技术栈、依赖 | `references/overview-md.md`  |
| `docs/{service}/business.md`  | 业务规则：为什么这么处理           | `references/business-md.md`  |
| `docs/{service}/flows.md`     | 执行链路：怎么流转                 | `references/flows-md.md`     |

### 文档间职责边界（必须遵守）

每份文档只回答一个问题，禁止交叉：

- **docs/{service}/overview.md** → 事实（是什么、有什么、依赖谁）
- **docs/{service}/business.md** → 规则（为什么这么处理），禁止出现具体名称和执行流程步骤
- **docs/{service}/flows.md** → 链路（怎么流转），禁止展开业务规则细节

文档间只做单向引用，不复制内容：
- flows.md 提到规则时：写"该规则见 business.md"

## 第一步：并行扫描项目

在生成任何文档之前，先建立对项目的全面认知。以下扫描并行执行：

**业务逻辑扫描：**
- `src/` 下的 文件

## 第二步：增量更新原则

写文件前先检查是否已存在：

- **不存在**：直接生成完整内容
- **已存在**：读取现有内容，保留手动补充的部分（业务背景、决策原因等），只更新可从代码推断的表格和列表，追加新发现的内容

手动补充的内容比代码扫描结果更有价值，不要覆盖。

## 第三步：逐份生成文档

按以下顺序生成，每份文档读取对应的 reference 文件获取详细规则和模板：

1. **docs/{service}/overview.md** → 读取 `references/overview-md.md`
2. **docs/{service}/business.md** → 读取 `references/business-md.md`
3. **docs/{service}/flows.md** → 读取 `references/flows-md.md`

如果用户只要求生成某一份文档，只读取对应的 reference 文件即可。

## 第四步：完成摘要

输出简短摘要：
- 扫描结果：模块数
- 标注了"待确认"的字段（信息不足处）
- 保留了哪些已有内容（增量更新时）
