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
  <div class="page-wrapper-padding alarm-history-container">
    <div class="header flex justify-between">
      <BkForm
        class="flex"
        :model="filterData"
      >
        <BkFormItem
          :label="t('选择时间')"
          class="ag-form-item-datepicker"
          label-width="85"
        >
          <BkDatePicker
            :key="dateKey"
            v-model="dateValue"
            class="w-320px"
            :placeholder="t('选择日期时间范围')"
            type="datetimerange"
            use-shortcut-text
            :shortcuts="shortcutsRange"
            :shortcut-selected-index="shortcutSelectedIndex"
            @shortcut-change="handleShortcutChange"
            @change="handleChange"
            @clear="handlePickClear"
            @pick-success="handlePickSuccess"
            @selection-mode-change="handleSelectionModeChange"
          />
        </BkFormItem>
        <BkFormItem
          :label="t('告警策略')"
          property="alarm_strategy_id"
          class="m-b-10px"
          label-width="108"
        >
          <BkSelect
            v-model="filterData.alarm_strategy_id"
            filterable
            :input-search="false"
            :scroll-loading="scrollLoading"
            @scroll-end="handleScrollEnd"
            @toggle="handleToggle"
          >
            <BkOption
              v-for="option in alarmStrategyOption"
              :key="option.id"
              :value="option.value"
              :label="option.label"
            />
          </BkSelect>
        </BkFormItem>
        <BkFormItem
          :label="t('告警状态')"
          property="status"
          class="m-b-10px"
          label-width="119"
        >
          <BkSelect v-model="filterData.status">
            <BkOption
              v-for="option in alarmStatus"
              :key="option.value"
              :value="option.value"
              :label="option.label"
            />
          </BkSelect>
        </BkFormItem>
      </BkForm>
    </div>
    <div class="alarm-history-content">
      <AgTable
        ref="tableRef"
        v-model:table-data="tableData"
        show-settings
        resizable
        :filter-value="filterData"
        :api-method="getTableData"
        :columns="tableColumns"
        @row-click="handleRowClick"
        @filter-change="handleFilterChange"
        @clear-filter="handleClearFilter"
      />
    </div>

    <!-- 详情 -->
    <BkSideslider
      v-model:is-show="sliderConfig.isShow"
      ext-cls="alarm-history-slider"
      :width="750"
      :title="sliderConfig.title"
      quick-close
    >
      <template #default>
        <div class="history-form p-30px">
          <section class="ag-kv-list">
            <div class="item">
              <div class="key">
                {{ t("告警ID：") }}
              </div>
              <div class="value">
                {{ sliderConfig?.data?.id }}
              </div>
            </div>
            <div class="item">
              <div class="key">
                {{ t("告警时间：") }}
              </div>
              <div class="value">
                {{ sliderConfig?.data?.created_time }}
              </div>
            </div>
            <div class="item">
              <div class="key">
                {{ t("告警策略：") }}
              </div>
              <div class="value strategy-name-list">
                <p
                  v-for="(name, index) of sliderConfig?.data?.alarm_strategy_names"
                  :key="index"
                  class="name-item"
                >
                  <span
                    class="ag-label"
                    :title="name"
                  >
                    {{ name }}
                  </span>
                </p>
              </div>
            </div>
            <div class="item">
              <div class="key">
                {{ t("告警内容：") }}
              </div>
              <div class="value message">
                <pre>{{ sliderConfig.data.message || "--" }}</pre>
              </div>
            </div>
            <div class="item">
              <div class="key">
                {{ t("状态：") }}
              </div>
              <div class="value">
                <span
                  class="m-r-4px ag-outline-dot"
                  :class="[sliderConfig.data.status]"
                />
                <span class="status-text">
                  {{ getAlarmStatusText(sliderConfig.data.status) }}
                </span>
              </div>
            </div>
          </section>
        </div>
      </template>
    </BkSideslider>
  </div>
</template>

