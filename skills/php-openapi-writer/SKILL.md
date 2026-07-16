---
name: php-openapi-writer
description: 为 PHP 项目（poppy 框架）的 API 控制器补全 OpenAPI / Swagger 注解与 FormRequest 类。覆盖 Schema 命名（PHP 类名与 OpenAPI schema 名分离）、文件位置、注解风格、模块级路由前缀发现、安全风险规避、input() 残留检查等踩坑点。
triggers:
  - "/php-openapi-writer"
  - "为 X 控制器添加接口文档"
  - "X 控制器补充 OpenAPI 注解"
  - "X 接口添加 Request"
  - "X 控制器缺少 FormRequest"
  - "按照 AuthController 模式"
  - "@OA\\Post"
  - "为 poppy 模块添加 swagger 文档"
---

# php-openapi-writer

## 适用场景

为 `{poppy|modules}/<module>/src/Http/Request/ApiV1/*Controller.php` 补全 OpenAPI / Swagger 注解，或为控制器方法添加专用 `FormRequest` 类，使 swagger-ui 能完整描述接口。

## 关键约束

### 1. 注解风格

- 使用 `use OpenApi\Annotations as OA;`（注释注解 / docblock 风格），**不是** `use OpenApi\Attributes as OA;`（PHP 8 attribute 风格）。
- 新代码与目标模块参考控制器保持一致。

### 2. Schema 命名（PHP 类名 vs OpenAPI schema 名分离）

| 维度 | 命名规则 | 示例（`StsController::tempOss`） |
|------|----------|-----------------------------------|
| **PHP 类名**（`class` / `use` / type-hint） | 无前缀 | `class StsTempOssRequest extends Request` |
| **`@OA\Schema(schema=...)` 标签** | 加前缀 | `schema="PoppyAliyunOssStsTempOssRequest"` |

**Schema 名规则**：

- `poppy/<module>` → `Poppy{ModuleTag}{Dummy}{Method}{Suffix}`，其中 `{ModuleTag}` = 路径段的 PascalCase（`aliyun-oss` → `AliyunOss`、`system` → `System`）
- `modules/<module>` → `{ModuleTag}{Dummy}{Method}{Suffix}`（保留模块原前缀，例 `DemoApiDocHowRequest`）
- `BaseResponseBody` 类名不变，但 `@OA\Schema(schema="PoppySystemResponseBody")` 显式命名

完整示例对照：
- `poppy/aliyun-oss` `StsController::tempOss` → 类 `StsTempOssRequest` / schema `PoppyAliyunOssStsTempOssRequest`
- `poppy/area` `AreaController::code` → 类 `AreaCodeResponseBody` / schema `PoppyAreaAreaCodeResponseBody`（Dummy 与 ModuleTag 重名时出现双词）
- `poppy/version` `VersionController::version` → 类 `VersionVersionRequest` / schema `PoppyVersionVersionVersionRequest`（重名不省略）
- `modules/demo` `ApiDocController::how` → 类 `DemoApiDocHowRequest` / schema `DemoApiDocHowRequest`

### 3. 文件位置

- **新建** Request / ResponseBody 类放到**控制器所在文件夹的 `<Dummy>` 子目录下**：
  - `ApiV1/Web/StsController.php` → 新文件 `ApiV1/Web/Sts/`
  - `ApiV1/AuthController.php` → 新文件 `ApiV1/Auth/`
- 完整路径：`{poppy|modules}/<module>/src/Http/Request/ApiV1/<...>/<Dummy>/<Dummy><Method>Request.php`
- 旧 `Http/Validation/X.php` 已 deprecated，**新代码不再写到旧路径**。已存在的旧文件保留原位置，仅补 `@OA\Schema` 注解。

### 4. 路由前缀

- 从目标模块的 `RouteServiceProvider.php` 读取 prefix，注解 `path=` 必须从该 prefix 算起
- `system` → `api_v1/system`，`content` → `api_v1/content`，`mgr-page` → 继承父级等
- 注意历史注解里有 `api_v1_system/` 错误写法，以本模块当前声明为准

