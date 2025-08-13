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
  <!--  IP访问限制控制插件  -->
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
  ValueRenderType,
} from '@/components/plugin-manage/types';
import CustomTable from './CustomTable.vue';

interface IIpRestrictionConfig {
  whitelist?: string
  blacklist?: string
}

interface IIpRestrictionTableRow extends IBaseTableRow { type: string }

interface IProps {
  plugin: IPlugin<IIpRestrictionConfig>
  firstColWidth: string
  valueRender: ValueRenderType
}

const {
  plugin,
  firstColWidth,
  valueRender,
} = defineProps<IProps>();

const { t } = useI18n();

const ipTypeTextMap: Record<string, string> = {
  whitelist: t('白名单'),
  blacklist: t('黑名单'),
};

// ip访问限制插件表格列
const tableCols = ref<IColumn[]>([
  {
    label: t('类型'),
    align: 'right',
    field: 'type',
    width: firstColWidth,
    index: 0,
    rowspan: ({ row }) => row.rowSpan || 1,
  },
  {
    label: 'IP',
    field: 'value',
    render: valueRender,
  },
]);

// ip访问限制插件表格数据
const tableData = computed(() => {
  const data: IIpRestrictionTableRow[] = [];
  const { config } = plugin;
  Object.entries(config).forEach(([type, ip]) => {
    data.push({
      type: ipTypeTextMap[type],
      value: ip,
    });
  });
  return data;
});

</script>

<style lang="scss" scoped>
:deep(.multi-line-table-cell-pre) {
  font: inherit;
  line-height: 1.4 !important;
  color: inherit;
}
</style>
