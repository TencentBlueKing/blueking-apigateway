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

// TDesign表格设置隐藏列
import type { ITableSettings } from '@/types/common';
import type { BkUiSettings } from '@blueking/tdesign-ui';
import { isEqual } from 'lodash-es';
import { locale } from '@/locales';
import router from '@/router';
import { useEnv } from '@/stores';

// 表格设置缓存 key 的唯一构造入口：
// use-max-table-limit 依赖同一份缓存读取行高(rowSize)来计算表格可展示条数，
// 两侧必须使用完全一致的 key，否则读取侧永远取不到值，行高变化后条数不会跟着变
export const getTableSettingsCacheKey = (identifier: string) => {
  const { env } = useEnv();
  return `table-settings-${identifier}-${locale.value}-${env.BK_APIGATEWAY_VERSION}`;
};

// 首次导航 finalize 之前 currentRoute 仍是初始 location(name 为 undefined)，单独取 name 会得到 'undefined'
// 这里依次兜底 name -> 最深一级 matched 记录的 name -> fullPath，保证标识始终有意义
export const resolveTableCacheIdentifier = (cacheIdentifier?: string) => {
  if (cacheIdentifier) {
    return cacheIdentifier;
  }
  const { name, matched, fullPath } = router.currentRoute.value;
  return String(name ?? matched[matched.length - 1]?.name ?? fullPath);
};

export function useTableSetting(
  settings: Ref<BkUiSettings>,
  useCache: boolean = false,
  cacheIdentifier?: string,
) {
  const tableIdentifier = ref(resolveTableCacheIdentifier(cacheIdentifier));

  const needCache = computed(() => useCache && tableIdentifier.value);

  const localStorageKey = computed(() => getTableSettingsCacheKey(tableIdentifier.value));

  const writeCache = () => {
    if (needCache.value) {
      localStorage.setItem(localStorageKey.value, JSON.stringify(settings.value));
    }
  };

  const readCache = () => {
    if (!needCache.value) {
      return;
    }
    const cache = localStorage.getItem(localStorageKey.value);
    if (!cache || !settings.value) {
      return;
    }
    try {
      const cachedSettings = JSON.parse(cache) ?? {};
      const curSettings = settings.value;
      const mergedSettings: BkUiSettings = {
        ...curSettings,
        ...cachedSettings,
      };
      const currentChecked = Array.isArray(curSettings.checked) ? curSettings.checked : [];
      // 与当前列取交集，避免缓存中已被移除的列被回显（当前列未知时不做过滤）
      if (Array.isArray(cachedSettings.checked) && currentChecked.length) {
        mergedSettings.checked = cachedSettings.checked.filter((key: string) => currentChecked.includes(key));
      }
      settings.value = mergedSettings;
    }
    catch (e) {
      console.error(e);
    }
  };

  const isEqualSettings = (newSettings: ITableSettings | BkUiSettings | null, oldSettings: BkUiSettings) =>
    isEqual(
      (newSettings as ITableSettings).columns || (newSettings as BkUiSettings).checked,
      oldSettings.checked,
    )
    && newSettings?.fontSize === oldSettings.fontSize
    && newSettings?.rowSize === oldSettings.rowSize;

  const changeTableSettings = (curSettings: ITableSettings) => {
    if (isEqualSettings(curSettings, settings.value)) {
      return;
    }
    if (settings.value) {
      const { columns, fontSize, rowSize } = curSettings;
      settings.value.checked = columns;
      settings.value.fontSize = fontSize;
      settings.value.rowSize = rowSize;
      writeCache();
    }
  };

  const updateCacheIdentifier = (cacheId?: string | undefined) => {
    if (!needCache.value) {
      return;
    }
    // 挂载后路由已就绪，重新解析一次，修正 setup 阶段取到的兜底值
    const nextIdentifier = resolveTableCacheIdentifier(cacheId || cacheIdentifier);
    if (nextIdentifier !== tableIdentifier.value) {
      tableIdentifier.value = nextIdentifier;
    }
    // 即使标识符未变化也要读一次缓存：setup 阶段 env（版本号）、locale 等依赖可能尚未就绪，
    // 首次读取会因 localStorageKey 不正确而失败，需要在此刻用最终 key 重新读取
    readCache();
  };

  // localStorageKey 依赖 env 版本与语言，二者在应用启动阶段异步就绪；
  // key 变化时用最终 key 重新读取，否则刷新后设置（行高等）无法回显
  watch(localStorageKey, () => {
    readCache();
  });

  onMounted(() => {
    nextTick(() => {
      updateCacheIdentifier();
    });
  });

  return {
    localStorageKey,
    changeTableSettings,
    isEqualSettings,
    readCache,
    updateCacheIdentifier,
  };
}
