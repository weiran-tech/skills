# rpc-conventions.md 生成指南

rpc-conventions.md 包含 RPC 接口暴露和调用的开发规范。通用模式固定输出，项目特有的框架细节优先从 docs 提取。

**数据来源优先级**：`docs/overview.md` + `docs/contracts.md` > 代码扫描。docs 存在时不做代码扫描。

## frontmatter

```yaml
---
description: RPC 接口暴露和调用的开发规范
globs:
  - "**/api/**"
  - "**/rpc/**"
  - "**/acl/**"
---
```

## 信息获取

### 从 docs 提取（优先）

如果 `docs/overview.md` 和 `docs/contracts.md` 存在，从中提取以下项目特有信息：

**从 `docs/overview.md`**：
- **RPC 框架类型**：从"技术栈"表格的"RPC 框架"行提取（Tesla / Dubbo / gRPC / Feign）
- **api 模块名**：从"模块结构"表格中识别 api 模块

**从 `docs/contracts.md`**：
- **RPC 接口列表**：从"供其他服务调用的 SDK / Feign 接口"表格提取接口定义包路径
- **外部 RPC 依赖**：从"依赖的外部 Feign / RPC 接口"表格提取 ACL Client 包路径
- **实现类注解**：从接口描述中推断注解组合（如果 contracts.md 中有记录）

**从 `docs/overview.md` 补充**：
- **REST Controller 注解和 URL 约定**：如果 overview.md 记录了 URL 模式或注解约定

### 从代码扫描提取（回退）

仅当 docs 不存在时执行：

- 扫描 `@Tesla`/`@DubboService`/`@GrpcService`/`@FeignClient` 确定 RPC 框架
- 扫描 api 模块中 `*RpcService` 接口的包路径
- 扫描 application 模块中 `*RpcServiceImpl` 类的类级注解
- 扫描 infrastructure 中的 `*RpcConfig` 和 `*Client` 类

## 文档结构

### 第零部分：本项目 RPC 框架约定（项目特有）

从 docs 或扫描结果中提取以下信息，作为文件头部的速查表：

```markdown
## 本项目 RPC 框架约定

- RPC 框架: {Tesla RPC / Dubbo / gRPC / Feign}
- 接口定义模块: {api 模块名}
- 实现类注解: {注解组合，如 @Service @Tesla}
- RPC 消费端注册: {注册方式，如 *RpcConfig + TeslaServiceConsumerFactory}
- REST Controller 注解: {注解组合}，返回 {返回类型}
- URL 约定: {URL 模式}
```

如果某项信息在 docs 中未记录且未做代码扫描，标注"待确认"。

### 第一部分：暴露 RPC 接口

**接口定义**：填充实际的 api 模块名、包路径、命名规则。

**接口实现**：填充实际的注解组合和实现类所在包路径。模板：

```java
{注解组合}
public class XxxRpcServiceImpl implements XxxRpcService {
    // 注入 application service 或 domain service
    // 禁止在 RPC 实现类中写业务逻辑，只做编排和转换
}
```

**DTO 规范（通用，固定输出）**：
- Request DTO 命名 `XxxReqDTO`
- Response VO 命名 `XxxRespDTO` 或 `XxxRespVO`
- DTO 类必须实现 `Serializable`
- 禁止使用 `Map`、`JSONObject` 作为字段类型

### 第二部分：调用外部服务 RPC

**ACL Client 模式**：填充实际的 infrastructure 模块名和包路径。

**RPC Config 注册模板**：根据框架类型填充模板（Tesla / Dubbo / Feign 各有不同）。

**调用规范（通用，固定输出）**：
- 禁止在 domain 层直接调用外部 RPC
- 外部调用必须经过 ACL Client，在 infrastructure 层完成
- Client 类负责异常转换、结果解包、日志记录
