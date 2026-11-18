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

import { computed, createApp, defineComponent, h, nextTick, ref, shallowRef } from 'vue';
import { Button, Exception } from 'bkui-vue';
import AgTable from '@/components/base/ag-table/Index.vue';
import { AG_TABLE_CONTEXT_KEY } from '@/components/base/ag-table/context';
import { pruneTablePreferences } from '@/components/base/ag-table/settings/table-preferences';

const testTableContext = {
  getNoticeHeight: () => 0,
};

const checks = [];
const errors = [];
const requests = [];
const filters = [];
const metrics = {};
const fixtureRows = [
  {
    id: 1,
    name: 'First row',
    status: 'on',
    optional: 'A',
  },
  {
    id: 'second',
    name: 'Second row',
    status: 'off',
    optional: 'B',
  },
];
const columns = [
  {
    colKey: 'name',
    displayTitle: 'Name setting',
    title: () => h('span', 'Name header'),
  },
  {
    colKey: 'status',
    title: 'Status',
    className: 'need-filter-icon-handler',
    filter: {
      type: 'single',
      showConfirmAndReset: true,
      list: [{
        label: 'Enabled',
        value: 'on',
      },
      {
        label: 'Disabled',
        value: 'off',
      }],
    },
  },
  {
    colKey: 'optional',
    title: 'Optional',
  },
];

const mode = ref('remote');
const tableInstanceKey = ref(0);
const remountTable = (nextMode) => {
  mode.value = nextMode;
  tableInstanceKey.value++;
};
const table = shallowRef(null);
const data = ref([]);
const settings = ref(null);
const filterValue = ref({});
const selectedKeys = ref([]);
const selected = ref({
  selections: [],
  selectionsRowKeys: [],
});
const disabledRowKeys = ref([]);
const childKeys = ref([]);
const childFilters = [];
const cacheIdentifier = ref('');
const extraColumn = ref(false);
const nativeSelectionColumn = {
  colKey: 'row-select',
  type: 'multiple',
};
const extraColumnDefinition = {
  colKey: 'extra',
  title: 'Extra',
};
const tableColumns = computed(() => {
  if (mode.value === 'native') return [nativeSelectionColumn, ...columns];
  return extraColumn.value ? [...columns, extraColumnDefinition] : columns;
});
let filterOpenCount = 0;
let filterConfirmCount = 0;
let selectionChangeCount = 0;
let pendingRequest;
let failNextRequest = false;
let clickedRow;
let source = fixtureRows;

const request = async (params) => {
  requests.push({ ...params });
  if (failNextRequest) {
    failNextRequest = false;
    throw Error('Fixture request failed');
  }
  if (pendingRequest) {
    const pending = pendingRequest;
    pendingRequest = undefined;
    await pending;
  }
  return {
    count: source.length,
    results: source.slice(params.offset, params.offset + params.limit),
  };
};

const Fixture = defineComponent({
  setup: () => () => h(AgTable, {
    'key': tableInstanceKey.value,
    'ref': table,
    'tableData': data.value,
    'onUpdate:tableData': (value) => {
      data.value = value;
    },
    'selectedRowKeys': selectedKeys.value,
    'onUpdate:selectedRowKeys': (value) => {
      selectedKeys.value = value;
    },
    'settings': settings.value,
    'onUpdate:settings': (value) => {
      settings.value = value;
    },
    'apiMethod': mode.value === 'remote' ? request : undefined,
    'localPage': mode.value === 'local' || mode.value === 'nested',
    'immediate': mode.value === 'remote',
    'showSettings': true,
    'showSelection': mode.value !== 'native',
    'columns': tableColumns.value,
    'selectOnRowClick': mode.value === 'native',
    'expandedRowKeys': mode.value === 'nested' ? [1] : undefined,
    'disabledCheckSelection': row => disabledRowKeys.value.includes(row.id),
    'uncheckedColumn': ['optional'],
    'cacheIdentifier': cacheIdentifier.value || 'fixture-' + mode.value,
    'filterValue': filterValue.value,
    'onFilterChange': (value) => {
      filters.push(value);
      filterValue.value = value;
    },
    'onFilterIconClick': () => {
      filterOpenCount++;
    },
    'onRowClick': ({ row }) => {
      clickedRow = row;
    },
    'onSelectionChange': (value) => {
      selectionChangeCount++;
      selected.value = value;
    },
  }, mode.value === 'nested'
    ? {
      expandedRow: () => h(AgTable, {
        class: 'nested-resources',
        localPage: true,
        showSelection: true,
        columns,
        onFilterChange: value => childFilters.push(value),
        tableData: fixtureRows,
        onSelectionChange: (selection) => {
          childKeys.value = selection.selectionsRowKeys;
        },
      }),
    }
    : {}),
});

