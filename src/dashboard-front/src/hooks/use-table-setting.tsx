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
import { useEnv } from '@/stores';

export function useTableSetting(
  settings: Ref<BkUiSettings>,
  useCache: boolean = false,
  cacheIdentifier?: string,
) {
  const { locale } = useI18n();
  const route = useRoute();
  const envStore = useEnv();
  const tableIdentifier = ref(cacheIdentifier || String(route.name));

  const needCache = computed(() => useCache && tableIdentifier.value);

  const localStorageKey = computed(() => {
    return `table-settings-${tableIdentifier.value}-${locale.value}-${envStore.env.BK_APIGATEWAY_VERSION}`;
  });

  const writeCache = () => {
    if (needCache.value) {
      localStorage.setItem(localStorageKey.value, JSON.stringify(settings.value));
    }
  };

  const readCache = () => {
    if (needCache.value) {
      const cache = localStorage.getItem(localStorageKey.value);
      if (cache && settings.value) {
        try {
          settings.value = { ...JSON.parse(cache) };
        }
        catch (e) {
          console.error(e);
        }
      }
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
    if (needCache.value && cacheId) {
      tableIdentifier.value = cacheId;
    }
    readCache();
  };

  onMounted(() => {
    nextTick(() => {
      updateCacheIdentifier();
    });
  });

  return {
    localStorageKey,
    changeTableSettings,
    isEqualSettings,
    updateCacheIdentifier,
  };
}
