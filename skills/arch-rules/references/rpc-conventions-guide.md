# rpc-conventions.md 生成指南

rpc-conventions.md 包含 RPC 接口暴露和调用的开发规范。通用模式固定输出，项目特有的框架细节从代码扫描填充。

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

## 扫描要点

### RPC 框架识别

扫描项目中使用的 RPC 框架，根据发现的注解/依赖确定：

| 框架标识 | 判断依据 |
|---------|---------|
| Tesla RPC | `@Tesla` 注解、`TeslaServiceConsumerFactory`、`ReferConfig` |
| Dubbo | `@DubboService`、`@DubboReference` |
| gRPC | `*.proto` 文件、`@GrpcService` |
| Feign | `@FeignClient` |

### 接口定义位置

扫描 api 模块中 `*RpcService` 接口的包路径，确定：
- 接口定义包路径
- Request DTO 包路径
- Response VO 包路径

### 实现类注解

扫描 application 模块中 `*RpcServiceImpl` 类的类级注解，确定实际使用的注解组合（如 `@Service @Tesla`）。

### 外部调用模式

扫描 infrastructure / common-infrastructure 中的：
- `*RpcConfig` 类 → Bean 注册模式
- `*Client` 类 → 调用封装模式（是否继承某个基类如 `ExecuteRpcClient`）

## 文档结构

### 第零部分：本项目 RPC 框架约定（项目特有，扫描填充）

从扫描结果中提取以下信息，作为文件头部的速查表：

```markdown
## 本项目 RPC 框架约定

- RPC 框架: {Tesla RPC / Dubbo / gRPC / Feign}
- 接口定义模块: {api 模块名}
- 实现类注解: {扫描到的注解组合，如 @Service @Tesla}
- RPC 消费端注册: {注册方式，如 *RpcConfig + TeslaServiceConsumerFactory}
- REST Controller 注解: {扫描到的注解组合}，返回 {返回类型}
- URL 约定: {从现有 Controller 推断的 URL 模式}
```

这部分是原先 CLAUDE.md 中的 RPC Conventions，现在统一放在这里。CLAUDE.md 不再持有这些事实内容。

### 第一部分：暴露 RPC 接口

**接口定义**：填充实际的 api 模块名、包路径、命名规则。

**接口实现**：填充实际的注解组合和实现类所在包路径。模板：

```java
{扫描到的注解组合}
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

**RPC Config 注册模板**：根据扫描到的框架填充模板（Tesla / Dubbo / Feign 各有不同）。

**调用规范（通用，固定输出）**：
- 禁止在 domain 层直接调用外部 RPC
- 外部调用必须经过 ACL Client，在 infrastructure 层完成
- Client 类负责异常转换、结果解包、日志记录
