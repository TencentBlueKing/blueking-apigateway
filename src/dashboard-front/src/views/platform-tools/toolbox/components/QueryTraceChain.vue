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
  <div class="query-trace-chain">
    <!-- 查询输入区域 -->
    <div class="flex items-center justify-center mb-24px">
      <BkInput
        v-model.trim="searchKeyword"
        class="w-640px mr-8px"
        clearable
        :placeholder="t('请输入 request_id 或 x_request_id 进行查询')"
        @enter="handleQueryTrace"
        @clear="handleReset"
      />

      <BkButton
        theme="primary"
        :loading="queryLoading"
        @click="handleQueryTrace"
      >
        {{ t('查询') }}
      </BkButton>
    </div>

    <!-- 内容展示区域 -->
    <div class="query-trace-chain-body">
      <!-- 查询结果标题 -->
      <div
        v-show="!isEmptyResult"
        class="body-header"
      >
        <span class="color-#4d4f56 font-bold">{{ t('查询结果') }}</span>
      </div>
      <BkLoading
        :loading="queryLoading"
        color="#ffffff"
      >
        <!-- 空状态 -->
        <div
          v-if="isEmptyResult"
          class="pt-126px"
        >
          <TableEmpty
            :empty-type="emptyConfig.emptyType"
            :abnormal="emptyConfig.isAbnormal"
            :description="t('请输入 request_id 或 x_request_id 进行查询')"
            @refresh="handleQueryTrace"
            @clear-filter="handleReset"
          />
        </div>

        <!-- 追踪链详情 -->
        <div
          v-else
          class="body-content"
        >
          <AgMcpTraceChain
            v-model:active-tab="activeTab"
            :trace-chain-detail="traceData"
          />
        </div>
      </BkLoading>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { cloneDeep } from 'lodash-es';
import { Message } from 'bkui-vue';
import { useTrace } from '@/stores';
import { t } from '@/locales';
import {
  type ITraceDetail,
  fetchObservabilityLogInfo,
  fetchObservabilityLogSummary,
  fetchObservabilityTraceChain,
} from '@/services/source/observability';
import { DEFAULT_TRACE_DATA } from '@/components/trace-view/constants/trace';
import AgMcpTraceChain from '@/components/ag-mcp-trace-chain/Index.vue';
import TableEmpty from '@/components/table-empty/Index.vue';

const route = useRoute();
const traceStore = useTrace();

const searchKeyword = ref('');
const activeTab = ref('proxy_log');
const traceData = ref<ITraceDetail>(cloneDeep(DEFAULT_TRACE_DATA));

// 空状态配置
const emptyConfig = ref({
  emptyType: '',
  isAbnormal: false,
});

const queryLoading = computed<boolean>(() => traceStore.traceLoading);

const isEmptyResult = computed<boolean>(() => {
  return !traceData.value?.spans?.length && !traceData.value?.logList?.length;
});

// 更新空状态展示配置
const updateEmptyConfig = () => {
  emptyConfig.value.emptyType = searchKeyword.value ? 'searchEmpty' : '';
};

// 重置清空
const handleReset = () => {
  searchKeyword.value = '';
  traceData.value = cloneDeep(DEFAULT_TRACE_DATA);
  updateEmptyConfig();
};

// 并行请求处理
const getParallelRequestResult = (item: PromiseSettledResult<any>) => {
  return item.status === 'fulfilled' ? item.value : {};
};

// 查询追踪链详情
const handleQueryTrace = async () => {
  const keyword = searchKeyword.value.trim();

  // 空值直接重置
  if (!keyword) {
    handleReset();
    return;
  }

  traceStore.setTraceLoading(true);

  try {
    const promiseList = [
      fetchObservabilityLogInfo(keyword),
      fetchObservabilityLogSummary(keyword),
      fetchObservabilityTraceChain(keyword),
    ];
    const results = await Promise.allSettled(promiseList);

    const [logInfo, logSummary, traceChain] = results.map(getParallelRequestResult);

    traceData.value = {
      ...cloneDeep(DEFAULT_TRACE_DATA),
      ...traceChain,
      ...logSummary,
      logList: logInfo.results ?? [],
    };
    // 同步存储至全局trace信息
    traceStore.setMcpTraceInfo(traceData.value);
  }
  catch (err) {
    const errMsg = (err as Error)?.message ?? '';
    Message({
      theme: 'error',
      message: errMsg,
    });
  }
  finally {
    updateEmptyConfig();
    traceStore.setTraceLoading(false);
  }
};

// 从路由参数自动查询
const initPage = () => {
  const { request_id, x_request_id } = route.query;
  const traceId = (request_id || x_request_id) as string;

  if (traceId) {
    searchKeyword.value = traceId;
    handleQueryTrace();
  }
};

onMounted(() => {
  initPage();
});
</script>

<style lang="scss" scoped>
.query-trace-chain {
  box-sizing: border-box;

  .query-trace-chain-body {

    :deep(.body-content) {
      overflow-x: hidden;
      overflow-y: auto;

      .ag-trace-chain-info {
        margin-top: 16px;
        padding: 16px;
        border: 1px solid #dcdee5;
        box-shadow: none;
      }

      .ag-trace-chain-chart {
        margin: 24px 0;
        padding: 0;
      }

      .ag-trace-chain-table {
        margin: 0;
        box-shadow: none;

        .bk-tab {

          &-header {
            padding: 0;
          }

          &-content {
            padding: 16px 0;
          }
        }
      }
    }
  }
}
</style>
