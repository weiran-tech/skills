---
name: fe-backend-page
description: 生成后台管理项目（Vue3 + TDesign + kr36-ui 技术栈）的标准页面（包含搜索、表格列表、表单弹窗提交）。当用户想要新建或重构一个包含增删改查、列表页或管理页面的 Vue 页面时使用。遇到用户描述"新建一个页面"、"增加管理功能"、"做一个列表页"、"加一个增删改查"时，必须使用此技能。
---

# 后台管理项目标准页面生成规范

生成基于 Vue 3 + TypeScript + TDesign + kr36-ui 封装组件的后台管理项目页面时，必须严格遵循以下规范。适用于所有采用该技术栈的后台项目（如 backend-kejinshou 等）。

> **依赖技能：** 组件库 API 详情请参考 `fe-kr36-ui-guide` 技能。该技能包含 KrCard、KrForm、KrTable、KrDialog、KrButton 等所有 kr36-ui 组件的完整 Props/Slots/Events 文档和 KrForm schema 示例。

> **项目特有约定：** 本技能只约定**页面结构与组件用法**这一通用层。各项目特有的部分——**权限对接**（权限接口地址、命名规则、注册流程）、**接口获取方式**（如 Apifox MCP）等——以目标项目根目录 `CLAUDE.md` 中的约定为准。目标项目的 `CLAUDE.md` 会自动加载进上下文，直接取其中参数即可，无需额外 Read。

## 1. 整体结构规范

- 使用 `<script setup lang="jsx">`（必须是 jsx，表格列需要 JSX 渲染）
- **组件优先级**：优先使用 kr36-ui 封装组件（KrCard、KrForm、KrTable、KrDialog、KrButton、KrTabs），仅在封装组件无法满足时才用 tdesign 原生组件，**绝不**引入 ElementPlus 等其他库
- 样式使用 `<style lang="less" scoped>`，**禁止内联样式**，通过 class 控制
- 代码需包含清晰的中文注释

## 2. 核心组件使用规范

**外层容器**
```vue
<KrCard title="页面标题">
    <template #actions>
        <KrButton v-isAuth="['<权限key>']" @click="handleAdd('add', {})">新增</KrButton>
    </template>
    <!-- 内容 -->
</KrCard>
```

> 权限 key 的具体取值、命名规则与注册流程，见目标项目 `CLAUDE.md` 的「权限对接」约定。

**搜索表单**（当搜索表单前面有 KrTabs 等组件时，需加 `class="table-wrapper"` 保持 8px 间距）
```vue
<!-- 无 Tabs 时 -->
<KrForm :layout="'inline'" :schema="searchSchema" :submit="submitSearch" :reset="resetSearch">
    <KrButton type="submit">搜索</KrButton>
    <KrButton theme="default" variant="base" type="reset">重置</KrButton>
</KrForm>

<!-- 有 Tabs 时，KrForm 需加 class="table-wrapper" -->
<KrTabs type="filter" :active="games.active" :list="games.list" @change="gameChange" />
<KrForm class="table-wrapper" :layout="'inline'" :schema="searchSchema" :submit="submitSearch" :reset="resetSearch">
    <KrButton type="submit">搜索</KrButton>
    <KrButton theme="default" variant="base" type="reset">重置</KrButton>
</KrForm>
```

**数据表格**（`class="table-wrapper"` 直接加在 KrTable 上，保持与搜索表单 8px 间距）
```vue
<KrTable
    class="table-wrapper"
    row-key="id"
    :data="dataList"
    :columns="columns"
    :pagination="pagination"
    :max-height="maxHeight"
    @page-change="onPageChange"
>
    <template #empty>暂无数据</template>
</KrTable>
```

**弹窗表单**
```vue
<KrDialog :visible="dialog.visible" :footer="false" :header="dialog.header" :close="dialog.close">
    <KrForm label-align="top" :label-width="60" :rules="dialog.rules" :schema="dialog.schema" :submit="dialog.submit">
        <div class="dialog-footer">
            <KrButton theme="default" @click="dialog.close">取消</KrButton>
            <KrButton type="submit">确定</KrButton>
        </div>
    </KrForm>
</KrDialog>
```

> **操作列按钮规范**
> 操作列按钮**必须使用 `KrButton size="small" variant="text"`**，禁止使用 `t-link`。
> `KrButton` 自带间距，外层用普通 `<div>` 包裹即可：
> ```jsx
> cell: (h, { row }) => (
>     <div>
>         <KrButton size="small" variant="text" onClick={() => handleView(row)}>查看</KrButton>
>         <KrButton size="small" variant="text" theme="danger" onClick={() => handleDelete(row)}>删除</KrButton>
>     </div>
> )
> ```

