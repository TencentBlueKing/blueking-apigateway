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
  <!--  header 转换插件  -->
  <BkTable
    :data="tableData"
    :columns="tableCols"
    v-bind="$attrs"
  />
</template>

<script setup lang="ts">
import type {
  IBaseTableRow,
  IColumn,
  IPlugin,
} from '@/components/plugin-manage/types';

interface IHeaderRewriteConfig {
  set?: {
    key: string
    value: string
  }[]
  remove?: {
    key: string
    value?: string
  }[]
}

interface IHeaderRewriteTableRow extends IBaseTableRow { action: string }

interface IProps {
  plugin: IPlugin<IHeaderRewriteConfig>
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
    rowspan: ({ row }) => row.rowSpan || 1,
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

// header转换插件表格数据
const tableData = computed(() => {
  const setterData: IHeaderRewriteTableRow[] = [];
  const removerData: IHeaderRewriteTableRow[] = [];
  const { config } = plugin;
  Object.entries(config).forEach(([action, keyValues]: [string, Array<{
    key: string
    value?: string
  }>]) => {
    if (action === 'set') {
      keyValues.forEach(({ key, value }) => {
        setterData.push({
          key,
          value,
          action: t('设置'),
        });
      });
    }
    else if (action === 'remove') {
      keyValues.forEach(({ key }) => {
        removerData.push({
          key,
          value: '--',
          action: t('删除'),
        });
      });
    }
  });
  if (setterData.length > 0) {
    setterData[0].rowSpan = setterData.length;
  }
  if (removerData.length > 0) {
    removerData[0].rowSpan = removerData.length;
  }
  return [...setterData, ...removerData];
});

</script>
