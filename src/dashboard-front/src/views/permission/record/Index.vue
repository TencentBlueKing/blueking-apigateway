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
  <div class="permission-record-container page-wrapper-padding">
    <div class="header">
      <BkForm class="flex">
        <BkFormItem
          :label="t('选择时间')"
          :label-width="locale === 'en' ? 108 : 80"
          class="ag-form-item-datepicker m-b-15px"
        >
          <BkDatePicker
            :key="dateKey"
            v-model="dateValue"
            style="width: 320px"
            :placeholder="t('选择日期时间范围')"
            :type="'datetimerange'"
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
          :label="t('授权维度')"
          label-width="108"
        >
          <BkSelect
            v-model="filterData.grant_dimension"
            class="w-150px"
          >
            <BkOption
              v-for="option of AUTHORIZATION_DIMENSION"
              :id="option.id"
              :key="option.id"
              :name="option.name"
            />
          </BkSelect>
        </BkFormItem>
        <BkFormItem
          :label="t('蓝鲸应用ID')"
          class="flex-grow"
          label-width="119"
        >
          <BkInput
            v-model="filterData.bk_app_code"
            :placeholder="t('请输入应用ID，按Enter搜索')"
            clearable
            style="max-width: 320px"
          />
        </BkFormItem>
      </BkForm>
    </div>
    <div class="record-content">
      <BkLoading :loading="isLoading">
        <BkTable
          ref="tableRef"
          size="small"
          class="perm-record-table"
          border="outer"
          :data="tableData"
          :columns="table.headers"
          :pagination="pagination"
          :max-height="clientHeight"
          remote-pagination
          show-overflow-tooltip
          :row-style="{ cursor: 'pointer' }"
          @row-click="handleRowClick"
          @page-limit-change="handlePageSizeChange"
          @page-value-change="handlePageChange"
        >
          <template #expandRow="row">
            <template v-if="['resource'].includes(row.grant_dimension)">
              <BkTable
                class="ag-expand-table resources"
                :size="'small'"
                :data="row.handled_resources"
                :columns="historyExpandColumn"
                :max-height="378"
                :outer-border="false"
                show-overflow-tooltip
                :header-cell-style="{ background: '#fafbfd', borderTop: 'none' }"
                :cell-style="{ background: '#fafbfd' }"
              />
            </template>
          </template>
          <template #empty>
            <TableEmpty
              :is-loading="isLoading"
              :empty-type="tableEmptyConf.emptyType"
              :abnormal="tableEmptyConf.isAbnormal"
              @refresh="getList"
              @clear-filter="handleClearFilterKey"
            />
          </template>
        </BkTable>
      </BkLoading>
    </div>

    <!-- 详情 -->
    <BkSideslider
      v-model:is-show="detailSliderConf.isShow"
      quick-close
      :title="detailSliderConf.title"
      :width="600"
    >
      <template #default>
        <div class="p-30px">
          <div class="ag-kv-list">
            <div class="item">
              <div class="key">
                {{ t("蓝鲸应用ID：") }}
              </div>
              <div class="value">
                {{ curRecord.bk_app_code }}
              </div>
            </div>
            <div class="item">
              <div class="key">
                {{ t("申请人：") }}
              </div>
              <div class="value">
                <span v-if="!featureFlagStore.isEnableDisplayName">{{ curRecord.applied_by }}</span>
                <span v-else><bk-user-display-name :user-id="curRecord.applied_by" /></span>
              </div>
            </div>
            <div class="item">
              <div class="key">
                {{ t("授权维度：") }}
              </div>
              <div class="value">
                {{ curRecord.grant_dimension_display || "--" }}
              </div>
            </div>
            <div class="item">
              <div class="key">
                {{ t("权限期限：") }}
              </div>
              <div class="value">
                {{ curRecord.expire_days_display || "--" }}
              </div>
            </div>
            <div class="item">
              <div class="key">
                {{ t("申请理由：") }}
              </div>
              <div class="value">
                {{ curRecord.reason || "--" }}
              </div>
            </div>
            <div class="item">
              <div class="key">
                {{ t("申请时间：") }}
              </div>
              <div class="value">
                {{ curRecord.applied_time }}
              </div>
            </div>
            <div class="item">
              <div class="key">
                {{ t("审批人：") }}
              </div>
              <div class="value">
                <span v-if="!featureFlagStore.isEnableDisplayName">{{ curRecord.handled_by }}</span>
                <span v-else><bk-user-display-name :user-id="curRecord.handled_by" /></span>
              </div>
            </div>
            <div class="item">
              <div class="key">
                {{ t("审批时间：") }}
              </div>
              <div class="value">
                {{ curRecord.handled_time }}
              </div>
            </div>
            <div class="item">
              <div class="key">
                {{ t("审批状态：") }}
              </div>
              <div class="value">
                {{ APPROVAL_HISTORY_STATUS_MAP[curRecord.status as keyof typeof APPROVAL_HISTORY_STATUS_MAP] }}
              </div>
            </div>
            <div class="item">
              <div class="key">
                {{ t("审批内容：") }}
              </div>
              <div class="value">
                {{ curRecord.comment }}
              </div>
            </div>
            <div class="item">
              <div class="key">
                {{ t("资源信息：") }}
              </div>
              <div class="value">
                <BkTable
                  :size="'small'"
                  :data="curRecord.handled_resources"
                  :border="['outer']"
                  :max-height="378"
                  :columns="resourceInfoColumn"
                  show-overflow-tooltip
                  ext-cls="ag-expand-table"
                />
              </div>
            </div>
          </div>
        </div>
      </template>
    </BkSideslider>
  </div>
