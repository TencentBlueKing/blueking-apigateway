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
  <div class="observability-flow-log">
    <BkCollapse v-model="activeCollapse">
      <BkCollapsePanel
        v-for="collapse of collapseList"
        :key="collapse.name"
        :name="collapse.name"
        class="collapse-panel"
      >
        <template #header>
          <div class="gap-8px collapse-panel-header">
            <AngleUpFill
              class="color-#4d4f56"
              :class="[
                {
                  'rotate--90deg': !activeCollapse?.includes(collapse.name)
                }
              ]"
            />
            <span class="text-14px font-bold color-#313238">
              {{ collapse.title }}
            </span>
            <template v-if="collapse.name.includes('Detail')">
              <span class="color-#4d4f56 text-12px">
                {{ t('共') }}
                <span class="font-bold">{{ pageCount }}</span>
                {{ t('条') }}
              </span>
              <div
                v-bk-tooltips="{
                  content: t('检索出的日志条数为 0，不需要下载'),
                  disabled: pageCount > 0
                }"
                class="color-#3a84ff text-12px"
                :class="[{ 'color-#c4c6cc cursor-not-allowed': isDisabledDownload }]"
                @click="handleDownload"
              >
                <AgIcon
                  v-show="!isDownloadLoading"
                  name="download"
                  size="14"
                />
                <Spinner
                  v-show="isDownloadLoading"
                  class="text-16px"
                />
                <span class="text-12px">{{ t('下载日志') }}</span>
              </div>
            </template>
          </div>
          <BkAlert
            v-if="collapse.name.includes('Detail') && pageCount > 9999"
            theme="warning"
            class="ml-46px mr-24px mb-20px"
            closable
            :title="t('每次查询操作最多只会返回 10,000 条记录。如果您未能查看全部需要的日志，请尝试缩小查询的时间范围')"
          />
        </template>
        <template #content>
          <Component
            :is="flowLogFormCompMap[collapse.name as keyof typeof flowLogFormCompMap]"
            :ref="(el: any) => setComponentRef(el, collapse.name)"
            v-model:page-count="pageCount"
            v-model:search-params="searchParams"
            v-model:include-query="includeQuery"
            v-model:exclude-query="excludeQuery"
            v-model:chart-empty-conf="chartEmptyConf"
            v-model:detail-empty-conf="detailEmptyConf"
            v-model:chart-loading="chartLoading"
            mode="FlowLog"
            :api-gateway-id="apigwId"
            @update-date="handleUpdateDateFromChart"
            @request="fetchFlowLog"
            @clear-filter="handleClearFilter"
            @refresh-request="getObservabilityLogChart"
          />
        </template>
      </BkCollapsePanel>
    </BkCollapse>
  </div>
</template>

<script lang="ts" setup>
import { Message } from 'bkui-vue';
import { AngleUpFill, Spinner } from 'bkui-vue/lib/icon';
import { t } from '@/locales';
import { useGateway } from '@/stores';
import { filterSimpleEmpty } from '@/utils/filterEmptyValues';
import { fetchExportFlowLog, fetchObservabilityLogChart } from '@/services/source/observability';
import ObservabilityBasicForm from '@/views/mcp-server/components/ObservabilityBasicForm.vue';
import FlowLogChart from '@/views/mcp-server/components/FlowLogChart.vue';
import FlowLogDetailTable from '@/views/mcp-server/components/FlowLogDetailTable.vue';

const flowLogFormCompMap = {
  Query: ObservabilityBasicForm,
  Request: FlowLogChart,
  Detail: FlowLogDetailTable,
};

const gatewayStore = useGateway();

const collapseList = shallowRef([
  {
    title: t('查询条件'),
    name: 'Query',
  },
  {
    title: t('请求数'),
    name: 'Request',
  },
  {
    title: t('日志详情'),
    name: 'Detail',
  },
]);
const activeCollapse = shallowRef(['Query', 'Request', 'Detail']);
// 查询条件参数
const searchParams = ref({
  time_start: '',
  time_end: '',
  app_code: '',
  request_id: '',
  status: 'all',
  query: '',
  mcp_server_name: '',
});
// 请求数空状态
const chartEmptyConf = ref({
  emptyType: '',
  isAbnormal: false,
});
// 日志详情空状态
const detailEmptyConf = ref({
  emptyType: '',
  isAbnormal: false,
});
const pageCount = ref(0);
const includeQuery = ref<string[]>([]);
const excludeQuery = ref<string[]>([]);
const isDownloadLoading = ref(false);
const chartLoading = ref(false);
const componentRefs = reactive(new Map());

const apigwId = computed(() => gatewayStore.apigwId);
const isDisabledDownload = computed(() => pageCount.value === 0 || isDownloadLoading.value);

