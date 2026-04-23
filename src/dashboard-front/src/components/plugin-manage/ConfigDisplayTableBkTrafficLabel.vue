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
  <!--  流量染色插件  -->
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

interface ITrafficLabelConfig {
  rules: {
    match: (string | string[])[]
    actions: {
      set_headers: Record<string, string>
      weight: number
    }[]
  }[]
}

interface IProps {
  plugin: IPlugin<ITrafficLabelConfig>
  firstColWidth: string
}

const {
  plugin,
  firstColWidth,
} = defineProps<IProps>();

const { t } = useI18n();

// 流量染色插件表格列
const tableCols = ref<IColumn[]>([
  {
    label: t('键'),
    align: 'right',
    field: 'key',
    width: firstColWidth,
    index: 0,
    rowspan: ({ row }: any) => row.rowSpan || 0,
  },
  {
    label: t('值'),
    field: 'value',
  },
]);

// 流量染色插件表格数据
const tableData = computed(() => {
  let matchRows: IBaseTableRow[] = [];
  let actionRows: IBaseTableRow[] = [];
  const { rules } = plugin.config;
  if (rules[0]) {
    const { match, actions } = rules[0];
    matchRows = match.map((item: any) => ({
      key: 'match',
      value: item,
    }));

    if (matchRows[0]) {
      matchRows[0].rowSpan = match.length;
    }

    actionRows = actions.map((item: any) => ({
      key: 'action',
      value: item,
    }));

    if (actionRows[0]) {
      actionRows[0].rowSpan = actions.length;
    }
  }
  return [...matchRows, ...actionRows];
});

</script>
