# http-conventions.md 生成指南

http-conventions.md 包含模块 HTTP 层（路由 / Request / Controller / 模板 / 分页）开发规范。通用部分固定输出，项目特有部分从代码扫描填充。

## frontmatter

```yaml
---
description: HTTP 接口、后台 Controller、模板与分页的开发规范
globs:
  - "modules/*/src/Http/**"
  - "modules/*/resources/views/**"
---
```

globs 覆盖所有模块的 HTTP 与视图目录，只有操作这两类文件时才加载。

## 文档结构

### 第一部分：路由生成（通用 + 项目特有）

**通用内容（固定输出）：**

```markdown
## 1. 路由生成

### 1.1 三类路由文件

每个模块在 `modules/{module}/src/Http/Routes/` 下维护三份路由文件，分别对应三类调用方：

| 文件          | 前缀                 | 典型中间件                                    | 用途                       |
| ------------- | -------------------- | --------------------------------------------- | -------------------------- |
| `api.php`     | `api/{module}/`      | `cross`, `api-sign`                           | 客户端/小程序/H5 JSON 接口 |
| `web.php`     | `{module}/`          | `cross`, `web-auth`                           | 用户工作台                 |
| `backend.php` | `{prefix}/{module}/` | `backend-auth`（RouteServiceProvider 自动加） | 管理后台                   |

### 1.2 RouteServiceProvider 注册

每模块有 `modules/{module}/src/Http/RouteServiceProvider.php`，负责把上述三份路由文件挂到对应前缀。

约定：
- `$namespace` 声明为 `{Module}\Http`，作为 Controller 的根命名空间
- Controller 按层分目录：`Web\`（用户界面）、`Backend\`（管理后台）、`Api\`（API）
- 路由文件统一使用 `[ControllerClass::class, 'method']` 数组格式引用 Controller，通过 `use` 导入完整类名
- 路由组中不再声明 `'namespace'` 键

### 1.3 路由命名与定义

| 类型    | 命名规则                             |
| ------- | ------------------------------------ |
| API     | `{module}:api.{domain}.{action}`     |
| Web     | `{module}:web.{domain}.{action}`     |
| Backend | `{module}:backend.{domain}.{action}` |

- 任何路由都必须有 `->name('xxx')`
- 业务子域用点分（如 `goods.up` / `publish_config.asset`）
- 模板统一通过 `route_url('xxx')` 反查，禁止在模板里拼 URI 字符串

### 1.4 注册到模块 ServiceProvider

模块根 `ServiceProvider.php` 的 `register()` 中必须注册 `Http\RouteServiceProvider`：

    public function register(): void
    {
        $this->app->register(RouteServiceProvider::class);
    }
```

**项目特有内容（扫描填充）：**

- 列出当前项目中最完整的某模块的 `RouteServiceProvider.php` 作为参考实现
- 列出 `modules/{module}/src/Http/Routes/` 下已存在的文件, 根据实际扫描结果补充
- 列出 `modules/{module}/src/Http/` 下已存在的文件夹（除 `Routes/`, `Middlewares/`）作为补充说明
- 若中间件有项目扩展（如 `staff_ip_confine`），补一行说明其触发条件

---

### 第二部分：Request 类编写（通用 + 项目特有）

**通用内容（固定输出）：**

