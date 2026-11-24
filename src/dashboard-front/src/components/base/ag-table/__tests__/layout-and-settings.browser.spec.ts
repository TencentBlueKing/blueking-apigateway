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

import { computed, h, nextTick, ref, shallowRef } from 'vue';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import AgTable from '@/components/base/ag-table/Index.vue';
import { pruneTablePreferences } from '@/components/base/ag-table/settings/table-preferences';
import {
  FIXTURE_ROWS,
  type IMountedFixture,
  cleanupFixtures,
  createDefaultColumns,
  findVisible,
  getExpectedDomMaxHeight,
  mountIsolated,
  waitUntil,
} from './helpers';

describe('AgTable 布局自适应、列设置与偏好缓存', () => {
  const fixtures: IMountedFixture[] = [];

  const track = (fixture: IMountedFixture) => {
    fixtures.push(fixture);
    return fixture;
  };

  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    try {
      cleanupFixtures(fixtures);
    }
    finally {
      localStorage.clear();
    }
  });

  it('初始化时读取并清洗缓存偏好、解析渲染函数列标题，并在父级置 null 与卸载时正确同步', async () => {
    localStorage.setItem('table-settings-fixture-remote', JSON.stringify({
      checked: ['name', 'status', 'optional', 'obsolete', 1],
      fontSize: 'large',
      rowSize: 'mini',
    }));

    const tableRef = shallowRef<any>(null);
    const data = ref<any[]>([]);
    const settings = ref<any>(null);
    const requests: any[] = [];

    const fixture = track(mountIsolated(() => h(AgTable, {
      'ref': tableRef,
      'tableData': data.value,
      'onUpdate:tableData': (value: any) => {
        data.value = value;
      },
      'settings': settings.value,
      'onUpdate:settings': (value: any) => {
        settings.value = value;
      },
      'apiMethod': async (params: any) => {
        requests.push({ ...params });
        return {
          count: FIXTURE_ROWS.length,
          results: FIXTURE_ROWS.slice(params.offset, params.offset + params.limit),
        };
      },
      'immediate': true,
      'showSettings': true,
      'columns': createDefaultColumns(),
      'uncheckedColumn': ['optional'],
      'cacheIdentifier': 'fixture-remote',
    })));

    await waitUntil(() => fixture.container.querySelector('tbody')?.textContent?.includes('First row'), fixture.errors);

    // 仅发一次请求，且使用自适应计算的默认 limit
    expect(requests).toHaveLength(1);
    expect(requests[0].offset).toBe(0);
    expect(requests[0].limit).toBe(tableRef.value.getPagination().pageSize);
    expect(requests[0].limit).toBeGreaterThan(10);

    // 废弃列与非法值已过滤，渲染函数标题取 displayTitle
    expect(settings.value.rowSize).toBe('mini');
    expect(settings.value.fontSize).toBe('large');
    expect(settings.value.checked).toEqual(['name', 'status', 'optional']);
    expect(settings.value.fields.find((col: any) => col.field === 'name')?.label).toBe('Name setting');

    // 父级重置 settings 为 null 后，应从缓存恢复行高
    settings.value = null;
    await nextTick();
    await waitUntil(() => settings.value?.rowSize === 'mini', fixture.errors);

    // 卸载后重置 settings 为 null
    fixture.unmount();
    await waitUntil(() => settings.value === null, fixture.errors);
    expect(fixture.errors).toEqual([]);
  });

  it('按缓存、父级设置、默认行高、旧版偏好与固定 maxHeight 精确计算首屏 pageSize', async () => {
    const cacheKey = 'table-settings-fixture-layout';
    const maxLimitConfig = {
      mode: 'tdesign',
      allocatedHeight: window.innerHeight - 680,
    };
    const sizeClass: Record<string, string> = {
      mini: 't-size-xs',
      medium: 't-size-m',
      large: 't-size-l',
    };

    const verifyLayout = async (props: Record<string, any>, expectedRowSize: string, expectedPageSize: number) => {
      let firstLimit: number | undefined;
      let appliedSettings = props.settings;
      const tableRef = shallowRef<any>(null);

      const fixture = mountIsolated(() => h(AgTable, {
        'ref': tableRef,
        'cacheIdentifier': 'fixture-layout',
        'columns': [{
          colKey: 'name',
          title: 'Name',
        }],
        'tableData': FIXTURE_ROWS,
        'showSettings': true,
        maxLimitConfig,
        'apiMethod': async ({ limit }: { limit: number }) => {
          firstLimit ??= limit;
          return {
            count: FIXTURE_ROWS.length,
            results: FIXTURE_ROWS,
          };
        },
        'onUpdate:settings': (value: any) => {
          appliedSettings = value;
        },
        ...props,
      }));

      let snapshotSettings: any;
      try {
        await waitUntil(() =>
          appliedSettings?.rowSize === expectedRowSize
          && fixture.container.querySelector('.t-table')?.classList.contains(sizeClass[expectedRowSize])
          && firstLimit === expectedPageSize
          && tableRef.value?.getPagination().pageSize === expectedPageSize, fixture.errors);
        snapshotSettings = appliedSettings;
      }
      finally {
        fixture.unmount();
      }
      expect(fixture.errors).toEqual([]);
      return snapshotSettings;
    };

    // 680px 可用高度预留 64px 分页器后，可容纳 18 行 mini、13 行 medium 或 10 行 large
    localStorage.setItem(cacheKey, JSON.stringify({ rowSize: 'mini' }));
    await verifyLayout({ cacheSettingsInLocalStorage: false }, 'medium', 13);
    await verifyLayout({ settings: { rowSize: 'large' } }, 'mini', 18);
    await verifyLayout({ autoHeight: false }, 'mini', 10);
    await verifyLayout({ maxHeight: 'none' }, 'mini', 10);
    await verifyLayout({
      autoHeight: false,
      maxHeight: 378,
    }, 'mini', 10);
    await verifyLayout({
      maxLimitConfig: null,
      maxHeight: 378,
      cacheSettingsInLocalStorage: false,
    }, 'medium', 8);

    localStorage.removeItem(cacheKey);
    await verifyLayout({ settings: { rowSize: 'large' } }, 'large', 10);
    await verifyLayout({ defaultRowSize: 'mini' }, 'mini', 18);
    await verifyLayout({
      settings: { checked: ['name'] },
      maxLimitConfig: {
        ...maxLimitConfig,
        defaultRowSize: 'large',
      },
    }, 'large', 10);

    // 兼容旧版 size 字段与旧版 className 存储键（只读取行高，不覆盖列选择）
    localStorage.setItem(cacheKey, JSON.stringify({ size: 'mini' }));
    await verifyLayout({}, 'mini', 18);
    localStorage.removeItem(cacheKey);

    const legacyKey = 'table-settings-old-layout';
    localStorage.setItem(legacyKey, JSON.stringify({
      size: 'mini',
      checked: ['status'],
    }));
    const legacySettings = await verifyLayout({
      maxLimitConfig: {
        ...maxLimitConfig,
        className: 'old-layout',
      },
    }, 'mini', 18);
    expect(legacySettings.checked).toContain('name');
  });

  it('支持固定 maxHeight 反推 small 行高条数、真实 DOM 高度动态更新、手动 fetchData 及隐藏显露补测', async () => {
    // 1. 固定 maxHeight=378 + small（表头 36 + 行高 36）-> floor((378 - 36) / 36) = 9
    const subtableRef = shallowRef<any>(null);
    const subtable = track(mountIsolated(() => h(AgTable, {
      ref: subtableRef,
      tableData: FIXTURE_ROWS,
      localPage: true,
      size: 'small',
      maxHeight: 378,
      columns: [{
        colKey: 'name',
        title: 'Name',
      }],
    })));
    await waitUntil(() =>
      subtableRef.value?.getPagination().pageSize === 9
      && subtable.container.querySelector<HTMLElement>('.t-table__content')?.style.maxHeight === '378px', subtable.errors);
    subtable.unmount();

    // 2. 默认 autoHeight 测量真实 DOM top；上方占位增高时更新 maxHeight，不重置 pageSize 也不重发请求
    const spacerHeight = ref(200);
    const domRequests: any[] = [];
    const domTableRef = shallowRef<any>(null);
    const domFixture = track(mountIsolated(() => h('div', [
      h('div', { style: { height: `${spacerHeight.value}px` } }),
      h('div', [
        h(AgTable, {
          ref: domTableRef,
          columns: [{
            colKey: 'name',
            title: 'Name',
          }],
          apiMethod: async (query: any) => {
            domRequests.push(query);
            return {
              count: FIXTURE_ROWS.length,
              results: FIXTURE_ROWS,
            };
          },
        }),
      ]),
    ])));

    await waitUntil(() => {
      const contentEl = domFixture.container.querySelector<HTMLElement>('.t-table__content');
      if (!contentEl || domRequests.length !== 1) {
        return false;
      }
      const expectedHeight = getExpectedDomMaxHeight(domFixture.container);
      const expectedLimit = Math.max(1, Math.floor((expectedHeight - 42) / 42));
      return contentEl.style.maxHeight === `${expectedHeight}px`
        && domRequests[0].limit === expectedLimit
        && domTableRef.value?.getPagination().pageSize === expectedLimit;
    }, domFixture.errors);

    const initialLimit = domRequests[0].limit;
    spacerHeight.value = 320;
    await waitUntil(() => {
      const contentEl = domFixture.container.querySelector<HTMLElement>('.t-table__content');
      const expectedHeight = getExpectedDomMaxHeight(domFixture.container);
      return contentEl?.style.maxHeight === `${expectedHeight}px`
        && domTableRef.value?.getPagination().pageSize === initialLimit
        && domRequests.length === 1;
    }, domFixture.errors);
    domFixture.unmount();

    // 3. immediate=false 时手动 fetchData 先同步实测 DOM limit 再发请求
    const manualRequests: any[] = [];
    const manualTableRef = shallowRef<any>(null);
    const manualFixture = track(mountIsolated(() => h('div', [
      h('div', { style: { height: '240px' } }),
      h(AgTable, {
        ref: manualTableRef,
        immediate: false,
        columns: [{
          colKey: 'name',
          title: 'Name',
        }],
        apiMethod: async (query: any) => {
          manualRequests.push(query);
          return {
            count: FIXTURE_ROWS.length,
            results: FIXTURE_ROWS,
          };
        },
      }),
    ])));
    manualTableRef.value.fetchData({ keyword: 'test' });
    await waitUntil(() => {
      if (manualRequests.length !== 1) {
        return false;
      }
      const expectedHeight = getExpectedDomMaxHeight(manualFixture.container);
      const expectedLimit = Math.max(1, Math.floor((expectedHeight - 42) / 42));
      return manualRequests[0].limit === expectedLimit && manualRequests[0].keyword === 'test';
    }, manualFixture.errors);
    manualFixture.unmount();

    // 4. 隐藏容器挂载的本地表在显露后补测真实 DOM 高度与 pageSize
    const showHiddenWrapper = ref(false);
    const hiddenTableRef = shallowRef<any>(null);
    const hiddenFixture = track(mountIsolated(() => h('div', {
      style: { display: showHiddenWrapper.value ? 'block' : 'none' },
    }, [
      h('div', { style: { height: '260px' } }),
      h(AgTable, {
        ref: hiddenTableRef,
        tableData: FIXTURE_ROWS,
        localPage: true,
        columns: [{
          colKey: 'name',
          title: 'Name',
        }],
      }),
    ])));
    showHiddenWrapper.value = true;
    await waitUntil(() => {
      const tableEl = hiddenFixture.container.querySelector<HTMLElement>('.t-table');
      const contentEl = hiddenFixture.container.querySelector<HTMLElement>('.t-table__content');
      if (!tableEl || !contentEl || tableEl.getBoundingClientRect().top < 200) {
        return false;
      }
      const expectedHeight = getExpectedDomMaxHeight(hiddenFixture.container);
      const expectedLimit = Math.max(1, Math.floor((expectedHeight - 42) / 42));
      return contentEl.style.maxHeight === `${expectedHeight}px`
        && hiddenTableRef.value?.getPagination().pageSize === expectedLimit;
    }, hiddenFixture.errors);
  });

  it('列设置面板支持外观切换、动态列、多表身份切换、损坏缓存回退与自定义 fields', async () => {
    localStorage.setItem('table-settings-fixture-remote', JSON.stringify({
      checked: ['name', 'status', 'optional'],
      fontSize: 'large',
      rowSize: 'mini',
    }));

    const baseColumns = createDefaultColumns();
    const extraColumn = ref(false);
    const cacheIdentifier = ref('');
    const settings = ref<any>(null);
    const requests: any[] = [];
    const tableRef = shallowRef<any>(null);
    const tableColumns = computed(() => (extraColumn.value
      ? [
        ...baseColumns,
        {
          colKey: 'extra',
          title: 'Extra',
        },
      ]
      : baseColumns));

    const fixture = track(mountIsolated(() => h(AgTable, {
      'ref': tableRef,
      'settings': settings.value,
      'onUpdate:settings': (value: any) => {
        settings.value = value;
      },
      'apiMethod': async (params: any) => {
        requests.push({ ...params });
        return {
          count: FIXTURE_ROWS.length,
          results: FIXTURE_ROWS,
        };
      },
      'immediate': true,
      'showSettings': true,
      'columns': tableColumns.value,
      'uncheckedColumn': ['optional'],
      'cacheIdentifier': cacheIdentifier.value || 'fixture-remote',
    })));

    await waitUntil(() => fixture.container.querySelector('tbody')?.textContent?.includes('First row'), fixture.errors);
    const { pageSize } = tableRef.value.getPagination();
    const requestCount = requests.length;

    // 打开列设置 -> 外观面板 -> 修改行高为 small
    fixture.container.querySelector<HTMLElement>('th[data-colkey="__col_setting__"]')!.click();
    await waitUntil(() => findVisible('.bkui-col-settings'), fixture.errors);
    findVisible('.bkui-col-settings')!.querySelectorAll<HTMLElement>('.settings-header > *')[1].click();
    await waitUntil(() =>
      findVisible('.appearance-settings')?.querySelector<HTMLInputElement>('input[value=mini]')?.checked, fixture.errors);
    findVisible('.appearance-settings')!.querySelector<HTMLInputElement>('input[value=small]')!.closest('label')!.click();
    await waitUntil(() =>
      findVisible('.appearance-settings')?.querySelector<HTMLInputElement>('input[value=small]')?.checked, fixture.errors);
    fixture.container.querySelector<HTMLElement>('th[data-colkey="__col_setting__"]')!.click();

    await waitUntil(() => settings.value.rowSize === 'small', fixture.errors);
    expect(tableRef.value.getPagination().pageSize).toBe(pageSize);
    expect(requests).toHaveLength(requestCount);
    expect(Object.keys(JSON.parse(localStorage.getItem('table-settings-fixture-remote')!)).sort())
      .toEqual(['checked', 'fontSize', 'rowSize']);

    // 动态新增列同步至 settings.fields
    extraColumn.value = true;
    await waitUntil(() => settings.value.fields.some((col: any) => col.field === 'extra'), fixture.errors);

    // 切换 cacheIdentifier 读取另一张表独立偏好并可切回恢复
    localStorage.setItem('table-settings-another-table', JSON.stringify({
      checked: ['status'],
      rowSize: 'large',
    }));
    cacheIdentifier.value = 'another-table';
    await waitUntil(() =>
      settings.value.rowSize === 'large'
      && settings.value.checked.join() === 'status'
      && fixture.container.querySelector('.t-table')?.classList.contains('t-size-l'), fixture.errors);

    cacheIdentifier.value = '';
    extraColumn.value = false;
    await waitUntil(() =>
      settings.value.rowSize === 'small'
      && fixture.container.querySelector('.t-table')?.classList.contains('t-size-s'), fixture.errors);

    // 损坏 JSON 缓存回退默认配置
    localStorage.setItem('table-settings-damaged', '{incomplete');
    cacheIdentifier.value = 'damaged';
    await waitUntil(() =>
      settings.value.rowSize === 'medium'
      && settings.value.checked.includes('name')
      && !settings.value.checked.includes('obsolete'), fixture.errors);

    // 调用方自定义 fields 生效，置 null 后恢复默认列
    settings.value = {
      fields: [{
        field: 'status',
        label: 'Custom status label',
      }],
      checked: ['status'],
      rowSize: 'large',
    };
    await waitUntil(() =>
      fixture.container.querySelector('tbody')?.textContent?.includes('on')
      && !fixture.container.querySelector('thead th[data-colkey="name"]'), fixture.errors);

    settings.value = null;
    await waitUntil(() =>
      settings.value?.rowSize === 'medium'
      && Boolean(fixture.container.querySelector('thead th[data-colkey="name"]')), fixture.errors);
  });

  it('覆盖 showSettings=false、无 cacheIdentifier 内存模式、禁缓存置 null 与自定义 settings 卸载还原', async () => {
    const columns = createDefaultColumns();

    // 1. showSettings=false 不渲染齿轮、不读缓存且保留 size="small"
    localStorage.setItem('table-settings-explicit-id', JSON.stringify({
      checked: ['name'],
      rowSize: 'large',
    }));
    const noSettings = track(mountIsolated(() => h(AgTable, {
      tableData: FIXTURE_ROWS,
      localPage: true,
      showSettings: false,
      cacheIdentifier: 'explicit-id',
      size: 'small',
      columns,
    })));
    await waitUntil(() =>
      !noSettings.container.querySelector('th[data-colkey="__col_setting__"]')
      && Boolean(noSettings.container.querySelector('thead th[data-colkey="status"]'))
      && noSettings.container.querySelector('.t-table')?.classList.contains('t-size-s'), noSettings.errors);
    noSettings.unmount();

    // 2. 开启 showSettings 但不传 cacheIdentifier：仅内存生效不碰 localStorage，且 noticeHeight 上下文生效
    const keysBefore = Object.keys(localStorage).sort();
    const ephemeralSettings = ref<any>(null);
    const ephemeralTableRef = shallowRef<any>(null);
    const ephemeral = track(mountIsolated(() => h(AgTable, {
      'ref': ephemeralTableRef,
      'tableData': FIXTURE_ROWS,
      'localPage': true,
      'showSettings': true,
      'maxLimitConfig': {
        mode: 'tdesign',
        allocatedHeight: window.innerHeight - 680,
      },
      'settings': ephemeralSettings.value,
      'onUpdate:settings': (val: any) => {
        ephemeralSettings.value = val;
      },
      columns,
    }), {
      // 680 - 40 = 640 可用高度，减去 64 分页与 42 表头后为 534，medium 42px 行高对应 12 条
      getNoticeHeight: () => 40,
    }));
    await waitUntil(() => ephemeralTableRef.value?.getPagination().pageSize === 12, ephemeral.errors);
    ephemeral.container.querySelector<HTMLElement>('th[data-colkey="__col_setting__"]')!.click();
    await waitUntil(() => findVisible('.bkui-col-settings'), ephemeral.errors);
    findVisible('.bkui-col-settings')!.querySelectorAll<HTMLElement>('.settings-header > *')[1].click();
    await waitUntil(() => findVisible('.appearance-settings'), ephemeral.errors);
    findVisible('.appearance-settings')!.querySelector<HTMLInputElement>('input[value=small]')!.closest('label')!.click();
    ephemeral.container.querySelector<HTMLElement>('th[data-colkey="__col_setting__"]')!.click();
    await waitUntil(() =>
      ephemeralSettings.value?.rowSize === 'small'
      && Object.keys(localStorage).sort().join() === keysBefore.join(), ephemeral.errors);
    ephemeral.unmount();

    // 3. cacheSettingsInLocalStorage=false 下置 null 保留内存编辑
    const memSettings = ref<any>(null);
    const memFixture = track(mountIsolated(() => h(AgTable, {
      'tableData': FIXTURE_ROWS,
      'localPage': true,
      'showSettings': true,
      'cacheSettingsInLocalStorage': false,
      'cacheIdentifier': 'no-cache-table',
      'settings': memSettings.value,
      'onUpdate:settings': (val: any) => {
        memSettings.value = val;
      },
      columns,
    })));
    await waitUntil(() => memSettings.value?.rowSize === 'medium', memFixture.errors);
    memFixture.container.querySelector<HTMLElement>('th[data-colkey="__col_setting__"]')!.click();
    await waitUntil(() => findVisible('.bkui-col-settings'), memFixture.errors);
    findVisible('.bkui-col-settings')!.querySelectorAll<HTMLElement>('.settings-header > *')[1].click();
    await waitUntil(() => findVisible('.appearance-settings'), memFixture.errors);
    findVisible('.appearance-settings')!.querySelector<HTMLInputElement>('input[value=small]')!.closest('label')!.click();
    memFixture.container.querySelector<HTMLElement>('th[data-colkey="__col_setting__"]')!.click();
    await waitUntil(() => memSettings.value?.rowSize === 'small', memFixture.errors);
    memSettings.value = null;
    await nextTick();
    await waitUntil(() => memSettings.value?.rowSize === 'small', memFixture.errors);
    memFixture.unmount();

    // 4. 调用方传入自定义 settings 对象时，卸载后还原为原对象引用
    const originalCustomSettings = {
      fields: [{
        field: 'name',
        label: 'Custom Name',
      }],
      checked: ['name'],
    };
    const customSettings = shallowRef<any>(originalCustomSettings);
    const customFixture = track(mountIsolated(() => h(AgTable, {
      'tableData': FIXTURE_ROWS,
      'localPage': true,
      'showSettings': true,
      'cacheIdentifier': 'custom-settings-table',
      'settings': customSettings.value,
      'onUpdate:settings': (val: any) => {
        customSettings.value = val;
      },
      columns,
    })));
    await waitUntil(() => customSettings.value?.rowSize === 'medium', customFixture.errors);
    customFixture.unmount();
    await waitUntil(() => customSettings.value === originalCustomSettings, customFixture.errors);
  });

  it('pruneTablePreferences 在跨构建启动时清理旧偏好键、保留无关存储且同构建内幂等', () => {
    localStorage.setItem('table-settings-AuditLog', JSON.stringify({ rowSize: 'large' }));
    localStorage.setItem('table-settings-AuditLog-zh-cn-1.24.0', JSON.stringify({ rowSize: 'small' }));
    localStorage.setItem('table-setting-zh-cn-LegacyPage', JSON.stringify({ size: 'small' }));
    localStorage.setItem('other-app-key', 'keep-me');

    expect(pruneTablePreferences('build-v1')).toBe(true);
    expect(localStorage.getItem('table-settings-AuditLog')).toBeNull();
    expect(localStorage.getItem('table-settings-AuditLog-zh-cn-1.24.0')).toBeNull();
    expect(localStorage.getItem('table-setting-zh-cn-LegacyPage')).toBeNull();
    expect(localStorage.getItem('other-app-key')).toBe('keep-me');
    expect(localStorage.getItem('table-settings:__build_id__')).toBe('build-v1');

    localStorage.setItem('table-settings-AuditLog', JSON.stringify({ rowSize: 'mini' }));
    expect(pruneTablePreferences('build-v1')).toBe(false);
    expect(JSON.parse(localStorage.getItem('table-settings-AuditLog')!).rowSize).toBe('mini');

    expect(pruneTablePreferences('build-v2')).toBe(true);
    expect(localStorage.getItem('table-settings-AuditLog')).toBeNull();
    expect(localStorage.getItem('other-app-key')).toBe('keep-me');
    expect(localStorage.getItem('table-settings:__build_id__')).toBe('build-v2');
  });
});