### 5. FormRequest getter 与 backward compatibility

- Getter 内部用 `$this->input(...)`，可同时读 query/body/route 参数
- 默认值 / clamp 逻辑写在 getter 内，不在 controller 里

### 6. BaseResponseBody 是全局共享基类

- 唯一定义：`Poppy\System\Http\OpenApi\BaseResponseBody`
- 引用方 `use Poppy\System\Http\OpenApi\BaseResponseBody;`
- schema 名 `PoppySystemResponseBody`
- 不要在目标模块下新建 `Http/OpenApi/BaseResponseBody.php`
- 改动 BaseResponseBody 字段会影响所有模块 swagger 文档，慎重

### 7. 安全 — 不要把开发期行为写入公开契约

- `!is_production()` 分支（如验证码泄露）绝不在 `@OA\Post description` 中描述
- 仅在代码内联注释说明

### 8. 移除遗留 `@api` 注解

- apidoc 风格 `@api {post} ...` / `@apiDescription` 等与新 `@OA\Post` 共存会导致 swagger 重复解析
- 必须彻底移除

### 9. 完成后扫描残留 `input()` 调用

```bash
grep -nE "\binput\(" <controller_file>
```

- 裸全局 `input()` 必须迁移到 Request getter
- `$request->input(...)`（FormRequest 实例方法）是允许的
- 文件上传的 `Request::file(...)` 是允许的
- 每条残留需在汇报中列出（行号 + 上下文），由调用方决定保留/迁移/删除

## 工作流

### 步骤 1：模块级侦察

```bash
# 0. 来源根
ls poppy/<module>/src/Http/Request/ApiV1/ 2>/dev/null || ls modules/<module>/src/Http/Request/ApiV1/

# 1. 参考控制器（通常是 AuthController）
ls {poppy|modules}/<module>/src/Http/Request/ApiV1/

# 2. 路由前缀
grep -E "prefix" {poppy|modules}/<module>/src/Http/RouteServiceProvider.php

# 3. 路由注册
cat {poppy|modules}/<module>/src/Http/Routes/*.php

# 4. 已有 Request / ResponseBody
ls {poppy|modules}/<module>/src/Http/Request/ApiV1/*/

# 5. 旧 Request 迁移状态（@deprecated）
grep -l "@deprecated" {poppy|modules}/<module>/src/Http/Validation/*.php

# 6. 已有 @OA\Tag
grep -rn "@OA.Tag" {poppy|modules}/<module>/src/Http/Request/ApiV1/

# 7. BaseResponseBody 全局共享
ls poppy/system/src/Http/OpenApi/BaseResponseBody.php
grep -rn "use Poppy\\\\System\\\\Http\\\\OpenApi\\\\BaseResponseBody" {poppy|modules}/
```

输出：`<MODULE>`（路径段）、`<MODULE_TAG>`（PascalCase）、`<PREFIX>`、参考控制器名。

### 步骤 2：阅读参考控制器

读该模块 `AuthController`（或同级）确定 `@OA\Tag`、`@OA\Post` 样板、中间件组（`api-sign` / `sys-jwt` / `api-sso`）。

### 步骤 3：设计 Schema

每个方法列表：
- 字段名 / 类型 / 必填 / 描述
- `required` 与 `Rule::required()` 一致
- `enum` 抄 `Rule::in([...])` 常量
- `default` / `minimum` / `maximum` 与运行时 clamp 一致
- nullable 字段必须 `nullable=true` + `Rule::nullable()`

### 步骤 4：创建 Schema 类

按"文件位置"约束放到 `<Dummy>/` 子目录下，namespace 与目录对应：

```php
<?php
declare(strict_types = 1);

namespace Poppy\{Module}\Http\Request\ApiV1\{Dummy};

use OpenApi\Annotations as OA;
use Poppy\Framework\Application\Request;
use Poppy\Framework\Validation\Rule;

/**
 * @OA\Schema(
 *     schema="Poppy{ModuleTag}{Dummy}{Method}Request",
 *     description="...",
 *     required={"..."},
 *     @OA\Property(property="...", type="string", description="..."),
 *     ...
 * )
 */
class {Dummy}{Method}Request extends Request
{
    public function get{Field}(): string
    {
        return (string) $this->input('{field}', '');
    }

    public function attributes(): array { return [...]; }
    public function rules(): array     { return [...]; }
}
```

