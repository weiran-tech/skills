---
name: aliyun-sql-slow-log
description: 查询阿里云 RDS 数据库慢 SQL 并生成 Markdown 统计报告。按 SQLHash 分组聚合，支持最大耗时过滤、多表扫描分析、执行频率排行。当用户提到"慢SQL"、"慢查询"、"RDS 慢日志"、"数据库慢SQL"、"获取 slow log"时触发。
---

# 阿里云 RDS 慢 SQL 统计

基于帕累托分析法输出慢 SQL 排行榜，按 SQLHash 分组聚合统计，自动识别高频慢查询和全表扫描嫌疑语句。

## 前置检查

先确认 aliyun-cli 已配置：

```bash
aliyun configure list
```

如果未配置，提示用户执行 `aliyun configure` 完成 AccessKey 配置。

同时确保 aliyun-cli-rds 插件已安装：

```bash
aliyun plugin install --names aliyun-cli-rds
hash -r
```

## 命令参数

| 参数               | 必填 | 默认值            | 说明                              |
| ------------------ | ---- | ----------------- | --------------------------------- |
| `--instance-id`    | 是   | -                 | RDS 实例 ID                       |
| `--region`         | 否   | cn-hangzhou       | 地域 ID                           |
| `--db-name`        | 否   | -                 | 数据库名过滤                      |
| `--days`           | 否   | 7                 | 统计天数                          |
| `--max-time-threshold` | 否 | 0              | 仅显示最大耗时 >= 此值(ms) 的 SQL |
| `--page-size`      | 否   | 100               | 每页记录数（30~100）              |
| `--top-N`          | 否   | 20                | 输出排名前 N 个不同 SQL           |
| `--title`          | 否   | 慢 SQL 统计报告    | 报告标题                          |
| `--dry-run`        | 否   | false             | 仅打印 API 调用信息，不执行       |

## 使用示例

### 示例 1: 查看最近 7 天慢 SQL TOP 20

```bash
uv run .claude/skills/aliyun-sql-slow-log/scripts/stats.py analyze \
  --instance-id rm-bp15v1z1h4qh9hw44 \
  --region cn-hangzhou
```

### 示例 2: 指定数据库 + 只查慢于 1 秒的 SQL

```bash
uv run .claude/skills/aliyun-sql-slow-log/scripts/stats.py analyze \
  --instance-id rm-bp15v1z1h4qh9hw44 \
  --db-name kr_v1 \
  --max-time-threshold 1000 \
  --days 7 \
  --top-N 30
```

### 示例 3: 自定义报告标题

```bash
uv run .claude/skills/aliyun-sql-slow-log/scripts/stats.py analyze \
  --instance-id rm-bp15v1z1h4qh9hw44 \
  --days 1 \
  --title "生产环境昨日慢 SQL 分析"
```

### 示例 4: Dry Run 预览

```bash
uv run .claude/skills/aliyun-sql-slow-log/scripts/stats.py analyze \
  --instance-id rm-bp15v1z1h4qh9hw44 \
  --days 3 \
  --dry-run
```

## 执行流程

1. **参数校验**: 验证必填参数
2. **时间计算**: 根据 `--days` 计算 UTC 时间戳范围
3. **API 调用**: 调用 `describe-slow-log-records` 获取原始慢 SQL 记录
4. **SQLHash 聚合**: 按 SQLHash 分组，计算最大耗时、出现次数、平均扫描行数等
5. **过滤排序**: 按最大耗时降序，应用阈值过滤
6. **格式化输出**: 以 Markdown 表格形式输出 TOP N 结果及详细 SQL

## 输出示例

```markdown
## 慢 SQL 统计报告 - 2026-05-11

> 统计范围：最近 7 天 | 实例：rm-bp15v1z1h4qh9hw44 (cn-hangzhou)

### TOP 10 最慢 SQL 排行

| 排名 | 最大耗时(ms) | 出现次数 | 累计执行 | 平均扫描行数 | SQLHash | 数据库 |
|------|-------------|---------|---------|-------------|---------|--------|
| 1    | 88,192      | 12      | 275     | 2,336,456   | 59ceebc1 | kr_v1 |
| 2    | 19,414      | 3       | 27      | 2,263,388   | c4f7ce15 | kr_v1 |
| 3    | 9,711       | 3       | 17      | 27,787      | af8f737a | kr_v1 |
...

### 详细信息

[1] Hash: 59ceebc1946afcd872070d96bcb4e415 | 最大耗时: 88,192ms | 出现: 12 次 | 累计执行: 275 次
   SQL: select third_goods_append.*, third_goods.status as kjs_status, ... from third_goods_append left join ... where platform_name = 'KeJinShou' ...

[2] Hash: c4f7ce15afc51a3f59ea20eddd523f44 | 最大耗时: 19,414ms | 出现: 3 次 | 累计执行: 27 次
   SQL: select third_goods_append.*, third_goods.status as yy_status, ... from third_goods_append left join ... where platform_name = 'YY' ...
```