```markdown
## 2. Request 类编写

### 2.1 基类选择


| 框架        | 基类                                   | 失败响应                 | 适用场景   |
| ----------- | -------------------------------------- | ------------------------ | ---------- |
| Poppy 框架  | `Poppy\Framework\Application\Request`  | 抛 `ValidationException` | 支持 scene |
| Weiran 框架 | `Weiran\Framework\Application\Request` | 抛 `ValidationException` | 支持 scene |

两类基类都暴露了相同的最小契约：`rules()` / `attributes()`, 如果需要友好提示，需要实现 `messages()` / `validated()`。

### 2.2 类模板

文件位置：`modules/{module}/src/Http/{Backend,Web,Api}/{Domain}/{Xxx}Request.php`。

类模板要点：
- 必须给类型化 getter（`getXxx(): int` 等），避免外部 `$request->input('xxx')`
- getter 内部用 `$this->input('xxx', $default)` 即可

### 2.3 命名与目录约定

 | 命名                   | 命名空间                                    |
 | ---------------------- | ------------------------------------------- |
 | `{Xxx}{Action}Request` | `{Module}\Http\<RequestDomain>\{BizDomain}` |

约定：Controller 直接放在层目录下，Request 放在 `{BizDomain}/` 子目录下。

### 2.4 校验规则速查


| 框架        | 基类                                |
| ----------- | ----------------------------------- |
| Poppy 框架  | `\Poppy\Framework\Validation\Rule`  |
| Weiran 框架 | `\Weiran\Framework\Validation\Rule` |

加载文件的公共方法便是支持的校验规则

### 2.5 自动校验

| 框架        | 基类                                   | 关闭字段                             |
| ----------- | -------------------------------------- | ------------------------------------ |
| Poppy 框架  | `Poppy\Framework\Application\Request`  | `protected bool $isValidate = false` |
| Weiran 框架 | `Weiran\Framework\Application\Request` | `protected bool $isValidate = false` |

### 2.6 Controller 里调用

通用示例（POST 走 `validated()` 触发校验 → 调 Action；）。

强制：
- 类型化 Request **必须**作为方法签名注入
- Controller / Action 内部都通过类型化 getter 取值
- `validated()` 抛异常即可，不要外层 try/catch
```

**项目特有内容（扫描填充）：**

- 列出一两个有代表性的 Request 类作为示例（覆盖两种基类）
- 将上边的固定内容中的{Poppy,Weiran}框架部分根据当前项目使用的情况, 移除没有匹配到的框架

---

### 第三部分：接口文档（通用，固定输出）

```markdown
## 3. 接口注释

### 3.1 注释位置

在 `modules/{module}/src/Http/{Backend,Web,Api,...}/{Xxx}Controller.php` 维护接口注释

### 3.2 注释写法

    /**
     * @api            {post} /api/rental/recycle_merchant/list 获取已启用的回收商户列表
     * @apiVersion     1.0.0
     * @apiName        RentalRecycleMerchantList
     * @apiGroup       回收商户
     *
     * @apiDescription 获取所有已启用状态的回收商户列表
     *
     * @apiParam {String} xxx  请求参数
     *
     *
     * @apiSuccess {Number}   status                状态码，0 表示成功
     * @apiSuccess {String}   message               提示信息
     * @apiSuccess {Object[]} data                  返回数据，商户列表
     * @apiSuccess {Number}   data.id               ID
     * @apiSuccess {String}   data.merchant_title   商家标题
     * @apiSuccess {Number}   data.shop_title       商店标题
     * @apiSuccess {String}   data.merchant_avatar  商家头像
     * @apiSuccess {String}   data.list_order       排序
     */
    public function listEnabled(XxxRequest $request)
    {
        $items = (new ActBeRecycleMerchant())->listEnabled();

        return Resp::success('操作成功', $items);
    }

api 接口使用使用json 返回, json 的默认格式是

    {
        "status": 0,
        "message": "操作成功",
        "data": []
    }

1. API 路由需要编写注释, 其他不需要
2. 路由使用 apidoc 格式注释
3. @apiParam 注释参数，格式：@apiParam {类型} {参数名} {参数描述}，参数来自于 Request 类的 getter（`getXxx(): int` 等）
4. @apiSuccess 注释返回值，格式：@apiSuccess {类型} {参数名} {参数描述}，参数来自于返回的 $items 格式, items 填充在 data 内

### 3.3 改路由后的强制动作

    php artisan route:list
    php -l modules/{module}/src/Http/RouteServiceProvider.php
    php -l modules/{module}/src/Http/Routes/{api,web,backend,...}.php

```

---

### 第四部分：用户上下文获取（通用 + 项目特有）

**通用内容（固定输出）：**

