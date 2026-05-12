---
name: project-report
description: 独立项目日报汇总技能。为单个项目生成独立的日报报告，支持 SLS 阈值调整，按时间戳命名输出文件。当用户提到"日报"、"项目报告"、"汇总"、"统计 bugs/req/sentry/sls"、"运行日报"、"生成报告"、"数据统计"、"线上故障统计"、"Sentry 异常统计"、"SLS 接口统计"、"需求统计"时，必须使用此技能。即使没有明确指定技能名称，只要涉及项目数据汇总和报告生成，就应该使用此技能。
compatibility: Python 3.8+, uv
---

# Project Report Skill

为单个项目生成独立的报告，支持多种数据源（云效故障、技术需求、Sentry 异常、SLS 接口统计）。

## 参数说明

| 参数         | 类型   | 必填 | 默认值       | 说明                                                                                                                                                          |
| ------------ | ------ | ---- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `project`    | string | 是   | -            | 项目名称，如 "氪金兽"                                                                                                                                         |
| `type`       | string | 否   | 全部启用类型 | 内容类型，逗号分隔，如 "req,bugs,sentry,sls,sql"                                                                                                              |
| `type:param` | string | 否   | 灵活参数     | 替换不同类型的参数，如 "sls:threshold" 会覆盖掉项目配置中 sls 中的 threshold 参数, sls[host=host.com] 会搜索项目配置中 sls 中的 host 参数 = 'host.com' 的条目 |

## 使用示例

```
# 基础用法
/project-report project=氪金兽

# 指定类型
/project-report project=氪金兽 type=bugs

# 指定日期范围
/project-report project=氪金兽 type=bugs,sentry bugs:range='-10 days'

# 自定义 SLS 阈值
/project-report project=氪金兽 type=sls sls:threshold=75 sls[name=www]

# slow log
/project-report project=氪金兽 type=slow_log slow_log[name=kjs-main]
```

## 执行流程

### Step 1: 读取配置文件

使用 Read 工具读取项目配置文件：
- `config/{项目名}.yaml` - 项目独立配置
- 根据类型读取默认配置项

**配置过滤规则**：
1. 根据 `project` 参数读取对应的项目配置文件
2. 若传入 `type` 参数，只保留指定的类型；否则使用**所有非空**的模块（只要 sentry/sls 配置非空就执行）
3. 若传入 `type:param` 参数，根据参数替换对应类型的配置

### Step 2: 数据采集映射

根据过滤后的类型，依次调用对应的技能收集数据：

| 类型     | 标题         | 技能调用                                                                              | 特殊处理                           |
| -------- | ------------ | ------------------------------------------------------------------------------------- | ---------------------------------- |
| bugs     | 线上故障     | `/yunxiao-bug-stats space_id={space_id} range={range}`                                | —                                  |
| req      | 技术需求     | `/yunxiao-req-stats space_id={space_id} range={range}`                                | —                                  |
| sentry   | Sentry       | 按分组逐组调用 `/sentry-exception-output projects={projects} title={项目名}-{分组名}` | 多分组循环执行                     |
| sls      | 接口高频统计 | `/aliyun-sls-stats {sls 段落配置, 除 name 参数外, 所有参数均透传}`                    | 每条配置独立执行，为空则跳过该条目 |
| slow_log | slow log     | `/aliyun-sql-slow-log {slow_log 段落配置, 除 name 参数外, 所有参数均透传}`            | 每条配置独立执行，为空则跳过该条目 |



### Step 3: 生成报告文件

**输出目录**：`report/{project}/QA/`（不存在则自动创建）

**文件名格式**：`{MM-DD-HH-MM}-{range}-{type:ALL}.md`

**文件内容格式**：
```markdown
# {项目名} - {date}

## 线上故障
{bugs 结果；未采集则填"（本次未采集）"}

## 技术需求
{req 结果；未采集则填"（本次未采集）"}

## Sentry
{sentry 结果，按分组输出小节；未采集则填"（本次未采集）"}

### {分组名}
{该分组的 Sentry 统计结果}

## 接口高频统计
{sls 结果，每个 host 一个小节；未采集则填"（本次未采集）"}

### {name}
{该 name 的 SLS 统计结果}

## slow log
{slow_log 结果，每个 name 一个小节；未采集则填"（本次未采集）"}

### {name}
{该 name 的 slow log 统计结果}
```

**异常处理**：
- 若某类型数据获取失败，对应部分填写"数据获取失败"
- SLS 配置中若 `project` 或 `logstore` 为空，跳过该条目

## 项目配置文件结构

每个项目在 `config/` 目录下有独立的 YAML 配置文件：

```yaml
name: 项目名称
space_id: 云效项目 space_id

# Sentry 分组配置
sentry:
  分组名:
    - 项目模式1
    - 项目模式2

# SLS 配置
sls:
  - name: domain
    host: domain.com
    project: sls-project
    logstore: logstore-name
    region: cn-hangzhou
    threshold: 50

slow_log:
  - name: domain
    instance-id: instance-id
```

## 输出约定

1. 使用 Write 工具写入报告文件
2. 只返回最终生成的文件路径，不输出中间结果
3. 报告文件使用 UTF-8 编码
4. 时间戳使用当前执行时间（精确到分钟）
