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
 * 表格复选框相关状态和事件
 */
import { cloneDeep } from 'lodash-es';

export type SelectionType = {
  checked: boolean
  data: any[]
  isAll?: boolean
  row?: Record<string, unknown>
};

export const useSelection = (
  { isRowSelectEnable }: { isRowSelectEnable?: (row: Record<string, unknown>) => boolean } = {},
) => {
  const selections: Ref<any[]> = ref([]);

  const isSelectable = isRowSelectEnable || (() => true);

  // 单选
  const handleSelectionChange = (selection: SelectionType) => {
    if (selection.checked) {
      selections.value.push(selection?.row);
    }
    else {
      const index = selections.value.findIndex(item => item.id === selection.row?.id);
      selections.value.splice(index, 1);
    }
  };

  // 多选
  const handleSelectAllChange = (selection: SelectionType) => {
    if (selection.checked) {
      selections.value = cloneDeep(selection.data.filter(item => isSelectable(item)));
    }
    else {
      selections.value = [];
    }
  };

  const resetSelections = (tableRef: { clearSelection: () => void }) => {
    selections.value = [];
    tableRef?.clearSelection();
  };

  return {
    selections,
    handleSelectionChange,
    handleSelectAllChange,
    resetSelections,
  };
};
