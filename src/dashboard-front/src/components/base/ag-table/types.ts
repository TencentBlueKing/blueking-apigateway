/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

import type { ComputedRef, ShallowRef, ShallowUnwrapRef, VNodeChild } from 'vue';
import type {
  BaseTableCellParams,
  BaseTableCol,
  BaseTableColumnAttributes,
  BkUiSettings,
  ExpandOptions,
  FilterValue,
  PrimaryTable,
  PrimaryTableCol,
  PrimaryTableProps,
  RowEventContext,
  SortInfo,
  SortOptions,
  TableColumnClassName,
  TableExpandedRowParams,
  TableFilterChangeContext,
  TableRowData,
  TableSort,
} from '@blueking/tdesign-ui';
import type { ICountAndResults } from '@/services/types/utils';

export type {
  BaseTableCellParams,
  BkUiSettings,
  ExpandOptions,
  FilterValue,
  RowEventContext,
  SortInfo,
  SortOptions,
  TableExpandedRowParams,
  TableFilterChangeContext,
  TableRowData,
  TableSort,
};

/** AgTable 运行时附加或读取的可选行元信息，不污染业务 DTO 定义。 */
export interface ITableRowMeta {
  /** 配合 handleCellEnter / handleCellLeave 维护的文本溢出状态。 */
  isOverflow?: boolean
  /** 禁用勾选行时的默认悬停提示文案。 */
  selectionTip?: string
  /** isExistUniqueKey 为 false 时由组件生成的临时行键。 */
  tempUniqueId?: string
}

/** 表格渲染行类型：保留 TRow 严格字段检查，同时附带 AgTable 行元信息。 */
export type TableRow<TRow extends TableRowData = TableRowData> = TRow & ITableRowMeta;

/** 列键与行主键类型：提供 TRow 字段自动补全，同时兼容操作列等自定义键名。 */
export type TableColumnKey<TRow extends TableRowData = TableRowData> = (keyof TRow & string) | (string & {});

/** 表格列定义：补齐上游 BaseTableCol 遗漏的行泛型，并扩展 displayTitle。 */
export interface ITableColumn<TRow extends TableRowData = TableRowData>
  extends Omit<
    PrimaryTableCol<TableRow<TRow>>,
    'colKey' | 'children' | 'attrs' | 'className' | 'thClassName' | 'ellipsis'
  > {
  colKey?: TableColumnKey<TRow>
  /** title 使用渲染函数时，列设置面板显示此文本。 */
  displayTitle?: string
  attrs?: BaseTableColumnAttributes<TableRow<TRow>>
  className?: TableColumnClassName<TableRow<TRow>> | TableColumnClassName<TableRow<TRow>>[]
  thClassName?: TableColumnClassName<TableRow<TRow>> | TableColumnClassName<TableRow<TRow>>[]
  ellipsis?: BaseTableCol<TableRow<TRow>>['ellipsis']
  children?: ITableColumn<TRow>[]
}

export interface ITableQuery extends Record<string, any> {
  offset: number
  limit: number
}

export type TableApiMethod<TRow extends TableRowData = TableRowData>
  = (params: ITableQuery) => Promise<ICountAndResults<TRow>>;

export type TableRowSize = NonNullable<BkUiSettings['rowSize']>;

export type ITableEmptyType = 'empty' | 'search-empty' | 'searchEmpty' | 'error';

export type ITableSettings = Parameters<
  NonNullable<InstanceType<typeof PrimaryTable>['$props']['onBkUiSettingsChange']>
>[0];

export interface ITableSelection<TRow extends TableRowData = TableRowData> {
  /** 已取得的选中行，顺序与 selectionsRowKeys 一致。 */
  selections: TRow[]
  /** 包括父页面传入、数据尚未加载的选中行键。 */
  selectionsRowKeys: NonNullable<PrimaryTableProps['selectedRowKeys']>
}

export type ITableLimit = {
  allocatedHeight: number
  /** 基于真实 DOM 位置测算剩余高度时，底部预留的安全间距（px），默认 24。 */
  bottomOffset: number
  customLineHeight: number
  mode?: string | undefined
  className: string
  hasPagination: boolean
  defaultRowSize?: string
};

export interface ITablePagination extends Pick<NonNullable<PrimaryTableProps['pagination']>, 'theme' | 'showPageSize'> {
  current: number
  pageSize: number
  total: number
  pageSizeOptions: number[]
}

export type TablePage = Pick<ITablePagination, 'current' | 'pageSize'>;

export type RowHoverEvent<TRow extends TableRowData = TableRowData> = Pick<RowEventContext<TRow>, 'e' | 'row'>;

export interface IRowCellOverflowEvent<TRow extends TableRowData = TableRowData> {
  e: MouseEvent
  row: TRow
}

