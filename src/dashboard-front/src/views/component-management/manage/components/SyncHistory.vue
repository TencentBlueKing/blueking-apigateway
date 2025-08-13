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
  <div class="apigw-access-manager-wrapper">
    <div class="p-24px wrapper">
      <BkForm
        form-type="inline"
        class="m-b-16px"
      >
        <BkFormItem
          :label="t('选择时间')"
          :label-width="locale === 'zh-cn' ? 86 : 100"
        >
          <BkDatePicker
            :key="dateKey"
            v-model="dateTimeRange"
            style="width: 320px;"
            :placeholder="t('选择日期时间范围')"
            type="datetimerange"
            :shortcuts="datepickerShortcuts"
            shortcut-close
            use-shortcut-text
            :shortcut-selected-index="shortcutSelectedIndex"
            @shortcut-change="handleShortcutChange"
            @clear="handleTimeClear"
            @pick-success="handleTimeChange"
            @change="handleTimeChange"
          />
        </BkFormItem>
      </BkForm>
      <BkLoading
        :loading="isLoading"
        :opacity="1"
      >
        <BkTable
          size="small"
          border="outer"
          :data="tableData"
          :columns="tableColumns"
          :max-height="clientHeight"
          :pagination="pagination"
          remote-pagination
          show-overflow-tooltip
          @page-value-change="handlePageChange"
          @page-limit-change="handlePageSizeChange"
        >
          <template #empty>
            <TableEmpty
              :empty-type="tableEmptyConf.emptyType"
              :abnormal="tableEmptyConf.isAbnormal"
              @refresh="getList"
              @clear-filter="handleClearFilterKey"
            />
          </template>
        </BkTable>
      </BkLoading>
    </div>
  </div>
</template>

<script lang="tsx" setup>
import { Loading } from 'bkui-vue';
import { useAccessLog } from '@/stores';
import { useMaxTableLimit, useQueryList } from '@/hooks';
import { OPERATE_STATUS_MAP } from '@/enums';
import { type ISyncHistoryItem, getSyncHistory } from '@/services/source/componentManagement';
import TableEmpty from '@/components/table-empty/Index.vue';
import dayjs from 'dayjs';

const router = useRouter();
const { t, locale } = useI18n();
const { maxTableLimit, clientHeight } = useMaxTableLimit({ allocatedHeight: 195 });
const accessLogStore = useAccessLog();

const datepickerShortcuts = shallowRef(accessLogStore.datepickerShortcuts);

const dateKey = ref('dateKey');
const shortcutSelectedIndex = ref(-1);
const tableColumns = ref([
  {
    label: 'ID',
    field: 'resource_version_title',
    render: ({ row }: { row?: Partial<ISyncHistoryItem> }) => {
      return (
        <BkButton
          theme="primary"
          class="m-rr-10px"
          text
          onClick={() => handleVersion(row?.id)}
        >
          { row?.id || '--' }
        </BkButton>
      );
    },
  },
  {
    label: t('同步时间'),
    field: 'created_time',
  },
  {
    label: t('同步版本号（版本标题）'),
    field: 'resource_version_name',
    render: ({ row }: { row?: Partial<ISyncHistoryItem> }) => {
      return (
        <span>
          { row?.resource_version_display || '--' }
        </span>
      );
    },
  },
  {
    label: t('操作人'),
    field: 'component_name',
    render: ({ row }: { row?: Partial<ISyncHistoryItem> }) => {
      return (
        <span>
          { row?.created_by || '--' }
        </span>
      );
    },
  },
  {
    label: t('操作结果'),
    field: 'status ',
    render: ({ row }: { row?: Partial<ISyncHistoryItem> }) => {
      if (['releasing'].includes(row?.status)) {
        return (
          <span>
            <Loading
              size="mini"
              theme="primary"
              mode="spin"
              class="m-r-5px"
            />
            { t('同步中') }
          </span>
        );
      }
      return (
        <span>
          <span class={`ag-dot ${row?.status} m-r-5px`} />
          { OPERATE_STATUS_MAP[row?.status] }
        </span>
      );
    },
  },
  {
    label: t('操作日志'),
    field: 'message',
    render: ({ row }: { row?: Partial<ISyncHistoryItem> }) => {
      return (
        <span>
          { row?.message || '--' }
        </span>
      );
    },
  },
]);
const dateTimeRange = ref([]);
const searchParams = ref({
  time_start: '',
  time_end: '',
});
const tableEmptyConf = ref({
  emptyType: '',
  isAbnormal: false,
});

const {
  isLoading,
  tableData,
  pagination,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList({
  apiMethod: getSyncHistory,
  filterData: searchParams,
  initialPagination: {
    limitList: [
      maxTableLimit,
      10,
      20,
      50,
      100,
    ],
    limit: maxTableLimit,
  },
  needApigwId: false,
});

const formatDatetime = (timeRange: number[]) => {
  if (!timeRange[0] || !timeRange[1]) {
    return [];
  }
  return [
    (+new Date(`${timeRange[0]}`)) / 1000,
    (+new Date(`${timeRange[1]}`)) / 1000,
  ];
};

const setSearchTimeRange = () => {
  // 选择了同一天，则需要把开始时间的时分秒设置为 00:00:00
  if (dayjs(dateTimeRange.value[0]).isSame(dateTimeRange.value[1])) {
    dateTimeRange.value[0].setHours(0, 0, 0);
  }
  let timeRange = dateTimeRange.value;
  // 选择的是时间快捷项，需要实时计算时间值
  if (shortcutSelectedIndex.value !== -1) {
    timeRange = datepickerShortcuts.value[shortcutSelectedIndex.value].value();
  }
  if (timeRange?.length) {
    const formatTimeRange = formatDatetime(timeRange);
    searchParams.value = Object.assign(searchParams.value, {
      time_start: formatTimeRange?.[0] || '',
      time_end: formatTimeRange?.[1] || '',
    });
  }
  else {
    searchParams.value = {};
  }
};
setSearchTimeRange();

const updateTableEmptyConfig = () => {
  const isEmpty = dateTimeRange.value?.some(Boolean);
  if (isEmpty) {
    tableEmptyConf.value.emptyType = 'searchEmpty';
    return;
  }
  tableEmptyConf.value.emptyType = '';
};

const handleClearFilterKey = () => {
  pagination.value = Object.assign(pagination.value, {
    current: 1,
    limit: 10,
  });
  handleTimeClear();
  dateKey.value = String(+new Date());
};

const handleVersion = (id: string) => {
  router.push({
    name: 'SyncVersion',
    query: { id },
  });
};

const handleShortcutChange = (value: string, index: number) => {
  shortcutSelectedIndex.value = index;
  updateTableEmptyConfig();
};

const handleTimeClear = () => {
  pagination.value.current = 1;
  shortcutSelectedIndex.value = -1;
  dateTimeRange.value = [];
  setSearchTimeRange();
  updateTableEmptyConfig();
};

const handleTimeChange = () => {
  pagination.value.current = 1;
  setSearchTimeRange();
  updateTableEmptyConfig();
};
</script>
