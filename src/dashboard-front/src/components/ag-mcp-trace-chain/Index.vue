/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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
  <div
    class="ag-mcp-trace-chain"
    v-bind="$attrs"
  >
    <!-- 基本信息 -->
    <AgMcpTraceChainInfo
      :trace-chain-detail="traceChainDetail"
      class="ag-trace-chain-info"
    />
    <!-- trace链路瀑布图 -->
    <AgMcpTraceChainChart
      class="ag-trace-chain-chart"
      :trace-chain-detail="traceChainDetail"
    />
    <!-- trace日志表格 -->
    <AgMcpTraceChainTable
      :trace-chain-detail="traceChainDetail"
      class="ag-trace-chain-table"
    />
  </div>
</template>

<script lang="ts" setup>
import type { ITraceDetail } from '@/services/source/observability';
import AgMcpTraceChainInfo from '@/components/ag-mcp-trace-chain/info/Index.vue';
import AgMcpTraceChainChart from '@/components/trace-view';
import AgMcpTraceChainTable from '@/components/ag-mcp-trace-chain/table/Index.vue';

interface IProps { traceChainDetail?: ITraceDetail }

const { traceChainDetail = {} } = defineProps<IProps>();

</script>

<style lang="scss" scoped>
.ag-trace-chain-info {
  padding: 12px 24px;
}

.ag-trace-chain-chart {
  margin: 24px;
  background-color: #ffffff;
  box-sizing: border-box;
}

.ag-trace-chain-table {
  margin: 24px;
}
</style>
