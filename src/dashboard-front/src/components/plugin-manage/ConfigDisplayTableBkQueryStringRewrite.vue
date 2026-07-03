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

<template>
  <!--  插件配置展示态组件  -->
  <!--  bk-query-string-rewrite 插件  -->
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

interface IQueryStringRewriteConfig {
  add?: Record<string, string | number>
  set?: Record<string, string | number>
  remove?: string[]
}

interface IQueryStringRewriteTableRow extends IBaseTableRow { action: string }

interface IProps {
  plugin: IPlugin<IQueryStringRewriteConfig>
  firstColWidth: string
}

const {
  plugin,
  firstColWidth,
} = defineProps<IProps>();

const { t } = useI18n();

// header转换插件表格列
const tableCols = ref<IColumn[]>([
  {
    label: t('行为'),
    align: 'right',
    field: 'action',
    width: firstColWidth,
    index: 0,
    rowspan: ({ row }: any) => row.rowSpan || 1,
  },
  {
    label: t('键'),
    field: 'key',
  },
  {
    label: t('值'),
    field: 'value',
  },
]);

// 转换表格数据
const tableData = computed(() => {
  const addData: IQueryStringRewriteTableRow[] = [];
  const setterData: IQueryStringRewriteTableRow[] = [];
  const removerData: IQueryStringRewriteTableRow[] = [];
  const { config } = plugin;
  if (config.add) {
    Object.entries(config.add).forEach(([key, value]) => {
      addData.push({
        key,
        value,
        action: 'Add',
      });
    });
  }
  if (config.set) {
    Object.entries(config.set).forEach(([key, value]) => {
      setterData.push({
        key,
        value,
        action: 'Set',
      });
    });
  }
  if (config.remove) {
    config.remove.forEach((key) => {
      setterData.push({
        key,
        value: '--',
        action: 'Remove',
      });
    });
  }
  if (addData.length) {
    addData[0].rowSpan = addData.length;
  }
  if (setterData.length) {
    setterData[0].rowSpan = setterData.length;
  }
  if (removerData.length) {
    removerData[0].rowSpan = removerData.length;
  }
  return [...addData, ...setterData, ...removerData];
});

</script>
