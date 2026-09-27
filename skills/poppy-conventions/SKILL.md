---
name: poppy-conventions
description: |
  Poppy 模块化框架的代码规范手册 + bash 静态预检脚本（基于 `poppy/core/src/Commands/InspectCommand.php`
  的 `py-core:inspect` 规则整理）。当用户在 Poppy 项目下新建/重构/审查 PHP 模块代码时使用：包括命名规范、
  文件结构、PHPDoc 注释、路由命名、权限定义、SEO/翻译键、验证规则中文化等。无论用户是否显式提到 inspect、
  py-core、命名规范或模块约定，只要在 Poppy 仓库中处理 `poppy/*/src/...` 下的代码，就应该调用本技能。
  如果用户希望在不启动 Laravel/PHP runtime 的前提下快速跑一遍规则检查，可直接调用 `scripts/poppy-inspect.sh`
  这个静态分析脚本（毫秒级返回）。涉及运行 PHP artisan 命令本身则不属于本技能范围。
metadata:
  type: reference
---

# Poppy 模块代码规范手册

本规范源自 `py-core:inspect` 命令的执行逻辑（`poppy/core/src/Commands/InspectCommand.php`）。
所有规则都通过 `php artisan py-core:inspect` 强制检查；写作或审查代码时主动遵守，可以避免 inspect 报错。

## 触发场景

- 在 `poppy/<module>/src/` 下新增类、控制器、Action、Model、Policy、Event、Listener、Command。
- 重构/补全现有代码的 PHPDoc、命名、注释。
- PR 或 diff 级别的代码审查。
- 设计新模块的目录结构、路由命名、权限点、翻译键。
- 用户提到「py-core:inspect」「命名规范」「命名约定」「代码检查」时直接调用。
- 用户希望快速静态检查（不跑 PHP）— 调用 `scripts/poppy-inspect.sh`。

---

## 1. 目录与文件结构

每个模块位于 `poppy/<slug>/src/` 下，使用下列约定目录：

| 目录                    | 用途                     | 文件名约定                              |
|-------------------------|--------------------------|-----------------------------------------|
| `src/Action/`           | 业务逻辑单元             | 自由命名（见 §2 驼峰）                  |
| `src/Models/`           | Eloquent 模型            | 自由命名                                |
| `src/Models/Policies/`  | 授权策略                 | 必须以 `Policy` 结尾                    |
| `src/Events/`           | 事件                     | 必须以 `Event` 结尾                     |
| `src/Listeners/`        | 监听器                   | 必须以 `Listener` 结尾                  |
| `src/Http/Request/`     | 请求/控制器（含子类）    | `*Controller.php` 或 `*Request.php`     |
| `src/Http/Routes/`      | 路由文件                 | 不参与 inspect 检查                     |
| `src/Commands/`         | Artisan 命令             | 自由命名                                |
| `src/Services/`         | 服务类                   | 自由命名                                |
| `src/Listeners/Middlewares/` | 中间件                | 自由命名                                |

**检查豁免（不会触发报错）：**
- `functions.php`
- `*ServiceProvider.php`
- `src/Http/Routes/` 下的所有文件
- 非 `.php` 文件

---

## 2. 命名规范（驼峰）

所有自定义类名、方法名、属性名必须满足 `Str::camel($name) === $name`。

✅ 正确：`$userInfo`、`getUserInfo()`、`PamAccount`  
❌ 错误：`$user_info`、`GetUserInfo()`、`pam_account`

模块命名空间（来自 `className()` 方法）：

| Slug 前缀        | 命名空间                            | 命令前缀    |
|------------------|-------------------------------------|-------------|
| `poppy.<name>`   | `Poppy\<Name>\...`                  | `py-<name>` |
| `poppy.ext-<x>`  | `Poppy\Extension\<X>\...`           | `py-<x>`    |
| `module.<name>`  | `<Name>\...`（首字母大写驼峰）      | `<name>`    |

translation 键前缀规则相同：`poppy.system` → `py-system::`，`module.foo` → `foo::`。

---

## 3. PHPDoc 注释规范

`py-core:inspect` 严格检查以下位置是否有完整注释，缺失或不全都会列出：

### 3.1 类级别

```php
/**
 * 简短的中文/英文功能说明
 */
class PamAccount
{
}
```

### 3.2 属性

每个非继承、非豁免属性必须有 `@var` 三段式（类型 + 变量名 + 描述）：

```php
/**
 * @var array $userInfo 用户信息缓存
 */
private array $userInfo = [];
```

**自动豁免的属性（不需要注释）：**
- Model (`*\\Models\\*`) 中的 `timestamps / table / fillable / primaryKey / dates`
- Command (`*\\Commands\\*`) 中的 `signature / description`

### 3.3 方法

```php
/**
 * 获取用户信息
 *
 * @param int     $userId 用户编号
 * @param bool    $withProfile 是否返回 profile
 * @return array{id:int, name:string}
 * @throws ReflectionException
 */
public function getUserInfo(int $userId, bool $withProfile = false): array
{
    // ...
}
```

