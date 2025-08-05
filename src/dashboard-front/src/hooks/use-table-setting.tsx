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

import { locale } from '@/locales';
import { cloneDeep, isEqual } from 'lodash-es';
import type { ShallowRef } from 'vue';
import { type Settings } from 'bkui-vue/lib/table/props';

export type ITableSettings = Settings;

export function useTableSetting(setting: ShallowRef<Settings>, name: string) {
  let tempName: string;
  if (!name) {
    const route = useRoute();
    tempName = route.name as string;
  }
  else {
    tempName = name;
  }

  const tableName = `table-setting-${locale.value}-${tempName}`;

  onMounted(() => {
    const cache = localStorage.getItem(tableName);
    if (cache) {
      try {
        setting.value = { ...JSON.parse(cache) };
      }
      catch (err) {
        console.error(err);
      }
    }
  });

  function changeTableSetting(value: Settings) {
    const curSetting = cloneDeep(setting.value);
    const latestSetting = cloneDeep(value);
    // 这里需要对比下数据是否一致，避免重复回调
    if (isEqual(curSetting, latestSetting)) {
      return;
    }
    setting.value = {
      ...curSetting,
      ...value,
    };
    localStorage.setItem(tableName, JSON.stringify(setting.value));
  }

  function isDiffSize(value: Settings) {
    return setting.value?.size !== value.size;
  }

  return {
    changeTableSetting,
    isDiffSize,
  };
}
