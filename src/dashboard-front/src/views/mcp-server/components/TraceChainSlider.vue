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
  <BkSideslider
    v-model:is-show="isShow"
    :width="1280"
    class="trace-chain-slider"
    quick-close
    @closed="handleCloseSlider"
  >
    <template #header>
      <div class="flex items-center text-16px">
        <span class="color-#313238">{{ `${t('请求ID')} (request_id)` }}</span>
        <Divider
          direction="vertical"
          type="solid"
        />
        <div class="flex items-center color-#979ba5">
          <span class="truncate">{{ requestId }}</span>
          <AgIcon
            v-bk-tooltips="t('复制 request_id')"
            name="copy"
            class="ml-8px hover-color-#3a84ff cursor-pointer"
            @click="handleCopy(requestId)"
          />
          <AgIcon
            v-bk-tooltips="t('复制链接')"
            name="link-2"
            class="ml-8px hover-color-#3a84ff cursor-pointer"
            @click.stop="handleCopy('link')"
          />
        </div>
      </div>
    </template>
    <template #default>
      <BkLoading
        :loading="detailLoading"
        :z-index="999"
      >
        <div class="trace-chain-content">
          <AgMcpTraceChain :trace-chain-detail="traceData" />
        </div>
      </BkLoading>
    </template>
  </BkSideslider>
</template>

<script lang="ts" setup>
import { Divider, Message } from 'bkui-vue';
import { cloneDeep } from 'lodash-es';
import { t } from '@/locales';
import { copy } from '@/utils';
import { useTrace } from '@/stores';
import {
  type ITraceDetail,
  fetchObservabilityLogInfoByGateway,
  fetchObservabilityTraceChainByGateway,
} from '@/services/source/observability';
import { DEFAULT_TRACE_DATA } from '@/components/trace-view/constants/trace';
import AgMcpTraceChain from '@/components/ag-mcp-trace-chain/Index.vue';

interface IProps {
  apiGatewayId: string | number
  requestId?: string
}

const { apiGatewayId, requestId = '' } = defineProps<IProps>();

const traceStore = useTrace();

const isShow = ref(false);
const traceData = ref<ITraceDetail>(DEFAULT_TRACE_DATA as ITraceDetail);

const detailLoading = computed(() => traceStore.traceLoading);

// 并行请求处理
const getParallelRequestResult = (item: PromiseSettledResult<any>) => {
  return item.status === 'fulfilled' ? item.value : {};
};

const getTraceChainDetail = async () => {
  traceStore.setTraceLoading(true);

  try {
    const promiseList = [
      fetchObservabilityLogInfoByGateway(apiGatewayId as number, requestId, {} as any),
      fetchObservabilityTraceChainByGateway(apiGatewayId as number, requestId),
    ];
    const results = await Promise.allSettled(promiseList);

    const [logInfo, traceChain] = results.map(getParallelRequestResult);

    const { upstream_log, downstream_log } = traceStore.parseTraceChainLogs(traceChain);

    const logList = [
      ...(logInfo.results ?? []),
      upstream_log,
      downstream_log,
    ].filter(Boolean);

    traceData.value = {
      ...cloneDeep(DEFAULT_TRACE_DATA),
      ...traceChain,
      logList,
    };
    // 同步存储至全局trace信息
    traceStore.setMcpTraceInfo(traceData.value);
  }
  catch (err) {
    Message({
      message: (err as Error)?.message,
      theme: 'error',
    });
  }
  finally {
    traceStore.setTraceLoading(false);
    traceStore.setMcpTraceInfo(traceData.value);
  }
};

const show = () => {
  isShow.value = true;
  getTraceChainDetail();
};

const handleCopy = (value: string) => {
  let content: string = value;
  if (value === 'link') {
    const url = new URL(location.href);
    url.searchParams.set('request_id', requestId);
    url.searchParams.set('showTraceChain', 'true');
    content = url.toString();
  }
  copy(content);
};

const handleCloseSlider = () => {
  traceStore.setTraceLogTab('proxy_log');
};

defineExpose({
  show,
  handleCloseSlider,
  getTraceChainDetail,
});
</script>

<style lang="scss" scoped>
.trace-chain-slider {

  :deep(.bk-modal-body) {
    background-color: #f5f7fb;
  }

  .trace-chain-content {
    box-sizing: border-box;
  }
}
</style>
