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
  <!--  通用的展示表格  -->
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
  ValueRenderType,
} from '@/components/plugin-manage/types';

interface IGenericConfig { [key: string]: unknown }

interface IProps {
  plugin: IPlugin<IGenericConfig>
  firstColWidth: string
  valueRender: ValueRenderType
}

const {
  plugin,
  firstColWidth,
  valueRender,
} = defineProps<IProps>();

const { t } = useI18n();

// 键名对应文本
const rowKeyTextMap: Record<string, string> = {
  // 熔断插件
  break_response_body: t('熔断响应体'),
  break_response_code: t('熔断响应状态码'),
  break_response_headers: t('熔断响应头'),
  healthy: t('健康状态'),
  max_breaker_sec: t('最大熔断时间'),
  unhealthy: t('不健康状态'),
  http_statuses: t('状态码'),
  successes: t('健康次数'),
  failures: t('不健康次数'),
  // mocking 插件
  response_status: t('响应状态码'),
  response_example: t('响应体'),
  response_headers: t('响应头'),
};

// 通用表格列
const tableCols = ref<IColumn[]>([
  {
    label: t('键'),
    align: 'right',
    field: 'key',
    width: firstColWidth,
    index: 0,
    rowspan: ({ row }) => row.rowSpan || 1,
  },
  {
    label: t('值'),
    field: 'value',
    render: valueRender,
  },
]);

// 通用表格数据
const tableData = computed(() => {
  const data: IBaseTableRow[] = [];
  const { config } = plugin;
  Object.entries(config).forEach(([key, value]) => {
    key = rowKeyTextMap[key] || key;
    if (!Array.isArray(value)) {
      data.push({
        key,
        value,
        rowSpan: 1,
      });
    }
    else {
      value.forEach((subValue, index) => {
        data.push({
          key,
          value: subValue,
          rowSpan: index === 0 ? value.length : 0,
        });
      });
    }
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
