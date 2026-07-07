# summary：版本级交付对接清单

> 处理 `/dev-workflow summary [版本号]` 时读本文件。用途：对已 READY 或 RELEASED 的版本，聚合其下所有子需求的 DDL 变更、新增队列、API 接口清单，输出一份对接清单分发给 DBA / 运维 / 前端（AC9）。粒度对齐 spec C10：`rework` 按子需求，`summary` 按版本聚合。

---

## §1. 命令形式

```
/dev-workflow summary {版本号}
```

- **必传版本号**（spec D8：无活动指针；缺参报错）
- 缺参时主 Agent 必须立即报错 + 扫描 `docs/version/` 列出所有存在的版本号 + 列出哪些版本状态 ∈ {IN_PROGRESS, READY, RELEASED} 适合产出清单
- 错误信息三段式：`[字段 command.args] 缺少版本号。建议：执行 /dev-workflow version list 查可用版本；或直接传 /dev-workflow summary {版本号}`

---

## §2. 数据来源

按以下顺序汇聚数据：

### 2.1 版本文件（聚合起点）

读 `docs/version/{版本号}`（templates.md §2 的 9 字段文件）：
- `versionNumber` / `status` / `owner` — 版本头
- `subRequirements[]` — 参与聚合的子需求完整 ID 列表（含 `#`）
- `stageRecord` — 阶段记录参考（用于显示每个子需求当前阶段，但**不参与聚合判定**）

> 校验：`status` 必须 ∈ {IN_PROGRESS, READY, RELEASED}；DRAFT 无清单可聚（子需求尚未编码）、ARCHIVED 永久封存（禁止输出）。不满足时立即报错。

### 2.2 逐子需求 metadata.md

对 `subRequirements[]` 中每个完整 ID `{域}/{父需求名}#{子需求名}`，按 templates.md §0 解析为路径 `docs/discuss/{域}/{父需求名}/.task/{子需求名}/metadata.md`，读其 `阶段产物引用` 区。

### 2.3 三块数据的实际来源

| 块 | 数据源（按 metadata.md 阶段产物引用读取） |
|----|------------------------------------------|
| **DDL 变更** | `dev-tasks.md` 中带「迁移」标签的任务条目 / `done/` 已归档任务里带「migration」标志的文件 / `acceptance.md` 的「DB 变更」段 / 实际代码 `{module_root_glob}/*/resources/migrations/*` 跨任务汇总 |
| **新增队列 / MQ** | `dev-tasks.md` 中带「Job / MQ / 队列」标签的任务条目 / `done/` 已归档任务 / `acceptance.md` 的「异步任务」段 |
| **API 接口清单** | `dev-tasks.md` 中带「路由 / controller / API」标签的任务条目 / `acceptance.md` 的「API 变更」段 / `design-consensus.md` 中的「对外契约」附录（如有） |

> 阶段产物引用区是元数据级别的指针；具体明细仍以 `dev-tasks.md` / `acceptance.md` 的正文为准（spec 原则：metadata 仅存路径，详情靠阶段产物）。

---

## §3. 执行流程（静态可分析）

主 Agent 收到 `/dev-workflow summary {版本号}` 后：

### 步骤 1：解析与校验

```
read {项目根}/docs/version/{版本号}
  ├─ 不存在 → 报错 [字段 version.file] {版本号} 不存在。建议：执行 /dev-workflow version list 查可用版本
  └─ 存在 → 提取 versionNumber / status / owner / subRequirements[]
       ├─ status ∈ {DRAFT, ARCHIVED} → 报错（见 §6 错误矩阵）
       └─ status ∈ {IN_PROGRESS, READY, RELEASED} → 进入步骤 2
```

### 步骤 2：逐子需求读 metadata.md

对 `subRequirements[]` 中每个 ID：
```
parseSubReqId(id) → { parent, child }                    # templates.md §0
read docs/discuss/{parent}/.task/{child}/metadata.md
  ├─ 不存在 → 跳过该子需求 + 记入「缺失子需求清单」（见 §4 注）
  └─ 存在 → 提取「阶段产物引用」表的每行路径
```

### 步骤 3：合并三块（DDL / 队列 / API）

