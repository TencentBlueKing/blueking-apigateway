# AgTable 表格组件使用与类型指南

`AgTable` 是基于 `@blueking/tdesign-ui` `PrimaryTable` 封装的通用泛型业务表格组件（`<script setup lang="ts" generic="TRow extends TableRowData = TableRowData">`），统一提供远程/本地分页、自适应高度与首屏条数测算、行勾选与跨页回显、列显示与行高偏好持久化、空态/错误态以及完整 TypeScript 行/列类型推导。

## 目录结构

```text
src/components/base/ag-table/
├── index.ts                          # 统一对外出口（组件、defineTableColumns、全部公开类型）
├── Index.vue                         # 泛型组件入口
├── types.ts                          # 泛型列、行、Props/Emits/Slots/Expose 与透传类型定义
├── context.ts                        # 运行时注入键（通知栏高度，由 main.ts 提供）
├── use-table-data-source.ts          # 静态数据、本地分页与远程请求管理
├── use-table-layout.ts               # 自适应高度与首屏 pageSize 估算
├── use-tdesign-table-adapter.ts      # TDesign 语言、筛选图标、单元格溢出状态适配
├── table.scss                        # 组件样式
├── selection/
│   ├── use-row-selection.ts          # 行选择与跨页勾选回显
│   └── row-selection-column.tsx      # 表头/行复选框列渲染
└── settings/
    ├── use-table-settings.ts         # 列设置合并与状态同步
    └── table-preferences.ts          # 列显隐与行高偏好 localStorage 读写及构建清理
```

---

## 核心约定（必读）

### 1. 统一导入路径与禁用写法

| 场景 | 正确写法 | 禁止写法 |
| --- | --- | --- |
| 导入组件与类型 | `import AgTable, { type ITableColumn, type IAgTableInstance } from '@/components/base/ag-table';` | `import AgTable from '@/components/base/ag-table/Index.vue';` |
| 模板引用类型 | `useTemplateRef<IAgTableInstance<IRow>>('tableRef')` | `useTemplateRef<InstanceType<typeof AgTable>>('tableRef')`、`ITableMethod` |
| 列定义类型 | `ITableColumn<IRow>[]` 或 `defineTableColumns<IRow>([...])` | `PrimaryTableProps['columns']`、`any[]` |
| TDesign 事件/筛选类型 | 从 `@/components/base/ag-table` 导入 `FilterValue`、`RowEventContext`、`ExpandOptions`、`SortOptions`、`TableSort` | 业务文件直接 `import type { ... } from '@blueking/tdesign-ui'` |
| 列回调参数类型 | `cell: (_h, { row }) => ...`（自动推导 `TableRow<IRow>`） | `cell: (_h: any, { row }: { row: any }) => ...` |

### 2. 行类型来源原则

1. 优先直接复用 `src/services/types/**` 中的接口响应 DTO（如 `IStageListOutput`、`IResourceListOutput`）或 `src/types/**` 中的领域类型。
2. 仅当表格行需要挂载页面局部运行时字段（如 `statusUpdating?: boolean`）或合并多个接口数据时，在当前组件内定义局部 `interface IMyRow extends IDto { ... }` 或联合类型 `type IMyRow = IDtoA | IDtoB`。
3. `AgTable` 运行时附加的元信息（`isOverflow`、`selectionTip`、`tempUniqueId`）已通过 `TableRow<TRow>` 自动混入，无需写进业务 DTO。

### 3. 泛型推导规则

`<AgTable>` 根据传入的 `:api-method`、`v-model:table-data` / `:table-data`、`:columns` 自动推导行类型 `TRow`，并同步约束：
- `columns` 中 `colKey` 的字段补全及 `cell` / `attrs` / `className` / `thClassName` / `ellipsis` 回调中的 `row`
- `table-row-key`、`hidden-column`、`unchecked-column`、`disabled-check-selection`、`row-class-name`
- `@row-click`、`@row-mouseenter`、`@row-mouseleave`、`@expand-change`、`@filter-change`、`@sort-change`、`@selection-change`
- `#expandedRow`、`#firstFullRow`、`#cellEmptyContent`、`#selectionPopoverContent` 插槽参数