const app = createApp(Fixture);
app.provide(AG_TABLE_CONTEXT_KEY, testTableContext);
app.component('BkException', Exception);
app.component('BkButton', Button);
app.config.errorHandler = error => errors.push(error.stack || String(error));
window.addEventListener('error', event => errors.push(event.message));
window.addEventListener('unhandledrejection', event => errors.push(String(event.reason)));

const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const find = selector => document.querySelector(selector);
const visible = selector => [...document.querySelectorAll(selector)].find(el =>
  el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden' && !el.closest('.t-popup--hidden'));
const shows = text => find('tbody')?.textContent.includes(text);
const checkbox = () => find('tbody input[type=checkbox]');
const filterIcon = () => find('.t-table__filter-icon');
const popup = () => visible('.t-table__filter-pop-content');

async function assertEventually(label, predicate) {
  const deadline = performance.now() + 5000;
  while (!predicate()) {
    if (errors.length || performance.now() > deadline) throw Error([label, ...errors].join('\n'));
    await wait(16);
  }
  checks.push(label);
}

async function verifySingleSelectFilter() {
  await assertEventually('Single-select trigger renders', filterIcon);
  for (const [index, status] of ['on', 'off'].entries()) {
    filterIcon().click();
    await assertEventually('Filter opens for ' + status, () => popup()?.querySelector('label.t-radio'));
    const panel = popup();
    panel.querySelector('button.t-button--theme-primary').addEventListener('click', () => {
      filterConfirmCount++;
    });
    panel.querySelectorAll('label.t-radio .t-radio__label')[index].click();
    await assertEventually('Radio choice applied: ' + status, () => filters.at(-1)?.status === status);
    await assertEventually('Popup closes after ' + status, () => !popup());
    await assertEventually('One notification and confirmation per choice', () =>
      filterOpenCount === index + 1 && filterConfirmCount === index + 1 && filters.length === index + 1);
  }
  await assertEventually('Default filter result row stays hidden', () => !find('.t-table__filter-result'));
  filterIcon().click();
  await assertEventually('Filter reopens', popup);
  filterIcon().click();
  await assertEventually('Header toggles the popup closed', () => !popup());
  await assertEventually('Closing does not confirm or reload options', () => filterOpenCount === 3 && filterConfirmCount === 2);
}

async function verifyInitialSettings() {
  localStorage.setItem('table-settings-fixture-remote', JSON.stringify({
    checked: ['name', 'status', 'optional', 'obsolete', 1],
    fontSize: 'large',
    rowSize: 'mini',
  }));
  app.mount('#app');
  await assertEventually('Remote first page renders', () => shows('First row'));
  await assertEventually('Exactly one initial request', () =>
    requests.length === 1 && requests[0].offset === 0 && requests[0].limit === 10);
  await assertEventually('Cached visible columns and sizes', () => settings.value.rowSize === 'mini'
    && settings.value.fontSize === 'large' && settings.value.checked.join() === 'name,status,optional');
  await assertEventually('Text setting label for a rendered title', () =>
    settings.value.fields.find(col => col.field === 'name')?.label === 'Name setting');
  settings.value = null;
  await nextTick();
  await assertEventually('Parent null reset restores cached sizes', () => settings.value?.rowSize === 'mini');
}

async function verifyInitialPageSize() {
  const cacheKey = 'table-settings-fixture-layout';
  const maxLimitConfig = {
    mode: 'tdesign',
    allocatedHeight: window.innerHeight - 680,
  };
  const sizeClass = {
    mini: 't-size-xs',
    medium: 't-size-m',
    large: 't-size-l',
  };
  const checkLayout = async (label, props, rowSize, pageSize) => {
    const container = document.body.appendChild(document.createElement('div'));
    let firstLimit;
    let appliedSettings = props.settings;
    const tableProps = {
      'cacheIdentifier': 'fixture-layout',
      'columns': [{
        colKey: 'name',
        title: 'Name',
      }],
      'tableData': fixtureRows,
      'showSettings': true,
      maxLimitConfig,
      'apiMethod': async ({ limit }) => {
        firstLimit ??= limit;
        return {
          count: fixtureRows.length,
          results: fixtureRows,
        };
      },
      'onUpdate:settings': (value) => {
        appliedSettings = value;
      },
      ...props,
    };
    const fixture = createApp(AgTable, tableProps);
    fixture.provide(AG_TABLE_CONTEXT_KEY, testTableContext);
    fixture.config.errorHandler = app.config.errorHandler;
    fixture.component('BkException', Exception);
    fixture.component('BkButton', Button);
    try {
      const instance = fixture.mount(container);
      await assertEventually(label, () => appliedSettings?.rowSize === rowSize
        && container.querySelector('.t-table')?.classList.contains(sizeClass[rowSize])
        && firstLimit === pageSize && instance.getPagination().pageSize === pageSize);
      return appliedSettings;
    }
    finally {
      fixture.unmount();
      container.remove();
    }
  };

  // 680px 可用高度预留 64px 分页器后，可容纳 18 行 mini、13 行 medium 或 10 行 large。
  localStorage.setItem(cacheKey, JSON.stringify({ rowSize: 'mini' }));
  await checkLayout('Disabling preferences ignores a stale row size for both settings and the first request',
    { cacheSettingsInLocalStorage: false }, 'medium', 13);
  await checkLayout('Cached row size takes precedence over the parent row size',
    { settings: { rowSize: 'large' } }, 'mini', 18);
  await checkLayout('An empty layout config keeps the default ten rows', { maxLimitConfig: {} }, 'mini', 10);
  localStorage.removeItem(cacheKey);
  await checkLayout('The parent row size sets the first request limit', { settings: { rowSize: 'large' } }, 'large', 10);
  await checkLayout('The configured default row size sets the first request limit', { defaultRowSize: 'mini' }, 'mini', 18);
  await checkLayout('A layout default also applies to parent settings that only specify columns', {
    settings: { checked: ['name'] },
    maxLimitConfig: {
      ...maxLimitConfig,
      defaultRowSize: 'large',
    },
  }, 'large', 10);
  localStorage.setItem(cacheKey, JSON.stringify({ size: 'mini' }));
  await checkLayout('Legacy size preferences set the displayed row size and the first request limit', {}, 'mini', 18);
  localStorage.removeItem(cacheKey);

  const legacyKey = 'table-settings-old-layout';
  localStorage.setItem(legacyKey, JSON.stringify({
    size: 'mini',
    checked: ['status'],
  }));
  const legacySettings = await checkLayout('A legacy className supplies the row size for this table', {
    maxLimitConfig: {
      ...maxLimitConfig,
      className: 'old-layout',
    },
  }, 'mini', 18);
  await assertEventually('The legacy layout key supplies only row size', () => legacySettings.checked.includes('name'));
  localStorage.removeItem(legacyKey);
}

async function verifyRemotePaginationAndSelection() {
  const firstSearch = Promise.withResolvers();
  pendingRequest = firstSearch.promise;
  table.value.fetchData({
    search: 'api',
    unused: '',
  }, { resetPage: true });
  await assertEventually('Remote search strips empty filters', () => requests.at(-1).search === 'api' && !('unused' in requests.at(-1)));
  table.value.setPagination({
    current: 1,
    pageSize: 1,
  });
  await assertEventually('Paging an in-flight search retains the query', () => requests.at(-1).search === 'api' && requests.at(-1).limit === 1);
  firstSearch.resolve();
  await assertEventually('Page one contains one visible row', () => shows('First row') && !shows('Second row'));
  await assertEventually('Custom checkbox renders', () => checkbox()?.closest('.custom-ag-table-checkbox'));
  const beforeClick = selectionChangeCount;
  checkbox().click();
  await nextTick();
  await assertEventually('A custom click updates v-model and emits exactly once', () => selectionChangeCount === beforeClick + 1
    && selectedKeys.value.length === 1 && selectedKeys.value[0] === 1);
  await assertEventually('Numeric key is selected', () => selected.value.selectionsRowKeys.includes(1));
  table.value.setPagination({
    current: 2,
    pageSize: 1,
  });
  await assertEventually('Remote page two keeps the query', () => requests.at(-1).offset === 1 && shows('Second row'));
  checkbox().click();
  await assertEventually('Mixed row keys survive across pages', () => selected.value.selectionsRowKeys.join() === '1,second');
  table.value.setPagination({
    current: 1,
    pageSize: 1,
  });
  await assertEventually('Returning to page one restores its checkbox', () => shows('First row') && checkbox()?.checked);
}

async function verifyColumnSettings() {
  const { pageSize } = table.value.getPagination();
  const requestCount = requests.length;
  find('th[data-colkey="__col_setting__"]').click();
  await assertEventually('Settings header opens panel', () => visible('.bkui-col-settings'));
  visible('.bkui-col-settings').querySelectorAll('.settings-header > *')[1].click();
  await assertEventually('Appearance panel reflects mini', () => visible('.appearance-settings')?.querySelector('input[value=mini]')?.checked);
  visible('.appearance-settings').querySelector('input[value=small]').closest('label').click();
  await assertEventually('Row size changes inside the open panel', () =>
    visible('.appearance-settings')?.querySelector('input[value=small]')?.checked);
  find('th[data-colkey="__col_setting__"]').click();
  await assertEventually('Appearance edit is reflected in v-model', () => settings.value.rowSize === 'small');
  await assertEventually('Editing row size preserves the selected page size and request count', () =>
    table.value.getPagination().pageSize === pageSize && requests.length === requestCount);
  await assertEventually('Cache stores only user preferences', () =>
    Object.keys(JSON.parse(localStorage.getItem('table-settings-fixture-remote'))).sort().join() === 'checked,fontSize,rowSize');
  extraColumn.value = true;
  await assertEventually('New column definitions reach the settings panel', () =>
    settings.value.fields.some(({ field }) => field === 'extra'));
  localStorage.setItem('table-settings-another-table', JSON.stringify({
    checked: ['status'],
    rowSize: 'large',
  }));
  cacheIdentifier.value = 'another-table';
  await assertEventually('Switching table identity reads its own preferences', () =>
    settings.value.rowSize === 'large' && settings.value.checked.join() === 'status'
    && find('.t-table')?.classList.contains('t-size-l'));
  cacheIdentifier.value = '';
  extraColumn.value = false;
  await assertEventually('Switching back restores the edited preferences', () =>
    settings.value.rowSize === 'small' && find('.t-table')?.classList.contains('t-size-s'));
  localStorage.setItem('table-settings-damaged', '{incomplete');
  cacheIdentifier.value = 'damaged';
  await assertEventually('Invalid cache contents fall back to current column defaults', () =>
    settings.value.rowSize === 'medium' && settings.value.checked.includes('name') && !settings.value.checked.includes('obsolete'));
  settings.value = {
    fields: [{
      field: 'status',
      label: 'Custom status label',
    }],
    checked: ['status'],
    rowSize: 'large',
  };
  await assertEventually('Caller-defined fields reach the actual table', () => shows('on') && !find('thead th[data-colkey="name"]'));
  settings.value = null;
  await assertEventually('Resetting caller-defined fields rebuilds defaults', () =>
    settings.value?.rowSize === 'medium' && find('thead th[data-colkey="name"]'));
  cacheIdentifier.value = '';
}

async function verifyLocalPaginationAndSelection() {
  table.value.handleResetSelection();
  await assertEventually('Clear selection empties rows and keys', () => !selected.value.selections.length && !selected.value.selectionsRowKeys.length);
  remountTable('local');
  data.value = fixtureRows;
  await assertEventually('Injected local data renders', () => shows('Second row'));
  await assertEventually('New table gets its own defaults', () => settings.value?.rowSize === 'medium' && !settings.value.checked.includes('optional'));
  table.value.setPagination({
    current: 2,
    pageSize: 1,
  });
  await assertEventually('Local pagination slices data once', () => shows('Second row') && !shows('First row'));
  const headerCheckbox = () => find('thead .custom-ag-table-checkbox input');
  headerCheckbox().click();
  await assertEventually('Local select-all includes both pages', () => selected.value.selectionsRowKeys.join() === '1,second');
  table.value.handleResetSelection();

  disabledRowKeys.value = ['second'];
  await nextTick();
  headerCheckbox().click();
  await assertEventually('Select-all observes changes to the disabled rule with identical row keys', () =>
    selected.value.selectionsRowKeys.join() === '1');
  selectedKeys.value = ['second', 'unloaded'];
  await assertEventually('External keys resolve known rows and retain unloaded keys', () =>
    selected.value.selectionsRowKeys.join() === 'second,unloaded' && selected.value.selections.length === 1);
  data.value = [
    ...fixtureRows,
    {
      id: 'unloaded',
      name: 'New resource',
    },
  ];
  await assertEventually('Selected keys resolve when matching records arrive', () =>
    selected.value.selections.map(row => row.name).join() === 'Second row,New resource');
  table.value.setSelectionData([{
    ...fixtureRows[0],
    tool_name: 'edited_alias',
  }]);
  await assertEventually('Programmatic row selection updates the model', () => selectedKeys.value.join() === '1');
  data.value = fixtureRows.map(row => ({ ...row }));
  await nextTick();
  await assertEventually('Reloading source rows preserves the caller-supplied tool alias', () =>
    selected.value.selections[0]?.tool_name === 'edited_alias');
  disabledRowKeys.value = [];
  table.value.handleResetSelection();
  data.value = fixtureRows.map(row => ({
    ...row,
    detail: { resources: [row.id] },
  }));
  await nextTick();
  find('tbody .custom-ag-table-checkbox').closest('tr').click();
  await assertEventually('Rendered row is available for editing', () => clickedRow?.id === 'second');
  clickedRow.isOverflow = true;
  clickedRow.detail.resources.push('view only');
  await assertEventually('View edits are isolated from input rows, including nested edits', () =>
    !data.value[1].isOverflow && data.value[1].detail.resources.length === 1);
  data.value[1].detail.resources[0] = 'updated by parent';
  await assertEventually('In-place parent edits update nested view data', () =>
    clickedRow.detail.resources[0] === 'updated by parent' && clickedRow.detail.resources.length === 1);
  data.value = [fixtureRows[0]];
  await assertEventually('Removing the last page corrects pagination without selection', () =>
    table.value.getPagination().current === 1 && table.value.getPagination().total === 1 && shows('First row'));
  const missingKeyRow = { name: 'Missing key' };
  const zeroKeyRow = {
    id: 0,
    name: 'Zero key',
  };
  data.value = [missingKeyRow, zeroKeyRow];
  await assertEventually('A row without a key cannot be selected', () => shows('Missing key') && checkbox()?.disabled);
  headerCheckbox().click();
  await assertEventually('Select-all accepts zero as a row key', () => selectedKeys.value.length === 1 && selectedKeys.value[0] === 0);
  table.value.setSelectionData([missingKeyRow, zeroKeyRow]);
  await assertEventually('Restoring rows uses the same key rules as clicking', () =>
    selected.value.selections.length === 1 && selectedKeys.value.length === 1 && selectedKeys.value[0] === 0);
  table.value.handleResetSelection();
}

async function verifyNativeAndNestedSelection() {
  data.value = fixtureRows;
  remountTable('native');
  await assertEventually('Native selection column renders', () => find('tbody .t-checkbox'));
  find('tbody .t-checkbox').closest('tr').click();
  await assertEventually('Native selection updates model and event', () =>
    selectedKeys.value.includes(1) && selected.value.selectionsRowKeys.includes(1));
  selectedKeys.value = ['unloaded'];
  await assertEventually('Native table accepts an external key before its row loads', () =>
    selected.value.selectionsRowKeys.join() === 'unloaded' && !selected.value.selections.length);
  find('tbody .t-checkbox').closest('tr').click();
  await assertEventually('Native selection keeps unloaded keys when another row is checked', () =>
    selectedKeys.value.join() === 'unloaded,1' && selected.value.selections[0]?.id === 1);
  table.value.handleResetSelection();
  data.value = [{ name: 'Missing native key' }, fixtureRows[0]];
  await assertEventually('Native table renders the row without a key', () => shows('Missing native key'));
  find('thead .t-checkbox input').click();
  await assertEventually('Native select-all only emits valid row keys', () =>
    selectedKeys.value.length === 1 && selectedKeys.value[0] === 1);
  table.value.handleResetSelection();
  data.value = fixtureRows;
  remountTable('nested');
  await assertEventually('Expanded resource table renders', () => find('.nested-resources tbody .custom-ag-table-checkbox'));
  find('.nested-resources thead .custom-ag-table-checkbox input').click();
  await assertEventually('Child table selects its resources independently', () => childKeys.value.join() === '1,second'
    && !selectedKeys.value.length);

  const parentFilterCount = filters.length;
  find('.nested-resources .t-table__filter-icon').click();
  await assertEventually('Nested table opens its own filter', () => popup()?.querySelector('label.t-radio'));
  popup().querySelector('label.t-radio .t-radio__label').click();
  await assertEventually('Nested filter confirms only in the owning table', () => childFilters.length === 1
    && childFilters[0].status === 'on' && filters.length === parentFilterCount);
  await assertEventually('Nested filter closes cleanly', () => !popup());
}

async function verifyStaticData(requestCountBeforeLocalModes) {
  remountTable('static');
  data.value = [fixtureRows[0]];
  await assertEventually('Static data renders', () => shows('First row'));
  table.value.fetchData();
  table.value.refresh();
  await nextTick();
  await assertEventually('Static refresh preserves injected data', () => data.value.length === 1 && requests.length === requestCountBeforeLocalModes);
}

async function verifyRequestRetry() {
  remountTable('remote');
  await assertEventually('Remounted remote table finishes its initial request', () => shows('Second row'));
  failNextRequest = true;
  table.value.fetchData({ search: 'retry-me' });
  await assertEventually('Request failure clears rows and shows refresh', () =>
    table.value.getPagination().total === 0 && !!find('.api-gateways-exception button'));
  find('.api-gateways-exception button').click();
  await assertEventually('Retry reuses filters and restores results', () => requests.at(-1).search === 'retry-me' && shows('First row'));
}

async function verifySwitchToLocalAfterError() {
  failNextRequest = true;
  table.value.fetchData({ search: 'remote-only' });
  await assertEventually('Remote error is visible before switching data sources', () => find('.api-gateways-exception button'));
  mode.value = 'local';
  await assertEventually('Switching to local data clears the remote error and search empty state', () =>
    find('.api-gateways-exception')?.textContent.includes('暂无数据') && !find('.api-gateways-exception button'));
}

async function run() {
  await verifyInitialSettings();
  await verifyRemotePaginationAndSelection();
  await verifySingleSelectFilter();
  await verifyColumnSettings();

  const requestCountBeforeLocalModes = requests.length;
  await verifyLocalPaginationAndSelection();
  await verifyNativeAndNestedSelection();
  await verifyStaticData(requestCountBeforeLocalModes);

  await verifyRequestRetry();
  await measureLogPagination();
  await verifySwitchToLocalAfterError();
  app.unmount();
  await assertEventually('Unmount releases settings', () => settings.value === null);
  await verifyInitialPageSize();
  await verifyFixRegressions();
  await assertEventually('No browser or Vue errors', () => errors.length === 0);
}

async function verifyFixRegressions() {
  const mountIsolated = (renderRoot, runtimeContext = testTableContext) => {
    const container = document.body.appendChild(document.createElement('div'));
    const isolatedApp = createApp(() => renderRoot());
    isolatedApp.provide(AG_TABLE_CONTEXT_KEY, runtimeContext);
    isolatedApp.config.errorHandler = app.config.errorHandler;
    isolatedApp.component('BkException', Exception);
    isolatedApp.component('BkButton', Button);
    isolatedApp.mount(container);
    return {
      container,
      unmount: () => {
        isolatedApp.unmount();
        container.remove();
      },
    };
  };

  // 1. null 数据源、非法 selectedRowKeys 与缺少 count 的远程返回不崩溃且兜底 total=0
  const nullTableRef = shallowRef(null);
  const nullData = ref(null);
  const badKeys = ref(null);
  const nullSelected = ref({
    selections: [],
    selectionsRowKeys: [],
  });
  const nullFixture = mountIsolated(() => h(AgTable, {
    'ref': nullTableRef,
    'tableData': nullData.value,
    'onUpdate:tableData': (val) => {
      nullData.value = val;
    },
    'selectedRowKeys': badKeys.value,
    'onUpdate:selectedRowKeys': (val) => {
      badKeys.value = val;
    },
    'showSelection': true,
    'columns': [{
      colKey: 'name',
      title: 'Name',
    }],
    'apiMethod': async () => [],
    'onSelectionChange': (val) => {
      nullSelected.value = val;
    },
  }));
  try {
    await assertEventually('Missing count falls back to zero total', () =>
      nullTableRef.value?.getPagination().total === 0);
    badKeys.value = [undefined, null, {}, 1, 'valid'];
    await nextTick();
    await assertEventually('Invalid selectedRowKeys entries are filtered out', () =>
      nullSelected.value.selectionsRowKeys.join() === '1,valid');
  }
  finally {
    nullFixture.unmount();
  }

  // 2. showSettings=false 不渲染列设置齿轮、不读取缓存、且保留 size="small"
  const existingCacheKey = 'table-settings-explicit-id';
  localStorage.setItem(existingCacheKey, JSON.stringify({
    checked: ['name'],
    rowSize: 'large',
  }));
  const noSettingsFixture = mountIsolated(() => h(AgTable, {
    tableData: fixtureRows,
    localPage: true,
    showSettings: false,
    cacheIdentifier: 'explicit-id',
    size: 'small',
    columns,
  }));
  try {
    await assertEventually('Disabled settings omits setting column and preserves size prop', () =>
      !noSettingsFixture.container.querySelector('th[data-colkey="__col_setting__"]')
      && noSettingsFixture.container.querySelector('thead th[data-colkey="status"]')
      && noSettingsFixture.container.querySelector('.t-table')?.classList.contains('t-size-s'));
  }
  finally {
    noSettingsFixture.unmount();
    localStorage.removeItem(existingCacheKey);
  }

  // 2b. 开启 showSettings 但不传 cacheIdentifier 时，设置仅在内存生效，不读写 localStorage；且 noticeHeight 由上下文注入控制
  const storageKeysBefore = Object.keys(localStorage).sort();
  const ephemeralSettings = ref(null);
  const ephemeralTableRef = shallowRef(null);
  const ephemeralFixture = mountIsolated(() => h(AgTable, {
    'ref': ephemeralTableRef,
    'tableData': fixtureRows,
    'localPage': true,
    'showSettings': true,
    'maxLimitConfig': {
      mode: 'tdesign',
      allocatedHeight: window.innerHeight - 680,
    },
    'settings': ephemeralSettings.value,
    'onUpdate:settings': (val) => {
      ephemeralSettings.value = val;
    },
    'columns': columns,
  }), {
    // 680 - 40 = 640 可用高度，减去 64 分页与 42 表头后为 534，medium 42px 行高对应 12 条
    getNoticeHeight: () => 40,
  });
  try {
    await assertEventually('Runtime context injects noticeHeight into initial page size', () =>
      ephemeralTableRef.value?.getPagination().pageSize === 12);
    ephemeralFixture.container.querySelector('th[data-colkey="__col_setting__"]').click();
    await assertEventually('Settings without cacheIdentifier opens panel', () => visible('.bkui-col-settings'));
    visible('.bkui-col-settings').querySelectorAll('.settings-header > *')[1].click();
    await assertEventually('Settings without cacheIdentifier opens appearance tab', () => visible('.appearance-settings'));
    visible('.appearance-settings').querySelector('input[value=small]').closest('label').click();
    ephemeralFixture.container.querySelector('th[data-colkey="__col_setting__"]').click();
    await assertEventually('Settings without cacheIdentifier works in memory without touching localStorage', () =>
      ephemeralSettings.value?.rowSize === 'small'
      && Object.keys(localStorage).sort().join() === storageKeysBefore.join());
  }
  finally {
    ephemeralFixture.unmount();
  }

  // 3. cacheSettingsInLocalStorage=false 下置 null 不覆盖内存编辑；自定义 settings 卸载时还原不置 null
  const memSettings = ref(null);
  const memFixture = mountIsolated(() => h(AgTable, {
    'tableData': fixtureRows,
    'localPage': true,
    'showSettings': true,
    'cacheSettingsInLocalStorage': false,
    'cacheIdentifier': 'no-cache-table',
    'settings': memSettings.value,
    'onUpdate:settings': (val) => {
      memSettings.value = val;
    },
    'columns': columns,
  }));
  try {
    await assertEventually('No-cache settings initializes', () => memSettings.value?.rowSize === 'medium');
    memFixture.container.querySelector('th[data-colkey="__col_setting__"]').click();
    await assertEventually('No-cache settings panel opens', () => visible('.bkui-col-settings'));
    visible('.bkui-col-settings').querySelectorAll('.settings-header > *')[1].click();
    await assertEventually('No-cache appearance panel opens', () => visible('.appearance-settings'));
    visible('.appearance-settings').querySelector('input[value=small]').closest('label').click();
    memFixture.container.querySelector('th[data-colkey="__col_setting__"]').click();
    await assertEventually('No-cache edit updates model', () => memSettings.value?.rowSize === 'small');
    memSettings.value = null;
    await nextTick();
    await assertEventually('Null reset preserves in-memory edit when cache is disabled', () =>
      memSettings.value?.rowSize === 'small');
  }
  finally {
    memFixture.unmount();
  }

  const originalCustomSettings = {
    fields: [{
      field: 'name',
      label: 'Custom Name',
    }],
    checked: ['name'],
  };
  const customSettings = shallowRef(originalCustomSettings);
  const customFixture = mountIsolated(() => h(AgTable, {
    'tableData': fixtureRows,
    'localPage': true,
    'showSettings': true,
    'cacheIdentifier': 'custom-settings-table',
    'settings': customSettings.value,
    'onUpdate:settings': (val) => {
      customSettings.value = val;
    },
    'columns': columns,
  }));
  let customUnmounted = false;
  try {
    await assertEventually('Custom settings merges defaults', () => customSettings.value?.rowSize === 'medium');
    customFixture.unmount();
    customUnmounted = true;
    await assertEventually('Unmount restores caller-provided custom settings', () =>
      customSettings.value === originalCustomSettings);
  }
  finally {
    if (!customUnmounted) customFixture.unmount();
  }

  // 4. 常规勾选行在刷新后同步最新行对象，缺 key 行不弹出业务禁用提示
  const selRows = ref([
    {
      id: 1,
      name: 'Old Name',
    },
    { name: 'No Key Row' },
  ]);
  const selState = ref({
    selections: [],
    selectionsRowKeys: [],
  });
  const selFixture = mountIsolated(() => h(AgTable, {
    tableData: selRows.value,
    localPage: true,
    showSelection: true,
    columns: [{
      colKey: 'name',
      title: 'Name',
    }],
    disabledCheckSelection: () => false,
    onSelectionChange: (val) => {
      selState.value = val;
    },
  }, {
    selectionPopoverContent: () => 'Business disabled tip',
  }));
  try {
    await assertEventually('Selection regression rows render', () =>
      selFixture.container.querySelectorAll('tbody .custom-ag-table-checkbox input').length === 2);
    const inputs = selFixture.container.querySelectorAll('tbody .custom-ag-table-checkbox input');
    inputs[0].click();
    await assertEventually('Regular row selection captures initial row', () =>
      selState.value.selections[0]?.name === 'Old Name');
    selRows.value = [
      {
        id: 1,
        name: 'Refreshed Name',
      },
      { name: 'No Key Row' },
    ];
    await assertEventually('Regular row selection refreshes to latest row data', () =>
      selState.value.selections[0]?.name === 'Refreshed Name');
    // 缺 key 行被禁用但未触发业务禁用 Popover（不出现业务提示内容）
    const noKeyCheckbox = selFixture.container.querySelectorAll('tbody .custom-ag-table-checkbox')[1];
    noKeyCheckbox.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
    await wait(150);
    await assertEventually('Missing-key disabled row does not show business popover tip', () =>
      !document.body.textContent.includes('Business disabled tip'));
  }
  finally {
    selFixture.unmount();
  }

  // 5. Escape 键关闭筛选与跨表存在另一筛选弹层时，本表重新打开仍可自动确认单选筛选
  const escFilters = [];
  let escOpenCount = 0;
  const filterFixture = mountIsolated(() => h('div', [
    h(AgTable, {
      class: 'primary-filter-table',
      tableData: fixtureRows,
      localPage: true,
      columns,
      onFilterIconClick: () => {
        escOpenCount++;
      },
      onFilterChange: val => escFilters.push(val),
    }),
    h(AgTable, {
      class: 'sibling-filter-table',
      tableData: fixtureRows,
      localPage: true,
      columns,
    }),
  ]));
  try {
    await assertEventually('Escape filter fixture renders', () =>
      filterFixture.container.querySelector('.primary-filter-table .t-table__filter-icon')
      && filterFixture.container.querySelector('.sibling-filter-table .t-table__filter-icon'));
    const primaryTrigger = filterFixture.container.querySelector('.primary-filter-table .t-table__filter-icon');
    const siblingTrigger = filterFixture.container.querySelector('.sibling-filter-table .t-table__filter-icon');
    primaryTrigger.click();
    await assertEventually('Filter opens before Escape', () => popup()?.querySelector('label.t-radio'));
    document.dispatchEvent(new KeyboardEvent('keydown', {
      key: 'Escape',
      bubbles: true,
    }));
    // 兄弟表打开筛选弹层时，主表切回点击自己触发器仍能正常打开并自动确认单选筛选
    siblingTrigger.click();
    await assertEventually('Sibling filter popup opens', () => popup()?.querySelector('label.t-radio'));
    primaryTrigger.click();
    await assertEventually('Primary filter reopens after Escape and sibling popup', () => popup()?.querySelector('label.t-radio'));
    popup().querySelector('label.t-radio .t-radio__label').click();
    await assertEventually('Radio selection still auto-confirms after Escape and sibling popup', () =>
      escFilters.at(-1)?.status === 'on' && escOpenCount >= 2);
  }
  finally {
    filterFixture.unmount();
  }

  // 6. 新构建启动时清空旧的 table-settings-* / table-setting-* 缓存，保留无关存储且同构建内幂等
  localStorage.setItem('table-settings-AuditLog', JSON.stringify({ rowSize: 'large' }));
  localStorage.setItem('table-settings-AuditLog-zh-cn-1.24.0', JSON.stringify({ rowSize: 'small' }));
  localStorage.setItem('table-setting-zh-cn-LegacyPage', JSON.stringify({ size: 'small' }));
  localStorage.setItem('other-app-key', 'keep-me');
  const firstPruned = pruneTablePreferences('build-v1');
  await assertEventually('New build prunes stale table preference keys and keeps unrelated storage', () =>
    firstPruned === true
    && localStorage.getItem('table-settings-AuditLog') === null
    && localStorage.getItem('table-settings-AuditLog-zh-cn-1.24.0') === null
    && localStorage.getItem('table-setting-zh-cn-LegacyPage') === null
    && localStorage.getItem('other-app-key') === 'keep-me'
    && localStorage.getItem('table-settings:__build_id__') === 'build-v1');
  localStorage.setItem('table-settings-AuditLog', JSON.stringify({ rowSize: 'mini' }));
  const sameBuildPruned = pruneTablePreferences('build-v1');
  await assertEventually('Same build does not prune current table preferences', () =>
    sameBuildPruned === false
    && JSON.parse(localStorage.getItem('table-settings-AuditLog'))?.rowSize === 'mini');
  const nextBuildPruned = pruneTablePreferences('build-v2');
  await assertEventually('Subsequent build prunes preferences written by previous build', () =>
    nextBuildPruned === true
    && localStorage.getItem('table-settings-AuditLog') === null
    && localStorage.getItem('other-app-key') === 'keep-me'
    && localStorage.getItem('table-settings:__build_id__') === 'build-v2');
  localStorage.removeItem('other-app-key');
  localStorage.removeItem('table-settings:__build_id__');
}

async function measureLogPagination() {
  source = Array.from({ length: 300 }, (_, id) => ({
    id,
    name: 'Log entry #' + id + '#',
    details: Array.from({ length: 20 }, (_, span) => ({
      span,
      tags: ['gateway', 'upstream'],
      elapsed: span + id,
    })),
  }));
  table.value.fetchData({}, { resetPage: true });
  await assertEventually('Log fixture renders', () => shows('Log entry #0#'));
  const elapsed = [];
  for (const page of [2, 3, 4, 5, 6, 1, 2]) {
    const start = performance.now();
    table.value.setPagination({
      current: page,
      pageSize: 50,
    });
    await assertEventually('Log page ' + page, () => shows('Log entry #' + ((page - 1) * 50) + '#'));
    elapsed.push(performance.now() - start);
  }
  metrics.medianLogPageMs = Math.round(elapsed.sort((left, right) => left - right)[3]);
}

try {
  await run();
  await fetch('/result', {
    method: 'POST',
    body: JSON.stringify({
      checks,
      metrics,
    }),
  });
}
catch (error) {
  await fetch('/result', {
    method: 'POST',
    body: JSON.stringify({
      error: error.stack,
      checks,
    }),
  });
}
