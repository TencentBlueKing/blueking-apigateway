/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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

import type { Ref, ShallowRef } from 'vue';
import type {
  FilterValue,
  SortInfo,
  TableSort,
} from '@blueking/tdesign-ui';

/**
 * 表格排序(暂时只支持单字段排序)
 * @param orderBy 排序事件回调参数
 * @param filterData 接口过滤参数
 * @param sortData 排序参数
* @param allowSortField 允许排序的字段
 */
export function useTableSortChange() {
  function handleTableSortChange({
    orderBy,
    filterData,
    sortData,
    allowSortField,
  }: {
    orderBy: SortInfo
    filterData: Ref<Partial<FilterValue>>
    sortData: Ref<Partial<TableSort>>
    allowSortField: ShallowRef<string[]>
  }) {
    if (orderBy) {
      const { sortBy: colKey, descending } = orderBy;
      if (allowSortField.value.includes(colKey as string)) {
        filterData.value.order_by = descending ? `${colKey}:desc` : `${colKey}:asc`;
      }
      sortData.value = orderBy;
    }
    else {
      delete filterData.value.order_by;
      sortData.value = {};
    }
  }

  return { handleTableSortChange };
}
