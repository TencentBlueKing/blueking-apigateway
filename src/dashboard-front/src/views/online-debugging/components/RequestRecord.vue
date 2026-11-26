/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
  <AgSideslider
    v-model="isShow"
    :title="t('调用历史')"
    :scrollbar="false"
    ext-cls="sutra-scrollbar"
  >
    <template #default>
      <div class="history-container">
        <div class="history-search">
          <BkInput
            v-model="filterData.resource_name"
            class="search-input"
            type="search"
            :placeholder="t('请输入资源名称')"
            @enter="getList()"
            @input="handleInput"
          />
          <BkDatePicker
            ref="topDatePicker"
            :key="dateKey"
            v-model="dateValue"
            class="search-date"
            :placeholder="t('选择日期时间范围')"
            type="datetimerange"
            :shortcuts="shortcutsRange"
            use-shortcut-text
            :shortcut-selected-index="shortcutSelectedIndex"
            @shortcut-change="handleShortcutChange"
            @change="handleChange"
            @clear="handlePickClear"
            @pick-success="handlePickSuccess"
            @selection-mode-change="handleSelectionModeChange"
          />
        </div>

        <div class="history-data">
          <AgTable
            ref="tableRef"
            v-model:table-data="tableData"
            cache-identifier="OnlineDebugging"
            row-class-name="cursor-pointer"
            :columns="columns"
            resizable
            show-settings
            expand-on-row-click
            :expanded-row-keys="expandedRowKeys"
            :filter-value="filterData"
            local-page
            :immediate="false"
            @expand-change="handleExpandChange"
            @clear-filter="handleClearFilterKey"
          >
            <template #expandedRow="{ row }">
              <div class="details-tab">
                <div class="tab-header">
                  <div class="header-title">
                    <div
                      v-for="item in tabList"
                      :key="item.id"
                      class="title"
                      :class="{ 'active': item.id === row?.activeIndex }"
                      @click="() => handleTabClick(row, item.id)"
                    >
                      {{ item.name }}
                    </div>
                  </div>
                  <div
                    v-show="!['requestHeader', 'responseHeader'].includes(row?.activeIndex ?? '')"
                    class="header-copy"
                  >
                    <CopyShape @click="() => handleCopyDetails(row)" />
                  </div>
                </div>
                <div class="tab-content">
                  <div
                    v-show="row?.activeIndex === 'code'"
                    class="content-item code"
                    :class="`code-${row?.id}`"
                  >
                    <AgCodeEditor
                      v-if="row?.editorText"
                      ref="resourceEditorRef"
                      v-model="row.editorText"
                      theme="Visual Studio"
                      language="json"
                      :minimap="false"
                      :show-copy="false"
                      read-only
                    />
                  </div>

                  <div
                    v-show="row?.activeIndex === 'url'"
                    class="content-item request-url"
                  >
                    <span class="tag">{{ row?.request?.request_method }}</span>
                    <span class="url">{{ row?.request?.request_url }}</span>
                  </div>

                  <div
                    v-show="row?.activeIndex === 'requestHeader'"
                    class="content-item request-header"
                  >
                    <AgTable
                      class="request-header-table"
                      size="small"
                      max-height="400px"
                      table-row-key="name"
                      :immediate="false"
                      :show-pagination="false"
                      :show-settings="false"
                      :table-data="row?.requestHeaderList ?? []"
                      :columns="requestHeaderCols"
                    />
                  </div>

                  <div
                    v-show="row?.activeIndex === 'requestBody'"
                    class="content-item request-body"
                    :class="`request-body-${row?.id}`"
                  >
                    <AgCodeEditor
                      v-if="row?.requestBody"
                      v-model="row.requestBody"
                      theme="Visual Studio"
                      language="json"
                      :minimap="false"
                      :show-copy="false"
                      read-only
                    />
                  </div>

                  <div
                    v-show="row?.activeIndex === 'responseBody'"
                    class="content-item response-body"
                    :class="`response-body-${row?.id}`"
                  >
                    <AgCodeEditor
                      v-if="row?.responseBody"
                      v-model="row.responseBody"
                      theme="Visual Studio"
                      language="json"
                      :minimap="false"
                      :show-copy="false"
                      read-only
                    />
                  </div>

                  <div
                    v-show="row?.activeIndex === 'responseHeader'"
                    class="content-item request-header"
                  >
                    <AgTable
                      class="request-header-table"
                      size="small"
                      max-height="400px"
                      table-row-key="name"
                      :immediate="false"
                      :show-pagination="false"
                      :show-settings="false"
                      :table-data="row?.responseHeaderList ?? []"
                      :columns="requestHeaderCols"
                    />
                  </div>
                </div>
              </div>
            </template>
          </AgTable>
        </div>
      </div>
    </template>
  </AgSideslider>
</template>

