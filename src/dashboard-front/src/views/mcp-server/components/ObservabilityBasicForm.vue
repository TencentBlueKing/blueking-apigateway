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
  <div class="observability-basic-form">
    <BkForm
      class="collapse-panel-form"
      form-type="vertical"
    >
      <BkFormItem
        :label="t('起止时间')"
        class="ag-form-item-datepicker"
      >
        <DatePicker
          :key="dateKey"
          ref="datePickerRef"
          v-model="dateValue"
          type="datetimerange"
          :clearable="false"
          :placeholder="t('选择日期时间范围')"
          use-shortcut-text
          :shortcuts="shortcutsRange"
          :shortcut-selected-index="shortcutSelectedIndex"
          @change="handleChange"
          @shortcut-change="handleShortcutChange"
          @pick-success="handlePickerConfirm"
          @selection-mode-change="handleSelectionModeChange"
        />
      </BkFormItem>
      <BkFormItem label="MCP Server">
        <BkSelect
          v-model="searchParams.mcp_server_name"
          :placeholder="t('请选择 MCP Server')"
          :scroll-loading="scrollLoading"
          :remote-method="handleMcpServerSearch"
          filterable
          @change="handleQuery"
          @scroll-end="handleMcpServerScrollEnd"
        >
          <BkOption
            v-for="server of mcpServerList"
            :id="server.name"
            :key="server.name"
            :name="server.name"
          />
        </BkSelect>
      </BkFormItem>
      <BkFormItem :label="t('状态')">
        <BkSelect
          v-model="searchParams.status"
          :clearable="false"
          @change="handleQuery"
        >
          <BkOption
            v-for="status of STATUS_LIST"
            :id="status.id"
            :key="status.id"
            :name="status.name"
          />
        </BkSelect>
      </BkFormItem>
      <BkFormItem label="app_code">
        <BkSelect
          v-model="searchParams.app_code"
          filterable
          @change="handleQuery"
        >
          <BkOption
            v-for="appCode of appCodeList"
            :id="appCode"
            :key="appCode"
            :name="appCode"
          />
        </BkSelect>
      </BkFormItem>
      <BkFormItem label="request_id">
        <BkInput
          v-model="searchParams.request_id"
          :placeholder="t('请输入 request_id')"
          clearable
          @enter="fetchSearchData"
          @clear="handleRequestIdClear"
        />
      </BkFormItem>
      <BkFormItem
        :label="t('查询语句')"
        class="ag-form-item-inline"
      >
        <QueryStatement
          v-model:local-value="searchParams.query"
          @choose="handleChoose"
          @search="handleSearch"
        />
      </BkFormItem>
      <BkFormItem
        class="mb-0! form-btn-group"
        label=""
      >
        <BkButton
          theme="primary"
          @click="() => handleSearch(searchParams.query)"
        >
          {{ t('查询') }}
        </BkButton>
        <BkButton
          class="ml-8px"
          @click="handleClearFilter"
        >
          {{ t('重置') }}
        </BkButton>
      </BkFormItem>
    </BkForm>
    <!-- 检索项 -->
    <div
      v-show="searchConditions.length > 0"
      class="collapse-search-term"
    >
      <Funnel class="icon" />
      <span class="title">{{ t('检索项：') }}</span>
      <BkTag
        v-for="tag of searchConditions"
        :key="tag"
        class="search-term-tag"
        closable
        @close="() => handleTagClose(tag)"
      >
        <span v-bk-xss-html="generateTagContent(tag)" />
      </BkTag>
      <BkButton
        theme="primary"
        text
        @click.stop="handleClearFilter"
      >
        <AgIcon
          name="delet"
          class="color-#3a84ff!"
        />
        {{ t('清除') }}
      </BkButton>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { cloneDeep, debounce, uniq } from 'lodash-es';
import { DatePicker } from 'bkui-vue';
import { Funnel } from 'bkui-vue/lib/icon';
import { useStorage } from '@vueuse/core';
import { t } from '@/locales';
import { STATUS_LIST } from '@/constants';
import { useAccessLog } from '@/stores';
import { useDatePicker } from '@/hooks';
import { filterSimpleEmpty } from '@/utils/filterEmptyValues';
import { type IObservabilityBasicForm, fetchObservabilityAppCode } from '@/services/source/observability';
import { getServers } from '@/services/source/mcp-server';
import QueryStatement from '@/views/mcp-server/components/QueryStatement.vue';

