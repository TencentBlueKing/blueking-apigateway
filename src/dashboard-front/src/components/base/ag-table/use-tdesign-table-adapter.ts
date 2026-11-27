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

import { throttle } from 'lodash-es';
import type { TableRowData } from '@blueking/tdesign-ui';
import type { GlobalConfigProvider } from 'tdesign-vue-next';
import cnConfig from 'tdesign-vue-next/es/locale/zh_CN';
import enConfig from 'tdesign-vue-next/es/locale/en_US';
import { locale } from '@/locales';
import type { IRowCellOverflowEvent, RowHoverEvent, TableRow } from './types';

const FILTER_PANEL_SELECTOR = '.t-table__filter-pop-content';
const FILTER_ACTIONS_SELECTOR = '.t-table__filter--bottom-buttons';

interface ITDesignTableAdapterOptions<TRow extends TableRowData = TableRowData> {
  getTableElement: () => Element | undefined
  onFilterIconClick: () => void
  onRowMouseEnter: (event: RowHoverEvent<TableRow<TRow>>) => void
  onRowMouseLeave: (event: RowHoverEvent<TableRow<TRow>>) => void
}

// TDesign 在省略 filterRow 时会额外显示筛选结果行。
export const renderEmptyFilterRow = () => null;

export const updateCellOverflow = <TRow extends TableRowData = TableRowData>({
  e,
  row,
}: IRowCellOverflowEvent<TableRow<TRow>>) => {
  const target = e.target;
  if (!(target instanceof Element)) return;
  const truncatedElement = target.closest('.truncate');
  // 事件可能落在文本内部，也可能落在包住多个省略文本的单元格上。
  const isOverflow = truncatedElement
    ? truncatedElement.scrollWidth > truncatedElement.clientWidth
    : Array.from(target.querySelectorAll<HTMLElement>('.truncate'))
      .some(element => element.scrollWidth > element.clientWidth);
  if (row.isOverflow !== isOverflow) row.isOverflow = isOverflow;
};

export const clearCellOverflow = <TRow extends TableRowData = TableRowData>({
  row,
}: Pick<IRowCellOverflowEvent<TableRow<TRow>>, 'row'>) => {
  if (row.isOverflow) delete row.isOverflow;
};

export const useTDesignTableAdapter = <TRow extends TableRowData = TableRowData>(
  options: ITDesignTableAdapterOptions<TRow>,
) => {
  const localeConfig = computed<GlobalConfigProvider>(() => {
    const config = locale.value === 'zh-cn' ? cnConfig : enConfig;
    return {
      ...config,
      datePicker: {
        ...config.datePicker,
        months: [...config.datePicker.months],
        weekdays: [...config.datePicker.weekdays],
        quarters: [...config.datePicker.quarters],
      },
      rate: {
        ...config.rate,
        rateText: [...config.rate.rateText],
      },
    };
  });

  const handleRowEnter = throttle(({ e, row }: RowHoverEvent<TableRowData>) => {
    options.onRowMouseEnter({
      e,
      row: row as TableRow<TRow>,
    });
  }, 100);

  const handleRowLeave = throttle(({ e, row }: RowHoverEvent<TableRowData>) => {
    delete row.isOverflow;
    options.onRowMouseLeave({
      e,
      row: row as TableRow<TRow>,
    });
  }, 100);

  onScopeDispose(() => {
    handleRowEnter.cancel();
    handleRowLeave.cancel();
  });

  let activeFilterTrigger: Element | null = null;

  const isOwnedFilterPanel = (panel: Element) => {
    const ownerTable = panel.closest('.t-table');
    return !ownerTable || ownerTable === options.getTableElement();
  };

  const isElementVisible = (element: Element) =>
    element.isConnected
    && !element.closest('.t-popup--hidden')
    && getComputedStyle(element).display !== 'none'
    && getComputedStyle(element).visibility !== 'hidden';

  const hasVisibleOwnedFilterPanel = () =>
    Array.from(document.querySelectorAll(FILTER_PANEL_SELECTOR))
      .some(panel => isOwnedFilterPanel(panel) && isElementVisible(panel));

  const stopListeningToFilterPanel = () => {
    document.removeEventListener('click', handleFilterPanelClick);
    document.removeEventListener('keydown', handleFilterKeyDown);
    activeFilterTrigger = null;
  };

  const handleFilterKeyDown = (event: KeyboardEvent) => {
    if (event.key === 'Escape') stopListeningToFilterPanel();
  };

  // TDesign 的筛选弹层可以挂在表格之外，单选项也可能异步加载，仅在打开期间委托给 document。
  const handleFilterPanelClick = async (event: MouseEvent) => {
    const target = event.target;
    const openingTrigger = activeFilterTrigger;
    if (!openingTrigger || !(target instanceof Element) || openingTrigger.contains(target)) return;

    const filterPanel = target.closest(FILTER_PANEL_SELECTOR);
    if (!filterPanel || !isOwnedFilterPanel(filterPanel) || target.closest(FILTER_ACTIONS_SELECTOR)) {
      stopListeningToFilterPanel();
      return;
    }

    const radioInput = target.closest('.t-radio-group label.t-radio')
      ?.querySelector<HTMLInputElement>('input.t-radio__former');
    if (!radioInput || radioInput.disabled) return;

    // 点击 label 还会触发 input 的 click。等选中值同步后，只由仍持有本次弹层的回调确认一次。
    await nextTick();
    if (activeFilterTrigger !== openingTrigger || !radioInput.checked || !filterPanel.isConnected) return;
    stopListeningToFilterPanel();
    filterPanel.querySelector<HTMLButtonElement>(`${FILTER_ACTIONS_SELECTOR} > .t-button--theme-primary`)?.click();
  };

  const handleTableClick = (event: Event) => {
    const target = event.target;
    // 展开行里可以嵌套 AgTable，每个表只接收离点击目标最近的那个表格的事件。
    if (!(target instanceof Element) || target.closest('.t-table') !== event.currentTarget) return;
    const filterTrigger = target.closest('.t-table__filter-icon-wrap');
    if (filterTrigger) {
      if (filterTrigger === activeFilterTrigger && hasVisibleOwnedFilterPanel()) {
        stopListeningToFilterPanel();
        return;
      }
      activeFilterTrigger = filterTrigger;
      document.addEventListener('click', handleFilterPanelClick);
      document.addEventListener('keydown', handleFilterKeyDown);
      if (filterTrigger.closest('.need-filter-icon-handler')) options.onFilterIconClick();
      return;
    }
    const settingsHeader = target.closest('th[data-colkey="__col_setting__"]');
    if (settingsHeader) {
      event.stopPropagation();
      if (!target.closest('.column-settings-icon')) {
        settingsHeader.querySelector<HTMLElement>('.column-settings-icon')?.click();
      }
    }
  };

  watch(options.getTableElement, (tableElement, _, onCleanup) => {
    if (!(tableElement instanceof Element)) return;
    tableElement.addEventListener('click', handleTableClick);
    onCleanup(() => {
      tableElement.removeEventListener('click', handleTableClick);
      stopListeningToFilterPanel();
    });
  }, { flush: 'post' });

  return {
    localeConfig,
    handleRowEnter,
    handleRowLeave,
  };
};