**自动豁免的方法：**
- 魔术方法（以 `__` 开头）
- 继承自父类的方法（`$method->class !== 当前类` 直接跳过）
- `Listeners/`、`Middlewares/` 下的 `handle()`
- `Action/` 中的 `private/protected/__construct/get*/set*` 方法

**校验标记：** 方法 PHPDoc 中出现 `@verify` 即视为「已审核通过」，inspect 会跳过警告。

### 3.4 控制器（Http/Request）

控制器方法注释必须包含 `@api`，格式如下：

```php
/**
 * 登录接口
 *
 * @api {(post)} /api/v1/auth/login 用户名密码登录
 */
public function login(LoginRequest $request): JsonResponse
{
    // ...
}
```

支持 `post|get` 两种 HTTP 谓词，inspect 会从 `@api {(post|get)} /path ...` 中提取路径和描述。

---

## 4. 权限定义（perms）

权限点来源 3 处，必须保持一致：

1. **Request 控制器**：声明 `public static array $permission = [...]`
2. **Policy 类**：实现 `public static function getPermissionMap(): array`
3. **菜单（CoreModule::menus）**：在 `groups.children[].permission` 字段声明使用

`py-core:inspect perms` 会输出两类问题：
- **Defined But Not Used**：权限定义了但没有任何菜单/路由引用。
- **Used But Not Defined**：菜单/路由引用了但未在系统权限表中注册。

新增权限时三处必须同步更新。

---

## 5. 路由命名（SEO）

路由名必须匹配正则 `(.+?):(.+?)\.(.+?)\.(.+?)`，即 `{module}:{group}.{action}.{sub}` 四段式。

✅ 正确：`pam:auth.login`、`content:web.article.edit`  
❌ 错误：`pam-auth-login`（缺冒号）、`pam.auth.login`（缺冒号）

每个路由必须有对应的翻译键，规则：

```
路由名                → 翻译键
pam:auth.login       → pam::auth_login
content:web.article  → content::web_article
```

inspct 输出「Missing Seo Names」即说明翻译键缺失。API 路由（以 `api` 开头的翻译键）可豁免。

---

## 6. 翻译键（util/policy/trans）

`util` 检查以下两类键必须存在翻译：

- **Policy 方法**：`{prefix}::util.policy.{snake_model}.{method}`
- **Model 名称**：`{prefix}::util.classes.models.{snake_model}`

举例（模块 slug = `poppy.system`，模型 = `PamAccount`，Policy 方法 = `view`）：

```
py-system::util.policy.pam_account.view
py-system::util.classes.models.pam_account
```

`trans` 检查：导出单个文件后扫描 `trans('...')` / `trans("...")` 调用，凡是翻译值与键相等（即未翻译）的都会列出。

---

## 7. 验证规则（validation）

`py-core:inspect validation` 通过反射扫描 `Poppy\Framework\Validation\Rule` 的所有方法（排除
`mixin/hasMacro/__callStatic/__call/macro`），生成形如下面的翻译键：

- 普通方法：`{method_name}`（snake_case，去掉 `:`）
- `min/max/size/between`：展开为 `{method}.{numeric|file|string}` 三种

**所有这些键必须提供中文翻译。** 例：

```php
// lang/zh_CN/validation.php
'required' => ':attribute 不能为空',
'min.numeric' => ':attribute 不能小于 :min',
'min.file'    => ':attribute 文件不能小于 :min KB',
'min.string'  => ':attribute 长度不能小于 :min',
```

---

## 8. 代码审查清单（写作时自检）

写作或修改 Poppy 代码后，对照下列清单快速验证：

- [ ] 文件放在约定的 `src/<目录>/` 下，且符合文件名后缀规则（Event/Listener/Policy）
- [ ] 类名、方法名、属性名通过 `Str::camel($x) === $x`
- [ ] 类有简短 PHPDoc 描述
- [ ] 每个属性有 `@var 类型 $name 描述`
- [ ] 每个 public 方法有 PHPDoc，且 `@param` 包含「类型 + 变量名 + 描述」
- [ ] 控制器方法带 `@api {(post|get)} /path 描述`
- [ ] 必要时加 `@throws` 与 `@verify`（已审过）
- [ ] Request 控制器 `static $permission` 与 Policy `getPermissionMap()`、菜单声明一致
- [ ] 路由名符合 `{module}:{group}.{action}.{sub}` 并配齐翻译键
- [ ] Policy/Model 的 `util.*` 翻译键全部存在
- [ ] 涉及的 `Rule::*` 验证规则有中文翻译

---

## 9. 常用检查命令

### 9.1 完整检查（启动 Laravel runtime）

