# 阶段 1：需求讨论（DISCUSSING）

> 执行 `/devops-workflow start` 时读本文件。

## `/devops-workflow start {需求名}`

1. 询问用户需求所属的**业务域**（从项目构建配置、目录结构或架构文档读取本项目实际模块/组件），或从需求描述中推断
2. 检查 `{讨论根目录}{域}/{需求名}/discussion.md` 是否已存在，存在则提示用户是否要基于已有讨论继续
3. **初始化需求目录**：创建 `{讨论根目录}{域}/{需求名}/docs/` 目录，提示用户放入参考文档：
   ```
   需求目录已创建: {讨论根目录}{域}/{需求名}/
   参考文档目录: {讨论根目录}{域}/{需求名}/docs/

   请将本需求的参考文档放入 docs/ 目录（业务说明、接口文档、原始需求材料等）。
   放好后回复确认，或回复"无参考文档"直接进入讨论。
   ```
4. 用户确认后，调用 `/devops-discuss` skill，传入需求名作为讨论主题。**如 `docs/` 下有文件，在 devops-discuss prompt 中附加**：`参考文档见 {讨论根目录}{域}/{需求名}/docs/，讨论前先读取`
5. 讨论完成并保存后，创建 `.task/progress.md`（模板见 templates.md），状态设为 `ANALYZING`
6. **把该需求设为活动上下文**（写入 `{讨论根目录}.workflow-active`）
7. 按 automation.md「auto_advance 协议」处理：auto_advance=true 时自动进入阶段 2 分析与设计，否则提示 `/devops-workflow next`

**执行**：`/devops-discuss "{需求名}：{用户提供的需求描述}"`