## 3. 完整页面模板

```vue
<template>
    <KrCard title="页面标题">
        <!-- 操作栏 -->
        <template #actions>
            <KrButton v-isAuth="['<权限key>']" @click="handleAdd('add', {})">新增</KrButton>
        </template>

        <!-- 搜索表单 -->
        <KrForm :layout="'inline'" :schema="searchSchema" :submit="submitSearch" :reset="resetSearch">
            <KrButton type="submit">搜索</KrButton>
            <KrButton theme="default" variant="base" type="reset">重置</KrButton>
        </KrForm>

        <!-- 数据表格 -->
        <KrTable
            row-key="id"
            :data="dataList"
            :columns="columns"
            :pagination="pagination"
            :max-height="maxHeight"
            @page-change="onPageChange"
        >
            <template #empty>暂无数据</template>
        </KrTable>

        <!-- 新增/编辑弹窗 -->
        <KrDialog :visible="dialog.visible" :footer="false" :header="dialog.header" :close="dialog.close">
            <KrForm label-align="top" :label-width="60" :rules="dialog.rules" :schema="dialog.schema" :submit="dialog.submit">
                <div class="dialog-footer">
                    <KrButton theme="default" @click="dialog.close">取消</KrButton>
                    <KrButton type="submit">确定</KrButton>
                </div>
            </KrForm>
        </KrDialog>
    </KrCard>
</template>

<script setup lang="jsx">
import { get } from 'lodash';
import { DialogPlugin } from 'tdesign-vue-next';
import { onMounted, reactive, ref } from 'vue';

// 导入接口（按实际业务替换）
import { reqXxxAdd, reqXxxDelete, reqXxxEdit, reqXxxPage } from '@/services/xxx/xxxApi';
import { Perms } from '@/services/permissions';
import { toast } from '@/utils/helper';
import { isPermission, WindowHeight } from '@/utils/utils';

// 表格最大高度，适配屏幕
const maxHeight = WindowHeight() - 260;

// --- 搜索相关 ---
const searchValue = ref({});

// 搜索表单字段配置
const searchSchema = reactive([
    {
        component: 'Input',
        prop: 'keyword',
        props: {
            clearable: true,
            placeholder: '请输入关键字',
        },
    },
    {
        component: 'Select',
        prop: 'status',
        props: {
            clearable: true,
            placeholder: '请选择状态',
            options: [
                { label: '启用', value: 1 },
                { label: '禁用', value: 0 },
            ],
        },
    },
]);

// 提交搜索：重置到第一页再查询
const submitSearch = async (value) => {
    pagination.current = 1;
    searchValue.value = JSON.parse(JSON.stringify(value));
    await fetchData();
};

// 重置搜索
const resetSearch = async () => {
    pagination.current = 1;
    searchValue.value = {};
    await fetchData();
};

// --- 列表与分页 ---
const dataList = ref([]);
const pagination = reactive({
    current: 1,
    pageSize: 20,
    total: 0,
});

// 表格列定义
const columns = [
    {
        // 序号列：根据当前页码和页大小计算
        colKey: 'serial-number',
        title: '序号',
        width: 80,
        align: 'center',
        cell: (h, { rowIndex }) => (pagination.current - 1) * pagination.pageSize + rowIndex + 1,
    },
    {
        colKey: 'name',
        title: '名称',
        align: 'center',
    },
    {
        // 状态列：用 JSX 渲染标签/文字
        colKey: 'status',
        title: '状态',
        align: 'center',
        cell: (h, { row }) => {
            const status = get(row, 'status', -1);
            if (status === 1) return <t-tag theme="success">启用</t-tag>;
            if (status === 0) return <t-tag theme="danger">禁用</t-tag>;
            return '-';
        },
    },
    {
        colKey: 'operation',
        title: '操作',
        width: 150,
        align: 'center',
        fixed: 'right',
        cell: (h, { row }) => {
            // JSX 中用 isPermission 判断权限（权限常量约定见项目 CLAUDE.md）
            const hasEdit = isPermission(Perms.XxxEdit);
            const hasDel = isPermission(Perms.XxxDelete);
            return (
                <div>
                    {hasEdit && (
                        <KrButton size="small" variant="text" onClick={() => handleAdd('edit', row)}>编辑</KrButton>
                    )}
                    {hasDel && (
                        <KrButton size="small" variant="text" theme="danger" onClick={() => handleDelete(row)}>删除</KrButton>
                    )}
                </div>
            );
        },
    },
];

// 获取列表数据
const fetchData = async () => {
    try {
        const params = {
            page: pagination.current,
            size: pagination.pageSize,
            ...searchValue.value,
        };
        const { success, data, message } = await reqXxxPage(params);
        if (success) {
            dataList.value = get(data, 'list', []);
            pagination.total = get(data, 'pagination.total', 0);
        } else {
            toast(message, success);
        }
    } catch (error) {
        console.error('Fetch data error:', error);
    }
};

// 分页变化
const onPageChange = (pageInfo) => {
    pagination.current = pageInfo.current;
    pagination.pageSize = pageInfo.pageSize;
    fetchData();
};

// --- 弹窗表单 ---
const dialog = reactive({
    row: null,
    type: '', // 'add' | 'edit'
    header: '',
    visible: false,
    rules: {},
    schema: [],
    close: () => {
        dialog.visible = false;
        dialog.row = null;
        dialog.schema = [];
        dialog.rules = {};
    },
    submit: async (value) => {
        const params = JSON.parse(JSON.stringify(value));
        try {
            const api = dialog.type === 'add' ? reqXxxAdd : reqXxxEdit;
            if (dialog.type === 'edit') params.id = dialog.row?.id;
            const { success, message } = await api(params);
            if (success) {
                dialog.close();
                fetchData();
            }
            toast(message, success);
        } catch (error) {
            console.error('Submit error:', error);
        }
    },
});

// 打开新增或编辑弹窗
const handleAdd = (type = 'add', row = {}) => {
    dialog.row = row;
    dialog.type = type;
    dialog.header = type === 'add' ? '新增' : '编辑';
    dialog.rules = {
        name: [{ required: true, message: '请输入名称', type: 'error' }],
    };
    dialog.schema = [
        {
            component: 'Input',
            label: '名称',
            prop: 'name',
            default: get(row, 'name', ''), // lodash get 安全取值，避免 undefined
            props: { placeholder: '请输入名称' },
        },
        {
            component: 'Select',
            label: '状态',
            prop: 'status',
            default: get(row, 'status', 1),
            props: {
                options: [
                    { label: '启用', value: 1 },
                    { label: '禁用', value: 0 },
                ],
            },
        },
    ];
    dialog.visible = true;
};

// 删除操作（带二次确认）
const handleDelete = (row) => {
    const confirmDialog = DialogPlugin.confirm({
        header: '确认删除',
        body: '确定要删除该记录吗？',
        onConfirm: async () => {
            try {
                const { success, message } = await reqXxxDelete({ id: row.id });
                if (success) {
                    confirmDialog.hide();
                    fetchData();
                }
                toast(message, success);
            } catch (error) {
                console.error('Delete error:', error);
            }
        },
    });
};

onMounted(() => {
    fetchData();
});
</script>

<style lang="less" scoped>
.dialog-footer {
    display: flex;
    justify-content: flex-end;
    width: 100%;
    gap: 8px;
}

// 表格与搜索表单间距（8px）
.table-wrapper {
    margin-top: 8px;
}
</style>
```