### 步骤 5：创建 ResponseBody 类

```php
<?php
declare(strict_types = 1);

namespace Poppy\{Module}\Http\Request\ApiV1\{Dummy};

use OpenApi\Annotations as OA;
use Poppy\System\Http\OpenApi\BaseResponseBody;   // 全局共享基类

/**
 * @OA\Schema(
 *     schema="Poppy{ModuleTag}{Dummy}{Method}ResponseBody",
 *     description="..."
 * )
 */
class {Dummy}{Method}ResponseBody extends BaseResponseBody
{
    /**
     * @OA\Property(type="object",
     *     @OA\Property(property="...", type="string", description="..."))
     */
    public object $data;
}
```

### 步骤 6：改造 Controller

类级 docblock：

```php
/**
 * <中文描述>
 *
 * @OA\Tag(name="{MODULE_TAG}", description="<模块描述>")
 */
```

方法级 docblock（POST 例）：

```php
/**
 * @OA\Post(
 *     path="{PREFIX}/{action}",
 *     tags={"{MODULE_TAG}"},
 *     summary="[{Dummy}]{简短描述}",
 *     description="<详细描述, 仅描述生产契约>",
 *     @OA\RequestBody(
 *         required=true,
 *         @OA\MediaType(
 *             mediaType="application/json",
 *             @OA\Schema(ref="#/components/schemas/Poppy{ModuleTag}{Dummy}{Method}Request")
 *         )
 *     ),
 *     @OA\Response(
 *         response=200,
 *         description="<成功描述>",
 *         @OA\JsonContent(ref="#/components/schemas/Poppy{ModuleTag}{Dummy}{Method}ResponseBody")
 *     ),
 * )
 */
public function {action}({Dummy}{Method}Request $request) { ... }
```

方法体内：裸 `input('xxx')` 替换为 `$request->getXxx()`，controller 内 clamp 搬到 getter。

### 步骤 7：验证

```bash
# 语法
php -l <每个修改的文件>

# 遗留 @api
grep -n "@api" <controller>     # 应返回空

# schema ref 都有定义
grep -rn 'schema="Poppy<.*>' {poppy|modules}/<module>/src/

# 路由前缀与 path 一致
grep -E "prefix" RouteServiceProvider.php

# 残留 input()
grep -nE "\binput\(" <controller>
```

## 不在范围内

- 不修改业务类（Action / Model / Event）
- 不调整路由 / 中间件 / RouteServiceProvider
- 不引入新 composer 依赖

## 常见错误

1. **跨模块照搬 prefix** —— 必须从本模块 `RouteServiceProvider` 读
2. **重复 schema 名** —— 引用端 ref 不存在
3. **保留 `@api` 注解** —— swagger 重复解析
4. **clamp 写在 controller** —— 应搬到 getter
5. **`!is_production()` 行为写入 description** —— 安全风险
6. **忘记 `nullable=true`** —— Swagger UI 提示必填，与运行时冲突
7. **写到 `Http/Validation/`** —— 已 deprecated
8. **Schema 前缀与 `@OA\Tag` 不一致** —— 接口归类与命名脱节
9. **使用 `OpenApi\Attributes` style** —— 与现有注解风格冲突
10. **类名被 sed 误加 Poppy 前缀** —— 改 schema 名时只动 `@OA\Schema` 字符串，不动 `class`/`use`/type-hint

## 参考文件（system 模块范例）

- `poppy/system/src/Http/Request/ApiV1/AuthController.php` —— 注解风格基线
- `poppy/system/src/Http/Request/ApiV1/Auth/Auth*.php` —— Request / ResponseBody 范例
- `poppy/system/src/Http/OpenApi/BaseResponseBody.php` —— 通用响应基类
- `poppy/system/src/Http/RouteServiceProvider.php` —— 路由前缀声明
