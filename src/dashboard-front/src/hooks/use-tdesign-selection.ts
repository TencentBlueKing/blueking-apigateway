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

/**
 * TDesign表格复选框事件
 */
import type { PrimaryTableProps, SelectOptions, TableRowData } from '@blueking/tdesign-ui';

// 抽离自定义选择事件入参类型，提升复用性
export interface CustomSelectChangeParams {
  isCheck?: boolean
  tableRowKey?: string
  row?: TableRowData
}

// 抽离自定义全选事件入参类型
export interface CustomSelectAllChangeParams {
  isCheck?: boolean
  tableRowKey?: string
  tables?: TableRowData[]
}

export const useTDesignSelection = () => {
  // 已选择的所有行数的rowKey
  const selections = ref<TableRowData[]>([]);
  const selectionsRowKeys = ref<(string | number)[]>([]);

  /**
   * TDesign表格原生选择变化事件
   * @param selectedRowKeys 选中的行Key数组
   * @param options 选择配置项（包含选中行数据）
   */
  const handleSelectionChange: PrimaryTableProps['onSelectChange'] = (
    selectedRowKeys: (string | number)[],
    options: SelectOptions<TableRowData>,
  ) => {
    const { selectedRowData } = options;
    selections.value = [...selectedRowData];
    selectionsRowKeys.value = [...selectedRowKeys];
  };

  /**
   * 自定义单行选择事件（支持手动控制单勾选/取消）
   * @param params 选择参数：是否勾选、行唯一键、行数据
   */
  const handleCustomSelectChange = ({
    isCheck,
    tableRowKey = 'id',
    row = {},
  }: CustomSelectChangeParams) => {
    const rowKey = row[tableRowKey] as string | number;
    if (isCheck) {
      // 避免重复添加
      if (!selectionsRowKeys.value.includes(rowKey)) {
        selections.value.push(row);
        selectionsRowKeys.value.push(rowKey);
      }
    }
    else {
      selections.value = selections.value.filter((item: any) => item[tableRowKey] !== rowKey);
      selectionsRowKeys.value = selectionsRowKeys.value.filter((key: any) => key !== rowKey);
    }
  };

  /**
   * 自定义全选事件（支持跨页选择的全选/取消全选）
   * @param params 全选参数：是否全选、行唯一键、当前页表格数据
   */
  const handleCustomSelectAllChange = ({
    isCheck,
    tableRowKey = 'id',
    tables = [],
  }: CustomSelectAllChangeParams) => {
    if (!tables.length || !tableRowKey) return;

    // 生成当前页行Key集合（用于快速判断）
    const pageKeySet = new Set(
      tables.map((item: any) => item[tableRowKey]).filter((key: any) => key != null) as (string | number)[],
    );

    // 生成已选行Key集合
    const selectedKeySet = new Set(selectionsRowKeys.value);

    if (isCheck) {
      pageKeySet.forEach(key => selectedKeySet.add(key));
    }
    else {
      pageKeySet.forEach(key => selectedKeySet.delete(key));
    }

    // 计算新的已选行数据：过滤掉当前页需取消的，保留其他页+当前页需选中的
    const newSelections = selections.value
      .filter((item: any) => !pageKeySet.has(item[tableRowKey] as string | number))
      .concat(isCheck ? tables : []);
    const uniqueSelections = Array.from(
      new Map(newSelections.map((item: any) => [item[tableRowKey], item]))?.values(),
    );

    // 一次性更新响应式数据，减少视图更新次数
    selectionsRowKeys.value = Array.from(selectedKeySet);
    selections.value = uniqueSelections;
  };

  const resetSelections = () => {
    selections.value = [];
    selectionsRowKeys.value = [];
  };

  return {
    selections,
    selectionsRowKeys,
    resetSelections,
    handleSelectionChange,
    handleCustomSelectChange,
    handleCustomSelectAllChange,
  };
};