interface IProps {
  apiGatewayId: string | number
  mode: string
}

interface IEmits { request: [void] };

const searchParams = defineModel<IObservabilityBasicForm>('searchParams', { type: Object });
const includeQuery = defineModel('includeQuery', {
  type: Array,
  default: () => [],
});
const excludeQuery = defineModel('excludeQuery', {
  type: Array,
  default: () => [],
});

const { apiGatewayId, mode } = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const queryHistory = useStorage('observability-flow-log-query-history', []);
const accessLogStore = useAccessLog();

const datePickerRef = ref<InstanceType<typeof DatePicker>>();
const scrollLoading = ref(false);
const mcpServerName = ref('');
const dateKey = ref('dateKey');
const defaultPagination = ref({
  limit: 10,
  current: 1,
  count: 0,
  hasNoMore: false,
});
const mcpServerPagination = ref(cloneDeep(defaultPagination.value));

const mcpServerList = shallowRef([]);
const appCodeList = shallowRef([]);

const {
  dateValue,
  shortcutsRange,
  shortcutSelectedIndex,
  handleChange,
  handleConfirm,
  handleShortcutChange,
  handleSelectionModeChange,
} = useDatePicker(searchParams);

// 获取检索项
const searchConditions = computed(() => {
  const results: string[] = [];
  includeQuery.value?.forEach((item: string) => {
    const tempArr = item?.split(':');
    results.push(`${tempArr[0]}=${tempArr[1]}`);
  });
  excludeQuery.value?.forEach((item: string) => {
    const tempArr = item?.split(':');
    results.push(`${tempArr[0]}!=${tempArr[1]}`);
  });
  return results;
});

// 获取MCP Server列表
const fetchMcpServerList = async () => {
  const { hasNoMore, current, limit } = mcpServerPagination.value;
  scrollLoading.value = true;

  if (hasNoMore) {
    scrollLoading.value = false;
    return;
  };

  try {
    const params = {
      limit,
      offset: limit * (current - 1),
      keyword: mcpServerName.value,
    };
    const res = await getServers(apiGatewayId, filterSimpleEmpty(params));
    const { results = [], count = 0 } = res ?? {};
    mcpServerList.value = current === 1 ? results : [...mcpServerList.value, ...results];
    mcpServerPagination.value = {
      ...mcpServerPagination.value,
      count,
      hasNoMore: mcpServerList.value.length >= count,
      current: current + 1,
    };
  }
  catch {
    mcpServerPagination.value = cloneDeep(defaultPagination.value);
    mcpServerList.value = [];
  }
  finally {
    scrollLoading.value = false;
  }
};

// 获取AppCode列表
const fetchMcpAppCodeList = async () => {
  try {
    const res = await fetchObservabilityAppCode(apiGatewayId);
    appCodeList.value = res?.bk_app_codes ?? [];
  }
  catch {
    appCodeList.value = [];
  }
};

const formatDatetime = (timeRange: number[]) => {
  return [+new Date(`${timeRange[0]}`) / 1000, +new Date(`${timeRange[1]}`) / 1000];
};

// 设置日期选择
const handleSearchTimeRange = () => {
  let timeRange = dateValue.value;
  // 选择的是时间快捷项，需要实时计算时间值
  if (shortcutSelectedIndex.value !== -1) {
    timeRange = accessLogStore.datepickerShortcuts[shortcutSelectedIndex.value].value();
  }
  const formatTimeRange = formatDatetime(timeRange);
  searchParams.value = Object.assign(searchParams.value, {
    time_start: formatTimeRange?.at(0),
    time_end: formatTimeRange?.at(1),
  });
};

const generateTagContent = (tag: string) => {
  if (!tag) {
    return;
  }

  if (tag.indexOf('!=') !== -1) {
    return tag.replace('!=', '<span class="exclude-equal">!=</span>');
  }

  return tag.replace('=', '<span class="include-equal">=</span>');
};

const fetchSearchData = () => {
  handleSearchTimeRange();
  emit('request');
};

