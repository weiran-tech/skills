---
name: devops-openspec-workflow
description: Fast-forward the devops-workflow OpenSpec pipeline (L0-L10) for a change end to end, auto-advancing through every artifact and pausing only at the genuine human gates - unresolved L0 ambiguity, L3 design approval, and L9 final-diff sign-off. Use when the user wants to drive an openspec change from interview to archive without approving every single artifact.
allowed-tools: Bash(openspec:*), Bash(git:*), Bash(node:*), Read, Write, Edit, Grep, Glob, TodoWrite, Skill, AskUserQuestion, EnterWorktree, ExitWorktree
license: MIT
compatibility: Requires the openspec CLI with the devops-workflow schema registered in the target repo's openspec config. Schema-generic; project-specific facts (commands, worktree tooling, rule-ID meanings, historical incidents) are expected to live in the repo's own rules/docs (e.g. this repo's openspec/rules/), not in this file — every "查仓库规则" pointer below means look there.
metadata:
  author: project
  version: "2.0"
---
驱动一个 OpenSpec change 走完**整条** `devops-workflow` 流水线(interview → explore →
proposal → specs → design → tasks → exec-plan → implementation → verify → archive),
一次连续跑完,而不是每个 artifact 都停下来等确认。

本文件描述的是流水线本身——每个 Phase 产出什么,以及三个真正需要人类决策的点。
除了"仓库已注册 `devops-workflow` schema"这一条,本文不对所在仓库做任何假设。
所有仓库特定的事实(L7 具体跑哪些命令、worktree 怎么建、某个 validator rule ID 是什么意思、
历史事故)应该住在仓库自己的规则/文档里——在本仓库,就是 `openspec/rules/enforced/project.md`
(worktree 判据,§二)与 `openspec/rules/advisory/pitfalls.md`(rule-ID 含义与历史事故,
按流水线层索引)。Phase 0 之前先读一遍相关章节,后文每处"查仓库规则"都是去查这两处,
不是让你临场现编。

## 为什么需要这个 skill(改它之前先读这段)

以下三件事对 `devops-workflow` schema 普遍成立,不分仓库——不要想当然地认为不是这样:

1. **`openspec status --json` 的 `ready`/`done` 纯粹是文件存在性判断,不认"是否已批准"。** `design.md` 就算没有 `approved_by` 也照样把 `design` 标成 `done`、把 `tasks` 标成 `ready`。CLI 永远不会替你在 L3/L9 处停下来——必须靠你自己拦。
2. **通用的 `openspec-verify-change` / `openspec-archive-change` skill 和这个 schema 的 artifact 形状对不上。** `openspec-verify-change` 产出的是 Completeness/Correctness/Coherence 报告,不是这个 schema 要求的、带 通过/打回实现/打回设计 判定行的 `exec/verify.md`。`openspec-archive-change` 从不要求最终 diff 审阅,而且用 `mv` + agent 手工合并 spec 代替原生 `openspec archive` CLI——只要实测过就会发现这条路径是有损的(具体证据见仓库规则,例如本仓库 `openspec/project.json` 的 `capabilities.knownArchiveDrift` 注释)。**本 skill 完全不用这两个**:自己生成 `verify`(Phase 5),直接调 CLI 归档(Phase 7)。
3. **MODIFIED 标题漂移是机械校验能抓住的,不用记在脑子里。** 仓库实际跑的那个 validator(具体 rule ID 查仓库规则)会在 change 处于活跃状态时,把 MODIFIED 块里的需求/场景标题与当前主 spec 逐字比对。在编排层面你只需要知道:这类检查一旦报错,正确做法永远是"把标题改回去,只改正文",绝不是"把标题改得更准确"。

正因为第 1、2 条,本 skill **自己生成 `verify` artifact**——用生成任何 artifact 的同一套通用循环(拉 `openspec instructions <id> --change <name> --json`,逐字遵循它的 `template`/`instruction`/`rules`),而不是把这一步甩给那两个对不上号的 skill。

## 输入

一个 change 名字(已存在,用于续跑)或一句要做什么的描述(用于新开)。两者都推不出来时,
用 **AskUserQuestion** 问一次(开放式)——这不是真正的闸门,只是正常收集输入。

## Phase 0 — 确定 change 与 schema

0. **本 session 里如果还没读过,先读一遍仓库自己的 worktree/踩坑规则**(本仓库是
   `openspec/rules/enforced/project.md` §二 与 `openspec/rules/advisory/pitfalls.md`)。
   后文所有"命令/工具/规则去哪找"的问题,答案都在那两处。
1. **动手设计前先跟远端同步。** 跑:

   ```bash
   git fetch origin && git status --short --branch
   ```

   如果分支状态是 `behind`,在写 `interview.md` **之前**先 fast-forward(或 rebase)——
   否则 L1 explore 读到的是过时代码,整个设计都建立在错误基础上。这一步只花几秒钟。
   注意 `git status` 的 ahead/behind 计数是相对**远端追踪分支**算的,只有跟你上次 `git fetch`
   一样新——不跑 `git fetch` 的话,即使远端已经推进了,这一行也可能显示"已同步"。
   仓库本地的 worktree/并行判据(如果有)未必覆盖这类问题——它们的判据经常都是纯本地的。
2. **动手创建任何东西之前先摸底。** `openspec list --json` 看现有的 change,然后确定:

   - **change id**(kebab-case)。已存在的 change:如果有歧义,用 **AskUserQuestion** 让用户选,不要自己猜。
   - **本仓库是否要求每个 change 一个独立 worktree?** 查仓库的 worktree 规则。如果要求,
     还要确定本次 change 需要哪些仓库特定的 flag(数据库隔离、依赖安装等)——这些规则应该
     写清楚什么条件对应什么 flag,以及选错的后果为什么是静默的而不是报错。

   L1 explore 之前你不一定能百分百确定这些——凭手头最好的证据做判断即可;
   如果 L3 design 阶段发现了新信息(比如原来没想到要加迁移),这就是一个正当理由去重新考虑 worktree 方案。
3. **如果本仓库要求 worktree 隔离,要在 change 创建之前先建好,而不是之后补。** 按仓库的
   worktree-per-change 策略(如果有):

   - 先看这个 change 是不是已经有 worktree 了;有的话直接进入,跳到第 5 步。
   - 没有的话,按仓库文档记录的工具创建一个,然后进入。
   - 后续本文档的**每一个** Phase——规划、实现、L7、L9、Phase 7 归档——只要要求 worktree,
     就必须在那个 worktree 里做。仓库的写回校验钩子可能是在 session 启动时就解析好项目目录的,
     从别的目录改这个 worktree 里的文件,校验的会是错的目录,而且是静默失败。
   - 只有 Phase 8(合并)可以合法地碰主工作区的 checkout,而且只限于 change 本身工作完成之后
     最后的 rebase/push/PR 步骤。
4. **创建 change——现在动手,如果需要 worktree 就要在 worktree 里做。** `openspec new change "<change-id>"`
   (只有当仓库默认 schema 不是 `devops-workflow` 时才需要显式传 `--schema devops-workflow`——
   在刚创建的 change 上跑 `openspec status --json` 或查仓库 openspec 配置来确认)。

   只要要求 worktree 隔离,**第 3、4 步的顺序就是重点,不是风格偏好**:`openspec new change`
   写入的是当前 cwd,而创建 worktree 通常是从 `HEAD` 构建的——所以如果先创建 change 后建
   worktree,这个 change 就会作为未跟踪的孤儿留在主工作区,没有任何 commit 会带走或清理它。
   出现这种情况时,按仓库文档的恢复路径处理(如果有),优于在工作区之间手工搬运文件——
   后者会彻底破坏隔离保证。
5. `openspec status --change "<name>" --json`。如果 `schemaName` 不是 `devops-workflow`,
   **停下来**——本 skill 假定的是这个 schema 的 artifact 集合
   (interview/explore/proposal/specs/design/tasks/exec-plan/verify)和它的校验规则,
   遇到不匹配就如实报告,不要临场改用别的流水线套。
6. 用返回的 `artifacts[].status`(必要时直接读文件确认)判断该从哪个 Phase 续跑。
   **如果 change 已经有更靠后的 artifact,不要从 L0 重来**——直接跳到第一个未完成的 Phase。
7. 用你的任务追踪工具(TodoWrite/TaskCreate,视 harness 提供什么而定)跟踪跨 Phase 的进度——
   这一趟可能会跑很多步。

## Phase 1 — 规划循环(L0-L2): interview → explore → proposal → specs → design → tasks

循环:`openspec status --change "<name>" --json` → 在 `interview, explore, proposal, specs, design, tasks`
里取第一个 `status: "ready"` 的 artifact → `openspec instructions <id> --change "<name>" --json` →
读它的 `dependencies` 文件 → 按 `template` 把 artifact 写到 `resolvedOutputPath`,把
`context`/`rules`/`instruction` 当作约束来遵守(绝不要把这些块原样抄进产出物)→ 重复。

这个本应全自动的循环里嵌了两处硬性中断——**这不是建议,不要让"保持势头"盖过它们**:

- **L0 闸门,`interview.md` 一出现(不管是刚写的还是本来就有)就要立刻检查**:自己去读
  它的歧义/待决问题那一节。只要有任何一条没解决,就**停下**循环。直接把开放问题抛给用户
  (自然语言提问或 AskUserQuestion,看哪个合适),拿到答案后更新 `interview.md` 标记为已解决,
  再继续走 `explore`。歧义没清空之前不要生成 `explore`/`proposal`——这本来就是 schema 自己的
  instruction 要求的,只是没人真正执行,所以由你来兜底。
- **L3 闸门,生成 `tasks` 之前**:`tasks` 要求 `specs` 和 `design` 都是 `done`。创建它之前,
  打开 `design.md` 检查 frontmatter 里**同时**有没有审批人和审批日期。缺任何一个:
  - **停下**。把 `design.md` 的内容(或摘要,太长的话)展示给用户,明确请求批准——
    这是整条流水线里唯一一个"改起来还便宜"的节点。
  - 只有用户批准之后,才由你把审批字段写进 frontmatter,然后继续走 `tasks`。
  - 如果用户要求修改而不是批准,回去改 `design.md`(或者问题追溯更早的话改 `proposal.md`/`specs/`)
    再重新确认——不要半批准就往下走。

## Phase 2 — L4 exec-plan

跟 Phase 1 一样的通用循环,针对 `exec-plan` 这个 artifact(`requires: [tasks]`)。这里没有
人类闸门——直接自动生成。按它的 instruction 要求填(通常包括:任务映射、依赖 DAG、
共享层优先排序、契约冻结、worktree/执行单元归属、失败/降级预案),并填完模板末尾的
Gate checklist。

## Phase 3 — L5 实现

用 Skill 工具调用 **`openspec-apply-change`** skill 来处理这个 change,让它循环跑完所有
task。它已经有这个阶段该有的暂停语义(只在真正的歧义/报错/设计问题上暂停,不是每个
task 都停)——不要自己重新实现一遍。如果它因为设计问题暂停了,那是真正需要升级处理的情况:
回去修上游 artifact(如果 `design.md` 本身要改,可能需要重新走一遍 L3 审批),
而不是在 `exec/` 里绕过去。

## Phase 4 — L7 硬闸门:build / test / lint

这是一个**机器**闸门,自己跑,不要问人,也不要委托给不会真正执行它的 skill。

**读仓库的 build/test/lint 命令表(比如本仓库 `openspec/project.json` 的 `commands`),
逐条跑,把输出写到仓库指定的证据路径。** 这张命令表是唯一事实源——不要在这里或任何
别的地方硬编码命令字符串,两份副本迟早会漂移。

这里有两条判定规则,通常会被自动注入到 `verify` artifact 的 prompt 里,来源是仓库自己的
配置——具体在哪查仓库配置,读那边的原文而不是自己重新推导:(a) 怀疑有历史遗留的红时,
基线要先于证据确定的顺序;(b) 红灯归因(回归 vs 历史遗留),以及"条件性通过"需要满足什么。

编排层面你只需要:

- 全绿 → 继续 Phase 5。
- 有红 → 按仓库的 verify 规则归因。如果去修了,重试一次。如果**同一个**检查重试后还是红,
  **停下**,把失败日志片段展示给用户,而不是继续瞎猜——这是"反复失败才升级问人"的规则,
  不是"永远不能问"。

## Phase 5 — L6+L8 verify(集成 + spec 一致性)

用通用的 instructions 循环生成 `verify` artifact(重申一遍,不要用那个对不上号的
`openspec-verify-change` skill)。集成通常是这个 artifact 里的一节,spec 一致性是另一节——
具体结构看 `openspec instructions verify` 拉出来的模板。

它的 instruction 通常会自我限定为"`tasks.md` 没有未勾选的项才能生成"——遵守这条
(不要提前生成)。写之前先读 Phase 3 留下的执行笔记(如果有)。

- **集成一节**:按 `exec/plan.md` 里的执行单元数量调整篇幅。只有一个单元 → 写一句简短的
  "单执行单元,无并行集成"说明,加上必要的越界汇总,把只有多单元才有意义的子节
  (合并顺序、冲突清单、去重、被牺牲的方案)整段删掉。两个或以上 → 全部填齐。
  越界的判断按 schema 的"必要 vs 过度"标准来。
- **一致性一节**:必须以一个判定收尾(通过 / 打回实现 / 打回设计——具体措辞和校验器
  查仓库规则),并且要包含越界检查:把实际改动的文件集与 `exec/plan.md` 声明的归属 +
  笔记里声明的必要性附带改动做 diff。
- **通过** → Phase 6。
- **打回实现** → 回到 Phase 3,然后重跑 Phase 4-5。
- **打回设计** → **停下**。这是真正的设计缺陷,不是能在 `exec/` 里打补丁解决的。
  告诉用户设计需要重开;如果 `design.md` 被改动,原来的批准就不再算数——
  `tasks` 再次变更之前必须重新走一遍 Phase 1 的 L3 闸门。

**实际验证时(不是规划时)发现的 bug**——比如真实环境测试或 HTTP 层探测揭示了一个真实缺陷,
必须在 change 能算完成之前修掉。这种情况很常见,因为 L7 的 build/test/lint 闸门本来就
检测不出"编译通过、单元测试也过,但这个功能其实从没真正跑通过"这类 bug(路由顺序、
响应结构不匹配、缓存过期——这类只有端到端真实跑一遍才会暴露的问题)。不要为了每一个这种
发现回头补 `exec/plan.md` 的任务映射表——那张表存在的目的是防止并行 agent 互相踩,
一个 agent 独自在验证阶段发现并修复的问题,从一开始就不属于那个协调问题。正确做法:

1. 修掉它,验证它(build/test/lint + 揭示这个 bug 的那种验证方式),跟其他修复一样。
2. 直接记录在 `verify.md` 自己的结构里——schema 里管"不一致项归属判定"的那一节正是
   它该在的地方,不要虚构一个提前规划好的 task。写清楚发现了什么、为什么、怎么修的。
3. 在 `tasks.md` 里为每个发现补**一行**(让任务覆盖检查有东西可以指向),但不要为它去改
   `exec/plan.md` 的按单元映射表——指向 `verify.md` 就够了,不要凭空发明一个从未存在过的
   执行单元。
4. 如果仓库的 validator 仍然抱怨这行没有映射,先查仓库规则确认这在本仓库到底是硬性
   error 还是可接受的 warning,再决定怎么处理——不要没查就默认它无害
   (有些仓库的未映射任务检查是会拦住归档的硬性 error,不是 warning)。

不管这个 change 有没有用到 worktree,上面这条都成立——底层原因(一个 agent 独自发现并
修复的问题不存在并行协调风险)跟有没有 worktree 无关。

## Phase 6 — L9 硬性人类闸门:最终 diff 审阅

绝不能跳过这一步,也绝不能让某个自动归档的 skill 代劳(大多数根本不会请求签字确认)。
给用户看:

```bash
git status --short
git diff --stat
```

并主动提出可以按需展示完整 diff。明确地问(AskUserQuestion 或自然语言提问)是否批准归档。
拿到明确的"是"之前不要进入 Phase 7。

## Phase 7 — L10 归档

用**原生 CLI** 归档,不要用通用的 archive/sync skill:

1. 跑仓库的流水线校验命令——归档前必须干净(或者只有 warning)。
2. **在 change 离开活跃目录树之前,先处理好仓库层面的"现状追踪"文档**(如果仓库维护这类
   文档的话——查仓库根目录文档/规则索引)。它们的内容通常会在下一步移进归档位置,
   此后再也不会有人翻到:
   - 这个 change 关掉的条目 → 回去更新追踪文档里那一项的状态,注明是哪个 change 关的。
   - 发现了但故意没修的问题 → 必须已经带着症状登记在那里了。
   - 这个 change 改动了字段/操作的页面,如果有对应的"现状说明"文档 → 更新它;
     文档和代码对不上时,以代码为准。
3. ```bash
   openspec archive "<name>" --yes --json
   ```

   在非交互 shell 里 `--yes` 不是可选项:不加的话 CLI 会抛出一个等待确认的错误,
   而没人能对着非交互环境输入确认。绝不要加 `--no-validate`。这一步会把 delta specs
   合并进主 spec 目录,**同时**把 change 挪进归档,一步到位。不要提前单独跑一次 sync,
   也不要自己手动 `mv` 目录——这两件事 `openspec archive` 本来就会做。
4. 跑仓库提供的归档任务完整性闸门(如果有)——这个 change 现在是归档件了,可能属于
   这类闸门的检查范围。在这里跑,好过之后才发现遗留了未勾选的实现类任务。
   发布/上线后的声明性条目(本来就不该是可勾选任务)不算在内。
5. **如果归档过程中创建了新的主 spec**,如果仓库 schema 要求,自己补上它的 status
   frontmatter——`openspec archive` 通常不会自动写。具体要求的字段/取值查仓库 schema/规则。
6. **重新生成仓库维护的能力索引**(如果有,且 `openspec archive` 不会自动做——具体命令
   查仓库文档)。生成物绝不要手改——下一次归档又会变旧。
7. 再跑一次仓库的流水线校验命令——确认合并结果依然一致、每个主 spec 都有必需的元数据、
   任何生成的索引都是最新的。

**为什么用 CLI 而不是通用归档 skill。** `openspec archive` 是程序化合并的:ADDED 需求
原样复制,MODIFIED 指向 spec 里不存在的需求会直接报错,MODIFIED 丢了某个场景也会报错,
而且主 spec 会先做快照,归档失败可以回滚。通用的"`mv` + agent 手工合并"式归档 skill
反而会产生漂移——具体漂移的证据查仓库规则(比如本仓库 `openspec/project.json` 的
`capabilities.knownArchiveDrift` 注释)。

如果 `openspec archive` 拒绝执行,这个拒绝本身就是重点——去修 delta,而不是退回去用某个
skill 或 `mv`。`--no-validate` 会直接废掉用这个 CLI 的全部意义。

## Phase 8 — 合并(仅当用户要求 push / 开 PR / 合并时)

归档**不等于**工作到此结束,如果这份工作还要落到主分支上。这个 Phase 存在的原因是:
主分支在你工作的同时也在推进——从规划到归档常常要跑几个小时,而你归档时留下的 L7 证据
描述的是**你这条分支孤立状态下**的情况,不是最终真正会落地的状态。

不要主动进入这个 Phase——只有用户明确要求 commit、push、合并时才做(参考 harness 的
git 规则)。用户提出后:

1. **先 rebase 到最新的远端 main,再做任何事:**
   ```bash
   git fetch origin && git rebase origin/main
   ```
2. **rebase 时生成的能力索引冲突是预期内的,绝不能手工合并**(如果仓库维护这种索引的话)。
   两条分支各自归档时通常都会独立重新生成它,所以只要两个 change 前后脚落地就会冲突。
   靠重新生成解决(具体命令查仓库文档),不要手工合并——手工合的索引下次归档又会过时。
   之后确认重新生成的索引**同时包含双方**的能力,不是只有你这边的。
3. **在 rebase 后的状态上重跑完整的 L7 闸门。** 这正是这个 Phase 存在的全部意义:
   rebase 拉进来的代码是你归档的证据从没覆盖过的,而且可能刚好碰到你改过的同一批 package。
   证据新鲜度检查通常**抓不住这种情况**——它比较的是证据时间戳和源码 mtime,
   完全不知道别人 rebase 进来的 commit。这里出现红灯,就跟 Phase 4 一样,必须先修好再合并。
4. 之后才能 push(rebase 之后用 `--force-with-lease`)并开 PR。
5. **等 CI 真正跑完再合并。** 一个 PR 可能在检查还没跑完时就显示为 mergeable;
   只有检查全部通过,或者用户明确说不管检查结果也要合并,才能合并。
6. **PR 确认合并之后,清理 worktree**(如果用到了的话),按仓库文档记录的清理命令。
   只在合并确认之后做,不要 PR 一开就立刻清——review 反馈可能还需要往同一分支继续 push,
   提前删掉 worktree 会破坏那个进行中的 checkout。
   **如果当前 session 的 cwd 就在要删除的 worktree 里,不要在这里跑清理命令**——
   删除自己所在工作目录的 worktree 注册是自毁行为。要么让用户来跑,要么先用
   `ExitWorktree` 把 session 的 cwd 挪出目标路径。

**不要**在这里重跑 Phase 7 的归档步骤——这个 change 已经归档过了,它的证据日志是这条分支
被验证时的历史记录。第 3 步的重跑是合并时的闸门,不是要重写那份记录;如果它揭示了真实的
失败,那是需要修的代码问题,修完照常走 L5 → L7 → L8 再合并。

## 护栏

- L3/L9 这两个点上,永远不要只信 `status --json`——一定要自己去读实际的文件/diff。
- 永远不要用通用的 verify/archive skill 生成 `verify`——用直接的 instructions 循环,
  确保产出物跟这个 schema 的模板、跟仓库自己的校验规则对得上。
- 永远不要用通用的 archive/sync skill 或手写 `mv` 来归档——只用
  `openspec archive "<name>" --yes --json`。那些路径把 spec 合并甩给 agent 处理,
  绕开了 CLI 的逐字复制、找不到目标就报错、丢场景就报错这几层保护。加 `--yes` 是因为
  非交互 shell 没法回答确认提示;绝不要加 `--no-validate`,那会废掉用这条命令的全部意义。
- 不要跳过 L1 explore,不要跳过 L4 契约冻结,不要把 N 个 task 合并成一个 exec 单元——
  这些是 schema 层面的不变量(参见本仓库的 `openspec/design/pipeline.md` 或等价文档),
  本 skill 不会放松这些,只放松人工确认的节奏。
- 只要 `openspec status --json` 在任何时候报告的 schema 不是 `devops-workflow`,
  就停下来如实报告,不要临场改用别的流水线套。
- 永远不要跳过 Phase 0 的 `git fetch`,也永远不要在没做 Phase 8 的 rebase + L7 重跑的
  情况下合并。这两条守的是同一种失败:**证据描述的代码状态早已不存在。**
  归档的证据日志只证明你的分支在孤立状态下能跑通,证明不了合并后的结果。
- 如果本仓库要求 worktree-per-change(查仓库规则),永远不要因为"这次改动量小"或
  "眼看就要做完了"就直接在主工作区里做 Phase 1-7 的工作——这种例外已经导致过真实事故
  (见仓库规则)。
- 如果要求 worktree,永远不要在 worktree 存在之前先创建 change,也不要靠在工作区之间
  手工搬运 change 目录来补救这种顺序错误——出现这种情况按仓库文档的恢复路径处理。
- 生成的索引/注册文件(如果仓库有这种东西)永远不手改、不手工合并——归档时不行,
  解决 rebase 冲突时也不行。
- 每个真正的闸门只问一次 AskUserQuestion/自然语言问题(L0 待决问题、L3 审批、
  L7 反复失败、L8 打回设计、L9 签字)——其余情况都应该直接往下走,不要问"要不要继续"。
- 如果要求 worktree 且当前 session 的 cwd 被固定在这个 change 的 worktree 里,
  永远不要直接碰主工作区(或任何别的 worktree)里的文件,哪怕是用绝对路径跑一个
  非 git 的普通命令也不行——session 通常在启动时就一次性解析好了项目目录,
  碰目标之外的任何东西,解析出来的都会是错的目录。如果确实需要改动当前 worktree
  之外的东西,请用户来做,或者先用 `ExitWorktree`。
- 不要因为 PR 一开、"流程感觉上完成了"就忘了 Phase 8 的 worktree 清理步骤——
  归档和开 PR 都不等于关闭 worktree,在那一步之前没有任何环节会替你做这个清理。
