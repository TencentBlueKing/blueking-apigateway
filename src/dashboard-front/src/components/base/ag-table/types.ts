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

import type { BkUiSettings, PrimaryTableCol, PrimaryTableProps, RowEventContext, TableRowData } from '@blueking/tdesign-ui';
import type { ITableEmptyType, ITableSelection } from '@/types/common';
import type { ICountAndResults } from '@/services/types/utils';

export interface ITableColumn extends PrimaryTableCol<TableRowData> {
  /** title 使用渲染函数时，列设置面板显示此文本。 */
  displayTitle?: string
}

export interface ITableQuery extends Record<string, unknown> {
  offset: number
  limit: number
}

export type TableApiMethod = (params: ITableQuery) => Promise<ICountAndResults<TableRowData>>;

export type TableRowSize = NonNullable<BkUiSettings['rowSize']>;

export type ITableLimit = {
  allocatedHeight: number
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

export type RowHoverEvent = Pick<RowEventContext<TableRowData>, 'e' | 'row'>;

export interface IAgTableProps {
  apiMethod?: TableApiMethod
  disabledCheckSelection?: (row: TableRowData) => boolean
  columns?: ITableColumn[]
  tableRowKey?: string
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
  maxLimitConfig?: Partial<ITableLimit> | null
  /** 从设置面板排除的列键。 */
  hiddenColumn?: string[]
  /** 设置面板保留这些列，初始时取消勾选。 */
  uncheckedColumn?: string[]
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
}

export interface IAgTableEmits {
  'row-mouseenter': [payload: RowHoverEvent]
  'row-mouseleave': [payload: RowHoverEvent]
  'selection-change': [payload: ITableSelection]
  'page-change': [payload: TablePage]
  'filter-icon-click': []
  'clear-selection': []
  'clear-filter': []
  'request-done': []
  'refresh': []
}
