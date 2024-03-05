<template>
  <div class="page-wrapper-padding alarm-history-container">
    <div class="header flex-row justify-content-between">
      <bk-form class="flex-row">
        <bk-form-item :label="t('选择时间')" class="ag-form-item-datepicker" label-width="85">
          <bk-date-picker
            class="w320" v-model="initDateTimeRange" :key="dateKey"
            :placeholder="t('选择日期时间范围')" :type="'datetimerange'"
            :shortcuts="datepickerShortcuts" :shortcut-close="true" :use-shortcut-text="true" @clear="handleTimeClear"
            :shortcut-selected-index="shortcutSelectedIndex" @shortcut-change="handleShortcutChange"
            @pick-success="handleTimeChange">
          </bk-date-picker>
        </bk-form-item>
        <bk-form-item :label="t('告警策略')" class="mb10" label-width="108">
          <bk-select
            v-model="filterData.alarm_strategy_id"
            filterable
            :input-search="false"
            :scroll-loading="scrollLoading"
            @scroll-end="handleScrollEnd"
            @toggle="handleToggle"
            @change="handleStrategyChange"
            @clear="handleStrategyClear"
          >
            <bk-option v-for="option in alarmStrategies" :key="option.id" :value="option.value" :label="option.label">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="t('告警状态')" class="mb10" label-width="119">
          <bk-select v-model="filterData.status" @change="handleStatusChange" @clear="handleStatusClear">
            <bk-option v-for="option in alarmStatus" :key="option.value" :value="option.value" :label="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
      </bk-form>
    </div>
    <div class="alarm-history-content">
      <bk-loading :loading="isLoading">
        <bk-table
          class="alarm-history-table" :data="tableData" remote-pagination :pagination="pagination"
          @page-limit-change="handlePageSizeChange" @page-value-change="handlePageChange" row-hover="auto"
          @row-click="handleRowClick">
          <bk-table-column :label="t('告警ID')" prop="id" width="100">
            <template #default="{ data }">
              <bk-link theme="primary">{{ data?.id }}</bk-link>
            </template>
          </bk-table-column>
          <bk-table-column :label="t('告警时间')" prop="created_time" width="260">
          </bk-table-column>
          <bk-table-column :label="t('告警策略')" prop="alarm_strategy_names">
            <template #default="{ data }">
              <template v-if="data?.alarm_strategy_names.length">
                <div
                  class="pt10 strategy-names"
                  v-bk-tooltips.top="labelTooltip(data?.alarm_strategy_names)">
                  <template v-for="(label, index) of data?.alarm_strategy_names">
                    <span class="ag-label  mb5" v-if="index < 4" :key="index">
                      {{ label }}
                    </span>
                  </template>
                  <template v-if="data?.alarm_strategy_names.length > 4">
                    <span class="ag-label mb5">
                      ...
                    </span>
                  </template>
                </div>
              </template>
              <template v-else>
                --
              </template>
            </template>
          </bk-table-column>
          <bk-table-column :label="t('告警内容')" prop="message">
            <template #default="{ data }">
              <span v-bk-tooltips="{ content: data?.message, placement: 'left' }">
                {{ data?.message }}
              </span>
            </template>
          </bk-table-column>
          <bk-table-column :label="t('状态')" width="200">
            <template #default="{ data }">
              <span :class="['ag-ouline-dot', data?.status]"></span>
              <span class="status-text">{{ getAlarmStatusText(data?.status) }}</span>
            </template>
          </bk-table-column>
          <template #empty>
            <TableEmpty
              :keyword="tableEmptyConf.keyword"
              :abnormal="tableEmptyConf.isAbnormal"
              @reacquire="getList"
              @clear-filter="handleClearFilterKey"
            />
          </template>
        </bk-table>
      </bk-loading>
    </div>

    <!-- 详情sideslider -->
    <bk-sideslider
      ext-cls="alarm-history-slider" v-model:isShow="sidesliderConfig.isShow" :title="sidesliderConfig.title"
      :quick-close="true" width="600">
      <template #default>
        <div class="hitory-form p30">
          <section class="ag-kv-list">
            <div class="item">
              <div class="key"> {{ t('告警ID：') }} </div>
              <div class="value">{{ sidesliderConfig.data.id }}</div>
            </div>
            <div class="item">
              <div class="key"> {{ t('告警时间：') }} </div>
              <div class="value">{{ sidesliderConfig.data.created_time }}</div>
            </div>
            <div class="item">
              <div class="key"> {{ t('告警策略：') }} </div>
              <div class="value strategy-name-list">
                <p class="name-item" v-for="(name, index) of sidesliderConfig.data.alarm_strategy_names" :key="index">
                  <span class="ag-label" :title="name">{{ name }}</span>
                </p>
              </div>
            </div>
            <div class="item">
              <div class="key"> {{ t('告警内容：') }} </div>
              <div class="value message">
                <pre>{{ sidesliderConfig.data.message || '--' }}</pre>
              </div>
            </div>
            <div class="item">
              <div class="key"> {{ t('状态：') }} </div>
              <div class="value">
                <span :class="['ag-ouline-dot', sidesliderConfig.data.status]"></span>
                <span class="status-text">{{ getAlarmStatusText(sidesliderConfig.data.status) }}</span>
              </div>
            </div>
          </section>
        </div>

      </template>
    </bk-sideslider>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, computed, reactive, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useCommon, useAccessLog } from '@/store';