// 获取查询条件参数
const getSearchParams = () => {
  const params = { ...filterSimpleEmpty(searchParams.value) };

  if (['all'].includes(params?.status)) {
    delete params.status;
  }

  const includeStr = includeQuery.value?.map((item: any) => `include=${item}`).join('&') || '';
  const excludeStr = excludeQuery.value?.map((item: any) => `exclude=${item}`).join('&') || '';

  const path = [includeStr, excludeStr].filter(Boolean).join('&');

  return {
    params,
    path,
  };
};

// 请求数图表接口
const getObservabilityLogChart = async () => {
  try {
    const chartInstance = componentRefs.get('Request');
    if (!chartInstance) {
      chartEmptyConf.value = {
        emptyType: 'searchEmpty',
        isAbnormal: false,
      };
      return;
    }

    chartLoading.value = true;
    const { params, path } = getSearchParams();

    chartEmptyConf.value.emptyType = 'searchEmpty';

    const res = await fetchObservabilityLogChart(apigwId.value, params as any, path);

    if (!res || res?.series?.length === 0) {
      chartEmptyConf.value = {
        emptyType: 'searchEmpty',
        isAbnormal: false,
      };
      chartInstance.renderChart({
        series: [],
        timeline: [],
      });
      return;
    }

    chartInstance?.setChartData(res ?? {
      series: [],
      timeline: [],
    });
  }
  catch {
    chartEmptyConf.value = {
      emptyType: 'error',
      isAbnormal: true,
    };
  }
  finally {
    chartLoading.value = false;
  }
};

// 日志详情列表接口
const getObservabilityLogList = async () => {
  const detailInstance = componentRefs.get('Detail');
  if (!detailInstance) return;

  // 初始空状态
  detailEmptyConf.value = {
    emptyType: 'searchEmpty',
    isAbnormal: false,
  };

  try {
    const { params, path } = getSearchParams();

    let pathParams = new URLSearchParams();
    if (path && typeof path === 'string' && path.trim() !== '') {
      pathParams = new URLSearchParams(path);
    }

    // 获取第一个参数
    const pathEntries = Array.from(pathParams.entries());
    const [pathKey, pathValue = ''] = pathEntries[0] || [];

    const requestParams = { ...params };
    if (pathKey) {
      requestParams[pathKey] = pathValue;
    }

    // 调用实例获取列表
    await detailInstance.getList(requestParams);
  }
  catch {
    // 异常空状态
    detailEmptyConf.value = {
      emptyType: 'error',
      isAbnormal: true,
    };
    pageCount.value = 0;
  }
};

// 同步更新请求数图表和日志详情列表接口
const fetchFlowLog = () => {
  Promise.allSettled([
    getObservabilityLogChart(),
    getObservabilityLogList(),
  ]);
};

// 设置流水日志所有动态组件实例
const setComponentRef = (el: HTMLElement | null, name: string) => {
  if (el) {
    componentRefs?.set(name, el);
  }
  else {
    componentRefs?.delete(name);
  }
};

// 接收图表组件的日期更新事件
const handleUpdateDateFromChart = (dateInfo: { dateValue: string[] }) => {
  const formInstance = componentRefs?.get('Query');
  formInstance?.syncDateFromChart(dateInfo);
};

// 下载 MCP日志
const handleDownload = async (e: MouseEvent) => {
  e?.stopPropagation();
  if (isDisabledDownload.value) return;

  try {
    isDownloadLoading.value = true;

    const { params, path } = getSearchParams();
    const queryParams = Object.assign(params, {
      ...params,
      offset: componentRefs.get('Detail')?.getPagination()?.current || 1,
      limit: 10000,
    });

    await fetchExportFlowLog(apigwId.value, queryParams as any, path);

    Message({
      message: t('导出成功'),
      theme: 'success',
    });
  }
  catch (err: any) {
    Message({
      message: err?.message || t('导出失败'),
      theme: 'error',
    });
  }
  finally {
    isDownloadLoading.value = false;
  }
};

const handleClearFilter = () => {
  includeQuery.value = [];
  excludeQuery.value = [];
  componentRefs?.get('Query')?.handleClearFilter();
  fetchFlowLog();
};

onMounted(() => {
  fetchFlowLog();
});

onBeforeUnmount(() => {
  componentRefs?.clear();
});
</script>

<style lang="scss" scoped>
.observability-flow-log {
  box-sizing: border-box;

  .collapse-panel {
    margin: 24px;
    background-color: #fff;
    box-sizing: border-box;

    &-header {
      display: flex;
      align-items: center;
      padding: 24px;
      cursor: pointer;

      .panel-title-icon {
        font-size: 12px;
        transition: .2s;
      }

      .pack-up {
        transform: rotate(-90deg);
      }
    }

    :deep(.bk-collapse-content) {
      padding: 0;
      padding-bottom: 24px;

      .bk-form-label {
        font-size: 12px;
      }
    }
  }
}
</style>
