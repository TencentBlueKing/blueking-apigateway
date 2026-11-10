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
            :name="renderMcpDisplayName(server)"
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
          @click="() => handleSearch(searchParams.query ?? '')"
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
import { RECENT_DATE_PRESETS, useDatePicker } from '@/hooks';
import { filterSimpleEmpty } from '@/utils/filterEmptyValues';
import {
  type TimeRangeSeconds,
  intersectTimeRange,
  toTimeRangeSeconds,
} from '@/utils/time-range';
import type { IObservabilityBasicForm } from '@/services/source/gateway/mcp-server/log';
import { getMcpAppPermissionAppCodes } from '@/services/source/gateway/mcp-server/permission';
import { getServers } from '@/services/source/gateway/mcp-server/server';
import QueryStatement from '@/views/mcp-server/components/QueryStatement.vue';

interface IProps {
  apiGatewayId: string | number
  mode: string
}

interface IEmits { request: [void] }

const searchParams = defineModel<IObservabilityBasicForm>('searchParams', {
  type: Object,
  default: () => ({}),
});
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

const route = useRoute();
const queryHistory = useStorage<string[]>('observability-flow-log-query-history', []);

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

const mcpServerList = shallowRef<any[]>([]);
const appCodeList = shallowRef<any[]>([]);

const {
  dateValue,
  shortcutsRange,
  shortcutSelectedIndex,
  handleChange,
  handleConfirm,
  handleShortcutChange,
  handleSelectionModeChange,
  applySelectedRange,
  resetSelection,
} = useDatePicker(searchParams, {
  presets: ['today', ...RECENT_DATE_PRESETS],
  defaultPreset: 'today',
});

// 获取检索项
const searchConditions = computed(() => {
  const results: string[] = [];
  includeQuery.value?.forEach((item: any) => {
    const tempArr = (item as string)?.split(':');
    results.push(`${tempArr[0]}=${tempArr[1]}`);
  });
  excludeQuery.value?.forEach((item: any) => {
    const tempArr = (item as string)?.split(':');
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
  }

  try {
    const params = {
      limit,
      offset: limit * (current - 1),
      keyword: mcpServerName.value,
    };
    const res = await getServers(apiGatewayId as number, filterSimpleEmpty(params));
    const { results = [], count = 0 } = res ?? {};
    mcpServerList.value = current === 1 ? results as any : [...mcpServerList.value, ...results as any];
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
    const res = await getMcpAppPermissionAppCodes(apiGatewayId as number);
    appCodeList.value = res?.bk_app_codes ?? [];
  }
  catch {
    appCodeList.value = [];
  }
};

const renderMcpDisplayName = (option: Record<string, string>) => {
  return option?.title ? `${option.title} (${option.name})` : option.name;
};

/**
 * 设置日期选择：计算本次查询的秒级区间并写入查询参数
 * @returns 是否得到有效区间；无效时不修改查询参数，调用方不应发起查询
 */
const handleSearchTimeRange = () => applySelectedRange();

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
  if (!handleSearchTimeRange()) {
    return;
  }
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

const handlePickerConfirm = () => {
  if (!handleConfirm()) {
    return;
  }
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
  fetchSearchData();
};

const handleClearFilter = () => {
  searchParams.value = Object.assign(searchParams.value ?? {}, {
    query: '',
    mcp_server_name: '',
    app_code: '',
    status: 'all',
  });
  includeQuery.value = [];
  excludeQuery.value = [];
  // 恢复默认快捷项后重建日期组件
  resetSelection();
  dateKey.value = String(+new Date());
  fetchSearchData();
};

// 请求数组件图表调用的同步更新数据：range 为所选柱子的秒级区间，需与当前查询窗口取交集
const syncDateFromChart = (range: TimeRangeSeconds) => {
  const { time_start, time_end } = searchParams.value ?? {};
  const queryRange = typeof time_start === 'number' && typeof time_end === 'number'
    ? toTimeRangeSeconds(time_start * 1000, time_end * 1000)
    : null;
  const selectedRange = queryRange ? intersectTimeRange(range, queryRange) : range;
  if (!selectedRange) {
    return;
  }

  shortcutSelectedIndex.value = -1;
  dateValue.value = [new Date(selectedRange[0] * 1000), new Date(selectedRange[1] * 1000)];
  dateKey.value = String(+new Date());

  handlePickerConfirm();
};

watch(
  () => [
    route.query.mcp_server_name as string | undefined,
    route.query.request_id as string | undefined,
  ],
  ([serverName, requestId]) => {
    const validParams = [serverName, requestId].filter(Boolean);

    if (validParams.length) {
      searchParams.value = {
        ...searchParams.value,
        mcp_server_name: serverName ?? '',
        query: requestId ?? '',
      };
    }
  },
  { immediate: true },
);

onMounted(() => {
  handleSearchTimeRange();
  Promise.allSettled([fetchMcpAppCodeList(), fetchMcpServerList()]);
});

defineExpose({
  syncDateFromChart,
  handleClearFilter,
  handleSearchTimeRange,
});
</script>

<style lang="scss" scoped>
.observability-basic-form {
  padding: 0 24px 0 46px;
  box-sizing: border-box;

  .collapse-panel-form {
    display: flex;
    width: 100%;
    box-sizing: border-box;
    flex-wrap: wrap;
    align-items: center;
    gap: 0 16px;

    .bk-form-item {
      flex: 1;
      box-sizing: border-box;

      .bk-form-content {
        width: 100%;

        .bk-date-picker {
          width: 100%;
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
      color: #000;
    }

    :deep(.search-term-tag) {
      color: #4d4f56;
      background-color: #eae8f0;

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
