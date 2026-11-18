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

import { Checkbox, Popover } from 'bkui-vue';
import type { TableRowData } from '@blueking/tdesign-ui';
import type { IAgTableSlots, ITableColumn } from '../types';
import type { useRowSelection } from './use-row-selection';

export const createRowSelectionColumn = <TRow extends TableRowData = TableRowData>(
  selection: ReturnType<typeof useRowSelection<TRow>>,
  slots: IAgTableSlots<TRow>,
): ITableColumn<TRow> => ({
  colKey: 'row-select',
  align: 'center',
  fixed: 'left',
  width: 42,
  title: () => (
    <Checkbox
      class="custom-ag-table-checkbox"
      modelValue={selection.allSelectableRowsSelected.value}
      disabled={!selection.hasSelectableRows.value}
      indeterminate={selection.isPartiallySelected.value}
      onChange={selection.setAllRowsSelected}
    />
  ),
  cell: (_, { row }) => {
    const businessDisabled = selection.isRowBusinessDisabled(row);
    const disabled = selection.isRowDisabled(row);
    // 仅在业务禁用且存在提示内容时弹出 Popover，避免缺 key 禁用行误显示业务文案或空弹框。
    const showPopover = businessDisabled && (Boolean(slots.selectionPopoverContent) || Boolean(row.selectionTip));
    return (
      <Popover trigger="hover" placement="top" popoverDelay={100} disabled={!showPopover}>
        {{
          default: () => (
            <span class="inline-flex align-middle" onClick={(event: MouseEvent) => event.stopPropagation()}>
              <Checkbox
                class="custom-ag-table-checkbox"
                modelValue={selection.isRowSelected(row)}
                disabled={disabled}
                onChange={(checked: boolean) => selection.setRowSelected(row, checked)}
              />
            </span>
          ),
          content: () => (showPopover ? <div>{slots.selectionPopoverContent?.(row) ?? row.selectionTip}</div> : null),
        }}
      </Popover>
    );
  },
});
