# 命令处理逻辑

> **v2 重构说明**：本文件覆盖 dev-workflow v2 的全部命令处理逻辑。v1 里程碑模式的所有命令已被硬切换废弃（无迁移、无双轨、无适配层）。
>
> **统一解析规则**：
> 1. 所有命令必须显式传子需求 ID 或版本号，**不再支持活动指针省略**。
> 2. `next` / `approve` / `status` 缺参时：报错 + 扫描 `docs/discuss/` 与 `docs/version/` 列出可选项（AC16）。
> 3. 错误信息统一格式：`[字段 {X} {当前值}] {原因}。建议: {修复}`（AC18）。
>
> **ID 解析函数**（所有命令复用）：
> ```bash
> # 解析子需求 ID {域}/{父需求名}#{子需求名} → 子需求目录
> parse_sub_req_id() {
>   local id="$1"
>   # 按最后一个 # 拆分（ID 中如含 #，取最后一个为子需求分隔）
>   local last_hash="${id##*#}"
>   local prefix="${id%#*}"
>   local domain="${prefix%%/*}"
>   local parent="${prefix#*/}"
>   echo "docs/discuss/${domain}/${parent}/.task/${last_hash}"
> }
>
> # 解析父需求 ID {域}/{父需求名} → 父需求目录
> parse_parent_req_id() {
>   local id="$1"
>   local domain="${id%%/*}"
>   local parent="${id#*/}"
>   echo "docs/discuss/${domain}/${parent}"
> }
>
> # 解析版本号 → 版本文件路径
> parse_version_id() {
>   local v="$1"
>   echo "docs/version/${v}"
> }
> ```
>
> **状态枚举**：
> - 子需求（写 metadata.md）：`DISCUSSING | ANALYZING | PENDING_DESIGN_REVIEW | DEVELOPING | PENDING_PLAN_REVIEW | PENDING_CR_REVIEW | REVIEWING | COMPLETED`
> - 版本（写 `docs/version/{版本号}`）：`DRAFT → IN_PROGRESS → READY → RELEASED → ARCHIVED`
>
> **通用前置规则**（所有修改类命令）：任何修改 `docs/version/{版本号}` 的命令执行前必须先检查 `status == ARCHIVED`，若为 ARCHIVED 立即报错（D23/AC20）。

---

## §A. `req` 命令族（4 个）

### `/devops-workflow req create {域}/{父需求名}`

**用途**：创建父需求目录结构，作为后续子需求的容器。替代 v1 的 `start` 命令。

**处理步骤**：
1. **解析参数**：
   - 必传：域 + 父需求名（如 `payment/支付渠道重构`）
   - 缺参 → 报错：`[字段 reqId 缺失] 必须传 {域}/{父需求名} 格式。建议: /devops-workflow req create payment/支付渠道重构`
2. **校验域合法性**：域必须与项目 `manifest file` 中声明的 `{module_root_glob}` 匹配，或在 `docs/workflow/` 已声明的模块清单中存在，否则报错。详见 `discovery.md`
3. **校验父需求不存在**：
   - 检查 `docs/discuss/{域}/{父需求名}/` 是否已存在，存在则报错（AC3 + Appendix A）：
     `[字段 parentReqId {域}/{父需求名}] 父需求已存在。建议: 用 /devops-workflow req show {域}/{父需求名} 查看，或选其他名称`
4. **创建目录骨架**：
   ```bash
   mkdir -p "docs/discuss/{域}/{父需求名}/.task"
   ```
5. **初始化父需求摘要文件** `docs/discuss/{域}/{父需求名}/.task/parent.md`（元数据壳，含创建时间戳与域/名）
6. **回显**：提示用户下一步用 `/devops-workflow req split {父需求ID}` 进入交互式向导创建子需求

**缺参行为**：缺参立即报错，不创建任何文件。

**错误信息格式**：
- `[字段 reqId 缺失] 必须传 {域}/{父需求名} 格式。建议: /devops-workflow req create payment/支付渠道重构`
- `[字段 parentReqId {域}/{父需求名}] 父需求已存在。建议: 用 /devops-workflow req show {域}/{父需求名} 查看`
- `[字段 domain {域}] 域不在项目 manifest 声明的模块清单中。建议: 从 {module_root_glob} 目录选择合法域`

**边界情况**：
- 父需求名含特殊字符（空格、`/`）：建议用 `-` 或 `_` 替代；不阻止但提示
- 父需求名重复：即时检查，重名直接报错
- 子需求未创建时：父需求目录为空（仅含 `.task/parent.md`），不算异常

---

### `/devops-workflow req show {域}/{父需求名}`

**用途**：显示父需求详情及其下子需求列表（含状态 + 版本绑定）。

**处理步骤**：
1. **解析参数**：
   - 必传：父需求 ID
   - 缺参 → 报错：`[字段 parentReqId 缺失] 必须传父需求 ID。建议: /devops-workflow req show payment/支付渠道重构`
2. **校验父需求存在**：`docs/discuss/{域}/{父需求名}/.task/parent.md` 必须存在；不存在则报错 `[字段 parentReqId {X}] 父需求不存在。建议: 用 /devops-workflow req list 查看全部父需求`
3. **扫描子需求**：列出 `docs/discuss/{域}/{父需求名}/.task/{子需求名}/metadata.md` 全部文件
4. **解析每个 metadata.md**：读取 `subReqId / currentStage / currentState / versionBinding` 4 个字段
5. **输出格式**：
   ```
   父需求详情  payment/支付渠道重构

     创建时间: 2026-07-06 10:30
     子需求数: 3

     子需求清单:
       payment/支付渠道重构#alipay   阶段 4/5 (DEVELOPING)   绑定: v1.0
       payment/支付渠道重构#wechat   阶段 2/5 (ANALYZING)    绑定: v1.0
       payment/支付渠道重构#refund   阶段 1/5 (DISCUSSING)   绑定: -
   ```

**缺参行为**：缺参立即报错。

**错误信息格式**：
- `[字段 parentReqId 缺失] 必须传父需求 ID。建议: /devops-workflow req show payment/支付渠道重构`
- `[字段 parentReqId {X}] 父需求不存在。建议: 用 /devops-workflow req list 查看`

**边界情况**：
- 父需求下无任何子需求：显示"子需求数: 0" + 提示"用 /devops-workflow req split 创建子需求"
- 子需求 metadata.md 损坏（缺关键字段）：显示"⚠️ metadata.md 字段缺失"，但不影响其他子需求展示

