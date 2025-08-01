/*
 * Tencent is pleased to support the open source community by making
 * 蓝鲸智云PaaS平台 (BlueKing PaaS) available.
 *
 * Copyright (C) 2021 THL A29 Limited, a Tencent company.  All rights reserved.
 *
 * 蓝鲸智云PaaS平台 (BlueKing PaaS) is licensed under the MIT License.
 *
 * License for 蓝鲸智云PaaS平台 (BlueKing PaaS):
 *
 * ---------------------------------------------------
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
 * documentation files (the "Software"), to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
 * to permit persons to whom the Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all copies or substantial portions of
 * the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
 * THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
 * CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
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
