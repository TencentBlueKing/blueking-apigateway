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
  <div class="observability-time-interval">
    <div class="refresh-time">
      <BkSelect
        v-model="interval"
        class="refresh-time-select"
        :input-search="false"
        :clearable="false"
        :filterable="false"
        :popover-options="{
          width: ['off'].includes(interval) ? 'auto' : undefined,
        }"
        @toggle="handleRefreshTimeToggle"
        @change="handleRefreshTimeChange"
      >
        <template #trigger="{ selected }">
          <div class="refresh-time-trigger">
            <div
              v-bk-tooltips="{ content: t('自动刷新间隔') }"
              class="label"
            >
              <AgIcon name="lishijilu" />
            </div>
            <div
              class="value"
              :class="[
                { 'is-active': selected[0]?.label !== 'Off'}
              ]"
            >
              <span
                v-show="selected[0]?.label !== 'Off'"
                class="text"
              >
                {{ selected[0]?.label }}
              </span>
              <AgIcon
                name="down-small"
                class="apigateway-select-icon color-#979ba5"
                :class="{ 'is-open': isOpenInterval }"
              />
            </div>
          </div>
        </template>
        <BkOption
          v-for="inter of INTERVAL_TIME_LIST"
          :id="inter.value"
          :key="inter.value"
          :name="inter.label"
        />
      </BkSelect>
    </div>
    <div class="ml-8px refresh-time">
      <BkSelect
        v-model="searchParams.step"
        class="refresh-time-select"
        :input-search="false"
        :clearable="false"
        :filterable="false"
        :popover-options="{
          width: ['auto'].includes(searchParams.step) ? 'auto' : undefined,
        }"
        @toggle="handleStepToggle"
        @change="handleStepChange"
      >
        <template #trigger="{ selected }">
          <div class="refresh-time-trigger">
            <div
              v-bk-tooltips="{ content: t('精度') }"
              class="label"
            >
              <AgIcon name="xuanzejingdu" />
            </div>
            <div
              class="value"
              :class="[
                { 'is-active': selected[0]?.label !== 'Auto'}
              ]"
            >
              <span
                v-show="selected[0]?.label !== 'Auto'"
                class="text"
              >
                {{ selected[0]?.label }}
              </span>
              <AgIcon
                name="down-small"
                class="apigateway-select-icon color-#979ba5"
                :class="{ 'is-open': isOpenStep }"
              />
            </div>
          </div>
        </template>
        <BkOption
          v-for="st of PRECISION_STEPS_list"
          :id="st.value"
          :key="st.value"
          :name="st.label"
        />
      </BkSelect>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { t } from '@/locales';
import { INTERVAL_TIME_LIST, PRECISION_STEPS_list } from '@/constants';
import { useObservabilityDashboard } from '@/hooks';
import AgIcon from '@/components/ag-icon/Index.vue';

const {
  interval,
  isOpenStep,
  isOpenInterval,
  searchParams,
  handleStepChange,
  handleRefreshTimeChange,
} = useObservabilityDashboard();

const handleRefreshTimeToggle = (isVisible: boolean) => {
  isOpenInterval.value = isVisible;
};

const handleStepToggle = (isVisible: boolean) => {
  isOpenStep.value = isVisible;
};

const handleResetForm = () => {
  interval.value = 'off';
  searchParams.value.step = 'auto';
  handleRefreshTimeChange();
  handleStepChange();
};

defineExpose({ handleResetForm });
</script>

<style lang="scss" scoped>
.observability-time-interval {
  display: flex;
  align-items: center;

  .refresh-time-trigger {
    border: 1px solid #c4C6cc;
    border-radius: 2px;
    display: flex;
    align-items: center;
    cursor: pointer;

    .label {
      min-width: 26px;
      height: 26px;
      line-height: 26px;
      text-align: center;
      border-right: 1px solid #C4C6CC;
      font-size: 14px;
      color: #737987;
    }

    .value {
      display: flex;
      align-items: center;
      justify-content: space-between;
      line-height: 26px;
      height: 26px;
      cursor: pointer;

      :deep(.bk-input) {
        display: flex;
        align-items: center;
      }

      :deep(.apigateway-select-icon) {
        color: #979ba5;
        font-size: 20px !important;
        transition: transform .3s;

        &.is-open {
          transform: rotate(180deg);
        }
      }

      &.is-focus {

        :deep(.bk-input--default) {
          box-shadow: none;
        }
      }

      &.is-active {
        padding: 0 12px;

        .text {
          margin-right: 12px;
        }
      }
    }
  }
}
</style>
