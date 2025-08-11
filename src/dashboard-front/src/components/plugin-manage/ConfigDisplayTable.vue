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
  <component
    :is="tableComponent"
    :plugin="plugin"
    :first-col-width="firstColWidth"
    :value-render="valueRender"
    :cell-style="getFirstColCellStyle"
    :border="['outer', 'col']"
    show-overflow-tooltip
  />
</template>

<script setup lang="ts">
import ConfigDisplayTableHeaderRewrite from './ConfigDisplayTableHeaderRewrite.vue';
import ConfigDisplayTableRateLimit from './ConfigDisplayTableRateLimit.vue';
import ConfigDisplayTableIpRestriction from './ConfigDisplayTableIpRestriction.vue';
import ConfigDisplayTableStatusRewrite from './ConfigDisplayTableStatusRewrite.vue';
import ConfigDisplayTableGeneric from './ConfigDisplayTableGeneric.vue';
import type {
  IBaseTableRow,
  IColumn,
  IPlugin,
  ValueRenderType,
} from './types';

interface IProps {
  plugin?: IPlugin<unknown>
  firstColWidth?: string
  valueRender?: ValueRenderType
}

const {
  plugin = {
    code: '',
    config_id: 0,
    name: '',
    config: {},
  },
  firstColWidth = '200',
  valueRender = ({ row }: { row: IBaseTableRow }) => {
    // 为需要展示为多行文本的内容设置独立的自定义渲染
    if (typeof row.value === 'string') {
      if (row.value.includes('\n')) {
        return h('pre', {
          class: 'multi-line-table-cell-pre',
          innerHTML: row.value,
        });
      }
      return row.value;
    }
    if (typeof row.value === 'boolean') {
      return row.value ? 'true' : 'false';
    }
    return JSON.stringify(row.value || {});
  },
} = defineProps<IProps>();

// Header转换插件、频率控制插件、IP访问限制插件、网关错误使用HTTP状态码200插件、强制要求调用方传递X-Bk-Username header 头插件配置展示表格
const tableComponentMap: { [key: string]: Component } = {
  'bk-header-rewrite': ConfigDisplayTableHeaderRewrite,
  'bk-rate-limit': ConfigDisplayTableRateLimit,
  'bk-ip-restriction': ConfigDisplayTableIpRestriction,
  'bk-status-rewrite': ConfigDisplayTableStatusRewrite,
  'bk-username-required': ConfigDisplayTableStatusRewrite,
};

// 根据 code 或 type 动态获取表格组件
const tableComponent = computed(() => {
  return tableComponentMap[plugin.code || plugin.type || ''] || ConfigDisplayTableGeneric;
});

// 给表格最左列一个背景色
const getFirstColCellStyle = (col: IColumn) => {
  return col.index === 0 ? { backgroundColor: '#fafbfd' } : {};
};

</script>
