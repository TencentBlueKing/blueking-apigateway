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
    class="flex items-center ag-trace-chain-traceChainDetail"
    v-bind="$attrs"
  >
    <AgIcon
      name="request"
      size="28"
      color="#3a84ff"
      class="p-11px bg-#f0f5ff border-rounded-4px"
    />
    <div class="ml-12px text-12px">
      <div class="color-#313238 lh-20px mb-8px font-700">
        {{ traceChainDetail?.request_id }}
      </div>
      <div class="flex flex-wrap ag-trace-chain-traceChainDetail-form">
        <div class="item">
          <div class="label">
            {{ t('产生时间') }}:
          </div>
          <div class="value">
            {{ traceChainDetail?.timestamp
              ? dayjs.unix(traceChainDetail?.timestamp).format('YYYY-MM-DD HH:mm:ss')
              : 0
            }}
          </div>
        </div>
        <div class="item">
          <div class="label">
            {{ t('总耗时') }}:
          </div>
          <div class="value">
            {{ `${traceChainDetail?.total_latency_ms ?? 0 }ms` }}
          </div>
        </div>
        <div class="item">
          <div class="label">
            {{ t('耗时分布') }}:
          </div>
          <div class="value">
            {{ renderLatencyDistribution() }}
          </div>
        </div>
        <div class="item">
          <div class="label">
            {{ t('服务数') }}:
          </div>
          <div class="value">
            {{ traceChainDetail?.service_count ?? 0 }}
          </div>
        </div>
        <div class="item">
          <div class="label">
            {{ t('Span 总数') }}:
          </div>
          <div class="value">
            {{ traceChainDetail?.span_count ?? 0 }}
          </div>
        </div>
        <div class="item">
          <div class="label">
            {{ t('状态') }}:
          </div>
          <div class="value ml-14px!">
            <AgStatusDot
              class="lh-22px"
              :type="renderStatusDot()?.type"
              :text="renderStatusDot()?.text"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import dayjs from 'dayjs';
import { t } from '@/locales';
import type { ITraceDetail } from '@/services/source/observability';
import AgStatusDot from '@/components/ag-status-dot/Index.vue';

interface IProps { traceChainDetail?: ITraceDetail }

const { traceChainDetail = {} } = defineProps<IProps>();

const isSuccessStatus = computed(() => {
  return traceChainDetail?.status
    && ((Number(traceChainDetail.status) >= 200
      && Number(traceChainDetail.status) < 300) || ['success'].includes(traceChainDetail.status));
});

const renderStatusDot = () => {
  return {
    type: isSuccessStatus.value ? 'success' : 'error',
    text: t(isSuccessStatus.value ? '成功' : '失败'),
  };
};

const renderLatencyDistribution = () => {
  const latencyDistribution = traceChainDetail?.latency_distribution;

  if (latencyDistribution?.length) {
    return latencyDistribution.map((item: any) => `${item?.latency_ms}ms`)?.join(' - ');
  }

  return '0ms';
};
</script>

<style lang="scss" scoped>
.ag-trace-chain-traceChainDetail {
  background-color: #ffffff;
  box-shadow: 0 2px 4px 0 #1919290d;
  box-sizing: border-box;

  &-form {

    .item {
      display: flex;
      color: #313238;
      margin-right: 24px;
      line-height: 20px;

      .label {
        color: #979ba5;
      }

      .value {
        margin-left: 8px;
      }
    }
  }
}
</style>