<script lang="tsx" setup>
import type { ITableMethod } from '@/types/common';
import { useAccessLog, useGateway } from '@/stores';
import { useDatePicker } from '@/hooks';
import { type IAlarmRecord, getRecordList, getStrategyList } from '@/services/source/monitor';
import AgTable from '@/components/ag-table/Index.vue';

const { t } = useI18n();
const gatewayStore = useGateway();
const accessLogStore = useAccessLog();
const { alarmStatus } = accessLogStore;

const tableRef = useTemplateRef<InstanceType<typeof AgTable> & ITableMethod>('tableRef');
const dateKey = ref('dateKey');
const curStrategyCount = ref(0);
const scrollLoading = ref(false);
const tableData = ref([]);
const alarmStrategyOption = ref([]);
const initParams = reactive({
  limit: 10,
  offset: 0,
  order_by: 'name',
});
let sliderConfig = reactive({
  isShow: false,
  title: t('告警详情'),
  data: {
    id: -1,
    created_time: '',
    alarm_strategy_names: [],
    message: '',
    status: '',
  },
});
const filterData = ref({});

const {
  dateValue,
  shortcutsRange,
  shortcutSelectedIndex,
  handleChange,
  handleClear,
  handleConfirm,
  handleShortcutChange,
  handleSelectionModeChange,
} = useDatePicker(filterData);

const apigwId = computed(() => gatewayStore.apigwId);
const tableColumns = computed(() => ([
  {
    title: t('告警ID'),
    colKey: 'id',
    ellipsis: true,
    fixed: 'left',
  },
  {
    title: t('告警时间'),
    colKey: 'created_time',
    ellipsis: true,
  },
  {
    title: t('告警策略'),
    colKey: 'alarm_strategy_id',
    filter: {
      type: 'single',
      showConfirmAndReset: true,
      popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
      list: alarmStrategyOption.value,
    },
    cell: (h, { row }: { row?: Partial<IAlarmRecord> }) => {
      if (row?.alarm_strategy_names?.length) {
        return (
          <div class="lh-1">
            <span
              v-bk-tooltips={{
                content: row.alarm_strategy_names?.join('; '),
                placement: 'top',
              }}
              class="strategy-names"
            >
              {
                row.alarm_strategy_names.map((strategy, index) => {
                  if (index < 4) {
                    return (
                      <span class="ag-label">
                        { strategy }
                      </span>
                    );
                  }
                  if (index === row.alarm_strategy_names.length - 1 && index > 3) {
                    return <span class="ag-label">...</span>;
                  }
                })
              }
            </span>
          </div>
        );
      }
      return '--';
    },
  },
  {
    title: t('告警内容'),
    colKey: 'message',
    ellipsis: true,
    cell: (h, { row }: { row?: Partial<IAlarmRecord> }) => {
      return (
        <span>
          { row?.message }
        </span>
      );
    },
  },
  {
    title: t('状态'),
    colKey: 'status',
    filter: {
      type: 'single',
      showConfirmAndReset: true,
      popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
      list: alarmStatus,
    },
    cell: (h, { row }: { row?: Partial<IAlarmRecord> }) => {
      return (
        <span>
          <span class={['m-r-4px', 'ag-outline-dot', row?.status]} />
          <span
            v-bk-tooltips={{
              content: row?.comment || '--',
              disabled: !['skipped'].includes(row?.status),
            }}
            class="status-text"
          >
            { getAlarmStatusText(row?.status) }
          </span>
        </span>
      );
    },
  },
]));

watch(() => filterData, () => {
  getList();
}, { deep: true });

function getList() {
  tableRef.value!.fetchData(filterData.value, { resetPage: true });
};

const getTableData = async (params: Record<string, any> = {}) => {
  const results = await getRecordList(apigwId.value, params);
  return results ?? [];
};

const handleFilterChange: PrimaryTableProps['onFilterChange'] = (filterItem: FilterValue) => {
  filterData.value = Object.assign(filterData.value, filterItem);
};

// 日期清除
const handleTimeClear = () => {
  filterData.value = Object.assign(filterData.value, {
    time_start: '',
    time_end: '',
  });
};

const handlePickClear = () => {
  handleClear();
  handleTimeClear();
};