## 4. 常用列渲染模式

> 注：下面枚举映射里的 `|| '-'` 是「字典查不到时的兜底」，与第 9 节「禁止在 `get()` 默认值后再叠加 `|| '--'`」不冲突——后者针对的是 `get(obj, 'x', 默认值) || '--'` 这种重复兜底。

```js
// 枚举值映射（先定义字典再用）
const TYPE_MAP = { 1: '正常', 2: '异常', 3: '未知' };
{ colKey: 'type', title: '类型', cell: (h, { row }) => TYPE_MAP[row.type] || '-' }

// 状态内联开关：列表里直接 switch 切换，调用 update_status 接口，成功后刷新
{
    colKey: 'status',
    title: '状态',
    align: 'center',
    cell: (h, { row }) => {
        const status = get(row, 'status', 0);
        const canEdit = isPermission(Perms.XxxUpdateStatus); // 无权则禁用开关
        return (
            <t-switch value={status === 1} disabled={!canEdit} onChange={(val) => handleStatusChange(row, val)} />
        );
    },
}
// const handleStatusChange = async (row, val) => {
//     const { success, message } = await reqXxxUpdateStatus({ id: get(row, 'id'), status: val ? 1 : 0 });
//     if (success) await fetchData();
//     toast(message, success);
// };

// 金额（分转元）
{ colKey: 'amount', title: '金额', cell: (h, { row }) => `¥${(get(row, 'amount', 0) / 100).toFixed(2)}` }

// 时间格式化
{ colKey: 'createdAt', title: '创建时间', cell: (h, { row }) => get(row, 'createdAt', '-') }

// 可点击链接
{ colKey: 'id', title: 'ID', cell: (h, { row }) => (
    <t-link theme="primary" onClick={() => handleDetail(row)}>{row.id}</t-link>
) }

// 纯展示字段无需 cell 函数，KrTable cellEmptyContent 默认显示 '-'
{ colKey: 'name', title: '名称', align: 'center' }
```