---

### `/devops-workflow req list`

**用途**：列出所有父需求及其进度摘要。

**处理步骤**：
1. **无参数**
2. **扫描** `docs/discuss/*/*/.task/parent.md` 全部文件
3. **聚合**：每个父需求计算 子需求总数 / 已绑定版本数 / 平均阶段进度
4. **输出格式**：
   ```
   父需求清单

     payment/支付渠道重构       3 子需求 / 2 已绑定版本 / 平均阶段 3.5
     order/订单取消优化         2 子需求 / 0 已绑定版本 / 平均阶段 1.0
   ```

**缺参行为**：无参数命令，不存在缺参。

**边界情况**：
- 无任何父需求：显示"无父需求。建议: /devops-workflow req create {域}/{父需求名} 创建第一个父需求"
- 部分 metadata.md 字段损坏：用最简信息展示，不阻塞其他父需求

---

### `/devops-workflow req split {域}/{父需求名}`

**用途**：交互式向导逐个创建子需求。向导中途支持 Ctrl+C 退出（AC17/D20）。

**处理步骤**：
1. **解析参数**：
   - 必传：父需求 ID
   - 缺参 → 报错：`[字段 parentReqId 缺失] 必须传父需求 ID。建议: /devops-workflow req split payment/支付渠道重构`
2. **校验父需求存在**：同 `req show`
3. **扫描现有子需求**：列出 `docs/discuss/{域}/{父需求名}/.task/` 下已存在的子需求名（用于向导重名检查）
4. **启动交互式向导**（循环询问，直到用户输入 `done` 或 Ctrl+C 退出）：
   ```
   === 子需求创建向导 ===
   父需求: payment/支付渠道重构
   现有子需求: alipay, wechat

   输入新子需求名（或输入 done 完成 / Ctrl+C 中途退出）:
   > refund
   子需求 refund 的描述（1-2 句话）:
   > 处理支付渠道退款逻辑
   子需求 refund 影响的模块（逗号分隔）:
   > payment, order

   [确认创建子需求 refund？] (y/n/cancel)
   > y
   ✓ 已创建 docs/discuss/payment/支付渠道重构/.task/refund/metadata.md

   输入新子需求名（或 done 完成）:
   > done
   === 向导结束：创建了 1 个子需求 ===
   ```
5. **每个子需求创建流程**：
   a. 输入子需求名 → 重名检查（同父需求下不能重复）
   b. 输入子需求描述（非空）
   c. 输入模块影响（可空）
   d. 确认创建（y/n/cancel）
   e. 创建目录 `docs/discuss/{域}/{父需求名}/.task/{子需求名}/`
   f. 写入 metadata.md（8 字段模板，详见 `templates.md`）
6. **Ctrl+C 处理**：保存已完成创建的子需求到临时清单 `docs/discuss/{域}/{父需求名}/.task/.split-progress`，下次执行 `req split` 时提示"检测到上次未完成的向导，是否继续？(y/n)"，用户选择继续则从断点恢复
7. **回显**：总结创建的子需求数 + 提示用户下一步用 `/devops-workflow version create {版本号}` 绑定子需求

**缺参行为**：缺父需求 ID 立即报错。

**错误信息格式**：
- `[字段 parentReqId 缺失] 必须传父需求 ID。建议: /devops-workflow req split payment/支付渠道重构`
- `[字段 subReqName {X}] 子需求名与现有子需求 {Y} 冲突。建议: 选择其他名称`
- `[字段 description 缺失] 描述不能为空。建议: 填写 1-2 句话描述`