---

## 导出清单与类型速查

统一从 `@/components/base/ag-table` 导入：

### 值导出

| 导出名 | 说明 |
| --- | --- |
| `default` / `AgTable` | 泛型表格组件 |
| `defineTableColumns<TRow>(columns)` | 零运行时开销的列声明辅助函数；适合在普通数组、`.filter()` 链式调用或复用列工厂中锁定 `TRow` 上下文推导 |

### 核心类型导出

| 类型 | 用途 |
| --- | --- |
| `ITableColumn<TRow>` | 列配置类型（扩展 `PrimaryTableCol<TableRow<TRow>>`，补齐 `attrs`/`className`/`thClassName`/`ellipsis` 的行泛型，支持 `displayTitle`） |
| `TableRow<TRow>` | `TRow & ITableRowMeta`，表格内行回调与插槽收到的实际行类型 |
| `ITableRowMeta` | `AgTable` 运行时可选元信息：`{ isOverflow?: boolean; selectionTip?: string; tempUniqueId?: string }` |
| `TableColumnKey<TRow>` | `(keyof TRow & string) \| (string & {})`，提供行字段补全同时允许操作列等自定义键名 |
| `ITableQuery` | 远程查询参数基类（含 `offset: number`、`limit: number` 及透传筛选键值） |
| `TableApiMethod<TRow>` | `(params: ITableQuery) => Promise<ICountAndResults<TRow>>` |
| `IAgTableInstance<TRow>` | `ShallowUnwrapRef<IAgTableExpose<TRow>>`，专用于 `useTemplateRef<IAgTableInstance<TRow>>('tableRef')` |
| `IAgTableExpose<TRow>` | 组件暴露实例类型（未解包版本） |
| `IAgTableProps<TRow>` / `IAgTableEmits<TRow>` / `IAgTableSlots<TRow>` | 组件 Props / Emits / Slots 类型定义 |
| `ITableSelection<TRow>` | 勾选事件载荷：`{ selections: TRow[]; selectionsRowKeys: Array<string \| number> }`（事件内 `TRow` 为 `TableRow<Row>`） |
| `ITableFilterChangeContext<TRow>` | 筛选变更上下文：`{ col?: ITableColumn<TRow>; trigger: ... }` |
| `RowHoverEvent<TRow>` | `row-mouseenter` / `row-mouseleave` 载荷：`{ e: MouseEvent; row: TRow }` |
| `IRowCellOverflowEvent<TRow>` | `handleCellEnter` 入参：`{ e: MouseEvent; row: TRow }` |
| `IAgTableFirstFullRowSlotProps<TRow>` | `#firstFullRow` 插槽参数：`{ selections, isAllSelection, handleSelectionChange }` |
| `ITablePagination` / `TablePage` | 分页完整状态与 `{ current, pageSize }` |
| `ITableLimit` | 自适应高度配置项（`allocatedHeight`、`bottomOffset`、`customLineHeight`、`className`、`hasPagination`、`defaultRowSize`） |
| `ITableEmptyType` | 空态类型：`'empty' \| 'search-empty' \| 'searchEmpty' \| 'error'` |
| `ITableSettings` / `TableRowSize` | 列设置回调参数与行高枚举（`'mini' \| 'small' \| 'medium' \| 'large'`） |

### 透传的 TDesign 类型

可直接从 `@/components/base/ag-table` 导入，无需引入 `@blueking/tdesign-ui`：
`FilterValue`、`RowEventContext`、`ExpandOptions`、`SortInfo`、`SortOptions`、`TableSort`、`TableExpandedRowParams`、`BaseTableCellParams`、`BkUiSettings`、`TableFilterChangeContext`、`TableRowData`。

---

## 场景代码示例

### 场景 1：远程分页列表（最常用）

适用于标准后端分页接口（返回 `{ count, results }`）。