import { useQueryList } from '@/hooks';
import {
  getStrategyList,
  getRecordList,
} from '@/http';
import { cloneDeep } from 'lodash';
import TableEmpty from '@/components/table-empty.vue';

const { t } = useI18n();
const common = useCommon();
const accessLog = useAccessLog();
const { apigwId } = common; // 网关id
const { datepickerShortcuts, alarmStatus } = accessLog;

const dateKey = ref('dateKey');
const shortcutSelectedIndex = ref<number>(-1);
const scrollLoading = ref<boolean>(false);
const initDateTimeRange = ref([]);
const alarmStrategies = ref([]);
const curStrategyCount = ref<number>(0);
const initParams = reactive({
  limit: 10,
  offset: 0,
  order_by: 'name',
});
const initFilterData = ref({
  alarm_strategy_id: '',
  status: '',
  time_start: '',
  time_end: '',
});
const filterData = cloneDeep(initFilterData);
const sidesliderConfig = reactive({
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

// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList(getRecordList, filterData);

const tableEmptyConf = ref<{keyword: string, isAbnormal: boolean}>({
  keyword: '',
  isAbnormal: false,
});

// table 标签的tooltip
const labelTooltip = computed(() => {
  return function (labels: any) {
    const labelNameList = labels.map((item: any) => {
      return item;
    });
    return labelNameList.join('; ');
  };
});

// 日期清除
const handleTimeClear = async () => {
  shortcutSelectedIndex.value = -1;
  filterData.value.time_start = '';
  filterData.value.time_end = '';
  await fetchRefreshTable();
};
// 日期快捷方式改变触发
const handleShortcutChange = (value: any, index: any) => {
  shortcutSelectedIndex.value = index;
};
// 日期快捷方式改变触发
const handleTimeChange = () => {
  nextTick(async () => {
    const startStr: any = (+new Date(`${initDateTimeRange.value[0]}`)) / 1000;
    const endStr: any = (+new Date(`${initDateTimeRange.value[1]}`)) / 1000;
    // eslint-disable-next-line radix
    const satrt: any = parseInt(startStr);
    // eslint-disable-next-line radix
    const end: any = parseInt(endStr);
    filterData.value.time_start = satrt;
    filterData.value.time_end = end;
    await fetchRefreshTable();
  });
};

// 获取状态name
const getAlarmStatusText = (status: string) => {
  const curStatus: any = alarmStatus.find(item => item.value === status) || {};
  return curStatus.name;
};
// 获取告警策略list
const getStrategy = async () => {
  try {
    const { results, count } = await getStrategyList(apigwId, initParams);
    curStrategyCount.value = count;
    alarmStrategies.value = results.map((item: any) => ({ label: item.name, value: item.id }));
    console.log(alarmStrategies.value);
  } catch (error) {
    console.log('error', error);
  }
};
// 滚动获取告警策略
const handleScrollEnd = async () => {
  if (alarmStrategies.value.length === curStrategyCount.value) return;
  scrollLoading.value = true;
  initParams.offset += 10;
  try {
    const { results } = await getStrategyList(apigwId, initParams);
    const addData = results.map((item: any) => ({ label: item.name, value: item.id }));
    alarmStrategies.value = alarmStrategies.value.concat(addData);
    scrollLoading.value = false;
  } catch (error) {
    console.log('error', error);
  }
};

const handleStrategyChange = async () => {
  await fetchRefreshTable();
};

const handleStrategyClear = async () => {
  filterData.value.alarm_strategy_id = '';
  await fetchRefreshTable();
};

const handleStatusChange = async () => {
  await fetchRefreshTable();
};

const handleStatusClear = async () => {
  filterData.value.status = '';
  await fetchRefreshTable();
};

// 刷新表格
const fetchRefreshTable = async () => {
  await getList();
  updateTableEmptyConfig();
};

// 切换告警策略选项下拉折叠状态
const handleToggle = () => {
  initParams.offset = 0;
  getStrategy();
};

// 鼠标点击
const handleRowClick = (e: any, row: any) => {
  console.log('row', row);
  sidesliderConfig.isShow = true;
  sidesliderConfig.data = row;
};

const handleClearFilterKey = async () => {
  initDateTimeRange.value = [];
  shortcutSelectedIndex.value = -1;
  dateKey.value = String(+new Date());
  filterData.value = Object.assign({}, {
    alarm_strategy_id: '',
    status: '',
    time_start: '',
    time_end: '',
  });
  await fetchRefreshTable();
};

const updateTableEmptyConfig = () => {
  const list = Object.values(filterData.value).filter(item => item !== '');
  if (list.length && !tableData.value.length) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (list.length) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

watch(() => filterData.value,  () => {
  updateTableEmptyConfig();
}, {
  deep: true,
});
</script>

<style lang="scss" scoped>
.w300 {
  width: 300px
}

.w80 {
  width: 80px
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

.strategy-names{
  display: inline-block;
}
.ag-label {
  height: 24px;
  line-height: 22px;
  border: 1px solid #DCDEE5;
  text-align: center;
  padding: 0 10px;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: normal;
  display: inline-block;
  margin-right: 4px;
  border-radius: 2px;
  white-space: nowrap;
}

.ag-ouline-dot {
  width: 10px;
  height: 10px;
  border: 2px solid #C4C6CC;
  display: inline-block;
  border-radius: 50%;
  vertical-align: middle;
  line-height: 1;

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
    border-color: #3A84FF;
  }
}

.ag-kv-list {
  border: 1px solid #F0F1F5;
  border-radius: 2px;
  background: #FAFBFD;
  padding: 10px 20px;

  .item {
    display: flex;
    font-size: 14px;
    border-bottom: 1px dashed #DCDEE5;
    min-height: 40px;
    line-height: 40px;

    &:last-child {
      border-bottom: none;
    }

    .key {
      min-width: 130px;
      padding-right: 24px;
      color: #63656E;
      text-align: right;
    }

    .value {
      color: #313238;
      flex: 1;

      pre {
        margin: 0;
        white-space: pre-wrap;
      }
    }
    .message{
      line-height: 22px;
      padding: 10px 0;
    }
  }
}

.strategy-name-list {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  margin: 6px 0;

  .name-item {
    margin: 0 0 4px 0;
    line-height: 0;

    .ag-label {
      max-width: 300px;
    }
  }
}
:deep(.alarm-history-content){
  .bk-exception{
    height: 280px;
    max-height: 280px;
    justify-content: center;
  }
}
</style>
