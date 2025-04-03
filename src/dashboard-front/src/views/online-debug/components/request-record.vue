<template>
  <bk-sideslider
    v-model:is-show="isShow"
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
            @enter="getList()"
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
            :pagination="pagination"
            @row-click="handleRowClick"
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
            <bk-table-column :label="t('耗时')" prop="proxy_time">
              <template #default="{ data }">
                {{ data?.response?.data?.proxy_time }} ms
              </template>
            </bk-table-column>
            <bk-table-column :label="t('调用时间')" prop="created_time"></bk-table-column>
            <bk-table-column :label="t('操作')">
              <template #default="{ row }">
                <bk-button theme="primary" text @click="(e: any) => handleShowDetails(e, row)">
                  {{ t('请求详情') }}
                </bk-button>
              </template>
            </bk-table-column>
            <template #expandRow="row">
              <div class="details-tab">
                <div class="tab-header">
                  <div class="header-title">
                    <div
                      :class="{ 'title': true, 'active': item.id === row?.activeIndex }"
                      @click="handleTabClick(row, item.id)"
                      v-for="item in tabList"
                      :key="item.id">
                      {{ item.name }}
                    </div>
                  </div>
                  <div class="header-copy" v-show="row?.activeIndex !== 'requestHeader'">
                    <copy-shape @click="handleCopyDetails(row)" />
                  </div>
                </div>
                <div class="tab-content">
                  <div
                    class="content-item code"
                    :class="`code-${row?.id}`"
                    v-show="row?.activeIndex === 'code'">
                    <editor-monaco
                      v-if="row?.editorText"
                      v-model="row.editorText"
                      theme="Visual Studio"
                      ref="resourceEditorRef"
                      language="json"
                      :minimap="false"
                      :show-copy="false"
                      :read-only="true"
                    />
                  </div>

                  <div class="content-item request-url" v-show="row?.activeIndex === 'url'">
                    <span class="tag">{{ row?.request?.request_method }}</span>
                    <span class="url">{{ row?.request?.request_url }}</span>
                  </div>

                  <div class="content-item request-header" v-show="row?.activeIndex === 'requestHeader'">
                    <bk-table
                      ref="tabTableRef"
                      class="request-header-table"
                      size="small"
                      row-hover="auto"
                      header-align="left"
                      max-height="252px"
                      :stripe="true"
                      :columns="requestHeaderCols"
                      :data="getRequestHeader(row)" />
                  </div>

                  <div
                    class="content-item request-body"
                    :class="`request-body-${row?.id}`"
                    v-show="row?.activeIndex === 'requestBody'">
                    <editor-monaco
                      v-if="row?.requestBody"
                      v-model="row.requestBody"
                      theme="Visual Studio"
                      ref="requestBodyRef"
                      language="json"
                      :minimap="false"
                      :show-copy="false"
                      :read-only="true"
                    />
                  </div>

                  <div
                    class="content-item response-body"
                    :class="`response-body-${row?.id}`"
                    v-show="row?.activeIndex === 'responseBody'">
                    <editor-monaco
                      v-if="row?.responseBody"
                      v-model="row.responseBody"
                      theme="Visual Studio"
                      ref="responseBodyRef"
                      language="json"
                      :minimap="false"
                      :show-copy="false"
                      :read-only="true"
                    />
                  </div>
                </div>
              </div>
            </template>
            <template #empty>
              <TableEmpty
                :keyword="tableEmptyConf.keyword"
                :abnormal="tableEmptyConf.isAbnormal"
                @reacquire="setSearchTimeRange"
                @clear-filter="handleClearFilterKey"
              />
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
// @ts-ignore
import TableEmpty from '@/components/table-empty.vue';
// @ts-ignore
import editorMonaco from '@/components/ag-editor.vue';
import { getTestHistories, getTestHistoriesDetails } from '@/http';
import { Message } from 'bkui-vue';
import { CopyShape } from 'bkui-vue/lib/icon';
import { copy } from '@/common/util';

const { t } = useI18n();
const common = useCommon();

const isShow = ref<boolean>(false);
const filterData = ref<any>({
  resource_name: '',
  time_start: '',
  time_end: '',
});
const dateTimeRange = ref([]);
const dateKey = ref<string>('dateKey');
const topDatePicker = ref(null);
const AccessLogStore = useAccessLog();
const shortcutSelectedIndex = shallowRef(-1);
const tableRef = ref(null);
const resourceEditorRef: any = ref<InstanceType<typeof editorMonaco>>();
const tableList = ref<any>([]);
const tableEmptyConf = reactive<any>({
  keyword: '',
  isAbnormal: false,
});
let expandIds: number[] = [];
const pagination = ref<{count: number, limit: number}>({ count: 0, limit: 10 });
const tabList = ref([
  {
    name: t('请求代码'),
    id: 'code',
  },
  {
    name: t('请求URL'),
    id: 'url',
  },
  {
    name: 'Request Header',
    id: 'requestHeader',
  },
  {
    name: 'Request Body',
    id: 'requestBody',
  },
  {
    name: 'Response Body',
    id: 'responseBody',
  },
]);
const requestHeaderCols = [
  {
    label: t('名称'),
    field: 'name',
  },
  {
    label: t('值'),
    field: 'value',
  },
];

const handleTabClick = (row: Record<string, any>, id: string) => {
  row.activeIndex = id;
};

