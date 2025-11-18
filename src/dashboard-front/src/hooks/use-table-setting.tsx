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

// TDesign表格设置隐藏列
import type { ShallowRef } from 'vue';
import type { ITableSettings } from '@/types/common';
import { isEqual } from 'lodash-es';
import i18n from '@/locales';

export function useTableSetting(setting: ShallowRef<ITableSettings>, name?: string) {
  const lang = i18n.global.locale;
  let tempName: string;
  if (!name) {
    const route = useRoute();
    tempName = route.name as string;
  }
  else {
    tempName = name;
  }
  const tableName = `table-setting-${lang.value}-${tempName}`;

  onMounted(() => {
    const cache = localStorage.getItem(tableName);
    if (cache && setting) {
      try {
        setting.value = { ...JSON.parse(cache) };
      }
      catch (e) {
        console.error(e);
      }
    }
  });

  function changeTableSetting(curSetting: ITableSettings) {
    // 这里需要对比下数据是否一致，避免重复回调
    if (isEqual(curSetting, setting?.value)) {
      return;
    }
    if (setting) {
      setting.value = { ...curSetting };
      localStorage.setItem(tableName, JSON.stringify(setting.value));
    }
  }

  function isDiffSize(value: ITableSettings) {
    return setting?.value?.rowSize !== value.rowSize;
  }

  return {
    changeTableSetting,
    isDiffSize,
  };
}