const handleQuery = () => {
  // 只有仪表盘tab切换表单项才需要实时刷新接口
  if (!['Dashboard'].includes(mode)) return;

  fetchSearchData();
};

// 搜索McpServer列表
const handleMcpServerSearch = debounce((value: string) => {
  mcpServerName.value = value;
  mcpServerPagination.value = cloneDeep(defaultPagination.value);
  fetchMcpServerList();
}, 200);

// 滚动加载MCP Server
const handleMcpServerScrollEnd = debounce(() => {
  const { hasNoMore } = mcpServerPagination.value;
  if (hasNoMore) return;
  fetchMcpServerList();
}, 200);

const handleRequestIdClear = () => {
  searchParams.value.request_id = '';
  fetchSearchData();
};

const handlePickerConfirm = () => {
  handleConfirm();
  fetchSearchData();
};

const handleChoose = (value: string) => {
  searchParams.value.query = value;
};

const handleSearch = (value: string) => {
  // 若是非空字符串则写入搜索历史
  if (value?.trim?.() !== '') {
    queryHistory.value.unshift(value);
    queryHistory.value = uniq(queryHistory.value).slice(0, 10);
  }
  fetchSearchData();
};

// 移除检索项
const handleTagClose = (tag: string) => {
  if (!tag) return;

  if (tag?.indexOf('!=') !== -1) {
    const tagList = tag?.split('!=');
    const field = `${tagList[0]}:${tagList[1]}`;

    const index = excludeQuery.value?.indexOf(field);
    if (index !== -1) {
      excludeQuery.value?.splice(index, 1);
    }
  }
  else {
    const tagList = tag?.split('=');
    const field = `${tagList[0]}:${tagList[1]}`;

    const index = includeQuery.value?.indexOf(field);
    if (index !== -1) {
      includeQuery.value?.splice(index, 1);
    }
  }
};

const handleClearFilter = () => {
  searchParams.value = Object.assign(searchParams.value, {
    query: '',
    request_id: '',
    mcp_server_name: '',
    app_code: '',
    status: 'all',
  });
  [datePickerRef.value.shortcut] = [accessLogStore.datepickerShortcuts[0]];
  dateValue.value = [];
  shortcutSelectedIndex.value = 0;
  dateKey.value = String(+new Date());
  fetchSearchData();
};

// 请求数组件图表调用的同步更新数据
const syncDateFromChart = (dateInfo) => {
  if (dateInfo?.dateValue?.length) {
    shortcutSelectedIndex.value = -1;
    dateValue.value = dateInfo.dateValue;
  }
  else {
    dateValue.value = [];
    shortcutSelectedIndex.value = 0;
    [datePickerRef.value.shortcut] = [accessLogStore.datepickerShortcuts[0]];
  }
  dateKey.value = String(+new Date());

  handlePickerConfirm();
};

onMounted(() => {
  handleSearchTimeRange();
  Promise.allSettled([fetchMcpAppCodeList(), fetchMcpServerList()]);
});

defineExpose({
  syncDateFromChart,
  handleClearFilter,
});
</script>

<style lang="scss" scoped>
.observability-basic-form {
  padding: 0 24px 0 46px;
  box-sizing: border-box;

  .collapse-panel-form {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0 16px;
    box-sizing: border-box;

    .bk-form-item {
      flex: 1;
      box-sizing: border-box;

      .bk-form-content {
        width: 100%;

        .bk-date-picker {
          width: 100%;

          :deep(.bk-picker-confirm-action) {

            a:first-child {
              display: none;
            }
          }
        }
      }

      &.form-btn-group {
        flex: 0 0 100%;
      }
    }
  }

  .collapse-search-term {
    display: flex;
    align-items: center;
    margin-top: 24px;

    .icon {
      margin-right: 4px;
      font-size: 16px;
      color: #979ba5;
    }

    .title {
      font-size: 12px;
      color: #000000;
    }

    :deep(.search-term-tag) {
      background-color: #eae8f0;
      color: #4d4f56;

      .include-equal,
      .exclude-equal {
        font-size: 14px;
        font-weight: bold;
      }

      .exclude-equal {
        color: #ea3636;
      }

      .include-equal {
        color: #2dcb56;
      }

      &:not(:nth-last-child(1)) {
        margin-right: 8px;
      }
    }
  }
}
</style>
