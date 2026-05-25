# PHP / Laravel 模块化项目扫描规则

## 重要前置约定

**排除引入文件**：RouteServiceProvider 中的 `require_once` 只是路由文件的加载机制，不是实际接口！
- 只在具体路由文件（`Routes/*.php`）中扫描实际路由定义
- 不统计 `require_once __DIR__ . '/Routes/xxx.php'` 为接口

---

## 第一步：解析 RouteServiceProvider（建立前缀映射）

遍历 `modules/*/src/(Http|http)/RouteServiceProvider.php`，建立「路由文件 → 前缀信息」映射表。

### 1.1 提取 Route::group 配置

| 配置项 | 说明 |
|-------|------|
| prefix | 路径前缀 |
| middleware | 中间件列表 |
| 路由文件 | `require_once __DIR__ . '/[Routes|routes]/xxx.php' 中的路径 |

### 1.2 prefix 解析规则

| 格式 | 处理方式 | 示例 |
|------|---------|------|
| 静态字符串 | 直接提取 | `'prefix' => 'api/web/order/v1'` → 原样保留 |
| 变量拼接 | `$this->prefix` 替换为 `'mgr-page'` | `'prefix' => $this->prefix . '/order'` → `'mgr-page/order'` |

### 1.3 URL 拼接规则

```
完整前缀不以 / 开头则添加 /
路由路径不以 / 开头且前缀不以 / 结尾则添加 /
例：'mgr-page/order' + 'list' → '/mgr-page/order/list'
```

---

## 第二步：扫描路由文件（实际提取接口）

### 2.1 处理嵌套 group（重要！

路由文件内可能有多层 `$route->group()` 嵌套，需要逐层解析：

```php
$route->group(['prefix' => 'admin', 'middleware' => 'backend-auth'], function() {
    $route->group(['prefix' => 'order', 'namespace' => 'Order\Http\Request\Backend'], function() {
        $route->get('list', [OrderController::class, 'index']); // 实际路径: admin/order/list
    });
});
```

**逐层累积**：
- 累积完整 prefix 链
- 继承 namespace（用于定位控制器类）
- 继承 middleware（用于业务方二次判断）

### 2.2 支持两种路由格式

| 格式 | 示例 |
|------|------|
| 数组格式 | `$route->get('path', [Controller::class, 'action'])` |
| 字符串格式 | `$route->get('path', 'Controller@action')` |

### 2.3 扫描步骤

1. 根据路由文件路径查找映射表，获取外层 prefix
2. 解析文件内所有嵌套的 `$route->group()`，累积完整 prefix 链
3. 解析每个 group 内的 `namespace`
4. 解析每个 group 内的 `middleware`
5. 提取 HTTP 方法（get/post/put/delete/patch/any）和 URI 路径
6. 拼接完整 URL = 外层 prefix + 内层累积 prefix + 路由路径
7. 用 URI 路径 + 方法名推断功能点名称
8. 标记每个接口的业务方类型（二次校验）
9. 记录控制器完整类名和方法名

---

## 第三步：业务方细分规则

### 3.1 三步校验机制

| 步骤 | 判断依据 | 规则 |
|------|---------|------|
| 第一步 | 文件名初判 | 见下表 |
| 第二步 | middleware 二次校验 | middleware 含 merchant → 商户<br>middleware 含 soldier/hunter → 打手<br>middleware 含 admin/backend/staff → 员工/后台<br>middleware 含 user/consumer → 用户 |
| 第三步 | 路径关键词最终细分 | 路径含 merchant → 商户/商户API<br>路径含 soldier/hunter → 打手/打手API<br>路径含 consumer/user → 用户/用户API<br>路径含 kf/customer_service → 客服/客服API<br>路径含 notify/callback/webhook → 回调通知 |

### 3.2 文件名初判表

| 文件路径 | 初步分类 | 备注 |
|---------|---------|------|
| backend.php | 后台 | 通常不需要二次校验 |
| web.php | 员工网页 | 需要二次校验 |
| merchant_web.php | 商户网页 | 需要二次校验 |
| soldier_web.php | 打手网页 | 需要二次校验 |
| web_notify.php | 回调通知 | 通常不需要二次校验 |
| api_v1.php | 通用API | 需要进一步细分 |

---

## 第四步：功能组来源（按路径 / 分层级分组）

### 4.1 分组规则

**取路径的第 N 段作为功能组**：

```
路径格式：/{prefix}/{group-segment}/{action}...
取除前缀外的第一段路径作为功能组
```

### 4.2 示例

| 路径 | 提取段 | 功能组 |
|------|--------|--------|
| /order/list | order | 订单管理 |
| /order/publish/cancel | order | 订单管理 |
| /publish/cancel/{id} | publish | 发布管理 |
| /finance/settlement/detail | finance | 财务管理 |

### 4.3 常见路径段映射表

| 路径段 | 功能组 |
|-------|--------|
| order | 订单管理 |
| publish | 发布管理 |
| finance | 财务管理 |
| settlement | 结算管理 |
| employee | 员工管理 |
| game | 游戏管理 |
| refund | 退款管理 |
| progress / picture | 进度管理 |
| user / staff | 用户管理 |
| merchant | 商户管理 |
| soldier / hunter | 打手管理 |
| config / setting | 系统配置 |
| message / notice | 消息通知 |
| im / chat | 即时通讯 |
| kf / ticket | 客服工单 |
| upload | 文件上传 |
| statistics / report | 数据统计 |

### 4.4 特殊情况

同路径段功能差异大时，取第二段细分：
- `order/refund/xxx` → 退款管理
- `order/publish/xxx` → 发布管理

---

## 第五步：功能点命名规则

### 5.1 方法 + 动作映射

| HTTP 方法 | 动作前缀 | 示例 |
|----------|---------|------|
| GET | 获取/查看/列表 | GET /order/{id} → 获取订单详情 |
| POST | 创建/提交 | POST /order → 创建订单 |
| PUT / PATCH | 更新/修改 | PUT /order/{id} → 更新订单 |
| DELETE | 删除 | DELETE /order/{id} → 删除订单 |
| ANY | （根据 action 推断 | |

### 5.2 常用 action 中文映射（80+）

| action | 中文名称 |
|--------|---------|
| list / index | 列表 |
| detail / show / view | 详情/查看 |
| create / store / establish | 创建 |
| edit / update / modify | 更新/修改 |
| destroy / delete / remove | 删除/移除 |
| add / save | 添加/保存 |
| get / set | 获取/设置 |
| login / logout | 登录/登出 |
| export / import | 导出/导入 |
| upload / download | 上传/下载 |
| audit / check | 审核/检查 |
| confirm / cancel | 确认/取消 |
| refund / pay | 退款/支付 |
| send / sync | 发送/同步 |
| refresh / reset | 刷新/重置 |
| status | 状态切换 |
| info / config | 获取信息/获取配置 |
| scan_login | 扫码登录 |
| batch_assign_hunter | 批量指派打手 |
| export_progress | 导出进度 |
| pub_cancel_back | 取消撤销 |
| screenshot | 上传截图 |
| exception | 提交异常 |
| revoke | 撤销 |
| apply | 申请 |
| accept | 接单/同意 |

### 5.3 无法推断时

保留原始方法名。

---

## 第六步：模块中文名称映射

| 目录名 | 模块名 |
|--------|--------|
| order | 订单模块 |
| user | 用户模块 |
| finance | 财务模块 |
| merchant | 商户模块 |
| setting | 设置模块 |
| message | 消息模块 |
| im | IM模块 |
| kf | 客服模块 |
| soldier | 打手模块 |
| statistics | 统计模块 |
| common | 通用模块 |

不在表中时，直接翻译目录名或保留原文。

---

## 第七步：相同路径不同 HTTP 方法处理

**同一个路径，不同 HTTP 方法视为不同接口：

| 路径 | 方法 | 功能点 |
|------|------|--------|
| /order/{id} | GET | 获取订单详情 |
| /order/{id} | PUT | 更新订单 |
| /order/{id} | DELETE | 删除订单 |

---

## 第八步：文档输出格式

### 整体结构参见 SKILL.md 中的「PHP 模块化项目格式」