启动 `document-specialist`（只读）以版本为单位聚合：
- 输入：版本号 + 各子需求的 `metadata.md` + 关联 `dev-tasks.md` / `acceptance.md` / `design-consensus.md`
- 输出文件：根据步骤 4 的路径策略落盘

> 子 agent 返回后必须呈现结果：把三块的条数摘要（DDL N 张表 / 队列 M 个 / API K 个）+ 文件路径打给用户，不许静默结束。

### 步骤 4：落盘文件路径

按 spec 与 plan §6 Step 8 要求，change-manifest.md 落到**每个版本单独一份**：

| 范围 | 路径 |
|------|------|
| 单域版本（默认） | `docs/discuss/{域}/{父需求名}/.task/.versions/{版本号}/change-manifest.md` |
| 跨域版本（聚合不同时落到一个父需求目录易误导） | `docs/version/{版本号}/change-manifest.md` |

> 落地策略由 document-specialist 在步骤 2 完成后判定：所有子需求 `parentReqId` 域相同落单域路径；跨域时落全局路径。

### 步骤 5：用户可触发的多版本合并（可选）

**所有相关版本 RELEASED 后**，用户可主动调用 `/dev-workflow summary --merge {版本号A} {版本号B} ...` 出需求级合并清单：把各版本 change-manifest.md 的三块拼起来，每行带 `(来源: {版本号} / {子需求ID})` 标注。此命令不自动触发，仅在用户显式传 `--merge` 时启用。

---

## §4. 输出格式

change-manifest.md 顶部为版本头 + 三块。受众是前端和运维/DBA，**不关心代码实现细节**（类名/方法名/中间件等都不列）。

### 版本头

```markdown
# {版本号} — 交付对接清单

- 版本号: {versionNumber}
- 状态: {status（IN_PROGRESS / READY / RELEASED）}
- 负责人: {owner}
- 涉及子需求: {subRequirements.length} 个
- 生成时间: {YYYY-MM-DD}
```

### 三块：DDL / 队列 / API

```markdown
## 一、DDL 变更（DBA）

### {子需求ID 1} — {表名}（新建 / 变更）

```sql
CREATE TABLE `{表名}` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  -- ...
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='{注释}';
```

### {子需求ID 2} — {表名}（新建 / 变更）

```sql
ALTER TABLE `{表名}` ADD COLUMN `{字段}` varchar(32) NOT NULL DEFAULT '' COMMENT '{注释}';
```

> 子需求无 DDL 时不出该小节；整版本无 DDL 时写「本次无 DDL 变更」。

## 二、新增队列（运维）

| 队列名称 | 来源子需求 |
|---------|-----------|
| {queue_name_1} | {子需求ID} |
| {queue_name_2} | {子需求ID} |

> 整版本无新增队列时写「本次无新增队列」。

## 三、API 接口清单（前端）

| Method Path | 入参 | 出参要点 | 用途 | 来源子需求 |
|-------------|------|---------|------|-----------|
| POST /api/xxx | field1:string(必填), field2:int | {要点} | {一句话} | {子需求ID} |
```

### 缺失子需求清单（如适用）

```markdown
## 缺失子需求（需人工跟进）

| 子需求 ID | 状态 |
|-----------|------|
| {完整 ID} | metadata.md 不存在或路径非法 |
```

---

## §5. 生成用 agent prompt

