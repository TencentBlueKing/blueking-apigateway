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
  <div
    class="resource-top-bar"
    :style="stage.getNotUpdatedStages?.length ? 'top: 42px' : 'top: -1px'"
  >
    <div class="top-title-wrapper">
      <div class="title">
        {{ t('在线调试') }}
      </div>
      <div
        class="history"
        @click="showHistory"
      >
        <i class="apigateway-icon icon-ag-cc-history history-icon" />
        <span>{{ t('请求记录') }}</span>
      </div>
    </div>
  </div>

  <!-- 调用历史 -->
  <RequestRecord
    ref="requestRecordRef"
    @retry="(row) => emit('retry', row)"
  />
</template>

<script setup lang="ts">
import { useStage } from '@/stores';
import RequestRecord from '@/views/online-debugging/components/RequestRecord.vue';

const emit = defineEmits<{ retry: [data: any] }>();
const { t } = useI18n();
const stage = useStage();
const requestRecordRef = ref(null);

const showHistory = () => {
  requestRecordRef.value?.show();
};
</script>

<style lang="scss" scoped>
.resource-top-bar {
  position: absolute;
  width: 100%;
  height: 52px;
  box-sizing: border-box;
  padding: 0 24px;
  background: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: space-between;
  //min-width: 1280px;
  .top-title-wrapper {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    .title {
      font-size: 16px;
      color: #313238;
      margin-right: 8px;
    }
    .history {
      color: #3A84FF;
      cursor: pointer;
      .history-icon {
        font-size: 16px;
      }
      span {
        font-size: 12px;
      }
    }
  }
}
</style>