<script lang="tsx" setup>
import { useGateway } from '@/stores';
import { RECENT_DATE_PRESETS, useDatePicker } from '@/hooks';
import AgCodeEditor from '@/components/base/ag-code-editor/Index.vue';
import AgSideslider from '@/components/base/ag-sideslider/Index.vue';
import AgTable, {
  type ExpandOptions,
  type IAgTableInstance,
  type ITableColumn,
  type TableRow,
} from '@/components/base/ag-table';
import { getApiTestHistoryDetail, getApiTestHistoryList } from '@/services/source/gateway/api-test';
import type { IAPIDebugHistoriesListOutput } from '@/services/types/gateway/api-test';
import { createNameValueColumns, objectToKvRows } from '@/views/online-debugging/utils';
import { CopyShape } from 'bkui-vue/lib/icon';
import { copy } from '@/utils';
import { toTimeRangeQuery } from '@/utils/time-range';
import type { ITimeRangeFilter } from '@/types/common';

interface IRequestRecordFilter extends ITimeRangeFilter {
  resource_name: string
}

interface IHeaderRow {
  name: string
  value: unknown
}

interface IRequestRecordRow extends IAPIDebugHistoriesListOutput {
  activeIndex?: string
  editorText?: string
  requestBody?: string
  responseBody?: string
  requestHeaderList?: IHeaderRow[]
  responseHeaderList?: IHeaderRow[]
}

const emit = defineEmits<{ retry: [data: IRequestRecordRow] }>();
const { t } = useI18n();
const gatewayStore = useGateway();

const isShow = ref<boolean>(false);
const filterData = ref<IRequestRecordFilter>({
  resource_name: '',
  time_start: '',
  time_end: '',
});

const {
  dateValue,
  shortcutsRange,
  shortcutSelectedIndex,
  handleChange,
  handleClear,
  resetSelection,
  handleConfirm,
  handleShortcutChange,
  handleSelectionModeChange,
} = useDatePicker(filterData, { presets: RECENT_DATE_PRESETS });

const dateKey = ref<string>('dateKey');
const topDatePicker = useTemplateRef('topDatePicker');
const tableData = ref<IRequestRecordRow[]>([]);
const expandedRowKeys = ref<Array<string | number>>([]);
const tableRef = useTemplateRef<IAgTableInstance<IRequestRecordRow>>('tableRef');
const resourceEditorRef: any = useTemplateRef<InstanceType<typeof AgCodeEditor>>('resourceEditorRef');
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
  {
    name: 'Response Header',
    id: 'responseHeader',
  },
]);
const requestHeaderCols: ITableColumn<IHeaderRow>[] = createNameValueColumns(t);

const columns = shallowRef<ITableColumn<IRequestRecordRow>[]>([
  {
    title: t('资源名称'),
    colKey: 'resource_name',
    ellipsis: true,
  },
  {
    title: t('响应状态码'),
    colKey: 'status_code',
    ellipsis: true,
    width: 120,
    cell: (_h, { row }) => (
      <div>
        <span
          class={[String(row.response?.data?.status_code)?.startsWith('2') ? 'dot success' : 'dot failure']}
        />
        { row.response?.data?.status_code }
      </div>
    ),
  },
  {
    title: t('耗时'),
    colKey: 'proxy_time',
    ellipsis: true,
    width: 120,
    cell: (_h, { row }) => (
      <span>
        { row.response?.data?.proxy_time }
        ms
      </span>
    ),
  },
  {
    title: t('调用时间'),
    colKey: 'created_time',
    ellipsis: true,
  },
  {
    title: t('操作'),
    colKey: 'act',
    width: 140,
    cell: (_h, { row }) => (
      <div class="flex items-center">
        <bk-button
          theme="primary"
          class="mr-10px"
          text
          onClick={(e: MouseEvent) => handleShowDetails(e, row)}
        >
          { t('请求详情') }
        </bk-button>
        <bk-button
          theme="primary"
          text
          onClick={(e: MouseEvent) => handleRetry(e, row)}
        >
          { t('去重试') }
        </bk-button>
      </div>
    ),
  },
]);

const apigwId = computed(() => gatewayStore.apigwId);

const handleTabClick = (row: IRequestRecordRow, id: string) => {
  row.activeIndex = id;
};

const handleCopyDetails = (row: IRequestRecordRow) => {
  const { activeIndex } = row;

  let copyValue = '';
  switch (activeIndex) {
    case 'code':
      copyValue = row.editorText ?? '';
      break;
    case 'url':
      copyValue = row.request?.request_url ?? '';
      break;
    case 'requestBody':
      copyValue = row.requestBody ?? '';
      break;
    case 'responseBody':
      copyValue = row.responseBody ?? '';
      break;
  }

  copy(copyValue);
};

const formatHeaders = (headers?: Record<string, any>): IHeaderRow[] => objectToKvRows(headers ?? {});

const getRequestHeader = (row: IAPIDebugHistoriesListOutput): IHeaderRow[] => {
  if (!row) return [];

  return formatHeaders(row.request?.headers);
};

const getResponseHeader = (row: IAPIDebugHistoriesListOutput): IHeaderRow[] => {
  if (!row) return [];

  return formatHeaders(row.response?.data?.headers);
};

const handlePickClear = () => {
  handleClear();
  getList();
};

