# package-map.md 生成指南

package-map.md 是包路径速查表，让 agent 快速定位"我要改的东西在哪"。完全由代码扫描生成。

## frontmatter

```yaml
---
description: 项目关键包路径速查，帮助快速定位代码位置
---
```

无 globs，无条件加载。包路径速查是高频需求，任何开发场景都可能用到。

## 扫描方法

### 1. 确定基础包名

从以下位置推断（按优先级）：
1. 根 pom.xml 的 `<groupId>` + artifactId 推断
2. adapter 模块的 `src/main/java/` 下第一层实际包结构
3. 任意一个 Controller 类的 package 声明

### 2. 扫描各模块的实际包结构

对每个模块，扫描 `src/main/java/{base-package}/` 下的目录结构，映射到功能角色：

| 要找什么 | 扫描方法 | 预期模块 |
|---------|---------|---------|
| REST Controller | 包含 `controller` 的包路径 | adapter |
| MQ 消费者 | 包含 `listener` 或 `consumer` 的包路径 | adapter |
| 应用服务 | application 模块下包含 `service` 的包路径 | application |
| 事件发布 Handler | 包含 `event` 且有 `Handler` 类的包路径 | application |
| RPC 实现类 | application 模块下包含 `rpc` 的包路径 | application |
| 领域实体 | domain 模块下包含 `entity` 的包路径 | domain |
| 领域服务 | domain 模块下包含 `service` 的包路径 | domain |
| 领域事件 | domain 模块下包含 `event` 的包路径 | domain |
| Repository 接口 | domain 模块下包含 `repository` 的包路径 | domain |
| MQ 常量 | domain 模块下包含 `constants` 的包路径 | domain |
| 枚举 | domain 模块下包含 `enums` 的包路径 | domain |
| 错误码 | domain 模块下包含 `code` 或 `exception` 的包路径 | domain |
| Repository 实现 | infrastructure 模块下包含 `repository` 的包路径 | infrastructure |
| PO 类 | infrastructure 模块下包含 `po` 或 `dataobject` 的包路径 | infrastructure |
| MyBatis Mapper | infrastructure 模块下包含 `mapper` 的包路径 | infrastructure |
| ACL Client | infrastructure 模块下包含 `acl` 或 `client` 的包路径 | infrastructure / common-infrastructure |
| RPC 接口定义 | api 模块下包含 `rpc` 的包路径 | api |
| RPC DTO | api 模块下包含 `req` / `resp` 的包路径 | api |

### 3. 扫描 MQ 消费者子包

列出 `adapter.event.listener` 下的所有子包，作为业务域速查。

### 4. 识别独立子域

如果某个模块内部有自己的 domain + infrastructure 子模块，标记为独立子域。

## 输出格式

参考已生成的 kjs-product 示例（`kjs-product/.claude/rules/package-map.md`），包含：
1. 基础包名声明
2. 主模块包路径表（要找什么 → 包路径 → 模块）
3. MQ 消费者子包列表（树形结构）
4. 独立子域表（如有）