```vue
<template>
  <AgTable
    ref="tableRef"
    v-model:table-data="tableData"
    cache-identifier="BackendServiceList"
    show-settings
    resizable
    :filter-value="filterData"
    :api-method="getTableData"
    :columns="columns"
    @clear-filter="handleClearFilter"
  />
</template>

<script setup lang="tsx">
import { Button } from 'bkui-vue';
import AgTable, {
  type IAgTableInstance,
  type ITableColumn,
  type ITableQuery,
} from '@/components/base/ag-table';
import { getBackendServiceList } from '@/services/source/gateway/backend';
import type { IBackendListOutput } from '@/services/types/gateway/backend';
import { useGateway } from '@/stores';

const { t } = useI18n();
const gatewayStore = useGateway();

const tableRef = useTemplateRef<IAgTableInstance<IBackendListOutput>>('tableRef');
const tableData = ref<IBackendListOutput[]>([]);
const filterData = ref<{ name?: string }>({});

const columns = shallowRef<ITableColumn<IBackendListOutput>[]>([
  {
    title: t('后端服务名称'),
    colKey: 'name',
    ellipsis: true,
    fixed: 'left',
  },
  {
    title: t('关联资源数'),
    colKey: 'resource_count',
    width: 120,
    // row 自动推导为 TableRow<IBackendListOutput>，无需手动标注类型
    cell: (_h, { row }) => <span>{ row.resource_count ?? 0 }</span>,
  },
  {
    title: t('操作'),
    colKey: 'operate',
    fixed: 'right',
    width: 140,
    cell: (_h, { row }) => (
      <Button
        theme="primary"
        text
        onClick={() => handleEdit(row)}
      >
        { t('编辑') }
      </Button>
    ),
  },
]);

const getTableData = (params: ITableQuery) => getBackendServiceList(gatewayStore.apigwId, params);

const handleSearch = () => {
  tableRef.value?.fetchData(filterData.value, { resetPage: true });
};

const handleEdit = (row: IBackendListOutput) => {
  // row 为强类型 IBackendListOutput
  console.log(row.id, row.name);
};

const handleClearFilter = () => {
  filterData.value = {};
  handleSearch();
};
</script>
```

### 场景 2：静态数据 / 本地分页 + 动态过滤列

不传 `api-method`，直接绑定 `:table-data`；如需在前端分页，传 `local-page`。  
当列定义后面需要链式 `.filter(...)` 时，**用 `defineTableColumns<TRow>([...])` 包裹**以保持列内上下文类型推导。

```vue
<template>
  <AgTable
    table-row-key="name"
    local-page
    :auto-height="false"
    :show-pagination="false"
    :table-data="rows"
    :columns="columns"
  />
</template>

<script setup lang="tsx">
import AgTable, { defineTableColumns } from '@/components/base/ag-table';

interface IHeaderRow {
  name: string
  value: string
  deprecated?: boolean
}

const showDeprecated = ref(false);
const rows = ref<IHeaderRow[]>([]);

const columns = computed(() => defineTableColumns<IHeaderRow>([
  {
    title: '名称',
    colKey: 'name',
    ellipsis: true,
  },
  {
    title: '值',
    colKey: 'value',
    ellipsis: true,
  },
  {
    title: '状态',
    colKey: 'deprecated',
    cell: (_h, { row }) => (row.deprecated ? '已废弃' : '正常'),
  },
]).filter(col => showDeprecated.value || col.colKey !== 'deprecated'));
</script>
```

### 场景 3：行勾选、禁用勾选与跨页回显