## 5. Service 文件规范

服务文件放在 `src/services/<模块名>/` 下，统一使用 `req` 前缀命名。**所有接口 URL 必须先提取为顶部导出对象常量，函数体内引用对象属性，禁止在函数内硬编码 URL 字符串。**

```typescript
// src/services/xxx/xxxApi.ts
import { request } from '@/utils/request';

// ===== 接口地址 =====

export const xxx = {
    page: '/api/xxx/v1/page',     // 分页查询
    create: '/api/xxx/v1/create', // 新增
    update: '/api/xxx/v1/update', // 编辑
    delete: '/api/xxx/v1/delete', // 删除
    detail: '/api/xxx/v1/detail', // 详情（GET 拼接 /{id}）
    recordPage: '/api/xxx/v1/record_page', // 操作记录
};

// ===== 接口函数 =====

export async function reqXxxPage(data: any) {
    return request.post({ url: xxx.page, data });
}

export async function reqXxxAdd(data: any) {
    return request.post({ url: xxx.create, data });
}

export async function reqXxxEdit(data: any) {
    return request.post({ url: xxx.update, data });
}

export async function reqXxxDelete(data: { id: number | string }) {
    return request.post({ url: xxx.delete, data });
}

export async function reqXxxDetail(data: { id: number | string }) {
    return request.get({ url: `${xxx.detail}/${data.id}` });
}
```

> 接口定义（URL、入参、出参）来源因项目而异（如 Apifox MCP），以目标项目 `CLAUDE.md` 的约定为准。

## 6. 路由配置规范

路由文件放在 `src/router/modules/<模块名>.ts`，路由通过 `import.meta.glob('./modules/**/!(homepage).ts', { eager: true })` 自动发现，无需手动注册。

```typescript
// src/router/modules/xxx.ts
import { Perms } from '@/services/permissions';
import { LAYOUT } from '@/utils/route/constant';

export default [
    {
        path: '/xxx',
        name: 'xxxConfig',
        component: LAYOUT,
        redirect: '/',
        meta: { title: 'XXX管理', icon: 'setting', orderNo: 130 },
        children: [
            {
                path: 'xxxList',
                name: 'xxxList',
                component: () => import('@/pages/xxx/xxxList.vue'),
                meta: {
                    title: 'XXX列表',
                    permissions: Perms.XxxPage, // 若有对应权限枚举则使用，否则用 'view_page' 兜底
                },
            },
        ],
    },
];
```

## 7. 权限对接规范（严禁自行编造权限）

**核心原则：只对接后端已注册的权限，严禁新增不存在的权限。页面对应权限若后端未注册，路由用 `Perms.PAGE_VIEW`（`'view_page'`）兜底。**

> **项目级参数在目标项目 `CLAUDE.md` 中配置**：权限接口请求地址、本地快照路径、`Perms` 常量前缀与权限 key 前缀。这些参数随项目 `CLAUDE.md` 自动进上下文，直接取用即可。

### 7.1 页面层使用方式
- **模板按钮**：`v-isAuth` 接受两种**等价**写法，皆可——
  - 字符串：`v-isAuth="['kjs_backend.xxx.add']"`（项目现存以此为主）
  - 常量：`v-isAuth="[Perms.XxxAdd]"`（更利于重构与追踪）
- **JSX/JS 判断**：`isPermission(Perms.XxxEdit)`（从 `@/utils/utils` 引入）
- **路由权限**：router `meta.permissions` 引用 `Perms` 枚举

### 7.2 自动检测与添加（按序执行，不可跳过）

1. **拉取后端最新权限**（请求地址见项目 `CLAUDE.md`）
   ```bash
   curl -s <项目配置的权限接口地址> -o /tmp/permissions_latest.json
   ```
   返回格式：`{ status: 0, data: [{ url, permission, name }] }`

2. **与本地快照对比，找出新增权限**
   - 旧集合：项目快照（如 `src/services/permissionsCur.json`）的 `data[].permission`
   - 新集合：步骤 1 数据的 `data[].permission`
   - 求差集得 `newOnly`（新有旧无），输出 `url` / `permission` / `name`，标注与当前功能相关项