```markdown
## 4. 用户上下文获取和约定

| 框架        | 基类                                                    | 使用场景        |
| ----------- | ------------------------------------------------------- | --------------- |
| Poppy 框架  | `\Poppy\System\Http\Request\ApiV1\WebApiController`     | API 接口（JWT） |
| Weiran 框架 | `\Weiran\System\Http\Web\ApiV1\WebApiController`        | API 接口（JWT） |
| Poppy 框架  | `\Poppy\MgrPage\Http\Request\Backend\BackendController` | 后台接口        |
| Weiran 框架 | `\Poppy\MgrPage\Http\Backend\BackendController`         | 后台接口        |

### 4.1 基类暴露的上下文

| Controller 基类     | 暴露的属性                | 适用层  |
| ------------------- | ------------------------- | ------- |
| `BackendController` | `$this->pam`（可空）      | Backend |
| `WebApiController`  | `$this->pam`（JWT，可空） | API     |

### 4.2 上下文怎么被注入

业务代码只通过 `$this->pam` / `$this->parentPam` 取上下文

Action 类通过 `(new ActXxx())->setPam($this->pam)->setParentPam($this->parentPam)` 接收上下文

### 4.3 后台权限配置

Backend Controller 构造函数必须设置 `self::$permission = ['global' => 'backend:{module}.{domain}.manage'];`。

权限 slug 同步登记到 `modules/{module}/configurations/permissions.yaml`：

    backend:{module}.{domain}.manage:
      name: {中文名}
```

**项目特有内容（扫描填充）：**

- 列出三个 Controller 基类的实际命名空间路径
- 列出当前项目实际用到的 `permissions.yaml` 权限点示例
- 若某基类在本项目无 Controller 继承，写"暂无使用"
- 将上边的固定内容中的{Poppy,Weiran}框架部分根据当前项目使用的情况, 移除没有匹配到的框架

---

### 第五部分：后台 CRUD（通用，固定输出）

```markdown
## 5. 后台 CRUD（列表/编辑/删除/...）

### 5.1 标准模板

模板覆盖：index（列表+搜索+分页）→ establish（新建/编辑同路径）→ delete → ...。

### 5.2 命名约定

| 操作      | 方法名                                       | 路由 URI 模式              | 命名                                  |
| --------- | -------------------------------------------- | -------------------------- | ------------------------------------- |
| 列表      | `index(XxxRequest $request)`                 | `{domain}`                 | `{module}:backend.{domain}.index`     |
| 新建/编辑 | `establish(XxxRequest $request, $id = null)` | `{domain}/establish/{id?}` | `{module}:backend.{domain}.establish` |
| 删除      | `delete($id)`                                | `{domain}/delete/{id}`     | `{module}:backend.{domain}.delete`    |

### 5.3 Controller 与 Action 的边界

Controller 只做：取输入 / 判断 is_post / 调 Action / Resp 返回 / view 渲染。
- 严禁：直接 `DB::table()->update()` / 复杂业务校验 / 事务管理
- 严禁：`return view(...)`（Action）
- 严禁：裸用 `$request->input('xxx')` / `$request->all()` 取值；如需接收 Request 只能走其类型化 getter

### 5.4 响应语义

- 保存成功（弹窗内）`Resp::success('保存成功', '_top_reload|1')`
- 删除成功（列表内）`Resp::success('删除成功', '_reload|1')`
- 上传返回 `Resp::success('{Success Tip}', ['key' => $key, 'url' => $url])`
- 业务错误 `Resp::error($action->getError())`

### 5.5 列表页搜索参数约定

- 搜索表单用 GET 提交
- Controller 用 `$request->validated()` 取过滤参数
- 过滤逻辑用 Eloquent `->when(...)` 链式
- 翻页必须 `->appends($input)`
```

**项目特有内容（扫描填充）：**

- 从 `modules/*/src/Http/Backend/*Controller.php` 扫描所有 CRUD 控制器
- 列出一两个有代表性的 Controller 作为模板示例

---

### 第六部分：模板文件（通用 + 项目特有）

