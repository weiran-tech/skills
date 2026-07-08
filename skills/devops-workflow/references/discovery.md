# Runtime Discovery Engine（运行时上下文发现引擎）

> 本文件描述 `/devops-workflow` skill 在执行任意命令前如何**运行时**发现项目语言、测试/校验/静态分析命令、模块布局、跨模块契约类型。所有发现结果缓存于会话内存内，**不需要单独的 config 文件**。命令执行时随用随查。

---

## §1. Discovery sources（发现源，按优先级合并）

任何 `/devops-workflow` 命令执行前必须按以下顺序解析必需字段：

1. **项目 manifest 文件**（根目录）：读取 `engines` / `scripts` / `workspaces` 等字段，识别语言和测试/校验命令
2. **`CLAUDE.md`**（项目根）：项目级指令文件，可显式覆盖 manifest 默认推断
3. **`docs/workflow/{module}/`** 目录：模块契约层声明，发现跨模块 `{contract_type}` 类型

后置来源可覆盖前置来源；冲突按 §5 conflict 规则处理。

---

## §2. Required fields（必需字段）

执行任何 `req create` / `version create` / `next` / `summary` 等命令前必须已解析以下字段：

| 字段 | 类型 | 含义 |
|------|------|------|
| `language` | `string`（node \| go \| java \| python \| rust \| ...） | 主语言 |
| `test_cmd` | `string` | 项目测试命令（占位符 `{test_cmd}` 替换为该值） |
| `lint_cmd` | `string` | 项目语法校验命令（占位符 `{lint_cmd}` 替换为该值） |
| `static_analysis_cmd` | `string` \| 空 | 项目静态分析命令（可选；缺省留空，不纳入 DoD） |
| `module_root_glob` | `glob` | 模块根目录匹配模式（如 `modules/*/`、`apps/*/`、`packages/*/`） |
| `contract_type` | `string`（rpc \| grpc \| kafka \| event \| queue \| http \| ...） | 跨模块调用通道类型 |

**默认占位符映射**（即 SKILL.md 中的 `{test_cmd}` 等）：
- `{test_cmd}` ↔ `discovery.test_cmd`
- `{lint_cmd}` ↔ `discovery.lint_cmd`
- `{static_analysis_cmd}` ↔ `discovery.static_analysis_cmd`
- `{module_root_glob}` ↔ `discovery.module_root_glob`
- `{contract_type}` ↔ `discovery.contract_type`
- `{discovery_cmd}` ↔ 由 `discovery.discovery_cmd` 提供（缺省时使用 manifest 中声明的等价工具，如 `compo` / `asm` / `go mod` 等）

---

## Manifest Reference Table

```
| Language | Manifest file            | Fields to read                                  | Notes |
|----------|--------------------------|-------------------------------------------------|-------|
| Node     | package.json             | engines.node, scripts.test, scripts.lint, workspaces | (legacy php-workflow reference; not supported in dev-workflow) |
| Node     | pnpm-workspace.yaml      | packages (glob list)                            | overrides package.json#workspaces when present; precedence: YAML > JSON |
| Go       | go.mod + go.work         | module name; go.work#use                        | affects module-root resolution when go.work is absent |
| Go       | go.mod replace directive | replace targets                                 | carve-out: ignore replace targets outside the workspace |
| Java     | pom.xml                  | <modules>, <parent>                             | parent POM <parent> + child POM <modules> > root POM only (Java: nested inheritance) |
| Rust     | Cargo.toml               | [package], [workspace.members]                  | (legacy php-workflow reference; not supported in dev-workflow) |
| Python   | pyproject.toml           | [project], [tool.poetry.packages]               | (legacy php-workflow reference; not supported in dev-workflow) |
| PHP      | composer.json            | (legacy php-workflow reference; not supported in dev-workflow) | reserved for migration from php-workflow |
```

> **使用规则**：执行发现逻辑时，按当前目录 root 下存在的 manifest 文件查找对应行；多 manifest 并存按 §6 Case A 处理。

---

## §4. Missing rule（必需字段缺失硬阻塞）

任何必需字段在所有发现源中都找不到对应值时，硬阻塞并报错：

```
[字段 {X} 缺失] 未从 manifest / CLAUDE.md / docs/workflow 找到 {X} 的值。建议: 在 CLAUDE.md 中声明 ## {X} 段，或在 manifest 文件中添加 {X} 字段。
```

