# Step 3 — 编码实现（implement）

根据 spec 的设计章节（lite 模式为需求部分），按项目规范生成完整功能代码。

## 前置检查

1. **文档就绪**：full 模式要求 spec 含「二、设计」章节；lite 模式要求「一、需求」存在
2. **【多功能互斥】** 同流水线内不得有其他功能的 implement/verify/e2e 处于 `in-progress`——写代码阶段同一时刻只允许一个功能进行；冲突时提示先完成或标记 blocked
3. **【commit 边界提示】** 工作区存在其他功能的未提交改动（对照其 files_changed）→ 提示"建议先按功能 commit 上一个功能的改动再继续"，**提示但不阻断**
4. **分支安全**：在 master/main/develop 上 → AskUserQuestion 警告并建议创建 `feature/{name}` 分支后再继续

## 执行步骤

### 1. 【强制·阻断性前置条件】加载项目编码规范 skill

> **⛔ 阻断规则：必须通过 Skill tool 实际调用项目编码规范 skill，在调用返回结果之前，禁止编写任何业务代码（包括 Service、页面、路由、权限）。"已知规范内容"或"上下文中已有规范"不能替代实际调用——每次编码都必须产生一次 Skill tool call。违反此规则等同于步骤未执行，代码需要重写。**

解析顺序（找到即执行）：
1. `docs/pipeline/config.yaml` 的 `coding_standard_skill`
2. 项目 `.claude/CLAUDE.md` 声明的编码规范技能名
3. 按项目特征自动匹配 SKILL.md「项目约定」的映射表（fe-kejinshou-h5-vue / fe-kejinshou-h5-nuxt / fe-backend-page / fe-mp-taobao）
4. 都没有 → 提示用户在 CLAUDE.md 或 config.yaml 登记，不得凭猜测编码

> 规范 skill 中定义的组件库、请求模式、路由模式、样式规范、命名约定，优先级高于本文件的通用规范。

### 2. 获取接口数据

- Apifox MCP 可用 → 按接口文档定义 Service/Request 层
- 不可用或接口未就绪 → 生成 mock 数据，代码中标注 `// TODO: 替换为真实接口`（api-sync 子命令按此标记扫描）

### 3. 读取相似模块作为参考

找到与当前功能最相似的已有模块，读取其关键文件作为编码风格参考。

### 4. 按规范生成代码

严格遵循已加载的项目编码规范 skill（组件库、请求层、路由、权限、Toast、常量管理等均以其为准）。通用生成顺序：

1. 配置常量（如需新增枚举/常量）
2. Request/Service 层（如需新增接口）
3. 路由配置（如需新增路由）
4. 页面/组件代码

### 5. 代码自检

- TypeScript 类型完整；导入路径正确
- 是否遵循项目现有代码模式（对比参考模块）
- mock 数据结构与接口定义匹配

### 6. 【必做】回写 files_changed

将本功能实际新增/修改的文件列表写入 progress.yaml 该功能的 `files_changed`——这是功能之间的代码边界，verify/e2e 分析范围与 commit 分组都依赖它。

### 7. 暂停

`是否继续 Step 4（代码验证）？ y — 继续 / s — 跳过`

## Guardrails

- **【强制·阻断】编码规范 skill 必须实际 Skill tool 调用**，`--auto`/`--start` 同样不可跳过，未调用不得编码
- 必须遵循项目现有代码风格，不引入新模式；不同项目的组件体系不得混用
- mock 数据必须标注 TODO 注释，便于 api-sync 替换
- 不创建不必要的 store，简单状态用组件内 ref
- 不过度封装，保持与项目其他模块一致的复杂度
- 功能扩展型需求可直接基于需求部分编码，不强制要求设计章节