```markdown
## 6. 模板文件（Blade）

### 6.1 路径与继承

| 层                  | 目录                                                                   | 父模板                                         |
| ------------------- | ---------------------------------------------------------------------- | ---------------------------------------------- |
| Backend 列表/普通页 | `modules/{module}/resources/views/backend/{domain}/index.blade.php`    | `@extends('py-mgr-page::backend.tpl.default')` |
| Backend 弹窗表单    | `modules/{module}/resources/views/backend/{domain}/{action}.blade.php` | `@extends('py-mgr-page::backend.tpl.dialog')`  |

### 6.2模板结构

- 列表页结构（搜索 form + table + 分页 + script）
- 弹窗表单（Form::model + Form::text + Form::button）
- 常用约定（`route_url` / `request()` / `J_iframe` / `J_request` / 分页渲染）
- 子模板（`inc/*.blade.php` 用于 AJAX 片段）

### 6.3 Form 表单

Form 表单默认使用 laravelcollective/html 写法, 但是 Poppy / Weiran 框架中对此进行了扩展, 

| 框架        | 目录                                  |
| ----------- | ------------------------------------- |
| Poppy 框架  | `\Poppy\MgrPage\Classes\FormBuilder`  |
| Weiran 框架 | `\Weiran\MgrPage\Classes\FormBuilder` |

{这里补充 Form 表单对应的非继承公共方法}
```

**项目特有内容（扫描填充）：**

- 从 `modules/*/resources/views/` 扫描所有 blade 文件，统计各层模板数量
- 列出当前项目实际可用的 parent 模板路径
- 读取 Form 表单对应的非继承公共方法并列举补充

---

### 第七部分：模板中的上下文变量（通用，固定输出）

```markdown
## 7. 模板中的上下文变量

### 7.1 自动共享的全局变量

- `_pam`：BackendController 中间件注入

### 7.2 Controller 显式传入

推荐 `compact()` 或数组方式；禁止把 `$this->pam` / Action 对象传入模板。

### 7.3 KV 字典回显

列表/表单展示枚举值统一传 KV 字典，Model 提供 `kvXxx()` 静态方法。
```

**项目特有内容（扫描填充）：**

- 列出当前项目 Model 中 `kvXxx()` 方法的命名示例

---

### 第八部分：分页（通用，固定输出）

```markdown
## 8. 分页

### 8.1 Action 返回 `LengthAwarePaginator`

Action 必须返回 `LengthAwarePaginator`，`$perPage` 作为参数传入，不允许硬编码。

### 8.2 BackendController 默认 pagesize

`$this->pagesize` 由父类提供。

### 8.3 翻页保留搜索条件

必须 `->appends($input)`。

### 8.4 模板渲染

- Backend：`{!! $items->render('py-mgr-page::vendor.pagination-layui') !!}`
- Web：`{!! $items->render('vendor.pagination.full') !!}`

### 8.5 禁止事项

- 禁止 `array_slice` 手动分页
- 禁止 Controller 内联 `->paginate()` 不抽到 Action
- 禁止前端"加载更多"分页
```

---

### 第九部分：检查清单（通用，固定输出）

```markdown
## 9. 检查清单

新增接口后逐项确认：
- [ ] Controller 继承正确的基类（API/Backend/Web）
- [ ] 路由有 `->name(...)` 命名
- [ ] 类型化 Request 注入方法签名
- [ ] Request 类提供类型化 getter
- [ ] Controller 业务方法只编排流程
- [ ] 用户上下文通过 `$this->pam` / `$this->parentPam` 获取
- [ ] Backend Controller 构造函数设置 `self::$permission`
- [ ] 列表页使用 `paginate(...)` + `appends(...)`
- [ ] 模板用 `route_url(...)`
- [ ] 模板继承正确的父模板
- [ ] `docs/workflow/{module}/contracts.md` 同步更新

验证命令：

    php -l modules/{module}/src/Http/Routes/{api,web,backend}.php
    php -l modules/{module}/src/Http/Request/{Api,Backend,Web}/**/*.php
    php artisan route:list --columns=method,uri,middleware
```

**项目特有内容（扫描填充）：**

- 无（检查清单通用）
