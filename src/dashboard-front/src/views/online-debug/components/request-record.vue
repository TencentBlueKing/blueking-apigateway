<template>
  <bk-sideslider
    v-model:isShow="isShow"
    :title="t('调用历史')"
    :width="960"
    class="sutra-scrollbar"
    quick-close>
    <template #default>
      <div class="history-container">
        <div class="history-search">
          <bk-input
            class="search-input"
            v-model="filterData.resource_name"
            type="search"
            :placeholder="t('请输入资源名称')"
            @blur="getList()"
          />

          <bk-date-picker
            ref="topDatePicker"
            class="search-date"
            v-model="dateTimeRange"
            :key="dateKey"
            :placeholder="t('选择日期时间范围')"
            :type="'datetimerange'"
            :shortcuts="AccessLogStore.datepickerShortcuts"
            :shortcut-close="true"
            :use-shortcut-text="true"
            :shortcut-selected-index="shortcutSelectedIndex"
            @shortcut-change="handleShortcutChange"
            @pick-success="handleTimeChange"
            @clear="handleTimeClear"
          >
          </bk-date-picker>
        </div>

        <div class="history-data">
          <bk-table
            ref="tableRef"
            size="small"
            class="history-table"
            border="outer"
            :data="tableList"
            :row-style="{ cursor: 'pointer' }"
            :show-overflow-tooltip="true"
          >
            <bk-table-column :label="t('资源名称')" prop="resource_name"></bk-table-column>
            <bk-table-column :label="t('响应状态码')" prop="status_code">
              <template #default="{ data }">
                <span
                  :class="['dot', String(data?.response?.data?.status_code)?.startsWith('2') ? 'success' : 'failure']">
                </span>
                {{ data?.response?.data?.status_code }}
              </template>
            </bk-table-column>
            <bk-table-column :label="t('调用时间')" prop="created_time"></bk-table-column>
            <bk-table-column :label="t('操作')">
              <template #default="{ row }">
                <bk-button theme="primary" text @click="(e: any) => handleRowClick(e, row)">
                  {{ t('请求详情') }}
                </bk-button>
              </template>
            </bk-table-column>
            <template #expandRow="row">
              <div class="details">
                <editor-monaco
                  v-if="row?.editorText"
                  v-model="row.editorText"
                  theme="Visual Studio"
                  ref="resourceEditorRef"
                  language="json"
                  :minimap="false"
                  :show-copy="true"
                  :read-only="true"
                />
                <editor-monaco
                  v-else
                  v-model="placeholderText"
                  theme="Visual Studio"
                  language="json"
                  :minimap="false"
                  :show-copy="true"
                  :read-only="true"
                />
              </div>
            </template>
          </bk-table>
        </div>
      </div>
    </template>
  </bk-sideslider>
</template>

<script lang="ts" setup>
import { ref, shallowRef, reactive, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAccessLog, useCommon } from '@/store';
import editorMonaco from '@/components/ag-editor.vue';
import { getTestHistories, getTestHistoriesDetails } from '@/http';
import { Message } from 'bkui-vue';

const { t } = useI18n();
const common = useCommon();

const isShow = ref<boolean>(false);
const filterData = ref<any>({
  resource_name: '',
  time_start: '',
  time_end: '',
});
const dateTimeRange = ref([]);
const dateKey = ref('dateKey');
const topDatePicker = ref(null);
const AccessLogStore = useAccessLog();
const shortcutSelectedIndex = shallowRef(-1);
const tableRef = ref(null);
const resourceEditorRef: any = ref<InstanceType<typeof editorMonaco>>();
const tableList = ref<any>([]);
const placeholderText = ref<string>('');
const tableEmptyConf = reactive<any>({
  keyword: '',
  isAbnormal: false,
});

const updateTableEmptyConfig = () => {
  // if (!curPagination.value.count) {
  //   tableEmptyConf.keyword = 'placeholder';
  //   return;
  // }
  tableEmptyConf.keyword = '';
};

const handleShortcutChange = (value: Record<string, any>, index: number) => {
  shortcutSelectedIndex.value = index;
  updateTableEmptyConfig();
};

const formatDatetime = (timeRange: number[]) => {
  return [+new Date(`${timeRange[0]}`) / 1000, +new Date(`${timeRange[1]}`) / 1000];
};

const setSearchTimeRange = () => {
  let timeRange = dateTimeRange.value;
  // 选择的是时间快捷项，需要实时计算时间值
  if (shortcutSelectedIndex.value !== -1) {
    timeRange = AccessLogStore.datepickerShortcuts[shortcutSelectedIndex.value].value();
  }
  const formatTimeRange = formatDatetime(timeRange);
  filterData.value = Object.assign(filterData.value, {
    time_start: formatTimeRange[0] || '',
    time_end: formatTimeRange[1] || '',
  });

  getList();
};

const handleTimeChange = () => {
  const internalValue = topDatePicker.value?.internalValue;
  if (internalValue) {
    dateTimeRange.value = internalValue;
    setSearchTimeRange();
  } else {
    Message({ theme: 'warning', message: t('输入的时间错误'), delay: 2000, dismissable: false });
  }
};

const handleTimeClear = () => {
  shortcutSelectedIndex.value = -1;
  dateTimeRange.value = [];
  setSearchTimeRange();
};

const handleRowClick = async (e: Event, row: Record<string, any>) => {
  e.stopPropagation();
  if (!row.isExpand) {
    await getDetails(row.id, row);
  } else {
    row.isExpand = !row.isExpand;
    nextTick(() => {
      tableRef.value.setRowExpand(row,  row.isExpand);
    });
  }
};

const clear = () => {
  filterData.value.resource_name = '';
  filterData.value.time_start = '';
  filterData.value.time_end = '';
  shortcutSelectedIndex.value = -1;
  dateTimeRange.value = [];
};

const show = () => {
  clear();
  isShow.value = true;
  getList();
};

const getList = async () => {
  const data = {
    offset: 0,
    limit: 10000,
    ...filterData.value,
  };
  const res = await getTestHistories(common.apigwId, data);
  res?.forEach((item: any) => {
    item.editorText = '';
  });
  tableList.value = res;
};

const getDetails = async (id: number, row: Record<string, any>) => {
  const res = await getTestHistoriesDetails(common.apigwId, id);

  row.editorText = res?.response?.data?.curl;
  row.isExpand = !row.isExpand;
  nextTick(() => {
    tableRef.value.setRowExpand(row,  row.isExpand);
  });
};

defineExpose({
  show,
});
</script>

<style lang="scss" scoped>
.history-container {
  padding: 20px 24px;
  height: calc(100vh - 52px);
  box-sizing: border-box;
  .history-search {
    display: flex;
    align-items: center;
    margin-bottom: 18px;
    .search-input {
      width: 420px;
      margin-right: 8px;
    }
    .search-date {
      flex: 1;
    }
  }
  .history-data {
    .details {
      width: 100%;
      height: 300px;
      max-height: 600px;
      padding: 12px 0;
      background: #FFFFFF;
      border-radius: 2px;
    }
  }
}
.sutra-scrollbar {
  :deep(.bk-modal-content) {
    scrollbar-gutter: auto;
  }
  :deep(.bk-table-body) {
    scrollbar-gutter: auto;
  }
}
</style>
