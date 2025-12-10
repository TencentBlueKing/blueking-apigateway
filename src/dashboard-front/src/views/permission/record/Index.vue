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
      <AgTable
        ref="permissionTableRef"
        v-model:table-data="tableData"
        show-settings
        resizable
        :expand-icon="false"
        :expandable="expandableConfig"
        :expanded-row-keys="expandableConfig.expandedRowKeys"
        :max-limit-config="{ allocatedHeight: 236, mode: 'tdesign'}"
        :filter-value="filterValue"
        :api-method="getTableData"
        :columns="getTableColumns"
        :row-class-name="handleSetRowClass"
        @row-click="handleRowClick"
        @filter-change="handleFilterChange"
        @clear-filter="handleClearFilter"
      >
        <template #expandedRow="{row}">
          <AgTable
            v-model:table-data="row.handled_resources"
            size="small"
            local-page
            :max-height="378"
            :columns="historyExpandColumn"
          />
        </template>
      </AgTable>
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
                <AgTable
                  v-model:table-data="curRecord.handled_resources"
                  size="small"
                  :max-height="378"
                  local-page
                  :columns="resourceInfoColumn"
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
import { Button } from 'bkui-vue';
import { getPermissionRecordList } from '@/services/source/permission';
import { useFeatureFlag, useGateway } from '@/stores';
import { useDatePicker } from '@/hooks';
import type { IApprovalListItem } from '@/types/permission';
import type { ITableMethod } from '@/types/common';
import { sortByKey } from '@/utils';
import { AUTHORIZATION_DIMENSION } from '@/constants';
import { APPROVAL_HISTORY_STATUS_MAP } from '@/enums';
import AgIcon from '@/components/ag-icon/Index.vue';
import AgTable from '@/components/ag-table/Index.vue';

const { t, locale } = useI18n();
const featureFlagStore = useFeatureFlag();
const gatewayStore = useGateway();

const historyExpandColumn = shallowRef([
  {
    title: '#',
    colKey: 'serial-number',
    align: 'center',
  },
  {
    title: t('资源名称'),
    colKey: 'name',
    ellipsis: true,
  },
  {
    title: t('请求路径'),
    colKey: 'path',
    ellipsis: true,
    cell: (h, { row }) => {
      return <span>{row.path || '--'}</span>;
    },
  },
  {
    title: t('请求方法'),
    colKey: 'method',
    ellipsis: true,
    cell: (h, { row }) => {
      return <span>{row.method || '--'}</span>;
    },
  },
  {
    title: t('审批状态'),
    colKey: 'status',
    ellipsis: true,
    cell: (h, { row }) => {
      if (['rejected'].includes(row['apply_status'])) {
        return (
          <div class="perm-record-dot">
            <span class="ag-dot default mr-4px" />
            <span>{ t('驳回') }</span>
          </div>
        );
      }
      else {
        return (
          <div class="perm-record-dot">
            <span class="ag-dot success mr-4px" />
            <span>{ t('通过') }</span>
          </div>
        );
      }
    },
  },
]);
const resourceInfoColumn = shallowRef([
  {
    title: t('资源名称'),
    colKey: 'name',
    ellipsis: true,
  },
  {
    title: t('审批状态'),
    colKey: 'status',
    ellipsis: true,
    cell: (h, { row }) => {
      if (['rejected'].includes(row['apply_status'])) {
        return (
          <div>
            <span class="ag-dot default mr-4px" />
            <span>{ t('驳回') }</span>
          </div>
        );
      }
      else {
        return (
          <div>
            <span class="ag-dot success mr-4px" />
            <span>{ t('通过') }</span>
          </div>
        );
      }
    },
  },
]);
const tableRef = useTemplateRef<InstanceType<typeof AgTable> & ITableMethod>('permissionTableRef');
const tableData = ref([]);
const filterData = ref({
  bk_app_code: '',
  grant_dimension: '',
  time_start: '',
  time_end: '',
});
const filterValue = ref({});
const resourceList = ref([]);
const expandableConfig = ref({
  expandColumn: false,
  expandedRowKeys: [],
  canExpand: (row) => {
    return ['resource'].includes(row.grant_dimension);
  },
});
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

const apigwId = computed(() => gatewayStore.apigwId);

