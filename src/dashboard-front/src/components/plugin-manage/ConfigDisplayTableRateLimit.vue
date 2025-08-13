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

<template>
  <!--  插件配置展示态组件  -->
  <!--  频率控制插件  -->
  <CustomTable
    :columns="tableCols"
    :data="tableData"
  />
</template>

<script setup lang="ts">
import type {
  IBaseTableRow,
  IColumn,
  IPlugin,
} from '@/components/plugin-manage/types';
import CustomTable from './CustomTable.vue';

interface IRateLimitConfig {
  rates: {
    [key: string]: {
      period: number
      tokens: number
    }[]
  }
}

interface IRateLimitTableRow extends IBaseTableRow {
  type: string
  tokens: number
  period: string
  appId?: string
}

interface IProps {
  plugin: IPlugin<IRateLimitConfig>
  firstColWidth: string
}

const {
  plugin,
  firstColWidth,
} = defineProps<IProps>();

const { t } = useI18n();

const periodTextMap: Record<number, string> = {
  1: t('秒'),
  60: t('分'),
  3600: t('时'),
  86400: t('天'),
};

// 频率控制插件表格列
const tableCols = ref<IColumn[]>([
  {
    label: t('类别'),
    align: 'right',
    field: 'type',
    width: firstColWidth,
    index: 0,
    rowspan: ({ row }) => row.rowSpan || 1,
  },
  {
    label: t('次数'),
    field: 'tokens',
  },
  {
    label: t('时间范围'),
    field: 'period',
  },
  {
    label: t('蓝鲸应用ID'),
    field: 'appId',
  },
]);

// 频率控制插件表格数据
const tableData = computed(() => {
  const defaultData: IRateLimitTableRow[] = [];
  const specialData: IRateLimitTableRow[] = [];
  const { rates } = plugin.config;
  Object.entries(rates).forEach(([appId, rateConfig]) => {
    const { tokens, period } = rateConfig[0];
    if (appId === '__default') {
      defaultData.push({
        tokens,
        type: t('默认频率限制'),
        period: periodTextMap[period],
        appId: '--',
      });
    }
    else {
      specialData.push({
        appId,
        tokens,
        type: t('特殊频率限制'),
        period: periodTextMap[period],
      });
    }
  });
  if (specialData.length > 0) {
    specialData[0].rowSpan = specialData.length;
  }
  return [...defaultData, ...specialData];
});

</script>
