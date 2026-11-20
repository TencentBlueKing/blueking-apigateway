/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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

import type { ITableLimit, TableRowSize } from './types';

interface IInitialTableLayoutOptions {
  viewportHeight: number
  noticeHeight: number
  rowSize: TableRowSize
  config?: Partial<ITableLimit> | null
}

type TableHeights = Record<TableRowSize, [rowHeight: number, headerHeight: number]>;

// 同一行高设置在不同表格模式下对应的行高、表头高度（px）。
const tableHeights = {
  bkui: {
    mini: [42, 42],
    small: [42, 42],
    medium: [60, 42],
    large: [78, 42],
  },
  tdesign: {
    mini: [32, 32],
    small: [36, 36],
    medium: [42, 42],
    large: [56, 56],
  },
  other: {
    mini: [32, 32],
    small: [42, 42],
    medium: [60, 42],
    large: [44, 47],
  },
} satisfies Record<string, TableHeights>;

export function calculateInitialTableLayout({
  viewportHeight, noticeHeight, rowSize, config,
}: IInitialTableLayoutOptions) {
  const availableHeight = viewportHeight - (config?.allocatedHeight ?? 186) - noticeHeight;
  if (!config || !Object.keys(config).length) return {
    availableHeight,
    initialPageSize: 10,
  };

  const mode = config.mode ?? 'bkui';
  const heights = mode === 'bkui' || mode === 'tdesign' ? tableHeights[mode] : tableHeights.other;
  const [defaultRowHeight, headerHeight] = heights[rowSize];
  const { customLineHeight = defaultRowHeight } = config;
  const rowHeight = Number.isFinite(customLineHeight) && customLineHeight > 0 ? customLineHeight : defaultRowHeight;
  // TDesign 的现有布局固定为底部分页区域预留 64px。
  const paginationHeight = mode === 'tdesign' ? 64 : (config.hasPagination === false ? 0 : 60);
  const bodyHeight = availableHeight - headerHeight - paginationHeight;
  return {
    availableHeight,
    initialPageSize: Math.max(1, Math.floor(bodyHeight / rowHeight)),
  };
}