const getTableColumns = computed(() => {
  return [
    {
      title: t('蓝鲸应用ID'),
      colKey: 'bk_app_code',
      ellipsis: true,
    },
    {
      title: t('授权维度'),
      colKey: 'grant_dimension',
      ellipsis: true,
      filter: {
        type: 'single',
        showConfirmAndReset: true,
        popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
        list: AUTHORIZATION_DIMENSION.map(({ name, id }) => ({
          label: name,
          value: id,
        })),
      },
      cell: (h, { row }: { row?: Partial<IApprovalListItem> }) => {
        if (['resource'].includes(row.grant_dimension)) {
          return (
            <div class="flex items-center">
              <AgIcon
                name={row.isExpand ? 'down-shape' : 'right-shape'}
                size="10"
                class="mr-4px"
              />
              {`${row.grant_dimension_display} (${row.resource_ids?.length || '--'})`}
            </div>
          );
        }
        return row.grant_dimension_display || '--';
      },
    },
    {
      title: t('权限期限'),
      colKey: 'expire_days_display',
      ellipsis: true,
      cell: (h, { row }: { row?: Partial<IApprovalListItem> }) => {
        return row.expire_days_display || '--';
      },
    },
    {
      title: t('申请人'),
      colKey: 'applied_by',
      ellipsis: true,
      cell: (h, { row }: { row: Partial<IApprovalListItem> }) =>
        !featureFlagStore.isEnableDisplayName
          ? <span>{row.applied_by}</span>
          : <span><bk-user-display-name user-id={row.applied_by} /></span>,
    },
    {
      title: t('审批时间'),
      colKey: 'handled_time',
      width: 260,
      ellipsis: true,
    },
    {
      title: t('审批人'),
      colKey: 'handled_by',
      ellipsis: true,
      cell: (h, { row }: { row: Partial<IApprovalListItem> }) =>
        !featureFlagStore.isEnableDisplayName
          ? <span>{row.handled_by}</span>
          : <span><bk-user-display-name user-id={row.handled_by} /></span>,
    },
    {
      title: t('审批状态'),
      colKey: 'status',
      ellipsis: true,
      cell: (h, { row }: { row?: Partial<IApprovalListItem> }) => {
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
      title: t('操作'),
      colKey: 'operate',
      fixed: 'right',
      ellipsis: true,
      cell: (h, { row }: { row?: Partial<IApprovalListItem> }) => {
        return (
          <div>
            <Button
              theme="primary"
              text
              onClick={(e: Event) => {
                handleShowRecord(e, row);
              }}
            >
              { t('详情') }
            </Button>
          </div>
        );
      },
    },
  ];
});

watch(() => filterData, () => {
  filterValue.value = Object.assign({}, filterData.value);
  getList();
}, { deep: true });

function getList() {
  tableRef.value?.fetchData(filterData.value, { resetPage: true });
};

const getTableData = async (params: Record<string, any> = {}) => {
  const results = await getPermissionRecordList(apigwId.value, params);
  return results ?? [];
};

const handleFilterChange: PrimaryTableProps['onFilterChange'] = (filterItem: FilterValue) => {
  filterData.value = Object.assign(filterData.value, filterItem);
  filterValue.value = { ...filterItem };
};

const handleRowClick = ({ e, row }: {
  e: Event
  row: IApprovalListItem
}) => {
  e.stopPropagation();
  if (row.grant_dimension.includes('resource')) {
    row.isExpand = !row.isExpand;
    expandableConfig.value.expandedRowKeys
      = expandableConfig.value.expandedRowKeys.filter(item => item === row.id);
    const curExpandRow = row.isExpand ? row : {};
    if (row.isExpand) {
      expandableConfig.value.expandedRowKeys.push(row.id);
    }
    else {
      expandableConfig.value.expandedRowKeys
        = expandableConfig.value.expandedRowKeys.filter(item => item !== row.id);
    }
    tableData.value.forEach((item) => {
      const isExpand = item.id === curExpandRow.id;
      item.isExpand = isExpand;
      if (!isExpand) {
        item = Object.assign(item, {
          isExpand: false,
          selection: [],
          isSelectAll: true,
        });
      }
    });
  }
};

const handlePickSuccess = () => {
  handleConfirm();
};

const handlePickClear = () => {
  handleClear();
};

const handleSetRowClass = ({ row }) => {
  if (row.grant_dimension.includes('resource')) {
    return 'cursor-pointer';
  }
  return '';
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

const handleClearFilter = () => {
  filterData.value = Object.assign({}, {
    bk_app_code: '',
    grant_dimension: '',
    time_start: '',
    time_end: '',
  });
  filterValue.value = {};
  shortcutSelectedIndex.value = -1;
  dateValue.value = [];
  dateKey.value = String(+new Date());
};
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

:deep(.t-table__header) {
  .t-table__ellipsis {
    font-weight: 700 !important;
    color: #63656e !important;
  }
}

:deep(.t-table__expanded-row) {
  .t-table__row-full-element {
    padding: 0;
  }

  td,
  th {
    height: 42px !important;
    padding: 0 !important;
    cursor: default !important;
  }
}
</style>