</template>

<script setup lang="tsx">
import { getPermissionRecordList } from '@/services/source/permission';
import { useFeatureFlag } from '@/stores';
import { useDatePicker, useMaxTableLimit, useQueryList } from '@/hooks';
import type { IApprovalListItem } from '@/types/permission';
import { sortByKey } from '@/utils';
import { AUTHORIZATION_DIMENSION } from '@/constants';
import { APPROVAL_HISTORY_STATUS_MAP } from '@/enums';
import AgIcon from '@/components/ag-icon/Index.vue';
import TableEmpty from '@/components/table-empty/Index.vue';

const { t, locale } = useI18n();
const { maxTableLimit, clientHeight } = useMaxTableLimit();
const featureFlagStore = useFeatureFlag();

const historyExpandColumn = shallowRef([
  {
    label: '#',
    width: 220,
    type: 'index',
    align: 'right',
  },
  {
    label: t('资源名称'),
    field: 'name',
  },
  {
    label: t('请求路径'),
    field: 'path',
    render: ({ row }) => {
      return <span>{row.path || '--'}</span>;
    },
  },
  {
    label: t('请求方法'),
    field: 'method',
    render: ({ row }) => {
      return <span>{row.method || '--'}</span>;
    },
  },
  {
    label: t('审批状态'),
    field: 'status',
    render: ({ row }) => {
      if (['rejected'].includes(row['apply_status'])) {
        return (
          <div class="perm-record-dot">
            <span class="ag-dot default m-r-5px" />
            <span>{ t('驳回') }</span>
          </div>
        );
      }
      else {
        return (
          <div class="perm-record-dot">
            <span class="ag-dot success m-r-5px" />
            <span>{ t('通过') }</span>
          </div>
        );
      }
    },
  },
]);
const resourceInfoColumn = shallowRef([
  {
    label: t('资源名称'),
    field: 'name',
  },
  {
    label: t('审批状态'),
    field: 'status',
    render: ({ row }) => {
      if (['rejected'].includes(row['apply_status'])) {
        return (
          <div>
            <span class="ag-dot default m-r-5px" />
            <span>{ t('驳回') }</span>
          </div>
        );
      }
      else {
        return (
          <div>
            <span class="ag-dot success m-r-5px" />
            <span>{ t('通过') }</span>
          </div>
        );
      }
    },
  },
]);
const tableRef = ref<InstanceType<typeof BkTable> & { setRowExpand: () => void }>();
const table = ref({ headers: [] });
const tableEmptyConf = ref<{
  emptyType: string
  isAbnormal: boolean
}>({
  emptyType: '',
  isAbnormal: false,
});
const filterData = ref({
  bk_app_code: '',
  grant_dimension: '',
  time_start: '',
  time_end: '',
});
const resourceList = ref([]);
const dateKey = ref('dateKey');
const curRecord = ref<IApprovalListItem>({
  bk_app_code: '',
  applied_by: '',
  applied_time: '',
  handled_by: '',
  handled_time: '',
  status: '',
  comment: '',
  resourceList: [],
  resource_ids: [],
  grant_dimension_display: '',
  expire_days_display: 0,
  reason: '',
  handled_resources: [],
});
const detailSliderConf = reactive({
  title: '',
  isShow: false,
});

// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList({
  apiMethod: getPermissionRecordList,
  filterData,
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
} = useDatePicker(filterData);