```vue
<template>
  <AgTable
    ref="tableRef"
    v-model:table-data="tableData"
    v-model:selected-row-keys="selectedRowKeys"
    show-selection
    show-first-full-row
    :disabled-check-selection="row => !row.deletable"
    :api-method="getTableData"
    :columns="columns"
    @selection-change="handleSelectionChange"
    @clear-selection="handleClearSelection"
  >
    <!-- 可选：自定义禁用勾选行的悬浮提示（不传时默认展示 row.selectionTip） -->
    <template #selectionPopoverContent="row">
      <span>{{ row.version }} 不可删除</span>
    </template>

    <!-- 可选：自定义表头下方选中提示条（不传时默认显示“已选 N 条，清除选择”） -->
    <template #firstFullRow="{ selections, isAllSelection }">
      <span>已选 {{ selections.length }} 项（当前页全选：{{ isAllSelection }}）</span>
    </template>
  </AgTable>
</template>

<script setup lang="ts">
import AgTable, {
  type IAgTableInstance,
  type ITableColumn,
  type ITableQuery,
  type ITableSelection,
  type TableRow,
} from '@/components/base/ag-table';
import { getVersionList } from '@/services/source/gateway/resource-version';
import type { IResourceVersionListOutput } from '@/services/types/gateway/resource-version';

const tableRef = useTemplateRef<IAgTableInstance<IResourceVersionListOutput>>('tableRef');
const tableData = ref<IResourceVersionListOutput[]>([]);
const selectedRowKeys = ref<Array<string | number>>([]);
const selectedRows = ref<IResourceVersionListOutput[]>([]);

const columns = shallowRef<ITableColumn<IResourceVersionListOutput>[]>([
  {
    title: '版本号',
    colKey: 'version',
  },
]);

const getTableData = (params: ITableQuery) => getVersionList(1, params);

const handleSelectionChange = ({
  selections,
  selectionsRowKeys,
}: ITableSelection<TableRow<IResourceVersionListOutput>>) => {
  selectedRows.value = selections;
  selectedRowKeys.value = selectionsRowKeys;
};

const handleClearSelection = () => {
  selectedRows.value = [];
};

// 主动替换选中行（受 TRow 类型约束）
const selectRows = (rows: IResourceVersionListOutput[]) => {
  tableRef.value?.setSelectionData(rows);
};

// 仅修改了 selectedRowKeys 后同步回显 selections 时调用
const syncSelection = () => {
  tableRef.value?.getSelectionData();
};
</script>
```

### 场景 4：表头筛选、排序、行点击与动态行类名

```vue
<template>
  <AgTable
    ref="tableRef"
    v-model:table-data="tableData"
    :filter-value="filterData"
    :sort="sort"
    :api-method="getTableData"
    :columns="columns"
    :row-class-name="getRowClass"
    @filter-change="handleFilterChange"
    @sort-change="handleSortChange"
    @row-click="handleRowClick"
  />
</template>

<script setup lang="tsx">
import AgTable, {
  type FilterValue,
  type IAgTableInstance,
  type ITableColumn,
  type ITableFilterChangeContext,
  type ITableQuery,
  type RowEventContext,
  type SortOptions,
  type TableRow,
  type TableSort,
} from '@/components/base/ag-table';
import { getRecordList } from '@/services/source/gateway/monitor';
import type { IAlarmRecordListOutput } from '@/services/types/gateway/monitor';

const tableRef = useTemplateRef<IAgTableInstance<IAlarmRecordListOutput>>('tableRef');
const tableData = ref<IAlarmRecordListOutput[]>([]);
const filterData = ref<FilterValue>({});
const sort = ref<TableSort>();

const columns = shallowRef<ITableColumn<IAlarmRecordListOutput>[]>([
  {
    title: '告警 ID',
    colKey: 'id',
    sorter: true,
  },
  {
    title: '状态',
    colKey: 'status',
    filter: {
      type: 'single',
      showConfirmAndReset: true,
      popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
      list: [
        { label: '成功', value: 'success' },
        { label: '失败', value: 'failure' },
      ],
    },
  },
]);

const getTableData = (params: ITableQuery) => getRecordList(1, params);

// 无需使用 PrimaryTableProps['onFilterChange']
const handleFilterChange = (
  filterItem: FilterValue,
  _context?: ITableFilterChangeContext<IAlarmRecordListOutput>,
) => {
  filterData.value = { ...filterData.value, ...filterItem };
};

const handleSortChange = (
  sortVal: TableSort,
  _options: SortOptions<TableRow<IAlarmRecordListOutput>>,
) => {
  sort.value = sortVal;
};

// RowEventContext 中的 e 为 MouseEvent | KeyboardEvent
const handleRowClick = ({ row }: RowEventContext<TableRow<IAlarmRecordListOutput>>) => {
  console.log(row.alarm_id, row.alarm_strategy_names);
};

const getRowClass = ({ row }: { row: TableRow<IAlarmRecordListOutput> }) => (
  row.status === 'failure' ? 'is-error-row cursor-pointer' : 'cursor-pointer'
);
</script>
```

