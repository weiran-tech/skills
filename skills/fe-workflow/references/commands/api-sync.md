# /fe-workflow api-sync — Mock 转真实接口

真实接口就绪后，从 Apifox MCP 读取接口定义，替换代码中的 mock 为真实接口调用。

**Input**: `/fe-workflow api-sync [--feat=<id|name>] [接口模块名或关键词]`

## 执行步骤

1. **确定接口层模式**：加载项目编码规范 skill（按 SKILL.md「项目约定」解析顺序），确定接口层的位置与写法（请求文件、API 枚举、类型定义的组织方式均以规范 skill 为准）

2. **扫描 mock 标记**：在功能相关代码（--feat 指定时以其 files_changed 为范围，否则全项目相关目录）查找：

   ```
   // TODO: 替换为真实接口
   ```

3. **从 Apifox 获取接口**：用 Apifox MCP 工具获取接口定义（工具名从当前可用 MCP 工具列表选取）；找不到对应接口 → AskUserQuestion 询问用户

4. **接口映射确认**：将 Apifox 接口与 mock 逐一映射，**AskUserQuestion 确认映射关系后才替换**

5. **替换接口层**：按规范 skill 的接口层模式添加 API 定义与请求函数，更新页面/组件中的调用与 TypeScript 类型

6. **替换页面内联 mock** → **移除已替换项的 TODO 标记**

7. **验证**：再次扫描确认无遗留标记（未就绪接口的 mock 保留）；运行项目类型检查确保类型匹配

8. **生成报告**：`api-sync-report.md` 写入流水线目录（模板见 `templates.md`），输出替换结果摘要

## Guardrails

- 替换前必须与用户确认映射关系，不能盲目替换
- 未找到接口的 mock 保留，不要删除
- 只替换数据来源，不改变业务逻辑
- TypeScript 类型必须与接口响应结构匹配；替换完成后必须运行类型检查
- 按项目规范 skill 的接口层模式执行，不同项目模式不得混用