export interface IAgTableProps<TRow extends TableRowData = TableRowData> {
  apiMethod?: TableApiMethod<TRow>
  disabledCheckSelection?: (row: TableRow<TRow>) => boolean
  columns?: ITableColumn<TRow>[]
  tableRowKey?: TableColumnKey<TRow>
  immediate?: boolean
  localPage?: boolean
  /** 与内部请求或本地翻页的加载态合并。 */
  loading?: boolean
  showFirstFullRow?: boolean
  showSelection?: boolean
  showSettings?: boolean
  showPagination?: boolean
  isExistUniqueKey?: boolean
  bordered?: boolean
  tableLayout?: PrimaryTableProps['tableLayout']
  tableEmptyType?: ITableEmptyType
  /** 是否默认启用自适应高度与首屏每页条数；传 false 可显式关闭。 */
  autoHeight?: boolean
  maxLimitConfig?: Partial<ITableLimit> | null
  /** 从设置面板排除的列键。 */
  hiddenColumn?: TableColumnKey<TRow>[]
  /** 设置面板保留这些列，初始时取消勾选。 */
  uncheckedColumn?: TableColumnKey<TRow>[]
  noSearchFields?: string[]
  resizable?: boolean
  showCellEmptyContent?: boolean
  maxHeight?: string | number
  cacheSettingsInLocalStorage?: boolean
  /** 持久化列设置的稳定唯一标识；未传时列设置仅在当前组件内存中生效。 */
  cacheIdentifier?: string
  hover?: boolean
  /** 没有缓存的行高偏好时使用的默认行高。 */
  defaultRowSize?: BkUiSettings['rowSize']
  /** 透传给 PrimaryTable 的行类名配置，支持按 TRow 动态计算。 */
  rowClassName?: PrimaryTableProps<TableRow<TRow>>['rowClassName']
}

export interface ITableFilterChangeContext<TRow extends TableRowData = TableRowData> {
  col?: ITableColumn<TRow>
  trigger: TableFilterChangeContext<TableRowData>['trigger']
}

export interface IAgTableEmits<TRow extends TableRowData = TableRowData> {
  'row-mouseenter': [payload: RowHoverEvent<TableRow<TRow>>]
  'row-mouseleave': [payload: RowHoverEvent<TableRow<TRow>>]
  'row-click': [context: RowEventContext<TableRow<TRow>>]
  'expand-change': [expandedRowKeys: Array<string | number>, options: ExpandOptions<TableRow<TRow>>]
  'filter-change': [filterValue: FilterValue, context: ITableFilterChangeContext<TRow>]
  'sort-change': [sort: TableSort, options: SortOptions<TableRow<TRow>>]
  'selection-change': [payload: ITableSelection<TableRow<TRow>>]
  'page-change': [payload: TablePage]
  'filter-icon-click': []
  'clear-selection': []
  'clear-filter': []
  'request-done': []
  'refresh': []
}

export interface IAgTableFirstFullRowSlotProps<TRow extends TableRowData = TableRowData> {
  selections: TableRow<TRow>[]
  isAllSelection: boolean
  handleSelectionChange: NonNullable<PrimaryTableProps['onSelectChange']>
}

export interface IAgTableSlots<TRow extends TableRowData = TableRowData> {
  default?: () => VNodeChild
  firstFullRow?: (props: IAgTableFirstFullRowSlotProps<TRow>) => VNodeChild
  expandedRow?: (props: TableExpandedRowParams<TableRow<TRow>>) => VNodeChild
  cellEmptyContent?: (props: BaseTableCellParams<TableRow<TRow>>) => VNodeChild
  selectionPopoverContent?: (row: TableRow<TRow>) => VNodeChild
  empty?: () => VNodeChild
}

export interface IAgTableExpose<TRow extends TableRowData = TableRowData> {
  TDesignTableRef: Readonly<ShallowRef<InstanceType<typeof PrimaryTable> | null>>
  loading: ComputedRef<boolean>
  fetchData: (filters?: Record<string, any>, options?: { resetPage?: boolean }) => void
  refresh: () => void
  getPagination: () => ITablePagination
  setPagination: (page: TablePage) => void
  setPaginationTheme: (options: {
    theme: 'default' | 'simple'
    showPageSize?: boolean
  }) => void
  resetPaginationTheme: () => void
  /** 按 v-model:selected-row-keys 同步回显勾选状态。 */
  getSelectionData: () => void
  setSelectionData: (rows: TRow[]) => void
  handleResetSelection: () => void
  handleCellEnter: (event: IRowCellOverflowEvent<TableRow<TRow>>) => void
  handleCellLeave: (event: Pick<IRowCellOverflowEvent<TableRow<TRow>>, 'row'>) => void
}

/** 供模板 ref（useTemplateRef / ref）使用的已解包 AgTable 实例类型。 */
export type IAgTableInstance<TRow extends TableRowData = TableRowData> = ShallowUnwrapRef<IAgTableExpose<TRow>>;

/** 列声明辅助函数：零运行时开销，便于在普通数组或 shallowRef 中锁定行泛型。 */
export const defineTableColumns = <TRow extends TableRowData = TableRowData>(
  columns: ITableColumn<TRow>[],
): ITableColumn<TRow>[] => columns;
