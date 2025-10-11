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
    class="top-bar"
    :style="stage.getNotUpdatedStages?.length ? 'top: 42px' : 'top: -1px'"
  >
    <div class="top-left-wrapper">
      <div class="title">
        {{ t('仪表盘') }}
      </div>
    </div>
    <div class="top-right-wrapper">
      <div class="refresh-time mr-12px">
        <BkSelect
          v-model="step"
          class="group-select refresh-time-select"
          :input-search="false"
          :clearable="false"
          :filterable="false"
          @change="handleStepChange"
        >
          <template #trigger="{ selected }">
            <div class="refresh-time-trigger">
              <div class="label">
                <AgIcon name="miniapi" />
              </div>
              <div class="value">
                <span
                  v-show="selected[0]?.label !== 'Auto'"
                  class="text"
                >
                  {{ selected[0]?.label }}
                </span>
                <AgIcon name="down-small" />
              </div>
            </div>
          </template>
          <BkOption
            v-for="item in stepList"
            :id="item.value"
            :key="item.value"
            :name="item.label"
          />
        </BkSelect>
      </div>

      <div class="refresh-time">
        <BkSelect
          v-model="interval"
          class="group-select refresh-time-select"
          :input-search="false"
          :clearable="false"
          :filterable="false"
          @change="handleRefreshChange"
        >
          <template #trigger="{ selected }">
            <div class="refresh-time-trigger">
              <div class="label">
                <AgIcon name="lishijilu" />
              </div>
              <div class="value">
                <span
                  v-show="selected[0]?.label !== 'Off'"
                  class="text"
                >
                  {{ selected[0]?.label }}
                </span>
                <AgIcon name="down-small" />
              </div>
            </div>
          </template>
          <BkOption
            v-for="item in intervalList"
            :id="item.value"
            :key="item.value"
            :name="item.label"
          />
        </BkSelect>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useStage } from '@/stores';
import AgIcon from '@/components/ag-icon/Index.vue';

type IntervalItem = {
  label: string
  value: string
};

const emit = defineEmits<{
  'refresh-change': [data: string]
  'step-change': [data: string]
}>();

const { t } = useI18n();
const stage = useStage();

const interval = ref<string>('off');
const intervalList = ref<IntervalItem[]>([
  {
    label: 'Off',
    value: 'off',
  },
  {
    label: '5s',
    value: '5s',
  },
  {
    label: '10s',
    value: '10s',
  },
  {
    label: '15s',
    value: '15s',
  },
  {
    label: '30s',
    value: '30s',
  },
  {
    label: '1m',
    value: '1m',
  },
  {
    label: '5m',
    value: '5m',
  },
  {
    label: '15m',
    value: '15m',
  },
  {
    label: '30m',
    value: '30m',
  },
  {
    label: '1h',
    value: '1h',
  },
  {
    label: '2h',
    value: '2h',
  },
  {
    label: '1d',
    value: '1d',
  },
]);

const step = ref<string>('auto');
const stepList = ref<IntervalItem[]>([
  {
    label: 'Auto',
    value: 'auto',
  },
  {
    label: '1m',
    value: '1m',
  },
  {
    label: '5m',
    value: '5m',
  },
  {
    label: '10m',
    value: '10m',
  },
  {
    label: '30m',
    value: '30m',
  },
  {
    label: '1h',
    value: '1h',
  },
  {
    label: '3h',
    value: '3h',
  },
  {
    label: '12h',
    value: '12h',
  },
]);

const handleRefreshChange = () => {
  emit('refresh-change', interval.value);
};

const handleStepChange = () => {
  emit('step-change', step.value);
};

const reset = () => {
  interval.value = 'off';
  step.value = 'auto';
  handleRefreshChange();
  handleStepChange();
};

defineExpose({ reset });

</script>

<style lang="scss" scoped>

.top-bar {
  position: absolute;
  width: 100%;
  height: 52px;
  box-sizing: border-box;
  padding: 0 24px;
  background: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: space-between;

  .top-left-wrapper {
    display: flex;
    align-items: center;
    .title {
      font-size: 16px;
      color: #313238;
    }
  }
  .top-right-wrapper {
    display: flex;
    align-items: center;
    .refresh-time {
      .refresh-time-trigger {
        border: 1px solid #C4C6CC;
        border-radius: 2px;
        display: flex;
        align-items: center;
        .label {
          width: 32px;
          height: 32px;
          line-height: 32px;
          text-align: center;
          border-right: 1px solid #C4C6CC;
          font-size: 14px;
          color: #737987;
        }
        .value {
          padding: 0 6px;
          display: flex;
          align-items: center;
          line-height: 32px;
          height: 32px;
          cursor: pointer;
          .text {
            margin-right: 14px;
          }
          .icon-ag-down-small {
            color: #979BA5;
            font-size: 20px;
          }
        }
      }
    }
  }
  .group-select.bk-select {
    :deep(.bk-input) {
      display: flex;
      align-items: center;
    }
    &.is-focus {
      :deep(.bk-input--default) {
        box-shadow: none;
      }
    }
  }
}
</style>
