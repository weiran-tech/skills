# /devops-workflow summary：交付对接清单

> 处理 `/devops-workflow summary` 时读本文件。用途：里程碑做完后产出一份**对接清单**，给 DBA（DDL SQL）和前端（API）、运维（新增队列）看。受众不关心代码实现、类名、方法、文件位置，只关心「要改什么表、有哪些新接口、要加什么队列」。

## `/devops-workflow summary [需求ID][#里程碑]`

1. 解析作用目标（省略=活动上下文；多里程碑按选中里程碑汇总）。建议在阶段 5 收尾验收**通过后**执行，确保汇总的是已验收的最终状态
2. 起一个 `writer` / `document-specialist`（只读）读取本里程碑产物 + 定向 grep，合成 `change-manifest.md`
3. 写入 `.task/[milestones/{里程碑}/]change-manifest.md`
4. **★ 子 agent 返回后必须呈现结果**：读生成的文件 → 把三块的条数摘要（DDL N 张表 / 队列 M 个 / API K 个）+ 文件路径打给用户，不许静默结束

> 多里程碑：每个里程碑各出一份；需求全部里程碑 COMPLETED 后可再出一份需求级合并清单（把各里程碑的三块拼起来，标注来源里程碑）。

## 生成用 agent prompt

```
writer "
为里程碑 [{需求ID}#{里程碑}] 产出对接交付清单，写入 {里程碑根}/change-manifest.md。
只汇总三块：DDL 变更 SQL、新增队列、API 接口清单。受众是前端和运维/DBA，不关心代码实现细节。
数据来源（交叉核对，以实际代码为准）：
- 本里程碑 dev-tasks.md 的改动摘要、design-consensus.md 的契约
- 实际代码：项目中的数据库迁移文件、路由文件、控制器/接口定义

一、DDL 变更（给 DBA）：
  逐表列出可直接执行的 SQL 语句。从迁移文件中提取，转为标准 SQL（CREATE TABLE / ALTER TABLE）。
  - 新建表：完整的 CREATE TABLE 语句（含全部字段、索引、注释）
  - 改表：ALTER TABLE 语句（ADD COLUMN / MODIFY COLUMN / ADD INDEX 等）
  不要列迁移文件路径、不要列字段类型表格，直接给 SQL。

二、新增队列（给运维）：
  只列本里程碑新增的 queue name（队列名称），一行一个。
  不要列 Job 类名、触发点、调度表达式等代码细节。

三、API 接口清单（给前端）：
  逐接口列：Method + Path | 入参(字段+类型+必填) | 出参要点 | 用途一句话
  不要列控制器名、方法名、中间件等代码实现信息。
  覆盖本里程碑新增/变更的路由。

格式：Markdown，简洁可直接交付。不展开业务流程、不含代码位置/类名/方法名。
Bash 命令必须可静态分析：禁止 for/while/if/case/here-doc/嵌套 $()。"
```

## change-manifest.md 模板

```markdown
# {需求ID}#{里程碑} — 交付对接清单

- 影响模块: {模块列表}
- 生成时间: {YYYY-MM-DD}

## 一、DDL 变更（DBA）

### {表名} — 新建

```sql
CREATE TABLE `{表名}` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL DEFAULT '' COMMENT '名称',
  -- ...
  PRIMARY KEY (`id`),
  KEY `idx_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='{表注释}';
```

### {表名} — 变更

```sql
ALTER TABLE `{表名}` ADD COLUMN `{字段}` varchar(32) NOT NULL DEFAULT '' COMMENT '{注释}' AFTER `{前字段}`;
ALTER TABLE `{表名}` ADD INDEX `idx_{字段}` (`{字段}`);
```

> 无 DDL 变更时写「本次无 DDL 变更」。

## 二、新增队列（运维）

| 队列名称 |
|---------|
| {queue_name_1} |
| {queue_name_2} |

> 无新增队列时写「本次无新增队列」。

## 三、API 接口清单（前端）

| Method Path | 入参 | 出参要点 | 用途 |
|-------------|------|---------|------|
| POST /api/xxx | field1:string(必填), field2:int | {要点} | {一句话} |

> 无新增/变更接口时写「本次无接口变更」。
```

## 与 release-docs 的衔接
`change-manifest.md` 是结构化"事实清单"（原料）；需要面向运维/DBA 的「上线配置说明」（含人工要配的开关/密钥/顺序/风险）时，把本文件喂给 `release-docs` skill 生成。两者不重复。
