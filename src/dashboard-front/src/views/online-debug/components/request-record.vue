<template>
  <bk-sideslider
    v-model:isShow="isShow"
    :title="t('调用历史')"
    :width="960"
    quick-close>
    <template #default>
      <div class="history-container">
        <div class="history-search">
          <bk-input
            class="search-input"
            v-model="name"
            type="search"
            :placeholder="t('请输入资源名称')"
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
            <bk-table-column :label="t('资源名称')" prop="name"></bk-table-column>
            <bk-table-column :label="t('响应状态码')" prop="status">
              <template #default="{ data }">
                <span :class="['dot', String(data?.status)?.startsWith('2') ? 'success' : 'failure']"></span>
                {{ data?.status }}
              </template>
            </bk-table-column>
            <bk-table-column :label="t('调用时间')" prop="time"></bk-table-column>
            <bk-table-column :label="t('操作')">
              <template #default="{ row }">
                <bk-button theme="primary" text @click="(e: any) => handleRowClick(e, row)">
                  {{ t('请求详情') }}
                </bk-button>
              </template>
            </bk-table-column>
            <!-- eslint-disable-next-line vue/no-unused-vars -->
            <template #expandRow="row">
              <div class="details">
                <editor-monaco v-model="editorText" theme="Visual Studio" ref="resourceEditorRef" />
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
import { useAccessLog } from '@/store';
import editorMonaco from '@/components/ag-editor.vue';

const { t } = useI18n();

const isShow = ref<boolean>(false);
const name = ref<string>('');
const dateTimeRange = ref([]);
const dateKey = ref('dateKey');
const AccessLogStore = useAccessLog();
const shortcutSelectedIndex = shallowRef(-1);
const tableRef = ref(null);
const resourceEditorRef: any = ref<InstanceType<typeof editorMonaco>>();
const tableList = ref<any>([
  {
    id: 1,
    name: 'bk_login_is_login',
    status: 200,
    time: '2024-12-12 12:00:00',
  },
  {
    id: 2,
    name: 'bk_login_is_login',
    status: 200,
    time: '2024-12-12 12:00:00',
  },
  {
    id: 3,
    name: 'bk_login_is_login',
    status: 400,
    time: '2024-12-12 12:00:00',
  },
  {
    id: 4,
    name: 'bk_login_is_login',
    status: 500,
    time: '2024-12-12 12:00:00',
  },
]);
const editorText = ref<string>(`{
	"type": "team",
	"test": {
		"testPage": "tools/testing/run-tests.htm",
		"enabled": true
	},
    "search": {
        "excludeFolders": [
			".git",
			"tools/testing/qunit",
			"tools/testing/chutzpah",
			"server.net"
        ]
}`);
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

// const formatDatetime = (timeRange: number[]) => {
//   return [+new Date(`${timeRange[0]}`) / 1000, +new Date(`${timeRange[1]}`) / 1000];
// };

const setSearchTimeRange = () => {
  // let timeRange = dateTimeRange.value;
  // // 选择的是时间快捷项，需要实时计算时间值
  // if (shortcutSelectedIndex.value !== -1) {
  //   timeRange = AccessLogStore.datepickerShortcuts[shortcutSelectedIndex.value].value();
  // }
  // const formatTimeRange = formatDatetime(timeRange);
  // filterData.value = Object.assign(filterData.value, {
  //   time_start: formatTimeRange[0] || '',
  //   time_end: formatTimeRange[1] || '',
  // });
};

const handleTimeChange = () => {
  setSearchTimeRange();
};

const handleTimeClear = () => {
  shortcutSelectedIndex.value = -1;
  dateTimeRange.value = [];
  setSearchTimeRange();
};

const handleRowClick = (e: Event, row: Record<string, any>) => {
  e.stopPropagation();
  row.isExpand = !row.isExpand;
  nextTick(() => {
    tableRef.value.setRowExpand(row,  row.isExpand);
  });
};

const show = () => {
  isShow.value = true;
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
      height: 400px;
      max-height: 600px;
      padding: 12px 0;
      background: #FFFFFF;
      border: 1px solid #DCDEE5;
      border-radius: 2px;
    }
  }
}
</style>
