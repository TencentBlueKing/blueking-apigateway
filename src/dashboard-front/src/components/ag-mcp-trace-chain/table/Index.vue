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
    class="trace-chain-log-table"
    v-bind="$attrs"
  >
    <BkTab
      :key="tabKey"
      v-model:active="traceStore.logActiveTab"
      type="unborder-card"
      @change="handleTabChange"
    >
      <BkTabPanel
        v-for="tab of logPanels"
        :key="tab.name"
        :label="tab.label"
        :name="tab.name"
      >
        <AgTable
          v-model:table-data="tableData"
          resizable
          local-page
          :show-pagination="false"
          :columns="tableColumns"
        />
      </BkTabPanel>
    </BkTab>
  </div>
</template>

<script lang="tsx" setup>
import dayjs from 'dayjs';
import { t } from '@/locales';
import type { PrimaryTableProps } from '@blueking/tdesign-ui';
import type { ITraceDetail } from '@/services/source/observability';
import { useTrace } from '@/stores';
import AgTable from '@/components/ag-table/Index.vue';

interface IProps { traceChainDetail?: ITraceDetail }

const { traceChainDetail = {} as ITraceDetail } = defineProps<IProps>();

const traceStore = useTrace();

let tabKey: string | number = -1;
const logPanels = [
  {
    name: 'proxy_log',
    label: t('MCP Proxy 日志'),
  },
  {
    name: 'gateway_upstream',
    label: t('上游网关日志'),
  },
  {
    name: 'gateway_downstream',
    label: t('下游网关日志'),
  },
];

const tableData = computed(() => {
  if (['proxy_log'].includes(traceStore.logActiveTab)) {
    return traceChainDetail?.logList?.filter((item: any) => ['http', 'mcp'].includes(item.layer));
  }

  if (['gateway_upstream'].includes(traceStore.logActiveTab)) {
    return traceChainDetail?.logList?.filter((item: any) => ['gateway_upstream'].includes(item.layer));
  }

  if (['gateway_downstream'].includes(traceStore.logActiveTab)) {
    return traceChainDetail?.logList?.filter((item: any) => ['gateway_downstream'].includes(item.layer));
  }

  return traceChainDetail?.logList ?? [];
});

const tableColumns = shallowRef<PrimaryTableProps['columns']>([
  {
    title: t('时间'),
    colKey: 'timestamp',
    ellipsis: true,
    width: 240,
    cell: (_: any, { row }: { row?: any }) => {
      return row?.timestamp ? <span>{dayjs.unix(row?.timestamp).format('YYYY-MM-DD HH:mm:ss ZZ')}</span> : '--';
    },
  },
  {
    title: t('服务'),
    colKey: 'service',
    ellipsis: true,
    cell: (_: any, { row }: { row?: any }) => {
      return row?.service || '--';
    },
  },
  {
    title: 'request_id',
    colKey: 'request_id',
    ellipsis: true,
  },
  {
    title: t('方法'),
    colKey: 'method',
    ellipsis: true,
    cell: (_: any, { row }: { row?: any }) => {
      return row?.mcp_method || row?.method;
    },
  },
  {
    title: t('路径/操作'),
    colKey: 'path',
    ellipsis: true,
    width: 260,
    cell: (_: any, { row }: { row?: any }) => {
      return row?.http_path || row?.path || row?.operation;
    },
  },
  {
    title: t('状态码'),
    colKey: 'status',
    ellipsis: true,
    cell: (_: any, { row }: { row?: any }) => {
      return row?.status || '--';
    },
  },
  {
    title: t('耗时'),
    colKey: 'latency',
    ellipsis: true,
    cell: (_: any, { row }: { row?: any }) => {
      const duration = row?.latency || row?.request_duration;
      if (!duration) {
        return '--';
      }
      return String(duration).replace(/(\d+\.\d{2})\d*/, '$1');
    },
  },
]);

const handleTabChange = (tab: string) => {
  traceStore.setTraceLogTab(tab);
};

onMounted(() => {
  tabKey = traceChainDetail?.request_id;
});
</script>

<style lang="scss" scoped>
.trace-chain-log-table {
  background-color: #fff;
  border-radius: 2px;
  box-shadow: 0 2px 4px 0 #1919290d;
  box-sizing: border-box;

  :deep(.bk-tab) {

    .bk-tab-header {
      padding: 0 24px;
      line-height: 48px !important;

      &-item {
        padding: 0;
        margin-right: 32px;
        font-size: 14px;
      }
    }

    .bk-tab-content {
      padding: 16px;
    }
  }
}
</style>
