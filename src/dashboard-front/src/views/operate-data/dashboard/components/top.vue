<template>
  <div class="top-bar" :style="stage.getNotUpdatedStages?.length ? 'top: 42px' : 'top: -1px'">
    <div class="top-left-wrapper">
      <div class="title">{{ t('仪表盘') }}</div>
    </div>
    <div class="top-right-wrapper">
      <div class="refresh-time">
        <bk-select
          class="group-select refresh-time-select"
          v-model="interval"
          :input-search="false"
          :clearable="false"
          :filterable="false"
          @change="handleRefreshChange"
        >
          <template #trigger="{ selected }">
            <div class="refresh-time-trigger">
              <div class="label">
                <span class="icon apigateway-icon icon-ag-lishijilu"></span>
              </div>
              <div class="value">
                <span
                  v-show="selected[0]?.label !== 'Off'"
                  class="text">
                  {{ selected[0]?.label }}
                </span>
                <span class="icon apigateway-icon icon-ag-down-small"></span>
              </div>
            </div>
          </template>
          <bk-option
            v-for="item in intervalList"
            :id="item.value"
            :key="item.value"
            :name="item.label"
          />
        </bk-select>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStage } from '@/store';
import '@blueking/date-picker/vue3/vue3.css';

type IntervalItem = {
  label: string;
  value: string;
};

const emit = defineEmits(['refresh-change']);

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

const handleRefreshChange = () => {
  emit('refresh-change', interval.value);
};

const reset = () => {
  interval.value = 'off';
  handleRefreshChange();
};

defineExpose({
  reset,
});

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
