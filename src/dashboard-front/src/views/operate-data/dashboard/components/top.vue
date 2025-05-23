<template>
  <div class="top-bar" :style="stage.getNotUpdatedStages?.length ? 'top: 42px' : 'top: -1px'">
    <div class="top-left-wrapper">
      <div class="title">{{ t('仪表盘') }}</div>
      <span class="line"></span>
      <div class="stage-choose">
        <bk-select
          class="group-select stage-select"
          v-model="searchParams.stage_id"
          :clearable="false"
          :input-search="false"
          filterable
          @toggle="stageSelectToggle"
          @change="handleSearchChange"
        >
          <template #trigger="{ selected }">
            <div class="stage-select-trigger">
              <div class="label">
                {{ t('环境：') }}
              </div>
              <div class="value">
                {{ typeof selected[0]?.label === 'number' ? getStageName(selected[0]?.label) : selected[0]?.label }}
              </div>
              <span
                :class="['icon', 'apigateway-icon', 'icon-ag-down-shape', stageToggle ? 'rotate' : '']">
              </span>
            </div>
          </template>
          <bk-option
            v-for="option in stageList"
            :key="option.id"
            :id="option.id"
            :name="option.name">
          </bk-option>
        </bk-select>
      </div>
    </div>
    <div class="top-right-wrapper">
      <div class="source-choose">
        <ResourceSearcher v-model="searchParams.resource_id" :list="resourceList" @change="handleSearchChange" />
      </div>
      <div class="date-choose">
        <date-picker
          v-model="dateTime"
          @update:model-value="handleValueChange"
          :valid-date-range="['now-2d', 'now/d']"
          format="YYYY-MM-DD HH:mm:ss" />
      </div>
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
import {
  computed,
  ref,
  watch,
} from 'vue';
import { useI18n } from 'vue-i18n';
import {
  useCommon,
  useStage,
} from '@/store';
import dayjs from 'dayjs';
import {
  getApigwResources,
  getApigwStages,
} from '@/http';
import DatePicker from '@blueking/date-picker';
import '@blueking/date-picker/vue3/vue3.css';
import { SearchParamsType } from '../type';
import { IStageData } from '@/views/stage/overview/types/stage';
import { ResourcesItem } from '@/views/resource/setting/types';
import ResourceSearcher from './resource-searcher.vue';
import { useRoute } from 'vue-router';

type InfoTypeItem = {
  formatText: null | string;
  dayjs: dayjs.Dayjs | null;
};

type IntervalItem = {
  label: string;
  value: string;
};

const emit = defineEmits(['search-change', 'refresh-change']);

const { t } = useI18n();
const stage = useStage();
const common = useCommon();
const route = useRoute();
const { apigwId } = common;

const searchParams = ref<SearchParamsType>({
  stage_id: 0,
  resource_id: '',
  time_start: 0,
  time_end: 0,
  metrics: '',
});

const stageToggle = ref(false);
const dateTime = ref(['now-10m', 'now']);
const formatTime = ref<string[]>([dayjs().subtract(10, 'minute')
  .format('YYYY-MM-DD HH:mm:ss'), dayjs().format('YYYY-MM-DD HH:mm:ss')]);
const stageList = ref<IStageData[]>([]);
const resourceList = ref<ResourcesItem[]>([]);
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

const getStageName = computed(() => (id: string | number) => {
  if (id === 0) return '';

  let name = '';
  const stage = stageList.value?.filter((stage: IStageData) => stage.id === id)[0];
  if (stage) {
    name = stage.name;
  }
  return name;
});

watch(() => route.query, () => {
  const span = route.query?.time_span;
  const stageId = route.query?.stage_id;

  if (span && span === 'now-6h' && stageId) {
    searchParams.value.stage_id = Number(stageId);
    dateTime.value = [
      'now-6h',
      'now',
    ];
    const now = dayjs();
    const sixHoursAgo = now.subtract(6, 'hours');
    formatTime.value = [
      sixHoursAgo.format('YYYY-MM-DD HH:mm:ss'),
      now.format('YYYY-MM-DD HH:mm:ss'),
    ];
  }
}, { deep: true, immediate: true });

const getStages = async () => {
  const pageParams = {
    no_page: true,
    order_by: 'name',
  };

  try {
    const response = await getApigwStages(apigwId, pageParams);
    stageList.value = response;
    if (!searchParams.value.stage_id) {
      searchParams.value.stage_id = stageList.value[0]?.id;
    }
  } catch (e) {
    // isDataLoading.value = false;
  }
};

const getResources = async () => {
  const pageParams = {
    no_page: true,
    order_by: 'path',
    offset: 0,
    limit: 10000,
  };

  try {
    const response = await getApigwResources(apigwId, pageParams);
    resourceList.value = response.results;
  } catch (e) {
    console.log(e);
    // isDataLoading.value = false;
  }
};

const stageSelectToggle = (value: boolean) => {
  stageToggle.value = value;
};

const handleValueChange = (value: string[], info: InfoTypeItem[]) => {
  const [startTime, endTime] = info;
  formatTime.value = [startTime?.formatText, endTime?.formatText];
  handleSearchChange();
};

const getParams = () => {
  const [time_start, time_end] = formatTime.value;
  if (time_start && time_end) {
    searchParams.value.time_start = dayjs(time_start).unix();
    searchParams.value.time_end = dayjs(time_end).unix();
  }

  return searchParams.value;
};

const handleSearchChange = () => {
  emit('search-change', getParams());
};

const handleRefreshChange = () => {
  emit('refresh-change', interval.value);
};

const reset = () => {
  searchParams.value = {
    stage_id: stageList.value[0]?.id,
    resource_id: '',
    time_start: 0,
    time_end: 0,
    metrics: '',
  };
  dateTime.value = ['now-10m', 'now'];
  formatTime.value = [dayjs().subtract(10, 'minute')
    .format('YYYY-MM-DD HH:mm:ss'),
  dayjs().format('YYYY-MM-DD HH:mm:ss')];

  emit('search-change', getParams());
};

const init = async () => {
  await getStages();
  await getResources();
  handleSearchChange();
};

init();

defineExpose({
  reset,
  init,
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
  // min-width: 1280px;
  .top-left-wrapper {
    display: flex;
    align-items: center;
    .title {
      font-size: 16px;
      color: #313238;
    }
    .line {
      width: 1px;
      height: 14px;
      background-color: #DCDEE5;
      margin: 0 16px;
    }
    .stage-choose {
      display: flex;
      align-items: center;
      .stage-select {
        width: 180px;
        :deep(.bk-input) {
          border: none;
        }
        .stage-select-trigger {
          display: flex;
          align-items: center;
          .label {
            font-size: 14px;
            color: #63656E;
          }
          .value {
            font-size: 14px;
            color: #3A84FF;
            cursor: pointer;
          }
          .icon {
            color: #3A84FF;
            margin-left: 8px;
            cursor: pointer;
            transition: all .4s;
            &.rotate {
              transform: rotate(-180deg);
            }
          }
        }
      }
    }
  }
  .top-right-wrapper {
    display: flex;
    align-items: center;
    .source-choose {
      width: 280px;
    }
    .date-choose {
      margin: 0 8px;
    }
    .refresh-time {
      .refresh-time-select {
        // width: 58px;
      }
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