```bash
# 全部检查
php artisan py-core:inspect

# 单项检查
php artisan py-core:inspect class
php artisan py-core:inspect file
php artisan py-core:inspect controller
php artisan py-core:inspect action
php artisan py-core:inspect util
php artisan py-core:inspect perms
php artisan py-core:inspect validation
php artisan py-core:inspect seo

# 仅检查某个模块
php artisan py-core:inspect class --module=poppy.system

# 只加载类不打印（CI 阶段使用）
php artisan py-core:inspect class --class_load_only

# 导出文件中所有 trans 键并审查
php artisan py-core:inspect trans --export=app/Http/Controllers/Foo.php
```

跑完全部无报错时，inspect 会逐项输出 `So good, You did not has bad design.` / `Beautiful, Name rules are matched.` 等正面提示。

### 9.2 静态预检（bash,毫秒级,免 PHP runtime）

随本技能附带 `scripts/poppy-inspect.sh`,镜像 `py-core:inspect` 中**可纯静态判定**的规则,
不必启动 Laravel/Composer autoload 即可在编辑器保存钩子或 pre-commit 中跑。

```bash
# 全部模块全部类型
~/.claude/skills/poppy-conventions/scripts/poppy-inspect.sh -r ./poppy

# 仅 system 模块
~/.claude/skills/poppy-conventions/scripts/poppy-inspect.sh -r ./poppy -m poppy.system

# 只跑某些类型 (file / class / controller / action / util)
~/.claude/skills/poppy-conventions/scripts/poppy-inspect.sh -r ./poppy -t file -t class

# 退出码: 0=全部通过, 1=有违规, 2=参数错误
```

**覆盖范围**:
- ✅ `file`  Events/Listeners/Policies 文件名后缀
- ✅ `class` 类/属性/方法 PHPDoc、@param 三段式、camelCase 命名
- ✅ `controller` Http/Request 下方法必须有 `@api`
- ✅ `action` Action 类 public 业务方法必须有 PHPDoc
- ✅ `util` Policy/Model 翻译键是否在 `resources/lang/*.php` 中已注册

**不覆盖**(需跑原 PHP 命令):
- ❌ `perms`   — 需要路由表 + 菜单交叉对比
- ❌ `seo`     — 需要 `\Route::getRoutes()`
- ❌ `trans`   — 需要 `trans()` 实际取值
- ❌ `validation` — 需要反射扫描 `Rule` 类方法

**违规码速查**:
| 违规码             | 含义                                | 对应 inspect 类型   |
|--------------------|-------------------------------------|---------------------|
| `[class-doc-missing]`   | 类缺少顶层 docblock           | class               |
| `[method-doc-missing]`  | public 方法缺少 docblock      | class / action      |
| `[param-incomplete]`    | `@param` 缺类型/变量名/描述   | class               |
| `[api-missing]`         | 控制器方法缺 `@api`           | controller          |
| `[action-doc-missing]`  | Action 业务方法缺 docblock    | action              |
| `[util-missing]`        | Policy/Model 翻译键未注册     | util                |
| Events 文件未以 `Event.php` 结尾 |       | file                |
| Listeners 文件未以 `Listener.php` 结尾 |   | file                |
| Policies 文件未以 `Policy.php` 结尾 |     | file                |

### 9.3 本仓库首次基线（参考数字）

在当前 dev-v4 分支对 18 个模块跑完整 bash 检查,得到：

| 违规类型             | 数量  |
|----------------------|-------|
| `class-doc-missing`  | 281   |
| `method-doc-missing` | 49    |
| `param-incomplete`   | 1417  |
| `api-missing`        | 109   |
| `util-missing`       | 17    |

最大头是 `@param` 描述缺失,占总违规的 **~75%** — 优先补齐 `@param` 收益最高。

---

## 10. 反例速查

| 反例                                                | 正确做法                                    |
|-----------------------------------------------------|---------------------------------------------|
| `class pam_account`                                 | `class PamAccount`                          |
| `public function Get_User($Id)`                     | `public function getUser(int $id)`          |
| `@param $userId 用户编号`                           | `@param int $userId 用户编号`               |
| `src/Events/LoginFailed.php`                        | `src/Events/LoginFailedEvent.php`           |
| `src/Models/Policies/PamAccount.php`                | `src/Models/Policies/PamAccountPolicy.php`  |
| 路由 `pam-auth-login`                               | 路由名 `pam:auth.login`                     |
| Policy 加方法不写 `py-system::util.policy.*` 翻译  | 同步在 `lang/zh_CN/...` 增加键值            |
| 加新验证规则不写中文                                 | 在 `validation.php` 补齐 `snake_case` 键   |
| 在 Model 里给 `fillable` 写 `@var`                  | 直接不写，inspect 自动豁免                  |

---

## 关键参考文件

- `poppy/core/src/Commands/InspectCommand.php` — 检查命令主入口
- `poppy/core/src/Classes/Inspect/CommentParser.php` — PHPDoc 解析器（`@param/@property/@verify`）
- `poppy/framework/src/Validation/Rule.php` — 验证规则来源（被 inspect validation 反射扫描）
- `poppy/core/src/Module/CoreModule.php` — `menus()` 权限声明来源

**写作时遵循这套规范，就是符合 `py-core:inspect` 预期的「干净」代码。**