const handlePickSuccess = () => {
  if (!handleConfirm()) {
    return;
  }
  getList();
};

const clear = () => {
  filterData.value.resource_name = '';
  filterData.value.time_start = '';
  filterData.value.time_end = '';
  resetSelection();
  expandedRowKeys.value = [];
};

const show = () => {
  clear();
  isShow.value = true;
  getList();
};

const getList = async () => {
  const { resource_name } = filterData.value;
  // 后端直接把时间按整数解析：只在两端都是有效秒数时成对传，不传空字符串
  const data = {
    offset: 0,
    limit: 10000,
    resource_name: resource_name || undefined,
    ...toTimeRangeQuery(filterData.value),
  };
  const results = await getApiTestHistoryList(apigwId.value, data);

  tableData.value = (results || []).map(item => ({
    ...item,
    editorText: '',
    requestBody: '',
    responseBody: '',
    activeIndex: 'code',
    requestHeaderList: getRequestHeader(item),
    responseHeaderList: getResponseHeader(item),
  }));
};

const handleClearFilterKey = () => {
  clear();
  getList();
  dateKey.value = String(+new Date());
};

const handleInput = () => {
  if (!filterData.value.resource_name) {
    getList();
  }
};

const getDetails = async (id: number, row: IRequestRecordRow) => {
  const response = await getApiTestHistoryDetail(apigwId.value, id);

  row.editorText = response?.response?.data?.curl ?? '';
  row.requestBody = response?.request?.body ?? '';
  row.responseBody = response?.response?.data?.body ?? '';

  nextTick(() => {
    const editorTextLen = Math.ceil((row.editorText?.length ?? 0) / 200);
    const requestBodyLen = Math.ceil((row.requestBody?.length ?? 0) / 200);
    const responseBodyLen = Math.ceil((row.responseBody?.length ?? 0) / 200);

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
  });
};

const handleShowDetails = async (event: Event, row: IRequestRecordRow) => {
  event.stopPropagation();

  if (!expandedRowKeys.value.includes(row.id)) {
    await getDetails(row.id, row);
    expandedRowKeys.value.push(row.id);
  }
  else {
    expandedRowKeys.value = expandedRowKeys.value.filter((id: number | string) => id !== row.id);
  }
};

const handleExpandChange = async (
  expandedKeys: Array<string | number>,
  expandedRowData: ExpandOptions<TableRow<IRequestRecordRow>>,
) => {
  expandedRowKeys.value = expandedKeys;
  const { currentRowData } = expandedRowData;

  if (expandedRowKeys.value.includes(currentRowData.id)) {
    await getDetails(currentRowData.id, currentRowData);
  }
};

const handleRetry = (event: Event, row: IRequestRecordRow) => {
  event.stopPropagation();
  emit('retry', row);
  isShow.value = false;
};

defineExpose({ show });
</script>

<style lang="scss" scoped>
.history-container {
  height: calc(100vh - 52px);
  padding: 20px 24px;
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

}

.details-tab {
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
      margin-right: 18px;
      color: #4D4F56;
      cursor: pointer;
    }

    .title {
      position: relative;
      padding: 8px 24px;
      font-family: PingFangSC-Regular, sans-serif;
      font-size: 12px;
      font-weight: regular;
      color: #313238;
      cursor: pointer;

      &:not(:nth-last-child(1)) {

        &::after {
          position: absolute;
          top: 50%;
          right: 0;
          width: 1px;
          height: 10px;
          background: #DCDEE5;
          content: ' ';
          transform: translateY(-50%);
        }
      }

      &.active {
        font-family: PingFangSC-Semibold, sans-serif;
        font-weight: bold;
        color: #313238;

        &::before {
          position: absolute;
          top: 0;
          left: 50%;
          width: 96px;
          height: 2px;
          background: #313238;
          content: ' ';
          transform: translateX(-50%);
        }
      }
    }
  }

  .tab-content {

    .code,
    .request-body,
    .response-body {
      width: 100%;
      max-height: 400px;
      min-height: 100px;
      transition: all, .1s;
    }

    .response-body {
      min-height: 250px;
    }

    .request-url {
      padding: 12px 24px 24px;

      .tag {
        padding: 1px 4px;
        font-size: 10px;
        color: #299E56;
        background: #DAF6E5;
        border-radius: 8px;
      }

      .url {
        margin-left: 4px;
        font-size: 12px;
        color: #313238;
      }
    }

    .request-header {
      padding: 12px 24px 24px;
      border: 1px solid #F0F1F5;
    }
  }
}

.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 2px;
  vertical-align: middle;
  border-radius: 50%;

  &.warning {
    background: #FFF3E1;
    border: 1px solid #FF9C01;
  }

  &.success {
    background: #E5F6EA;
    border: 1px solid #3FC06D;
  }

  &.failure {
    background: #FFE6E6;
    border: 1px solid #EA3636;
  }
}
</style>

<!-- eslint-disable-next-line vue/enforce-style-attribute -- 覆盖 Monaco Editor 与请求记录表格全局样式 -->
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