### 场景 5：展开行与单元格溢出提示

```vue
<template>
  <AgTable
    ref="tableRef"
    v-model:table-data="tableData"
    expand-on-row-click
    :expanded-row-keys="expandedRowKeys"
    :api-method="getTableData"
    :columns="columns"
    @expand-change="handleExpandChange"
  >
    <!-- row 自动推导为 TableRow<IOrderRow> -->
    <template #expandedRow="{ row }">
      <div class="p-16px">{{ row.detail }}</div>
    </template>
  </AgTable>
</template>

<script setup lang="tsx">
import AgTable, {
  type ExpandOptions,
  type IAgTableInstance,
  type ITableColumn,
  type ITableQuery,
  type TableRow,
} from '@/components/base/ag-table';
import type { ICountAndResults } from '@/services/types/utils';

interface IOrderRow {
  id: number
  title: string
  detail: string
}

const tableRef = useTemplateRef<IAgTableInstance<IOrderRow>>('tableRef');
const tableData = ref<IOrderRow[]>([]);
const expandedRowKeys = ref<Array<string | number>>([]);

const columns = shallowRef<ITableColumn<IOrderRow>[]>([
  {
    title: '标题',
    colKey: 'title',
    cell: (_h, { row }) => (
      <div
        class="truncate"
        v-bk-tooltips={{ content: row.title, disabled: !row.isOverflow }}
        onMouseenter={(e: MouseEvent) => tableRef.value?.handleCellEnter({ e, row })}
        onMouseleave={() => tableRef.value?.handleCellLeave({ row })}
      >
        { row.title }
      </div>
    ),
  },
]);

const getTableData = async (_params: ITableQuery): Promise<ICountAndResults<IOrderRow>> => ({
  count: 0,
  results: [],
});

const handleExpandChange = (
  keys: Array<string | number>,
  options: ExpandOptions<TableRow<IOrderRow>>,
) => {
  expandedRowKeys.value = keys;
  console.log(options.currentRowData.id);
};
</script>
```

### 场景 6：运行时扩展字段与双接口联合行类型

#### 运行时扩展字段

```ts
import type { IAlarmStrategyListOutput } from '@/services/types/gateway/monitor';

interface IAlarmStrategyTableRow extends IAlarmStrategyListOutput {
  statusUpdating?: boolean
}
```

#### 单表按 Tab 切换两个不同接口

不要让 `getTableData` 推导出 `Promise<ICountAndResults<A> | ICountAndResults<B>>`（TS 会优先匹配第一个分支并报类型不兼容），需显式标注合并后的返回类型 `Promise<ICountAndResults<A | B>>`：

```ts
import type { ICountAndResults } from '@/services/types/utils';
import type { ITableColumn, ITableQuery } from '@/components/base/ag-table';

type IMergedRow = IRecordA | IRecordB;

const tableData = ref<IMergedRow[]>([]);
const columns = computed<ITableColumn<IMergedRow>[]>(() => [
  // 在 cell 中按业务状态（如当前 Tab）或字段守卫收窄类型
]);

const getTableData = async (params: ITableQuery): Promise<ICountAndResults<IMergedRow>> => {
  if (activeTab.value === 'a') {
    return getListA(params);
  }
  return getListB(params);
};
```

---

## API 速查表

