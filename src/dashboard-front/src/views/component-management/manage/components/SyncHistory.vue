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
            v-model="dateValue"
            style="width: 320px;"
            :placeholder="t('选择日期时间范围')"
            type="datetimerange"
            use-shortcut-text
            :shortcuts="shortcutsRange"
            :shortcut-selected-index="shortcutSelectedIndex"
            @change="handleChange"
            @shortcut-change="handleShortcutChange"
            @clear="handlePickClear"
            @pick-success="handlePickSuccess"
            @selection-mode-change="handleSelectionModeChange"
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
import { Button, Loading } from 'bkui-vue';
import { useDatePicker, useMaxTableLimit, useQueryList } from '@/hooks';
import { OPERATE_STATUS_MAP } from '@/enums';
import { type ISyncHistoryItem, getSyncHistory } from '@/services/source/componentManagement';
import TableEmpty from '@/components/table-empty/Index.vue';

const router = useRouter();
const { t, locale } = useI18n();
const { maxTableLimit, clientHeight } = useMaxTableLimit({ allocatedHeight: 195 });

const dateKey = ref('dateKey');
const tableColumns = ref([
  {
    label: 'ID',
    field: 'resource_version_title',
    render: ({ row }: { row?: Partial<ISyncHistoryItem> }) => {
      return (
        <Button
          theme="primary"
          class="m-rr-10px"
          text
          onClick={() => handleVersion(row?.id)}
        >
          { row?.id || '--' }
        </Button>
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

const {
  dateValue,
  shortcutsRange,
  shortcutSelectedIndex,
  handleChange,
  handleClear,
  handleConfirm,
  handleShortcutChange,
  handleSelectionModeChange,
} = useDatePicker(searchParams);

const updateTableEmptyConfig = () => {
  const isEmpty = dateValue.value?.some(Boolean);
  if (isEmpty) {
    tableEmptyConf.value.emptyType = 'searchEmpty';
    return;
  }
  tableEmptyConf.value.emptyType = '';
};

const handlePickClear = () => {
  handleClear();
  handleTimeClear();
};

const handlePickSuccess = () => {
  handleConfirm();
  updateTableEmptyConfig();
};

const handleClearFilterKey = () => {
  handlePickClear();
  dateKey.value = String(+new Date());
  pagination.value = Object.assign(pagination.value, {
    current: 1,
    limit: 10,
  });
};

const handleVersion = (id: string) => {
  router.push({
    name: 'SyncVersion',
    query: { id },
  });
};

const handleTimeClear = () => {
  pagination.value.current = 1;
  updateTableEmptyConfig();
};
</script>