**示例**：
- `[字段 test_cmd 缺失] 未从 manifest / CLAUDE.md 找到 test_cmd 的值。建议: 在 CLAUDE.md 中声明 ## test_cmd 段（如 \`test_cmd: cargo test\`），或在 manifest 文件 scripts.test 中提供该值`
- `[字段 module_root_glob 缺失] 未从 manifest / CLAUDE.md 找到 module 根目录模式。建议: 在 CLAUDE.md 中声明 ## module_root_glob 段（如 \`module_root_glob: modules/*/\`）`

**回退机制**：
1. 优先尝试 manifest 文件推断（按 §3 表）
2. 缺则读 `CLAUDE.md` 中 `## {X}` 段
3. 仍缺则读 `docs/workflow/` 下任一模块的 `contracts.md`（仅对 `contract_type` 字段适用）
4. 最终缺 → 硬阻塞，不自动 fallback 占位值

---

## §5. Conflict rule（冲突硬阻塞 / conflicting context hard-block）

两个发现源对同一字段给出不同值时（conflicting values），硬阻塞并要求用户显式裁决：

```
[字段 {X} {当前值}] 冲突: {source1}={value1}, {source2}={value2}。建议: 在 CLAUDE.md 中显式声明 {X}={winning_value}。
```

**示例**：
- `[字段 test_cmd cargo test] 冲突: manifest.scripts.test=npm test, CLAUDE.md##test_cmd=cargo test。建议: 在 CLAUDE.md 中显式声明 test_cmd={winning_value}（CLAUDE.md 默认覆盖 manifest）`
- `[字段 module_root_glob modules/*/] 冲突: manifest#workspaces=[apps/*], CLAUDE.md##module_root_glob=modules/*/。建议: 在 CLAUDE.md 中显式声明 module_root_glob={winning_value}`

**优先级（当 CLAUDE.md 未显式覆盖时）**：
1. `CLAUDE.md` `## {X}` 段（最高）
2. `docs/workflow/{module}/` 中模块级声明
3. manifest 文件（按 §3 表推断）
4. 隐式默认（最少；如 `test_cmd` 缺省尝试 `npm test`，仍失败走 §4 missing）

---

## §6. Ambiguous rule（歧义硬阻塞 / ambiguous context hard-block — 4 cases）

以下 4 种歧义场景一律硬阻塞，要求用户在 `CLAUDE.md` 显式裁决：

### Case A — Multi-manifest no tie-breaker
根目录同时存在多个 manifest 文件（如 `package.json` 和 `Cargo.toml`），且 `CLAUDE.md` 中没有 `## 主语言` 段指定优先级。

硬阻塞格式：
```
[字段 language {当前推断}] 歧义: 项目根同时存在多种 manifest 文件（package.json + Cargo.toml），未在 CLAUDE.md 声明主语言。建议: 在 CLAUDE.md 中显式声明 ## 主语言: {language} 段。
```

### Case B — engines.node vs type
Node 项目中 `engines.node` 与 `package.json#type`（如 `"module"` / `"commonjs"`）对语言版本或模块系统给出冲突判断。

硬阻塞格式：
```
[字段 language {当前推断}] 歧义: manifest 中 engines.node 与 type 字段不一致，无法判定主语言运行时。建议: 在 CLAUDE.md 中显式声明 ## language: {language}（如 node 或 typescript-node）段。
```

### Case C — Workspace conflict
Node 项目中 `pnpm-workspace.yaml` 的 `packages` 字段与 `package.json#workspaces` 声明的模块集合不一致。

硬阻塞格式：
```
[字段 module_root_glob {当前值}] 歧义: pnpm-workspace.yaml 与 package.json#workspaces 声明的模块集合不同。建议: 在 CLAUDE.md 中显式声明 ## module_root_glob: {winning-glob} 段。
```

### Case D — Orphan go.work#use
`go.work#use` 列表中存在模块 A，但项目下没有模块 A 对应的 `go.mod`。

硬阻塞格式：
```
[字段 module_root_glob {当前值}] 歧义: go.work#use 声明了模块 {A}，但项目内无该模块对应的 go.mod。建议: 在 CLAUDE.md 中显式声明 ## module_root_glob: {winning-glob}，或在 go.work 中移除孤立模块声明。
```

> **通用回退**：遇到 §6 任一硬阻塞，用户修复 `CLAUDE.md` 后必须重新执行发现流程，**不可假设**任一来源默胜出。

---

## §7. Cache & lifetime（缓存与生命周期）

- 发现结果缓存于主 Agent 的会话内存，跨命令复用
- 缓存 key = `(project_root_hash, session_id)`
- 缓存失效触发：
  - `manifest` 文件 mtime 变更
  - `CLAUDE.md` 文件 mtime 变更
  - `docs/workflow/` 下任何模块契约文件 mtime 变更
  - 用户显式调用 `/devops-workflow discovery refresh`（保留命令，见 §9）