const handleCopyDetails = (row: Record<string, any>) => {
  const { activeIndex } = row;

  let copyValue = '';
  switch (activeIndex) {
    case 'code':
      copyValue = row.editorText;
      break;
    case 'url':
      copyValue = row.request.request_url;
      break;
    case 'requestBody':
      copyValue = row.requestBody;
      break;
    case 'responseBody':
      copyValue = row.responseBody;
      break;
  }

  copy(copyValue);
};

const getRequestHeader = (row: Record<string, any>) => {
  if (!row) return [];

  const { headers } = row.request;
  const keys = Object.keys(headers);

  if (!keys?.length) {
    return [];
  }

  return keys.map((key) => {
    return {
      name: key,
      value: headers[key],
    };
  });
};

const updateTableEmptyConfig = () => {
  if (filterData.value.resource_name || filterData.value.time_end) {
    tableEmptyConf.keyword = 'placeholder';
    return;
  }
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

const handleShowDetails = async (e: Event, row: Record<string, any>) => {
  e.stopPropagation();
  if (!row.isExpand) {
    await getDetails(row.id, row);
  } else {
    row.isExpand = !row.isExpand;
    expandIds = expandIds.filter((id: number) => id !== row.id);
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
  const response = await getTestHistories(common.apigwId, data);
  response?.forEach((item: any) => {
    item.editorText = '';
    item.requestBody = '';
    item.responseBody = '';
    item.activeIndex = 'code';
  });
  tableList.value = response;
  pagination.value.count = response?.length || 0;
  updateTableEmptyConfig();
};

const handleClearFilterKey = () => {
  clear();
  getList();
  dateKey.value = String(+new Date());
};

const getDetails = async (id: number, row: Record<string, any>) => {
  const response = await getTestHistoriesDetails(common.apigwId, id);

  row.editorText = response?.response?.data?.curl;
  row.requestBody = response?.request?.body;
  row.responseBody = response?.response?.data?.body;
  row.isExpand = !row.isExpand;
  expandIds.push(id);
  nextTick(() => {
    const editorTextLen = Math.ceil(row.editorText?.length / 200);
    const requestBodyLen = Math.ceil(row.requestBody?.length / 200);
    const responseBodyLen = Math.ceil(row.responseBody?.length / 200);

    const styleElement = document.createElement('style');
    styleElement.textContent = `
      .code-${row.id} {
        height: ${editorTextLen * 100}px !important;
      }
      .request-body-${row.id} {
        height: ${requestBodyLen * 100}px !important;
      }
      .response-body-${row.id} {
        height: ${responseBodyLen * 100}px !important;
      }
    `;
    document.head.appendChild(styleElement);

    tableRef.value.setRowExpand(row,  row.isExpand);
  });
};

const handleRowClick = (e: Event, row: Record<string, any>) => {
  handleShowDetails(e, row);
};

// const getCellClass = (_column: any, _index: number, row: any) => {
//   if (expandIds.includes(row.id)) {
//     return 'td-highlight-bg';
//   }
//   return '';
// };

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
}
.sutra-scrollbar {
  :deep(.bk-modal-content) {
    scrollbar-gutter: auto;
  }
  :deep(.bk-table-body) {
    scrollbar-gutter: auto;
  }
}

.details-tab {
  max-height: 600px;
  background: #f5f7fa;
  .tab-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    .header-title {
      display: flex;
      align-items: center;
    }
    .header-copy {
      color: #4D4F56;
      margin-right: 18px;
      cursor: pointer;
    }
    .title {
      font-size: 12px;
      color: #313238;
      font-family: PingFangSC-Regular;
      font-weight: Regular;
      padding: 8px 24px;
      cursor: pointer;
      position: relative;
      &:not(:nth-last-child(1)) {
        &::after {
          content: ' ';
          position: absolute;
          right: 0;
          top: 50%;
          transform: translateY(-50%);
          width: 1px;
          height: 10px;
          background: #DCDEE5;
        }
      }
      &.active {
        font-family: PingFangSC-Semibold;
        font-weight: bold;
        color: #313238;
        &::before {
          content: ' ';
          position: absolute;
          top: 0;
          left: 50%;
          transform: translateX(-50%);
          width: 96px;
          height: 2px;
          background: #313238;
        }
      }
    }
  }
  .tab-content {
    .code,
    .request-body,
    .response-body {
      width: 100%;
      transition: all, .1s;
      min-height: 100px;
      max-height: 400px;
    }
    .response-body {
      min-height: 250px;
    }
    .request-url {
      padding: 12px 24px 24px;
      .tag {
        font-size: 10px;
        color: #299E56;
        background: #DAF6E5;
        border-radius: 8px;
        padding: 1px 4px;
      }
      .url {
        font-size: 12px;
        color: #313238;
        margin-left: 4px;
      }
    }
    .request-header {
      padding: 12px 24px 24px;
      border: 1px solid #F0F1F5;
    }
  }
}
</style>

<style lang="scss">
/* .td-highlight-bg {
  background: #f5f7fa !important;
} */

.request-header-table.bk-table .bk-table-body table tbody tr td {
  background: none !important;
}

.content-item {
  .monaco-editor, .monaco-editor-background, .monaco-editor .inputarea.ime-input {
    background-color: #f5f7fa !important;
  }
  .monaco-editor .margin {
    background-color: #f5f7fa !important;
  }
  .monaco-editor .line-numbers {
    color: #979BA5 !important;
  }
  .monaco-editor .current-line ~ .line-numbers {
    color: #979BA5 !important;
  }
}

</style>