3. **将新增权限追加到 `permissions.ts` 末尾**（`};` 之前，有新增时执行）
   - Key 规则：去掉项目权限前缀 → 按 `.` 分段 → 每段转大驼峰（下划线也转驼峰）→ 拼项目 `Perms` 前缀
   - **写入时不加 ✅**，统一格式：
     ```typescript
     // {name}：{url}
     XxxYyy: '{permission}',
     ```

4. **覆盖更新本地快照**
   ```bash
   cp /tmp/permissions_latest.json <项目快照路径>
   ```

5. **页面对接权限后回标 ✅**
   - 按钮 `v-isAuth` / JSX `isPermission` / 路由 `meta.permissions` 引用对应 `Perms`
   - 页面权限若不在 `newOnly` 中 → 用 `Perms.PAGE_VIEW` 兜底，严禁编造
   - 对接后用 Grep 搜索 `Perms.Xxx` 在 `.vue`/`.ts` 的真实引用（排除 `permissions.ts` 自身）；只有被 `v-isAuth` / `isPermission()` / `meta.permissions` 引用的，才把注释 `//` 改为 `// ✅`。纯 Service 调用不算对接。

### 7.3 ✅ 标记约定
- `✅` 仅表示该常量已在页面 `v-isAuth` / JSX `isPermission()` / 路由 `meta.permissions` 中被引用
- 无 `✅` 表示已注册但前端尚未使用
- 严禁步骤 3 写入即标 ✅，必须步骤 5 对接并验证后才标

## 8. toast 使用说明

```js
import { toast } from '@/utils/helper';

toast('操作成功', true);   // 成功提示（绿色）
toast('操作失败', false);  // 警告提示（黄色）
toast('操作失败');         // 错误提示（红色）

// 接口返回后通用写法
const { success, message } = await reqXxx(params);
toast(message, success);   // success=true 显示成功，false 显示警告
```

**禁止**直接使用 `MessagePlugin.error`、`MessagePlugin.success` 等原生方法。

## 9. 关键注意事项

- **`get()` 全场景使用**：不论是表单默认值、模板绑定、还是 JSX cell 渲染，一律用 `get(obj, 'field', defaultValue)` 取值，禁止用 `obj?.field` 可选链。默认值本身即最终兜底，**禁止叠加 `|| '--'`**。字符串字段默认值用 `'--'`，数组字段用 `[]`
  ```html
  <!-- 模板绑定：默认值直接兜底，不加 || '--' -->
  {{ get(detailDrawer.data, 'gameTitle', '--') }}
  {{ get(detailDrawer.data, 'orderId', '--') }}

  <!-- v-if 判断数组 -->
  <div v-if="get(row, 'negatives', []).length">
      <div v-for="item in get(row, 'negatives', [])">...</div>
  </div>
  ```
- **表格列纯展示字段无需 `cell` 函数**：KrTable `cellEmptyContent` 默认显示 `-`，只有需要自定义渲染（枚举映射、JSX、按钮等）时才加 `cell`
- fetchData 中的接口响应结构固定为 `{ success, data: { list, pagination: { total } }, message }`
- 弹窗 close 时要清空 schema 和 rules，避免切换时残留旧数据
- 删除操作必须使用 `DialogPlugin.confirm` 做二次确认
- 搜索重置时要将 `pagination.current` 重置为 1
- **异步加载的下拉 options 必须用 `reactive([])` 数组并保持同一引用**：当 `searchSchema` / 弹窗 schema 里的 `options` 来自接口异步加载（如游戏列表）时，用 `const opts = reactive([])`，schema 里写 `options: opts`，加载完成后 `opts.push(...list)`。**不要用 `ref([])`**——schema 里拿到的是未解包的 Ref 对象，Select 渲染不出选项
- **分页查询有必填参数时，要设默认值且重置时保留**：若列表接口某入参为必填（如 `publishPlatform`），用一个 `DEFAULT_SEARCH` 常量承载默认值，`searchValue` 初始化与 `resetSearch` 都展开它，保证首次加载/重置/搜索三种路径都带上该参数
- **搜索表单字段禁止手动设置 `style: { width: '...' }`**，让组件自适应宽度
- **操作列按钮统一使用 `KrButton size="small" variant="text"`**，禁止使用 `t-link`
- **组件间距规则**：当 KrForm 前面有 KrTabs 等兄弟组件时，KrForm 需加 `class="table-wrapper"` 保持 8px 间距；KrTable 同理。`table-wrapper` 样式统一用于相邻组件间 8px 上间距