### `v-model` 双向绑定

| Model | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `v-model:table-data` | `TRow[]` | `[]` | 远程模式下请求完成自动同步；静态/本地分页模式作为数据源传入 |
| `v-model:selected-row-keys` | `Array<string \| number>` | `[]` | 已选行主键值集合（配合 `show-selection` 使用） |
| `v-model:settings` | `BkUiSettings \| null` | `null` | 外部托管列设置对象；通常仅在需要自定义 `fields`/`checked` 初始配置时传入 |

### Props

| Prop | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `api-method` | `TableApiMethod<TRow>` | `undefined` | 远程分页请求函数，入参含 `{ offset, limit, ...filters }`，需返回 `{ count, results }` |
| `columns` | `ITableColumn<TRow>[]` | `[]` | 列配置数组 |
| `table-row-key` | `TableColumnKey<TRow>` | `'id'` | 行唯一主键字段名 |
| `is-exist-unique-key` | `boolean` | `true` | 数据无稳定主键时设为 `false`，组件会改用 `tempUniqueId` 作为行键（仅远程模式请求成功时自动生成 `tempUniqueId`；本地/静态表请提供稳定的 `table-row-key`） |
| `immediate` | `boolean` | `true` | 挂载后是否自动执行首次请求（仅远程模式生效） |
| `local-page` | `boolean` | `false` | 开启前端本地分页（使用 `:table-data`） |
| `loading` | `boolean` | `undefined` | 外部 loading 状态，与内部请求 loading 合并 |
| `show-pagination` | `boolean` | `true` | 是否显示分页器 |
| `auto-height` | `boolean` | `true` | 默认开启自适应高度与首屏 `pageSize` 反推；传 `false` 或 `max-height="none"` 关闭 |
| `max-height` | `string \| number` | `undefined` | 显式高度上限；传固定像素（如 `400` / `'400px'`）时按该高度反推条数，传 `'none'` 关闭滚动限高 |
| `max-limit-config` | `Partial<ITableLimit> \| null` | `null` | 高度与条数估算微调：`allocatedHeight`、`bottomOffset`（默认 `24`）、`customLineHeight`、`className`、`hasPagination`、`defaultRowSize` |
| `show-selection` | `boolean` | `false` | 是否前置渲染复选框列 |
| `show-first-full-row` | `boolean` | `false` | 有选中行时是否在表头下方显示已选提示条 |
| `disabled-check-selection` | `(row: TableRow<TRow>) => boolean` | `() => false` | 判断指定行是否禁用勾选 |
| `show-settings` | `boolean` | `false` | 是否显示右上角列设置按钮（列显隐、行高、字号） |
| `cache-identifier` | `string` | `undefined` | 持久化列偏好的稳定唯一标识（存储键为 `table-settings-<cacheIdentifier>`）；开启 `show-settings` 需要持久化时**必须传入**，未传仅内存生效 |
| `cache-settings-in-local-storage` | `boolean` | `true` | 是否将列偏好写入 `localStorage` |
| `hidden-column` | `TableColumnKey<TRow>[]` | `[]` | 从列设置面板排除的列键（常用于操作列/固定隐藏列） |
| `unchecked-column` | `TableColumnKey<TRow>[]` | `[]` | 列设置面板保留、但初始默认取消勾选的列键 |
| `default-row-size` | `'mini' \| 'small' \| 'medium' \| 'large'` | `'medium'` | 无缓存偏好时的默认行高（未传时兼容透传属性 `size`） |
| `table-layout` | `'auto' \| 'fixed'` | `'fixed'` | 表格布局模式 |
| `bordered` | `boolean` | `false` | 是否显示边框 |
| `resizable` | `boolean` | `true` | 是否允许拖拽列宽 |
| `hover` | `boolean` | `true` | 是否开启行悬浮高亮 |
| `table-empty-type` | `ITableEmptyType` | `'empty'` | 空态类型，透传给 `AgTableEmpty` |
| `no-search-fields` | `string[]` | `[]` | 不计入“筛选条件”的查询参数名（用于区分无数据空态与搜索无结果空态） |
| `show-cell-empty-content` | `boolean` | `false` | 为空单元格自动渲染 `--`（或使用 `#cellEmptyContent` 插槽自定义） |
| `row-class-name` | `PrimaryTableProps<TableRow<TRow>>['rowClassName']` | `undefined` | 静态行类名或按 `TRow` 动态计算的函数 |

