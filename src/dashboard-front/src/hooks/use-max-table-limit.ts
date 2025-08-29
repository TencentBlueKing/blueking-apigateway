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
import { toValue } from 'vue';
import { useWindowSize } from '@vueuse/core';
import { locale } from '@/locales';
import { useFeatureFlag } from '@/stores';
import type { ReturnRecordType } from '@/types/common';

type ITableLimit = {
  allocatedHeight: number
  customLineHeight: number
  className: string
  hasPagination: boolean
};

/**
 * @description 根据表格设置大小获取表格行高
 * @param {String} className  获取缓存中每个table单独的class
 * @returns lineH行高  topHead 表头高度
 */
function getTableSizeLineHeight(className: string, mode = 'bkui'): Record<string, number> {
  const curSetting = localStorage.getItem(`table-setting-${locale.value}-${className}`);
  const tableSize = curSetting ? JSON.parse(curSetting)?.size : 'mini';
  // 后续其他表格也可以适配，默认先以bkui-vue表格为例
  const sizeMap: ReturnRecordType<string, Record<string, number>> = {
    mini: () => {
      if (['bkui'].includes(mode)) {
        return {
          lineH: 42,
          topHead: 42,
        };
      }
      return {
        lineH: 36,
        topHead: 42,
      };
    },
    small: () => {
      if (['bkui'].includes(mode)) {
        return {
          lineH: 42,
          topHead: 42,
        };
      }
      return {
        lineH: 42,
        topHead: 42,
      };
    },
    medium: () => {
      if (['bkui'].includes(mode)) {
        return {
          lineH: 60,
          topHead: 42,
        };
      }
      return {
        lineH: 44,
        topHead: 47,
      };
    },
    large: () => {
      if (['bkui'].includes(mode)) {
        return {
          lineH: 78,
          topHead: 42,
        };
      }
      return {
        lineH: 44,
        topHead: 47,
      };
    },
  };
  return sizeMap[tableSize || 'mini']?.();
}

/**
 * @description 获取表格最大显示行数
 * @param {ITableLimit} payload
 * allocatedHeight 已占用不能用来展示表格行的高度
 * customLineHeight 自定义行高，覆盖默认表格设置行高
 * hasPagination 表格是否有分页
 * className 获取缓存中每个table唯一标识的class，处理表格设置大小
 * @returns maxTableLimit → 最大展示条数   clientHeight → 剩余可视化最大高度
 */
export function useMaxTableLimit(payload?: Partial<ITableLimit>) {
  const route = useRoute();
  const featureFlagStore = useFeatureFlag();
  const viewportHeight = toValue(useWindowSize().height);
  // 默认已占位高度
  const hasAllocatedHeight = payload?.allocatedHeight ?? 186;
  // 默认分页器高度
  const paginationH = payload?.hasPagination || typeof payload?.hasPagination === 'undefined' ? 60 : 0;
  // 通知栏高度
  const noticeComH = featureFlagStore.isEnabledNotice ? 40 : 0;
  // 获取表格的最大可视化区域
  const clientHeight = viewportHeight - hasAllocatedHeight - noticeComH;
  const name = payload?.className ?? route.name;
  // topHead是指vxe-table根据不同表格大小动态设置了距离表头top
  const { lineH, topHead } = getTableSizeLineHeight(name as string);
  // 优先获取自定义传入行高，默认设置不同大小表格的固定行高
  const rowHeight = payload?.customLineHeight ?? lineH;
  // 为了防止body区域出现滚动条，需要减去表头和分页器的高度
  const maxTableLimit = Math.max(Math.floor((clientHeight - paginationH - topHead) / rowHeight), 1);

  return {
    maxTableLimit,
    clientHeight,
  };
}