**边界情况**：
- 向导中途 Ctrl+C：已完成创建的子需求保留，未创建的不创建；记录断点到 `.split-progress`
- 子需求名含特殊字符（含 `#`、`/`、`\`）：禁止，建议用 `-` 或 `_` 替代
- 父需求阶段 1 未完成（讨论文档缺失）：不阻止 `req split`（`req split` 在任何阶段都可执行）

---

## §B. `version` 命令族（8 个）

> **所有 version 修改类命令通用前置**：执行任何修改类操作前，必须读取版本文件并检查 `status == ARCHIVED`，若 ARCHIVED 立即报错 `[字段 versionStatus ARCHIVED] 版本已永久封存，禁止修改。建议: 版本无修改需求，无需操作`（AC20/D23）

### `/devops-workflow version create {版本号}`

**用途**：交互式创建版本，按 4 步流程固定执行（AC13/D16）。

**处理步骤（4 步）**：

**步骤 1：建空 DRAFT 文件**
1. 解析版本号（必传，缺参报错）
2. 校验版本号未存在：`docs/version/{版本号}` 不存在；存在则报错 `[字段 versionNumber {X}] 版本号已存在。建议: 选择其他版本号或用 /devops-workflow version show {X} 查看`
3. 创建版本文件 `docs/version/{版本号}`，写入 9 字段初始值（详见 `templates.md` §2）

**步骤 2：扫描未绑定子需求**
1. 全局扫描 `docs/discuss/*/*/.task/*/metadata.md`
2. 过滤条件：`metadata.md.versionBinding` 为空（未绑定任何版本）
3. 输出候选清单（含完整 ID + 所属父需求 + 当前状态）

**步骤 3：交互多选**
```
=== version create 向导 ===
当前版本: v1.0 (DRAFT)

未绑定子需求候选（输入编号多选，逗号分隔；输入 done 完成；输入 cancel 退出）:
  [1] payment/支付渠道重构#alipay    (DISCUSSING)
  [2] payment/支付渠道重构#wechat    (DISCUSSING)
  [3] order/订单取消优化#子需求1     (ANALYZING)

选择子需求编号（逗号分隔）:
> 1,2
[确认纳入 2 个子需求？] (y/n/cancel)
> y
✓ 选中: payment/支付渠道重构#alipay, payment/支付渠道重构#wechat
```

**步骤 4：回写 metadata.md.versionBinding**
1. 对每个选中的子需求：
   a. 读 `docs/discuss/{域}/{父需求名}/.task/{子需求名}/metadata.md`
   b. **冲突检查**（AC6 + Appendix A）：若 `versionBinding` 字段非空 → 报错 `[字段 subReqId {X}] 已绑定版本 {Y}，不可重复绑定。建议: 先 /devops-workflow version show {Y}，或选择其他未绑定子需求`
   c. 回写 `versionBinding: {版本号}` + 更新 `updatedAt: {当前ISO8601}`
   d. **类型校验**：回写时确保 `versionBinding` 是单值字符串，不是数组（AC6）
2. 更新 `docs/version/{版本号}` 的 `subRequirements` 字段为完整 ID 数组

**缺参行为**：缺版本号立即报错。

**错误信息格式**：
- `[字段 versionNumber 缺失] 必须传版本号。建议: /devops-workflow version create v1.0`
- `[字段 versionNumber {X}] 版本号已存在。建议: /devops-workflow version show {X} 查看`
- `[字段 subReqId {X}] 已绑定版本 {Y}，不可重复绑定。建议: 选择其他未绑定子需求`
- `[字段 candidateList 无未绑定子需求] 候选清单为空。建议: 先 /devops-workflow req split 创建子需求`

**边界情况**：
- 候选为空（无可绑定子需求）：仍允许建空 DRAFT 版本（subRequirements 为空数组），提示"已创建空 DRAFT 版本"
- Ctrl+C 中途退出：版本文件保留（即使空），不删除；下次执行 `version create {同版本号}` 会报"版本号已存在"，提示用 `version show` 查看
- 版本号格式（`v1.0` / `2024Q1` / `v1.0-rc1`）：任何非空字符串均合法，不做 SemVer 校验
- 多选时全部 `cancel`：不写回任何 metadata.md，提示"已取消，版本保留为 DRAFT 空版本"

---

### `/devops-workflow version show {版本号}`

**用途**：显示版本详情（含子需求列表 + 阶段记录 + 状态机位置）。

**处理步骤**：
1. 解析版本号（缺参报错）
2. 校验 `docs/version/{版本号}` 存在；不存在则报错
3. 解析 9 字段
4. **实时聚合子需求状态**：从各 metadata.md 读取 `currentState`，不缓存到版本文件（spec C2/D3）
5. **输出格式**：
   ```
   版本详情  v1.0

     状态: IN_PROGRESS
     创建时间: 2026-07-06 10:30
     发布时间: （未发布）
     归档时间: （未归档）
     描述: 2026 Q3 发布批次

     子需求清单（2 个，实时聚合自 metadata.md）:
       payment/支付渠道重构#alipay   当前状态: DEVELOPING
       payment/支付渠道重构#wechat   当前状态: ANALYZING

     阶段记录:
       2026-07-06 10:30  创建 (DRAFT)
       2026-07-06 11:00  start (DRAFT → IN_PROGRESS)
   ```

**缺参行为**：缺版本号立即报错。

**错误信息格式**：
- `[字段 versionNumber 缺失] 必须传版本号。建议: /devops-workflow version show v1.0`
- `[字段 versionNumber {X}] 版本不存在。建议: /devops-workflow version list 查看全部版本`

**边界情况**：
- 版本含 0 个子需求：显示"子需求清单（0 个）"，状态机不可推进
- 子需求 metadata.md 损坏：标注"⚠️ metadata 损坏"，不阻塞其他子需求展示

---

### `/devops-workflow version list`

**用途**：列出所有版本及其状态。

**处理步骤**：
1. 无参数
2. 扫描 `docs/version/*` 全部文件
3. 解析每个版本的 `versionNumber / status / subRequirements.length / createdAt`
4. **输出格式**：
   ```
   版本清单

     v1.0     IN_PROGRESS   2 子需求   2026-07-06 10:30
     v1.1     DRAFT         0 子需求   2026-07-05 14:20
     v2.0     ARCHIVED      5 子需求   2026-05-01 09:00
   ```

**缺参行为**：无参数命令。

**边界情况**：
- 无任何版本：显示"无版本。建议: /devops-workflow version create {版本号} 创建"

---

### `/devops-workflow version add-sub {版本号} {子需求ID}`

**用途**：向已存在的 DRAFT 版本增量加入子需求（D16 补充）。

**处理步骤**：
1. **解析参数**：
   - 必传：版本号 + 子需求 ID
   - 缺任一参 → 报错
2. **校验版本存在**：同 `version show`
3. **前置校验 1 — 状态门**：读版本 `status` 字段
   - 必须是 `DRAFT`，其他状态报错：`[字段 versionStatus {currentStatus} 当前状态不符] 只能在 DRAFT 状态添加子需求。建议: 版本已锁定，不可修改`
4. **前置校验 2 — ARCHIVED 只读**：若 `status == ARCHIVED` → 报错（AC20）
5. **校验子需求存在**：`metadata.md` 必须存在；不存在报错
6. **冲突检查（AC6）**：读子需求 `versionBinding` 字段
   - 若已绑定 → 报错：`[字段 subReqId {X}] 已绑定版本 {Y}。建议: 先解除绑定（当前版本不支持解绑，需新建版本）`
7. **回写**：
   a. 子需求 `metadata.md`：写入 `versionBinding: {版本号}` + 更新 `updatedAt`
   b. 版本文件 `docs/version/{版本号}`：追加到 `subRequirements` 数组 + 更新 `stageRecord`
8. **回显**：列出新增子需求 + 当前 subRequirements 总数

**缺参行为**：
- 缺版本号 → `[字段 versionNumber 缺失] 必须传版本号。建议: /devops-workflow version add-sub v1.0 payment/支付渠道重构#alipay`
- 缺子需求 ID → `[字段 subReqId 缺失] 必须传子需求 ID。建议: /devops-workflow version add-sub v1.0 payment/支付渠道重构#alipay`

**错误信息格式**：
- `[字段 versionStatus {currentStatus} 当前状态不符] 只能在 DRAFT 状态添加子需求。建议: 版本已锁定，不可修改`
- `[字段 subReqId {X}] 已绑定版本 {Y}。建议: 先解除绑定`
- `[字段 versionStatus ARCHIVED] 版本已永久封存，禁止修改`

**边界情况**：
- 子需求 ID 格式错（缺 `#`）：报错 `[字段 subReqId 缺失 #] 格式非法，必须含 #。建议: payment/支付渠道重构#alipay`
- 子需求 ID 含多个 `#`：按最后一个 `#` 拆分（Appendix A）

---

### `/devops-workflow version start {版本号}`

**用途**：DRAFT → IN_PROGRESS（AC14）。

**处理步骤**：
1. 解析版本号（缺参报错）
2. **前置校验 0 — ARCHIVED 只读**（AC20）
3. **前置校验 1 — 当前状态**：读 `status` 字段
   - 必须是 `DRAFT`，其他状态报错：
     - `IN_PROGRESS` → `[字段 versionStatus IN_PROGRESS 当前状态已启动] 版本已在 IN_PROGRESS。建议: /devops-workflow version show {X} 查看进度`
     - `READY` → `[字段 versionStatus READY 当前状态已就绪] 版本已到 READY，无法再 start。建议: 用 /devops-workflow version ready {X} 进入下一阶段`
     - `RELEASED` → `[字段 versionStatus RELEASED 当前状态已发布] 版本已发布，无法 start。建议: /devops-workflow version archive {X} 归档后建新版本`
     - `ARCHIVED` → `[字段 versionStatus ARCHIVED] 版本已永久封存`
4. **前置校验 2 — 子需求数**：必须 ≥ 1 个子需求
   - 为空 → 报错：`[字段 subRequirements 空] 版本无子需求，无法启动。建议: /devops-workflow version add-sub {X} {子需求ID} 添加子需求`
5. **前置校验 3 — 子需求状态**：检查所有子需求 `currentState`
   - 至少 1 个子需求 ∈ {ANALYZING, PENDING_DESIGN_REVIEW, DEVELOPING, PENDING_PLAN_REVIEW, PENDING_CR_REVIEW, REVIEWING}
   - 全是 `DISCUSSING` 或 `COMPLETED` → 报错：`[字段 subReqState 未进入执行阶段] 所有子需求都未进入执行阶段。建议: 用 /devops-workflow next {子需求ID} 推进子需求`
6. **状态转换**：写 `status: IN_PROGRESS` 到版本文件 + 追加 `stageRecord` 时间戳
7. **回显**：版本新状态 + 列出当前子需求进度

**缺参行为**：`[字段 versionNumber 缺失] 必须传版本号。建议: /devops-workflow version start v1.0`

**错误信息格式**：
- `[字段 subRequirements 空] 版本无子需求，无法启动。建议: /devops-workflow version add-sub {X} {子需求ID}`
- `[字段 subReqState 未进入执行阶段] 所有子需求都未进入执行阶段。建议: 用 /devops-workflow next {子需求ID} 推进子需求`

**边界情况**：
- ARCHIVED 版本触发：通用前置立即报错，不进入具体校验

---

### `/devops-workflow version ready {版本号}`

**用途**：IN_PROGRESS → READY（AC14）。要求所有子需求都 COMPLETED。

**处理步骤**：
1. 解析版本号（缺参报错）
2. **前置校验 0 — ARCHIVED 只读**
3. **前置校验 1 — 当前状态**：
   - 必须是 `IN_PROGRESS`，其他状态报错：
     - `DRAFT` → `[字段 versionStatus DRAFT 当前状态未启动] 版本未启动。建议: /devops-workflow version start {X} 先启动`
     - `READY` → `[字段 versionStatus READY 当前状态已 READY] 版本已 READY。建议: 用 /devops-workflow version close {X} 发布`
     - `RELEASED` → `[字段 versionStatus RELEASED 当前状态已发布] 版本已发布`
     - `ARCHIVED` → `[字段 versionStatus ARCHIVED] 版本已永久封存`
4. **前置校验 2 — 子需求状态**：所有子需求 `currentState == COMPLETED`
   - 任一子需求非 COMPLETED → 报错：
     ```
     [字段 subReqState 未全部完成] 存在未完成的子需求:
       - payment/支付渠道重构#alipay 当前状态: DEVELOPING
       - order/订单取消优化#子1 当前状态: ANALYZING
     建议: 用 /devops-workflow next {子需求ID} 推进到 COMPLETED，或 /devops-workflow rework {子需求ID} 返工
     ```
5. **状态转换**：写 `status: READY` + 追加 `stageRecord`
6. **回显**：版本新状态 + 提示下一步用 `version close`

**缺参行为**：`[字段 versionNumber 缺失] 必须传版本号。建议: /devops-workflow version ready v1.0`

**错误信息格式**：
- `[字段 subReqState 未全部完成] 存在未完成的子需求: {清单}。建议: /devops-workflow next {子需求ID} 或 /devops-workflow rework {子需求ID}`

**边界情况**：
- 子需求状态含 `DISCUSSING`：算未完成，必须先推进
- 子需求状态含错误字符串（非合法 8 态）：报错 `[字段 subReqState {X}] 状态非法。建议: 用 /devops-workflow req show {父需求ID} 检查子需求 metadata.md`

---

### `/devops-workflow version close {版本号}`

**用途**：READY → RELEASED（AC14）。发布版本，写发布时间戳。

**处理步骤**：
1. 解析版本号（缺参报错）
2. **前置校验 0 — ARCHIVED 只读**
3. **前置校验 1 — 当前状态**：
   - 必须是 `READY`，其他状态报错：
     - `DRAFT` → `[字段 versionStatus DRAFT 当前状态未启动] 版本未启动。建议: /devops-workflow version start {X}`
     - `IN_PROGRESS` → `[字段 versionStatus IN_PROGRESS 当前子需求未全部完成] 子需求未全部完成。建议: 用 /devops-workflow next {子需求ID} 推进或 /devops-workflow version ready {X} 进入 READY`
     - `RELEASED` → `[字段 versionStatus RELEASED 当前状态已发布] 版本已发布。建议: /devops-workflow version archive {X} 归档`
     - `ARCHIVED` → `[字段 versionStatus ARCHIVED] 版本已永久封存`
4. **二次确认**（破坏性操作）：提示用户"即将发布版本 {X}，所有子需求标记为正式交付。确认？(y/n)"
5. **状态转换**：
   - 写 `status: RELEASED`
   - 写 `releasedAt: {当前ISO8601}`
   - 追加 `stageRecord`
6. **回显**：版本新状态 + 发布时间 + 提示"版本发布后禁止 rework"

**缺参行为**：`[字段 versionNumber 缺失] 必须传版本号。建议: /devops-workflow version close v1.0`

**错误信息格式**：
- `[字段 versionStatus {current} 状态不符] close 需要 READY。建议: /devops-workflow version ready {X}`

**边界情况**：
- ARCHIVED 触发：通用前置报错，不进入具体校验

---

### `/devops-workflow version archive {版本号}`

**用途**：RELEASED → ARCHIVED（AC14 + AC20）。永久封存，不可恢复。

**处理步骤**：
1. 解析版本号（缺参报错）
2. **前置校验 0 — ARCHIVED 只读**：若 `status == ARCHIVED` → **直接报错并停止**：
   ```
   [字段 versionStatus ARCHIVED 不可重复归档] 版本已归档，不可重复归档。建议: ARCHIVED 是状态机终点，无修改入口
   ```
   （不再继续后续检查，避免死循环）
3. **前置校验 1 — 当前状态**：
   - 必须是 `RELEASED`，其他状态报错：
     - `DRAFT` → `[字段 versionStatus DRAFT 当前状态未发布] 版本未发布，无法归档。建议: 先 /devops-workflow version start → ready → close`
     - `IN_PROGRESS` → `[字段 versionStatus IN_PROGRESS 当前状态未发布] 版本未发布`
     - `READY` → `[字段 versionStatus READY 当前状态未发布] 版本未发布，建议先 /devops-workflow version close {X}`
4. **二次确认**（破坏性 + 不可逆）：提示"即将归档版本 {X}，归档后永久只读，禁止任何修改。确认？(y/n)"
5. **状态转换**：
   - 写 `status: ARCHIVED`
   - 写 `archivedAt: {当前ISO8601}`
   - 追加 `stageRecord`
6. **回显**：版本新状态 + 归档时间 + 强警告"ARCHIVED 不可逆"

**缺参行为**：`[字段 versionNumber 缺失] 必须传版本号。建议: /devops-workflow version archive v1.0`

**错误信息格式**：
- `[字段 versionStatus ARCHIVED 不可重复归档] 版本已归档，不可重复归档。建议: ARCHIVED 是状态机终点`
- `[字段 versionStatus {current} 状态不符] archive 需要 RELEASED。建议: 先 /devops-workflow version close {X}`

**边界情况**：
- 已 ARCHIVED 版本触发：步骤 2 直接报错，不进入步骤 3（避免后续校验逻辑误触）
- ARCHIVED 后所有修改类命令：通用前置规则拦截，统一报错"版本已永久封存"

---

## §C. 保留命令（7 个）

> 所有保留命令缺参时统一行为：报错 + 扫描 `docs/discuss/` 与 `docs/version/` 列出可选项（AC16/D19）。
>
> **第 6、7 条说明**：`summary --merge` 是 `summary` 的 `--merge` 选项触发形式（同一条命令的两种调用形态），并非独立命令族；`discovery refresh` 是独立命令，但作用域为会话内存缓存，无产物文件。

### `/devops-workflow next {子需求ID}`

**用途**：推进指定子需求到下一阶段。替代 v1 缺省活动指针的隐式行为。

**处理步骤**：
1. **解析子需求 ID**：
   - 缺参 → 报错：
     ```
     [字段 subReqId 缺失] 必须传子需求ID。建议: 格式 {域}/{父需求名}#{子需求名}

     当前可推进的子需求（扫描自 metadata.md，currentState ≠ COMPLETED）:
       - payment/支付渠道重构#alipay    当前状态: DEVELOPING
       - order/订单取消优化#子1        当前状态: ANALYZING

     用法: /devops-workflow next {子需求ID}
     ```
2. **校验子需求存在**：`metadata.md` 必须存在；不存在则报错 `[字段 subReqId {X}] 子需求不存在`
3. **校验版本绑定**：读 `metadata.md.versionBinding`
   - 为空 → 报错：`[字段 versionBinding 空] 子需求 {X} 未绑定版本，无法推进。建议: 用 /devops-workflow version add-sub {V} {X} 绑定后重试`
   - 绑定的版本 → 读版本 `status`：
     - `ARCHIVED` → 报错 `[字段 versionStatus ARCHIVED] 版本已永久封存，禁止推进子需求`
     - `DRAFT` → 报错 `[字段 versionStatus DRAFT 当前版本未启动] 子需求不能推进。建议: /devops-workflow version start {V}`
     - `RELEASED` 或 `ARCHIVED` → 禁止任何修改类操作
4. **状态分发**：根据 `metadata.md.currentState` 分发到对应阶段执行逻辑
   - `DISCUSSING` → 阶段 1（仅当父需求下所有子需求都是 DISCUSSING 时触发父需求讨论）
   - `ANALYZING` → 阶段 2（设计）
   - `PENDING_DESIGN_REVIEW` → 提示用户先 `/devops-workflow approve`（不重复执行）
   - `DEVELOPING` → 阶段 4（任务闭环）
   - `PENDING_PLAN_REVIEW` / `PENDING_CR_REVIEW` → 提示用户先 `approve`
   - `REVIEWING` → 阶段 5（验收）
   - `COMPLETED` → 提示"子需求已完成，无需推进"
5. **阶段执行**：调用 `stage-{2..5}-*.md` 描述的处理步骤（详见各 stage 文件）
6. **状态回写**：写 `metadata.md.currentState` + `currentStage` + `updatedAt` + `阶段产物引用`
7. **回显**：新状态 + 阶段进度 + 提示下一步操作

**缺参行为**：报错 + 列出全部可推进子需求（AC16）。

**错误信息格式**：
- `[字段 subReqId 缺失] 必须传子需求ID。建议: /devops-workflow next {域}/{父需求名}#{子需求名}`
- `[字段 subReqId {X}] 子需求不存在。建议: 用 /devops-workflow req show {父需求ID} 查看`
- `[字段 versionBinding 空] 子需求 {X} 未绑定版本，无法推进。建议: /devops-workflow version add-sub {V} {X}`
- `[字段 versionStatus DRAFT 当前版本未启动] 子需求不能推进。建议: /devops-workflow version start {V}`

**边界情况**：
- 多个子需求处于同一状态：缺参时全部列出，不自动选中
- 子需求处于审核门（`*_REVIEW`）：不推进，提示先 `approve`
- 子需求状态机非法字符串：报错 `[字段 currentState {X}] 状态非法`

---

### `/devops-workflow approve {子需求ID}`

**用途**：确认子需求当前的人工检查点。

**处理步骤**：
1. **解析子需求 ID**：
   - 缺参 → 报错：
     ```
     [字段 subReqId 缺失] 必须传子需求ID。建议: 显式传子需求ID

     当前待审核的子需求（currentState 含 REVIEW）:
       - payment/支付渠道重构#alipay    当前状态: PENDING_DESIGN_REVIEW
       - payment/支付渠道重构#wechat    当前状态: PENDING_CR_REVIEW

     用法: /devops-workflow approve {子需求ID}
     ```
2. **校验子需求存在**
3. **校验版本绑定**：同 `next`
4. **状态分发**：根据 `currentState` 分发到对应审核门
   - `PENDING_DESIGN_REVIEW` → 阶段 3 设计审核（详见 stage-3-review.md §A）
   - `PENDING_PLAN_REVIEW` → 阶段 4 任务 plan 确认（详见 stage-4-dev.md）
   - `PENDING_CR_REVIEW` → 阶段 4 CR 问题裁决（详见 stage-4-dev.md）
5. **审核执行**：详见各 stage 文件
6. **状态回写**：审核通过 → 推进到下一状态；审核打回 → 状态回退到对应阶段

**缺参行为**：报错 + 列出全部待审核子需求（AC16）。

**错误信息格式**：
- `[字段 subReqId 缺失] 必须传子需求ID。建议: /devops-workflow approve {域}/{父需求名}#{子需求名}`
- `[字段 subReqId {X} 不在审核门状态] 子需求不在审核门状态（currentState 不含 REVIEW）。建议: 用 /devops-workflow next {X} 推进到审核门`

**边界情况**：
- 子需求非审核门状态：报错并提示当前状态
- ARCHIVED 版本下子需求：通用前置拦截

---

### `/devops-workflow status [子需求ID|版本号]`

**用途**：显示进度（子需求或版本）。缺参时汇总所有进行中的子需求与版本。

**处理步骤**：
1. **解析参数类型**：
   - 不传参 → 扫描模式：扫描 `docs/discuss/*/*/.task/*/metadata.md` + `docs/version/*`，列出全部进行中（currentState ≠ COMPLETED 且 versionBinding ≠ 空）的子需求 + 全部非 ARCHIVED 的版本
   - 传子需求 ID（含 `#`）→ 子需求详情模式：显示该子需求 metadata.md 全部字段 + 阶段记录
   - 传版本号 → 版本详情模式：同 `version show`
2. **校验目标存在**：不存在则报错
3. **校验版本绑定**（子需求模式）：未绑定则显示提示"子需求未绑定版本"
4. **输出格式**（子需求详情模式）：
   ```
   子需求详情  payment/支付渠道重构#alipay

     父需求: payment/支付渠道重构
     版本绑定: v1.0
     当前阶段: 4/5 — 开发与逐任务审查
     当前状态: DEVELOPING
     创建时间: 2026-07-06 10:30
     更新时间: 2026-07-06 14:20

     阶段产物引用:
       阶段 1: docs/discuss/payment/支付渠道重构/.task/alipay/analysis/...
       阶段 2: docs/discuss/payment/支付渠道重构/.task/alipay/design-consensus.md
       阶段 3: （暂无）
   ```

**缺参行为**：扫描 + 列出全部可选项（AC16）。

**错误信息格式**：
- `[字段 subReqId {X}] 子需求不存在。建议: 用 /devops-workflow req list 查看`
- `[字段 versionNumber {X}] 版本不存在。建议: 用 /devops-workflow version list 查看`

**边界情况**：
- 目标含 ARCHIVED 版本：仍可显示（只读），但显示"⚠️ ARCHIVED 只读"
- 扫描模式无任何目标：显示"无进行中子需求或版本。建议: /devops-workflow req create 创建父需求"

---

### `/devops-workflow rework {子需求ID}`

**用途**：子需求从 COMPLETED 回退到 ANALYZING。**强门禁：版本状态必须 ∈ {DRAFT, IN_PROGRESS, READY}**（D22/AC19）。

**处理步骤**：
1. **解析子需求 ID**：
   - 缺参 → 报错：
     ```
     [字段 subReqId 缺失] 必须传子需求ID。建议: 显式传子需求ID

     当前可 rework 的子需求（currentState = COMPLETED 且版本未封存）:
       - payment/支付渠道重构#alipay    当前状态: COMPLETED, 版本: v1.0 (IN_PROGRESS)

     用法: /devops-workflow rework {子需求ID}
     ```
2. **校验子需求存在**
3. **校验子需求状态**：`currentState == COMPLETED`
   - 非 COMPLETED → 报错：`[字段 currentState {X} 非 COMPLETED 状态] rework 要求 COMPLETED 状态。建议: 用 /devops-workflow next {X} 推进到 COMPLETED 后再 rework`
4. **强门禁 — 版本状态校验**（AC19/D22）：
   - 读 `metadata.md.versionBinding` → 读版本 `status`
   - **DRAFT / IN_PROGRESS / READY** → 通过门禁，继续步骤 5
   - **RELEASED** → 报错：`[字段 versionStatus RELEASED 当前版本已发布] 不允许 rework。建议: 如需修复请新建子需求并 /devops-workflow version add-sub 加入新版本`
   - **ARCHIVED** → 报错：`[字段 versionStatus ARCHIVED] 版本已永久封存，禁止 rework`
5. **执行 rework**：详见 `rework.md`，含返工单路径 `docs/discuss/{域}/{父需求名}/.task/{子需求名}/rework/R{n}-{原因}.md`
6. **状态回写**：
   - `currentState: COMPLETED → ANALYZING`
   - `currentStage: 5 → 2`
   - 更新 `updatedAt`
   - 追加返工单引用到 `阶段产物引用`

**缺参行为**：报错 + 列出可 rework 的子需求（AC16）。

**错误信息格式**：
- `[字段 subReqId 缺失] 必须传子需求ID。建议: /devops-workflow rework {域}/{父需求名}#{子需求名}`
- `[字段 currentState {X} 非 COMPLETED 状态] rework 要求 COMPLETED 状态。建议: 用 /devops-workflow next {X} 推进到 COMPLETED 后再 rework`
- `[字段 versionStatus RELEASED 当前版本已发布] 不允许 rework。建议: 新建子需求 + 新版本`
- `[字段 versionStatus ARCHIVED] 版本已永久封存，禁止 rework`

**边界情况**：
- 子需求已 rework 过：允许再次 rework，每次返工独立编号（R{n} 单调递增）
- 版本 DRAFT 状态下子需求 COMPLETED：理论上不应存在（DRAFT 阶段子需求应未启动），若出现则报错提示用户检查 metadata.md

---

### `/devops-workflow summary {版本号}`

**用途**：按版本聚合 DDL / Job·MQ / API 清单（AC9）。替代 v1 按需求聚合的旧行为。

**处理步骤**：
1. **解析版本号**：
   - 缺参 → 报错：
     ```
     [字段 versionNumber 缺失] 必须传版本号。建议: 显式传版本号

     可汇总的版本（含子需求）:
       - v1.0 (IN_PROGRESS)  2 子需求
       - v1.1 (DRAFT)         0 子需求

     用法: /devops-workflow summary {版本号}
     ```
2. **校验版本存在**：`docs/version/{版本号}` 必须存在
3. **读 subRequirements 数组**：从版本文件读子需求列表（完整 ID）
4. **逐子需求聚合**：对每个子需求，扫描 `docs/discuss/{域}/{父需求名}/.task/{子需求名}/` 下的阶段产物
   - 阶段 2 产物：`analysis/` 目录的 DDL 文件
   - 阶段 4 产物：`plans/` 目录的 Job·MQ 任务清单 + `done/` 目录的 API 实现记录
   - 阶段 5 产物：`acceptance.md` 中确认的 API 接口清单
5. **输出格式**：
   ```
   版本交付清单  v1.0

     状态: IN_PROGRESS
     子需求数: 2
     发布窗口: 待发布

     === 子需求 1: payment/支付渠道重构#alipay ===
     DDL:
       - ALTER TABLE payment_order ADD COLUMN alipay_trade_no VARCHAR(64);
       - CREATE INDEX idx_alipay_trade_no ON payment_order(alipay_trade_no);

     Job·MQ:
       - 异步任务 AlipayRefundJob（路径见模块目录）

     API:
       - POST /api/payment/alipay/refund（路径见模块目录）

     === 子需求 2: payment/支付渠道重构#wechat ===
     DDL: （暂无）
     Job·MQ: （暂无）
     API: （暂无）
   ```
6. **回显**：提示用户把清单交给 DBA / 前端

**缺参行为**：报错 + 列出可汇总的版本（AC16）。

**错误信息格式**：
- `[字段 versionNumber 缺失] 必须传版本号。建议: /devops-workflow summary v1.0`
- `[字段 versionNumber {X}] 版本不存在。建议: 用 /devops-workflow version list 查看`

**边界情况**：
- 版本含 0 个子需求：显示"版本无子需求，聚合清单为空"
- 子需求阶段产物缺失：相应分类显示"（暂无）"，不阻塞其他子需求
- ARCHIVED 版本：仍可读聚合清单（只读）

---

### `/devops-workflow summary --merge {版本号A} {版本号B} ...`

**用途**：多版本合并清单（AC9 补充）。把多个已生成的 change-manifest.md 拼成一份合并视图，写入 `docs/version/.merged/`，避免重复扫描 dev-tasks.md。仅在用户显式传 `--merge` 时启用。

**处理步骤**：
1. **解析参数**：
   - 必须同时检测到 `--merge` 选项 + 至少 1 个版本号
   - 缺 `--merge` 标志 → 走 §C summary 子节（无 flag）
   - 缺版本号 → 报错：
     ```
     [字段 commandArgs 缺失] --merge 后必须传至少 1 个版本号。建议: 用 /devops-workflow version list 查可用版本
     ```
2. **校验所有版本 change-manifest.md 存在**：
   - 读 `docs/version/{V1}.change-manifest.md`、`docs/version/{V2}.change-manifest.md`...
   - 任一不存在 → 报错：`[字段 mergeInput {V}] change-manifest.md 不存在。建议: 先对该版本执行 /devops-workflow summary {V} 生成清单`
3. **校验所有版本 status == RELEASED**：
   - 任一不是 RELEASED → 报错：`[字段 versionStatus {V} 当前状态不符} --merge 要求全部 RELEASED。建议: 先用 /devops-workflow version close {V} 完成发布`
4. **拼接三块**：
   - 对每个版本依次读 change-manifest.md 的 DDL / 队列 / API 三段
   - 每行数据末尾追加 `(来源: {版本号} / {子需求ID})` 标注
   - **不重新读** dev-tasks.md（避免重复劳动）
5. **版本头改为多版本汇总表**：
   ```
   # 多版本合并清单 {日期}
   合并范围: {V1}, {V2}, {V3}（{N} 个版本 / {M} 个子需求）
   生成时间: {ISO 8601}
   ```
6. **落盘**：写 `docs/version/.merged/change-manifest-{YYYY-MM-DD}.md`（**不覆盖任何单版本清单，避免污染**）

**缺参行为**：
- `--merge` 后不传版本号 → 报错 + 扫描 `docs/version/` 下所有 `change-manifest.md` 列出已存在的版本清单
- 同时传 `--merge` 与 `{版本号}` → 报错：`[字段 commandArgs 冲突] --merge 与单版本 summary 互斥。建议: 二选一执行`

**错误信息格式**：
- `[字段 commandArgs 缺失] --merge 后必须传至少 1 个版本号。建议: 用 /devops-workflow version list 查可用版本`
- `[字段 mergeInput {V}] change-manifest.md 不存在。建议: 先 /devops-workflow summary {V} 生成`
- `[字段 versionStatus {V} {currentStatus}] --merge 要求全部 RELEASED。建议: 先 /devops-workflow version close {V} 发布`

**边界情况**：
- 1 个版本 `--merge`：仍然走合并清单流程，落地 `.merged/` 而非单版本路径（行为等价于"无合并意义但用户显式要求"，提示用户"如不要合并请去掉 --merge"）
- 版本不在跨域路径（误走单域路径生成的 `docs/discuss/{域}/{父}/.task/.versions/{V}/change-manifest.md`）：扫描两个位置都查，照常合并
- README.md 13 节参考索引同步指向本节

---

### `/devops-workflow discovery refresh`

**用途**：强制重新执行发现流程（AC9 补充 / discovery.md §1-§7）。清空主 Agent 会话内的 DiscoveryContext 缓存，从头解析 `language / test_cmd / lint_cmd / static_analysis_cmd / module_root_glob / contract_type / discovery_cmd` 7 字段。

**处理步骤**：
1. **无参数**：
   - 不接受任何位置参数（不接 `{ID}` / `{版本号}`）
   - 接收到参数 → 报错：`[字段 commandArgs 非法] discovery refresh 不接受参数。建议: 单独执行 /devops-workflow discovery refresh`
2. **清空 §7 缓存**：主 Agent 会话内的 `DiscoveryContext`（不落盘，仅内存对象）
3. **重新执行 §1 全部发现**：按优先级依次读
   - 项目根 manifest 文件（package.json / go.mod / pom.xml / Cargo.toml / pyproject.toml 等）
   - 项目根 `CLAUDE.md` 的 `## {字段}` 段
   - `docs/workflow/{模块}/` 下的模块契约文件（仅 `contract_type` 适用）
4. **冲突硬阻断**：若两份来源对同一字段给出不同值，按 `discovery.md` §5 三段式报错并停下，**不缓存**
5. **缺失硬阻断**：任意必需字段在所有来源都找不到，按 `discovery.md` §4 三段式报错并停下，**不缓存**
6. **成功路径**：写入会话内存 `DiscoveryContext`，输出新字段值给用户
   ```
   发现已刷新（{当前时间 ISO 8601}）：
     language: {L}
     test_cmd: {TC}
     lint_cmd: {LC}
     static_analysis_cmd: {SAC 或 "(空，未纳入 DoD)"}
     module_root_glob: {MRG}
     contract_type: {CT}
     discovery_cmd: {DC 或 "(未声明)"}
   ```

**缺参行为**：本身就是无参命令，不存在缺参。

**错误信息格式**：
- `[字段 commandArgs 非法] discovery refresh 不接受参数 {X}。建议: 单独执行 /devops-workflow discovery refresh`
- `[字段 {X} {当前值}] 冲突: {source1}={value1}, {source2}={value2}。建议: 在 CLAUDE.md 中显式声明 {X}={winning_value}`
- `[字段 {X} 缺失] 未从 manifest / CLAUDE.md / docs/workflow 找到。建议: 在 CLAUDE.md 中声明 ## {X} 段`

**边界情况**：
- 主 Agent 启动未读过任何 manifest：仍按 §1 顺序解析；若 manifest 也不存在则 §4 全部 7 字段缺失硬阻断
- 用户在 `discovery refresh` 中途改动 CLAUDE.md：以上次 mtime 为快照，差异字段重新解析；其他字段沿用缓存
- 自动失效已触发（manifest mtime 变更）：本命令为强制刷新入口，与自动失效触发机制并存

**何时触发**（用户主动）：
- 用户新增模块后需要刷新 `module_root_glob` 匹配
- 用户修改 `CLAUDE.md` 后希望立即生效
- `docs/workflow/` 重新生成后需要重新发现契约
- 缓存出现字段冲突 / missing 错误后人工排查

---

## §E. 错误信息格式规范（通用）

> 所有命令统一使用三段式错误信息：**`[字段 {X} {当前值}] {原因}。建议: {修复}`**（AC18/D21）

**规范要点**：
1. **第一段 `[字段 {X} {当前值}]`**：明确指出错误字段名 + 当前值（如 `versionStatus IN_PROGRESS`）。缺当前值时简写为 `[字段 {X} 缺失]`
2. **第二段 `{原因}`**：简明扼要描述失败原因（动词开头，≤ 30 字）
3. **第三段 `建议: {修复}`**：直接给出可执行的下一步命令或操作

**示例**：
- `[字段 versionNumber v1.0] 版本号已存在。建议: /devops-workflow version show v1.0`
- `[字段 subReqId payment/...#alipay] 已绑定版本 v0.9。建议: 选择其他未绑定子需求`
- `[字段 versionStatus ARCHIVED] 版本已永久封存，禁止修改。建议: 版本无修改需求`
- `[字段 subReqId 缺失] 必须传子需求ID。建议: /devops-workflow next {域}/{父需求名}#{子需求名}`

**禁止写法**：
- ❌ `参数错误`（无字段名）
- ❌ `版本不存在，请检查`（无具体值，无修复命令）
- ❌ `操作失败`（无字段、无原因、无建议）

---

## §F. 命令速查表（19 启用 + 3 删除）

| 命令族 | 命令 | 必传参数 | 主要校验 |
|--------|------|----------|----------|
| `req` | `create` | `{域}/{父需求名}` | 父需求不存在 |
| `req` | `show` | `{域}/{父需求名}` | 父需求存在 |
| `req` | `list` | （无） | 扫描 |
| `req` | `split` | `{域}/{父需求名}` | 父需求存在 + 子需求名重名 |
| `version` | `create` | `{版本号}` | 版本号未存在 + 子需求归属唯一 |
| `version` | `show` | `{版本号}` | 版本存在 |
| `version` | `list` | （无） | 扫描 |
| `version` | `add-sub` | `{版本号} {子需求ID}` | 版本 DRAFT + 子需求未绑定 |
| `version` | `start` | `{版本号}` | DRAFT + ≥1 子需求 + ≥1 子需求已推进 |
| `version` | `ready` | `{版本号}` | IN_PROGRESS + 全部子需求 COMPLETED |
| `version` | `close` | `{版本号}` | READY |
| `version` | `archive` | `{版本号}` | RELEASED |
| 保留 | `next` | `{子需求ID}` | 子需求存在 + 版本已启动 + 非 ARCHIVED |
| 保留 | `approve` | `{子需求ID}` | 子需求在审核门状态 |
| 保留 | `status` | `[子需求ID|版本号]` | 目标存在 |
| 保留 | `rework` | `{子需求ID}` | 子需求 COMPLETED + 版本非 RELEASED/ARCHIVED |
| 保留 | `summary` | `{版本号}` | 版本存在 + ∈ {IN_PROGRESS/READY/RELEASED} |
| 保留 | `summary --merge` | `{版本号A} {版本号B} ...` | 全部版本 change-manifest.md 存在 + 全部 RELEASED |
| 保留 | `discovery refresh` | （无） | 清空 §7 缓存，重跑 §1 发现 |

**计数修正**：
- req：create / show / list / split = **4 个**
- version：create / show / list / add-sub / start / ready / close / archive = **8 个**
- 保留：next / approve / status / rework / summary / `summary --merge` / `discovery refresh` = **7 个**
- **合计启用：4 + 8 + 7 = 19 个**（AC3 修订）
- **删除：use / split / start = 3 个**

> 注：`summary --merge` 计入"保留"族但本质是 `summary` 的 `--merge` 选项触发形态，调用方走同一条 `/devops-workflow summary` 入口，主 Agent 按是否带 `--merge` 分发到 §C summary 或 summary --merge 子节。
