---
name: repo-api-scan
description: 扫描项目接口，按模块/业务方/功能组三级整理功能清单大纲并输出到 .md 文件。支持 PHP/Laravel 和 Java/Spring Boot。当用户说 "api-scan"、"功能清单"、"接口扫描"、"feature scan"、"功能大纲" 时触发。
---

# API Scan

扫描项目全部接口端点，按「模块 → 业务方 → 功能组」三级分组，生成功能清单大纲。只关注"做什么"，不分析实现细节。

## 规则文件

| 项目类型 | 规则文件 |
|---------|---------|
| PHP / Laravel 模块化 | [rules/PHP-LARAVEL-MODULAR.md](./rules/PHP-LARAVEL-MODULAR.md) |
| PHP / Laravel 单体 | rules/PHP-LARAVEL-SINGLE.md (待补充) |
| Java / Spring Boot | rules/JAVA-SPRING-BOOT.md (待补充) |

---

## 第一步：识别项目类型

按优先级检测：

| 标志文件                          | 项目类型             | 规则文档 |
| --------------------------------- | -------------------- | -------- |
| `composer.json` + `modules/` 目录 | PHP / Laravel 模块化 | [PHP-LARAVEL-MODULAR.md](./rules/PHP-LARAVEL-MODULAR.md) |
| `composer.json`（无 modules）     | PHP / Laravel 单体   | 待补充 |
| `pom.xml` 或 `build.gradle`       | Java / Spring Boot   | 待补充 |

检测失败时询问用户。

---

## 第二步：整体流程（以 PHP 模块化为例）

### 核心原则

**RouteServiceProvider 中的 `require_once` 只是路由文件的加载机制，不是实际接口！**
- 只在具体路由文件（`Routes/*.php`）中扫描实际路由定义
- 不要把 require/include 统计为接口

### 2.1 解析 RouteServiceProvider
- 建立「路由文件 → 前缀信息」映射表
- 提取 prefix、middleware、路由文件路径
- 特殊处理 `$this->prefix` 变量替换为 `'mgr-page'`

### 2.2 扫描路由文件（实际提取接口）
- **支持两种路由格式**：数组格式 `[Controller::class, 'action']` 和字符串格式 `'Controller@action'`
- **处理嵌套 group**：逐层解析，累积完整 prefix 链、namespace、middleware
- 拼接完整 URL = 外层 prefix + 内层累积 prefix + 路由路径

### 2.3 业务方分类（三步校验）
1. **文件名初判**：backend.php → 后台、web.php → 员工网页...
2. **middleware 二次校验**：根据中间件关键词细分
3. **路径关键词最终细分**：根据路径含 merchant/soldier/consumer/notify 等最终确定

### 2.4 功能组划分（按路径 / 分层级）
- 按路径 `/` 分割，取除前缀外的第一段路径作为功能组
- 同路径段功能差异大时取第二段细分

### 2.5 功能点命名
- 根据 HTTP 方法 + action 中文名称映射（约 80+ 常用 action）
- 相同路径不同 HTTP 方法视为不同接口，功能点名称区分方法

详细规则参见：[rules/PHP-LARAVEL-MODULAR.md](./rules/PHP-LARAVEL-MODULAR.md)

---

## 第三步：生成文档

输出文件：项目根目录下 `docs/feature-list.md`（目录不存在则创建）。

### 三级嵌套结构（PHP 模块化项目）

```markdown
# {项目名} 功能清单

## 功能概览

- **总接口数**: {N} 个
- **模块总数**: {M} 个

### 按业务方分类统计

| 业务方 | 接口数量 |
| ------ | -------- |
| 商户网页 | XX 个 |
| 员工网页 | XX 个 |
| ... | ... |

### 按模块统计

| 模块 | 接口数量 |
| ---- | -------- |
| 订单模块 | XX 个 |
| ... | ... |

## 功能模块详情

---

### 订单模块 (XX 个接口)

#### 员工网页 (XX 个接口)

##### 订单管理 (XX 个接口)

| 功能点 | 接口 | 方法 |
| ------ | ---- | ---- |
| 扫码登录 | /order/scan_login | ANY |
| ... | ... | ... |
```

详细格式参见：[rules/PHP-LARAVEL-MODULAR.md](./rules/PHP-LARAVEL-MODULAR.md)

---

## 第四步：输出摘要

完成后输出：
- 检测到的项目类型
- 模块数 / 业务方数 / 功能组数 / 接口总数
- PHP 模块化项目额外输出按业务方分类统计
- 生成文件的路径