> **`{discovery_cmd}` 触发**：当发现结果失效或初次安装本 skill 时，应提示用户跑 `{discovery_cmd}` 重新生成 `docs/workflow/` 全部产物。

---

## §8. Invariant 8 cross-reference（与 SKILL.md 不变量 8 联动）

`contract_type` 字段在本文件中的发现结果直接绑定到 SKILL.md 不变量 8：

> **SKILL.md 不变量 8**：跨模块交互一律通过 `{contract_type}` 通道，禁止直接访问他模块实现细节（具体实现细节按语言而异，统一表述为"直接调用对模块内部的实体"）。

**联动规则**：
1. `discovery.contract_type` 是 SKILL.md 中 `{contract_type}` 占位符的唯一解析源
2. 当 `contract_type` 在任意命令中被引用（如 `summary` 阶段聚合输出），必须使用本文件发现的契约类型，不允许命令内硬编码
3. 跨模块禁令适用于**任何** `contract_type` 值（rpc、grpc、kafka、event、queue、http 等），不分语言、不分协议

**校验用例**：
- `next` 阶段 4 编码时检测到跨模块调用 → 必须用 `{contract_type}` 通道（具体实现按 `discovery.contract_type` 解析）
- `summary` 聚合跨模块交付清单 → 按 `discovery.contract_type` 分组

---

## §9. Reserved commands（保留：discovery refresh）

为支持长会话中的发现刷新，保留以下命令（详见 `commands.md` §C）：

```
/devops-workflow discovery refresh
```

**用途**：强制重新执行 §1 全部发现逻辑，清空 §7 缓存，从头解析所有必需字段。

**用途**：
- 用户新增模块后需要刷新 `module_root_glob` 匹配
- 用户修改 `CLAUDE.md` 后希望立即生效
- `docs/workflow/` 重新生成后需要重新发现契约

---

## §10. 字段 schema 对照

| 字段 | 来源（优先级 1 → 3） | 缺省行为 |
|------|---------------------|----------|
| `language` | CLAUDE.md → manifest#engines → docs/workflow 命名 | 缺则 §4 hard-block |
| `test_cmd` | CLAUDE.md → manifest#scripts.test | 缺则 §4 hard-block |
| `lint_cmd` | CLAUDE.md → manifest#scripts.lint | 缺则 §4 hard-block |
| `static_analysis_cmd` | CLAUDE.md → manifest#scripts.analyze | 缺则空字符串，不 DoD 校验 |
| `module_root_glob` | CLAUDE.md → manifest#workspaces → docs/workflow 命名 | 缺则 §4 hard-block |
| `contract_type` | docs/workflow/{module}/contracts.md → CLAUDE.md → manifest 推断 | 缺则 §4 hard-block |
| `discovery_cmd` | CLAUDE.md → manifest 推断 | 缺则空字符串 |

---

## §11. 示例：典型发现过程

### 场景 1：Node 多模块项目
```
CLAUDE.md:
## 主语言: typescript-node
## test_cmd: pnpm test
## lint_cmd: pnpm lint
## module_root_glob: apps/*/
## contract_type: http

发现结果:
  language = typescript-node
  test_cmd = pnpm test
  lint_cmd = pnpm lint
  static_analysis_cmd = ""  # CLAUDE.md 未声明 → 留空
  module_root_glob = apps/*/
  contract_type = http
  discovery_cmd = ""  # 未声明
```

### 场景 2：Java Spring 多模块项目
```
CLAUDE.md:  # 完全缺失相关段
manifest file (pom.xml): <modules>app1, app2</modules>

发现过程:
  1. CLAUDE.md 无 → 跳到 manifest
  2. manifest#<modules> = [app1, app2] → module_root_glob 推断为 "app*/"
  3. test_cmd: manifest 无 scripts 段 → §4 hard-block
     → [字段 test_cmd 缺失] 未从 manifest / CLAUDE.md 找到 test_cmd 的值。建议: 在 CLAUDE.md 中声明 ## test_cmd 段。
```

### 场景 3：Go workspace
```
go.work: use [./pkg/a, ./pkg/b, ./pkg/c]
但 ./pkg/c/go.mod 不存在

触发 §6 Case D → 硬阻塞
[字段 module_root_glob {当前值}] 歧义: go.work#use 声明了模块 c，但项目内无该模块对应的 go.mod。建议: 在 CLAUDE.md 中显式声明 ## module_root_glob: {winning-glob}，或在 go.work 中移除孤立模块声明。
```