```
document-specialist "
为版本 {版本号} 产出版本级交付对接清单。

数据来源（严格按此顺序汇聚，不许扩散到其他文件）：
1. 读 {项目根}/docs/version/{版本号}，提取 versionNumber / status / owner / subRequirements[]
2. 对 subRequirements[] 中每个 ID 按 templates.md §0 解析为路径，读 docs/discuss/{域}/{父需求名}/.task/{子需求名}/metadata.md
3. 从每个子需求 metadata.md 的「阶段产物引用」区读取 dev-tasks.md / acceptance.md / design-consensus.md 路径
4. 聚合三块：DDL 变更 / 新增队列 / API 接口

落地路径按以下规则二选一：
- 所有子需求域相同 → docs/discuss/{域}/{父需求名}/.task/.versions/{版本号}/change-manifest.md
- 跨域或域分散 → docs/version/{版本号}/change-manifest.md

输出格式（严格遵循，markdown 可直接交付）：
- 版本头：版本号、状态、负责人、子需求数量、生成时间
- 三块：DDL 变更（DBA）、新增队列（运维）、API 接口清单（前端）
- 每行数据末尾标注来源子需求 ID
- 不列迁移文件路径、字段类型表格、控制器名、方法名、中间件
- 不展开业务流程、不含代码实现位置

约束：
- 只读访问上述文件，禁止修改 metadata.md / version 文件 / 任何源代码
- 执行约束见 SKILL.md 不变量 12：所有 Bash 命令必须可静态分析，禁止 for/while/if/case/here-doc/嵌套 $()
- 子 agent 返回后必须把三块的条数摘要（DDL N 张表 / 队列 M 个 / API K 个）+ 文件路径打给主 Agent
"
```

---

## §6. 错误矩阵

| 场景 | 错误信息（三段式） | 建议 |
|------|-------------------|------|
| 版本文件不存在 | `[字段 version.file] {版本号} 不存在` | 执行 `/dev-workflow version list` 查可用版本 |
| 状态 = DRAFT | `[字段 version.status] {版本号} 仍为 DRAFT，子需求尚未编码` | 先推进子需求到阶段 4，再触发 summary |
| 状态 = ARCHIVED | `[字段 version.status] {版本号} 已 ARCHIVED，永久封存禁止输出` | 建新版本或新子需求 |
| 子需求 metadata.md 缺失 | `[字段 subReq.metadata] {子需求ID} metadata.md 不存在` | 该子需求跳过聚合，写入「缺失子需求清单」；不阻断整版本输出 |
| 跨域版本未指定落点 | `[字段 output.path] {版本号} 含 {N} 个域，需二选一` | 主 Agent 自动落 `docs/version/{版本号}/change-manifest.md`（跨域默认全局） |
| 缺参（无版本号） | `[字段 command.args] 缺少版本号` | 执行 `/dev-workflow version list` 查可用版本；或直接传 `/dev-workflow summary {版本号}` |

---

## §7. 与 release-docs 的衔接

`change-manifest.md`（本命令产物）是结构化「事实清单」（原料），仅列「改了哪些表 / 加了哪些队列 / 新增哪些接口」——这些是给 DBA / 前端 / 运维看的事实。

当需要面向运维上线操作的「上线配置说明」（人工要配的开关 / 密钥 / 顺序 / 风险 / 回滚步骤）时，把 `change-manifest.md` 喂给 `release-docs` skill 生成。两个产物边界清晰：

| 产物 | 命令 | 性质 | 受众 |
|------|------|------|------|
| change-manifest.md | `/dev-workflow summary {版本号}` | 事实清单（DDL/Job/API） | DBA + 前端 + 运维 |
| release-notes / 上线说明 | release-docs skill（外部） | 操作说明（开关/密钥/顺序/风险） | 运维上线负责人 |

> 两者不重复。summary 给出「改了什么」；release-docs 给出「怎么改 / 怎么回滚」。

---

## §8. 多版本合并清单（用户主动触发）

`/dev-workflow summary --merge {版本号A} {版本号B} ...` — 仅在用户显式传 `--merge` 时启用。

### 用途

所有纳入 RELEASED 后，用户希望一次性看到跨版本（如 v1.0 + v1.1 + v2.0）的总览清单（例：季度发布汇总、年度账单）。

### 与单版本 summary 的区别

- **不**重新读各子需求的 dev-tasks.md（避免重复劳动）
- 直接读各版本已生成的 `change-manifest.md`，把三块拼起来
- 每行带 `(来源: {版本号} / {子需求ID})` 标注
- 版本头改为多版本汇总表

### 落地路径

`docs/version/.merged/change-manifest-{Y}-{M}-{D}.md` —— 不覆盖任何单版本清单，避免污染。

### 缺参行为

`--merge` 后不传任何版本号 → 报错 + 扫描 `docs/version/*.md`（或 `docs/version/*/change-manifest.md`）列出所有已存在 change-manifest 的版本供选择。
