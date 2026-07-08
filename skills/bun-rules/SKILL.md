---
name: bun-rules
description: 为 Bun 项目生成标准化的 Claude Code 规则文件（CLAUDE.md + .claude/rules/）
---

# Bun 项目规则

为当前 Bun 项目生成标准化的 Claude Code 规则文件

**定位**：只生成开发规范和操作指南，不分析业务逻辑和执行流程（业务分析由 bun-analyzer 负责）


## 产出物

| 文件                              | 类型     | 来源        | 说明                                                                                 |
| --------------------------------- | -------- | ----------- | ------------------------------------------------------------------------------------ |
| `CLAUDE.md`                       | 项目级   | 模板 + 扫描 | 纯入口导航（一句话职责 + 文档阅读顺序 + 规则索引），不持有事实内容或编码规则         |
| `.claude/rules/architecture.md`   | 通用规则 | 模板复制    | 设计原则 + 编码原则 + API约定 + 完成检查清单, 文件位置 `./templates/architecture.md` |
| `.claude/rules/build-and-test.md` | 通用规则 | 模板复制    | 运行, 构建, 测试命令和规范, 文件位置 `./templates/build-and-test.md`                 |
| `.claude/rules/coding.md`         | 通用规则 | 模板复制    | 代码编写规范, 文件位置 `./templates/coding.md`                                       |