> **透传属性（`$attrs`）**：除上述显式 Props 外，未声明属性直接透传给底层 `PrimaryTable`，常见如 `filter-value`、`sort`、`expanded-row-keys`、`expand-on-row-click`、`expand-icon`、`size`、`scroll`、`active-row-type` 等。

### 自适应高度与分页条数行为说明

- **默认列表页**：`auto-height` 默认为 `true`，组件会在挂载后测量自身距视口底部的真实剩余高度（默认预留 `bottomOffset: 24px`），并按行高（默认 `tdesign` 模式下 `mini: 32px`、`small: 36px`、`medium: 42px`、`large: 56px`）反推首屏 `pageSize`；在首次测量完成且用户未手动改分页前自动生效。
- **底部有额外留白或吸底操作条**：可通过 `:max-limit-config="{ bottomOffset: 48 }"` 调大底部安全间距，避免表格贴底。
- **侧滑抽屉 / 弹窗 / 展开行子表 / 折叠面板内嵌表**：通常不需要按整页视口自适应，建议按场景二选一：
  - 固定限高滚动：传 `max-height="400px"`（或具体数值），组件会按给定高度滚动与估算条数；
  - 完全撑开随外层滚动：传 `:auto-height="false"` 或 `max-height="none"`。

### Emits

| 事件名 | 回调签名 | 说明 |
| --- | --- | --- |
| `row-click` | `(context: RowEventContext<TableRow<TRow>>) => void` | 行点击事件 |
| `row-mouseenter` | `(payload: RowHoverEvent<TableRow<TRow>>) => void` | 鼠标移入行 |
| `row-mouseleave` | `(payload: RowHoverEvent<TableRow<TRow>>) => void` | 鼠标移出行 |
| `expand-change` | `(expandedRowKeys: Array<string \| number>, options: ExpandOptions<TableRow<TRow>>) => void` | 展开行状态变更 |
| `filter-change` | `(filterValue: FilterValue, context: ITableFilterChangeContext<TRow>) => void` | 表头筛选确认/重置 |
| `sort-change` | `(sort: TableSort, options: SortOptions<TableRow<TRow>>) => void` | 表头排序变更 |
| `selection-change` | `(payload: ITableSelection<TableRow<TRow>>) => void` | 勾选行集合变化 |
| `page-change` | `(payload: TablePage) => void` | 页码或每页条数变化 |
| `filter-icon-click` | `() => void` | 点击表头筛选图标 |
| `clear-selection` | `() => void` | 点击默认提示条的“清除选择”或调用 `handleResetSelection` |
| `clear-filter` | `() => void` | 点击空态组件的“清空筛选条件” |
| `request-done` | `() => void` | 远程模式请求成功并写回数据后触发（失败分支不触发） |
| `refresh` | `() => void` | 点击错误空态的“刷新”按钮 |

### Slots

| 插槽名 | 参数类型 | 说明 |
| --- | --- | --- |
| `default` | 无 | 透传给 `PrimaryTable` 默认插槽 |
| `firstFullRow` | `IAgTableFirstFullRowSlotProps<TRow>` | 自定义表头下方已选提示条（仅 `show-first-full-row` 且存在已选项时渲染） |
| `expandedRow` | `TableExpandedRowParams<TableRow<TRow>>` | 展开行内容（解构 `{ row, index }`） |
| `cellEmptyContent` | `BaseTableCellParams<TableRow<TRow>>` | 自定义空单元格占位内容（需配合 `show-cell-empty-content`） |
| `selectionPopoverContent` | `row: TableRow<TRow>` | 禁用勾选行上的自定义气泡提示内容 |
| `empty` | 无 | 覆盖默认的 `AgTableEmpty` 空态组件 |

