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

import type { Ref } from 'vue';
import type { ISearchItem, ISearchValue } from 'bkui-vue/lib/search-select/utils';
/**
 * 表格筛选联动搜索框
 * @param filterItem filterChange回调参数
 * @param filterData 接口过滤参数
 * @param searchOptions 过滤参数列表
 * @param searchParams  搜索框选中参数
 */
export function useTableFilterChange() {
  function handleTableFilterChange({
    filterItem,
    filterData,
    searchOptions,
    searchParams,
  }: {
    filterItem: Record<string, string | string[]>
    filterData: Ref<Record<string, string | string[]>>
    searchOptions: Ref<ISearchItem[]>
    searchParams: Ref<ISearchValue[]>
  }) {
    Object.entries(filterItem).forEach(([colKey, checkValues]) => {
      const isMultiple = Array.isArray(checkValues);
      if (checkValues?.length) {
        Object.assign(filterData.value, { [colKey]: checkValues });
        const searchOption = searchOptions.value.find(option => option.id === colKey);
        const filterOption = searchParams.value.find(searchItem => searchItem.id === colKey);
        if (searchOption) {
          const filterChildren = searchOption?.children?.filter(item => (isMultiple
            ? checkValues.includes(item.id)
            : item.id === filterData.value[colKey]));
          if (filterOption) {
            filterOption.values = filterChildren ?? [];
          }
          else {
            searchParams.value.push({
              id: colKey,
              name: searchOption.name,
              values: filterChildren,
            });
          }
        }
      }
      else {
        searchParams.value = searchParams.value.filter(searchItem => searchItem.id !== colKey);
        delete filterData.value[colKey];
      }
    });
  }
  return { handleTableFilterChange };
}