const setTableHeader = () => {
  table.value.headers = [
    {
      field: 'bk_app_code',
      label: t('蓝鲸应用ID'),
    },
    {
      field: 'grant_dimension_display',
      label: t('授权维度'),
      render: ({ row }: { row?: Partial<IApprovalListItem> }) => {
        if (['resource'].includes(row.grant_dimension)) {
          return (
            <div class="flex items-center">
              <AgIcon
                name={row.isExpand ? 'down-shape' : 'right-shape'}
                size="10"
                class="m-r-5px"
              />
              {`${row.grant_dimension_display} (${row.handled_resources?.length || '--'})`}
            </div>
          );
        }
        return row.grant_dimension_display || '--';
      },
    },
    {
      field: 'expire_days_display',
      label: t('权限期限'),
      render: ({ row }: { row?: Partial<IApprovalListItem> }) => {
        return row.expire_days_display || '--';
      },
    },
    {
      field: 'applied_by',
      label: t('申请人'),
      render: ({ row }: { row: Partial<IApprovalListItem> }) =>
        !featureFlagStore.isEnableDisplayName
          ? <span>{row.applied_by}</span>
          : <span><bk-user-display-name user-id={row.applied_by} /></span>,
    },
    {
      field: 'handled_time',
      label: t('审批时间'),
    },
    {
      field: 'handled_by',
      label: t('审批人'),
      render: ({ row }: { row: Partial<IApprovalListItem> }) =>
        !featureFlagStore.isEnableDisplayName
          ? <span>{row.handled_by}</span>
          : <span><bk-user-display-name user-id={row.handled_by} /></span>,
    },
    {
      field: 'status',
      label: t('审批状态'),
      render: ({ row }: { row?: Partial<IApprovalListItem> }) => {
        if (['rejected'].includes(row?.status)) {
          return (
            <div class="perm-record-dot">
              <div class="ag-dot default m-r-5px" />
              {APPROVAL_HISTORY_STATUS_MAP[row?.status as keyof typeof APPROVAL_HISTORY_STATUS_MAP]}
            </div>
          );
        }
        else {
          return (
            <div class="perm-record-dot">
              <span class="ag-dot success m-r-5px" />
              {APPROVAL_HISTORY_STATUS_MAP[row?.status as keyof typeof APPROVAL_HISTORY_STATUS_MAP]}
            </div>
          );
        }
      },
    },
    {
      field: 'operate',
      label: t('操作'),
      fixed: 'right',
      render: ({ row }: { row?: Partial<IApprovalListItem> }) => {
        return (
          <div>
            <BkButton
              class="mr-8px"
              theme="primary"
              text
              onClick={(e: Event) => {
                handleShowRecord(e, row);
              }}
            >
              { t('详情') }
            </BkButton>
          </div>
        );
      },
    },
  ];
};

const handleRowClick = (e: MouseEvent, row: Partial<IApprovalListItem>) => {
  e.stopPropagation();
  if (['resource'].includes(row.grant_dimension)) {
    row.isExpand = !row.isExpand;
  }
  nextTick(() => {
    tableRef.value.setRowExpand(row, row.isExpand);
  });
};

const handlePickSuccess = () => {
  handleConfirm();
};

const handlePickClear = () => {
  handleClear();
};

// 展示详情
const handleShowRecord = (e: MouseEvent, data: IApprovalListItem) => {
  e.stopPropagation();
  const results: IApprovalListItem[] = [];
  detailSliderConf.title = `${t('申请应用：')}${data.bk_app_code}`;
  curRecord.value = Object.assign({}, {
    ...data,
    resourceList: [],
  });
  curRecord.value.resource_ids.forEach((resourceId) => {
    resourceList.value.forEach((item: { id: number }) => {
      if (item.id === resourceId) {
        results.push(item);
      }
    });
  });

  curRecord.value.resourceList = sortByKey(results, 'path');
  detailSliderConf.isShow = true;
};

const handleClearFilterKey = async () => {
  filterData.value = Object.assign({}, {
    bk_app_code: '',
    grant_dimension: '',
    time_start: '',
    time_end: '',
  });
  shortcutSelectedIndex.value = -1;
  dateValue.value = [];
  dateKey.value = String(+new Date());
  await getList();
  updateTableEmptyConfig();
};

const updateTableEmptyConfig = () => {
  const searchParams = { ...filterData.value };
  const list = Object.values(searchParams).filter(item => item !== '');
  if (list.length) {
    tableEmptyConf.value.emptyType = 'searchEmpty';
    return;
  }
  tableEmptyConf.value.emptyType = 'empty';
};

watch(() => filterData.value, () => {
  updateTableEmptyConfig();
}, { deep: true });

onMounted(() => {
  setTableHeader();
});
</script>

<style lang="scss" scoped>
.permission-record-container {

  .record-expand-alert {
    padding: 20px;
    line-height: 60px;
    background-color: #fafafa;
  }

  .header {

    .bk-form-item {
      margin-bottom: 16px;
    }
  }
}

.ag-kv-list {
  padding: 10px 20px;
  background: #fafbfd;
  border: 1px solid #f0f1f5;
  border-radius: 2px;

  .item {
    display: flex;
    font-size: 14px;
    line-height: 40px;
    border-bottom: 1px dashed #dcdee5;

    &:last-child {
      border-bottom: none;
    }

    .key {
      min-width: 130px;
      padding-right: 24px;
      color: #63656e;
      text-align: right;
    }

    .value {
      padding-top: 10px;
      line-height: 22px;
      color: #313238;
      flex: 1;
    }
  }
}

:deep(.perm-record-table),
:deep(.ag-expand-table) {

  tr {
    background-color: #fafbfd;
  }

  th {

    .head-text {
      font-weight: bold !important;
      color: #63656e !important;
    }
  }

  td,
  th {
    height: 42px !important;
    padding: 0 !important;
  }
}

:deep(.ag-expand-table.resources) {
  border-bottom: none;
  border-left: none;

  tr:not(:last-of-type) {
    border-bottom: 1px solid #dcdee5;
  }
}

:deep(.ag-expand-table) {

  .bk-fixed-bottom-border {
    display: none;
  }
}
</style>