const handlePickSuccess = () => {
  handleConfirm();
};

// 获取状态name
const getAlarmStatusText = (status: string) => {
  const curStatus = alarmStatus.find(item => item.value === status) ?? {};
  return curStatus.label ?? '--';
};

// 获取告警策略list
const getStrategyOption = async () => {
  const { results, count } = await getStrategyList(apigwId.value, initParams);
  curStrategyCount.value = count;
  alarmStrategyOption.value = results.map(item => ({
    label: item.name,
    value: item.id,
  }));
};
getStrategyOption();

// 滚动获取告警策略
const handleScrollEnd = async () => {
  if (alarmStrategyOption.value.length === curStrategyCount.value) return;
  scrollLoading.value = true;
  initParams.offset += 10;
  try {
    const { results } = await getStrategyList(apigwId.value, initParams);
    const addData = results.map(item => ({
      label: item.name,
      value: item.id,
    }));
    alarmStrategyOption.value = alarmStrategyOption.value.concat(addData);
  }
  finally {
    scrollLoading.value = false;
  }
};

// 切换告警策略选项下拉折叠状态
const handleToggle = (value: boolean) => {
  if (value) {
    initParams.offset = 0;
    getStrategyOption();
  }
};

// 鼠标点击
const handleRowClick = (e: MouseEvent, row: IAlarmRecord) => {
  sliderConfig = Object.assign(sliderConfig, {
    isShow: true,
    data: row,
  });
};

const handleClearFilter = () => {
  dateValue.value = [];
  shortcutSelectedIndex.value = -1;
  dateKey.value = String(+new Date());
  filterData.value = {};
};
</script>

<style lang="scss" scoped>
.w300 {
  width: 300px;
}

.w80 {
  width: 80px;
}

.w88 {
  width: 88px;
}

:deep(.alarm-history-table) {

  .bk-table-body {

    table {

      tbody {

        tr {
          cursor: pointer;

          td {

            .cell {
              height: auto !important;
              line-height: normal;
            }
          }
        }
      }
    }
  }
}

.ag-kv-list {
  padding: 10px 20px;
  background-color: #fafbfd;
  border: 1px solid #f0f1f5;
  border-radius: 2px;

  .item {
    display: flex;
    min-height: 40px;
    font-size: 14px;
    line-height: 40px;
    border-bottom: 1px dashed #dcdee5;

    &:last-child {
      border-bottom: none;
    }

    .key {
      min-width: 120px;
      padding-right: 24px;
      color: #63656e;
      text-align: right;
    }

    .value {
      color: #313238;
      flex: 1;

      pre {
        margin: 0;
        font-family: monospace;
        word-break: break-all;
        white-space: pre-wrap;
      }
    }

    .message {
      padding: 10px 0;
      line-height: 22px;
    }
  }
}

.strategy-name-list {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  margin: 6px 0;

  .name-item {
    margin: 0 0 4px;
    line-height: 0;

    .ag-label {
      max-width: 300px;
    }
  }
}

.strategy-name-list,
:deep(.strategy-names) {

  .ag-label {
    display: inline-block;
    height: 24px;
    padding: 0 10px;
    margin-right: 4px;
    overflow: hidden;
    line-height: 22px;
    text-align: center;
    text-overflow: ellipsis;
    white-space: normal;
    white-space: nowrap;
    border: 1px solid #dcdee5;
    border-radius: 2px;
  }
}

:deep(.ag-outline-dot) {
  display: inline-block;
  width: 10px;
  height: 10px;
  line-height: 1;
  vertical-align: middle;
  border: 2px solid #c4c6cc;
  border-radius: 50%;

  &.success {
    border-color: #34d97b;
  }

  &.failure,
  &.fail {
    border-color: #ea3536;
  }

  &.skipped,
  &.unknown {
    border-color: #979ba5;
  }

  &.received {
    border-color: #3a84ff;
  }
}
</style>

<style lang="scss">
.bk-popper.monitor-tooltips {
  width: 520px;
  word-break: break-all;
  white-space: pre-wrap;
}
</style>