### Expose 实例方法（通过 `useTemplateRef<IAgTableInstance<TRow>>('tableRef')` 访问）

| 成员 | 签名 / 类型 | 说明 |
| --- | --- | --- |
| `TDesignTableRef` | `InstanceType<typeof PrimaryTable> \| null` | 底层 `PrimaryTable` 实例引用 |
| `loading` | `boolean`（已解包） | 当前合并后的加载态 |
| `fetchData` | `(filters?: Record<string, any>, options?: { resetPage?: boolean }) => void` | 携带筛选条件触发查询；切换筛选时通常传 `{ resetPage: true }` |
| `refresh` | `() => void` | 沿用当前参数与页码重新请求 |
| `getPagination` | `() => ITablePagination` | 获取当前分页对象 `{ current, pageSize, total, pageSizeOptions, ... }` |
| `setPagination` | `(page: TablePage) => void` | 手动设置页码与每页条数并触发查询 |
| `setPaginationTheme` | `(options: { theme: 'default' \| 'simple'; showPageSize?: boolean }) => void` | 切换简洁分页（如左右分栏收窄时） |
| `resetPaginationTheme` | `() => void` | 恢复默认分页样式 |
| `getSelectionData` | `() => void` | **注意**：历史命名，实际功能是按 `v-model:selected-row-keys` 同步回显已选行，返回 `void` |
| `setSelectionData` | `(rows: TRow[]) => void` | 替换当前选中行集合并同步 `selected-row-keys` |
| `handleResetSelection` | `() => void` | 清空勾选并触发 `clear-selection` 事件 |
| `handleCellEnter` | `(event: IRowCellOverflowEvent<TableRow<TRow>>) => void` | 检测单元格文本是否溢出，写入 `row.isOverflow` |
| `handleCellLeave` | `(event: Pick<IRowCellOverflowEvent<TableRow<TRow>>, 'row'>) => void` | 重置 `row.isOverflow` |

---

## 常见类型报错与避坑

1. **列数组链式 `.filter()` 报 `Parameter '_h' implicitly has an 'any' type` 或 `filter.type` 不兼容**
   - 原因：数组字面量后面紧跟 `.filter()` 会切断左侧变量声明的上下文类型推导。
   - 解决：使用 `defineTableColumns<IRow>([...]).filter(...)`，或先声明 `const rawColumns: ITableColumn<IRow>[] = [...]` 再过滤。
2. **自定义 `title` 渲染函数导致列设置面板显示异常**
   - 列 `title` 为 JSX 渲染函数时，同时提供 `displayTitle: t('列名')`，列设置面板会优先显示 `displayTitle`。
3. **`@filter-change` 报 `TableFilterChangeContext<TableRowData>` 不兼容**
   - 不要给处理函数标注 `PrimaryTableProps['onFilterChange']`，直接写 `(filterItem: FilterValue) => ...` 或 `(filterItem: FilterValue, context: ITableFilterChangeContext<IRow>) => ...`。
4. **`@row-click` 报 `MouseEvent | KeyboardEvent` 不可赋值给 `MouseEvent`**
   - 将参数签名改为 `RowEventContext<TableRow<IRow>>`，而非手写 `{ e: MouseEvent; row: IRow }`。
5. **动态索引访问 `row[field]`（如按后端返回字段表渲染展开行）报 `TS7053`**
   - 为行类型显式扩展索引签名（如 `interface ILogRow extends IRequestLogOutput { [key: string]: any }`），并确保 `api-method` 返回 `Promise<ICountAndResults<ILogRow>>`。
6. **在已有表格上新增或修改列、事件或 `AgTable` 内部实现后的验证命令**（在 `src/dashboard-front/` 目录执行）：

```sh
pnpm type-check
pnpm lint:ci:oxlint
pnpm lint:ci
pnpm test:ag-table
```
