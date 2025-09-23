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

/**
 * TDesign表格复选框事件
 */
import type { PrimaryTableProps, SelectOptions, TableRowData } from '@blueking/tdesign-ui';

export const useTDesignSelection = () => {
  // 全选
  const isAllSelection = ref(false);
  // 已选择的所有行数的rowKey
  const selections = ref<any[]>([]);
  const selectionsRowKeys = ref<(string | number)[]>([]);

  const handleSelectionChange: PrimaryTableProps['onSelectChange'] = (
    selectedRowKeys: (string | number)[],
    options: SelectOptions<TableRowData>,
  ) => {
    const { selectedRowData } = options;
    selections.value = [...selectedRowData];
    selectionsRowKeys.value = [...selectedRowKeys];
  };

  // 自定义复选框事件
  const handleCustomSelectChange = ({
    isCheck,
    row = {},
    tableRowKey = 'id',
  }: {
    isCheck?: boolean
    row?: TableRowData
    tableRowKey?: string
  }) => {
    if (isCheck) {
      selections.value.push(row);
      selectionsRowKeys.value.push(row[tableRowKey]);
    }
    else {
      const index = selections.value.findIndex(item => item[tableRowKey] === row[tableRowKey]);
      selections.value.splice(index, 1);
      selectionsRowKeys.value = selectionsRowKeys.value.filter(item => item !== row[tableRowKey]);
    }
  };

  // 自定义全选事件, 处理复选框自定义交互
  const handleCustomSelectAllChange = ({
    isCheck,
    tables = [],
    tableRowKey = 'id',
  }: {
    isCheck?: boolean
    tables?: TableRowData[]
    tableRowKey?: string
  }) => {
    const pageSelection = tables.map(item => item[tableRowKey]);
    const hasSelected = selections.value.filter(item => !pageSelection.includes(item[tableRowKey]));
    if (isCheck) {
      selections.value = [...hasSelected, ...tables];
      selectionsRowKeys.value = [...new Set([...selectionsRowKeys.value, ...pageSelection])];
    }
    else {
      selections.value = [...hasSelected];
      selectionsRowKeys.value = selectionsRowKeys.value.filter(item => !pageSelection.includes(item));
    }
  };

  const resetSelections = () => {
    selections.value = [];
    selectionsRowKeys.value = [];
  };

  return {
    isAllSelection,
    selections,
    selectionsRowKeys,
    resetSelections,
    handleSelectionChange,
    handleCustomSelectChange,
    handleCustomSelectAllChange,
  };
};
