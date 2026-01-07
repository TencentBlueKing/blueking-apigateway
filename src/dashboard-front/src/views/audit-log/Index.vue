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
  <div class="page-wrapper-padding audit-log-content">
    <div class="ag-top-header">
      <BkForm class="audit-log-header">
        <BkFormItem class="ag-form-item-datepicker top-form-item-time h-32px! flex items-center">
          <template #label>
            <div :class="{'w-80px': locale === 'en'}">
              {{ t('选择时间') }}
            </div>
          </template>
          <BkDatePicker
            :key="dateKey"
            v-model="dateValue"
            type="datetimerange"
            class="w-320px!"
            format="yyyy-MM-dd HH:mm:ss"
            use-shortcut-text
            :placeholder="t('选择日期时间范围')"
            :shortcuts="shortcutsRange"
            :shortcut-selected-index="shortcutSelectedIndex"
            @change="handleChange"
            @shortcut-change="handleShortcutChange"
            @clear="handlePickClear"
            @pick-success="handlePickSuccess"
            @selection-mode-change="handleSelectionModeChange"
          />
        </BkFormItem>
        <BkFormItem class="ag-form-item-search">
          <BkSearchSelect
            v-if="!featureFlagStore.isTenantMode"
            v-model="searchValue"
            style="width: 100%"
            unique-select
            class="audit-log-search"
            :data="searchData"
            :placeholder="t('请输入关键字或选择条件搜索')"
            :clearable="false"
            :value-split-code="'+'"
            :value-behavior="'need-key'"
          />
          <BkSearchSelect
            v-else
            v-model="searchValue"
            :clearable="false"
            :data="searchData"
            :get-menu-list="getMenuList"
            :placeholder="t('请输入关键字或选择条件搜索')"
            :value-behavior="'need-key'"
            :value-split-code="'+'"
            class="audit-log-search"
            style="width: 100%"
            unique-select
          />
        </BkFormItem>
      </BkForm>
    </div>

    <AgTable
      ref="tableRef"
      v-model:table-data="tableData"
      row-key="event_id"
      show-settings
      resizable
      :max-limit-config="{ allocatedHeight: 260, mode: 'tdesign'}"
      :filter-value="filterData"
      :api-method="getTableData"
      :columns="tableColumns"
      @clear-filter="handleClearFilter"
      @filter-change="handleFilterChange"
    />
  </div>
</template>

<script lang="tsx" setup>
import { cloneDeep } from 'lodash-es';
import type { ISearchSelect, ITableMethod } from '@/types/common';
import type { FilterValue, PrimaryTableProps } from '@blueking/tdesign-ui';
import { useTableFilterChange } from '@/hooks/use-table-filter-change';
import { useDatePicker } from '@/hooks';
import {
  useAccessLog,
  useAuditLog,
  useFeatureFlag,
  useGateway,
  useUserInfo,
} from '@/stores';
import { getTenantUsers } from '@/services/source/basic';
import {
  type IAuditLog,
  getAuditLogList,
} from '@/services/source/audit-log.ts';
import AgTable from '@/components/ag-table/Index.vue';

const { t, locale } = useI18n();
const accessLogStore = useAccessLog();
const auditLogStore = useAuditLog();
const userInfoStore = useUserInfo();
const featureFlagStore = useFeatureFlag();
const gatewayStore = useGateway();
const { handleTableFilterChange } = useTableFilterChange();

const orderBy = ref('');
const dateKey = ref('dateKey');
const searchValue = ref([]);
const defaultSearchData = ref<IAuditLog>({
  keyword: '',
  op_type: '',
  op_object: '',
  op_object_type: '',
  op_status: '',
  username: '',
  time_start: '',
  time_end: '',
  order_by: '',
});

const tableData = ref([]);
const tableRef = useTemplateRef<InstanceType<typeof AgTable> & ITableMethod>('tableRef');
const filterData = ref<IAuditLog>(cloneDeep(defaultSearchData));
const OperateRecordObjectType = ref(
  accessLogStore.auditOptions.OPObjectType.map((item: Record<string, string>) => {
    return {
      ...item,
      id: item.value,
    };
  }),
);
const OperateRecordType = ref(
  accessLogStore.auditOptions.OPType.map((item: Record<string, string>) => {
    return {
      ...item,
      id: item.value,
    };
  }),
);
const OperateRecordStatus = ref(
  auditLogStore.operateStatus.map((item: Record<string, string>) => {
    return {
      ...item,
      id: item.value,
    };
  }),
);

const apigwId = computed(() => gatewayStore.apigwId);

const searchData = computed(() => {
  const isTenantMode = featureFlagStore.flags?.ENABLE_MULTI_TENANT_MODE || false;
  return [
    {
      name: t('模糊查询'),
      id: 'keyword',
      placeholder: t('请输入实例，操作人'),
      children: isTenantMode ? [] : undefined,
    },
    {
      name: t('操作对象'),
      id: 'op_object_type',
      placeholder: t('请选择操作对象'),
      onlyRecommendChildren: true,
      children: OperateRecordObjectType.value,
    },
    {
      name: t('操作类型'),
      id: 'op_type',
      placeholder: t('请选择操作类型'),
      onlyRecommendChildren: true,
      children: OperateRecordType.value,
    },
    {
      name: t('操作状态'),
      id: 'op_status',
      placeholder: t('请选择操作状态'),
      onlyRecommendChildren: true,
      children: OperateRecordStatus.value,
    },
    {
      name: t('实例'),
      id: 'op_object',
      placeholder: t('请输入实例'),
      children: isTenantMode ? [] : undefined,
    },
    {
      name: t('操作人'),
      id: 'username',
      placeholder: t('请输入操作人'),
      async: isTenantMode,
      children: isTenantMode ? [] : undefined,
    },
  ];
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

const getStatusText = (type: string) => {
  const name = auditLogStore.operateStatus.find((item: Record<string, string>) => item.value === type)?.name;
  return name ?? '--';
};

const getOpTypeText = (type: string) => {
  const name = accessLogStore.auditOptions.OPType.find((item: Record<string, string>) => item.value === type)?.name;
  return name ?? '--';
};

const getOpObjectTypeText = (type: string) => {
  const name = accessLogStore.auditOptions.OPObjectType.find(
    (item: Record<string, string>) => item.value === type,
  )?.name;
  return name ?? '--';
};

const tableColumns = shallowRef<PrimaryTableProps['columns']>([
  {
    title: t('操作对象'),
    colKey: 'op_object_type',
    ellipsis: true,
    cell: (h, { row }: { row: IAuditLog }) => {
      return (
        <div class="cell-field">
          <span class="content">{ getOpObjectTypeText(row.op_object_type) }</span>
        </div>
      );
    },
    filter: {
      type: 'single',
      showConfirmAndReset: true,
      popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
      list: accessLogStore.auditOptions.OPObjectType.map((item: Record<string, string>) => ({
        ...item,
        label: item.name,
      })),
    },
  },
  {
    title: t('实例'),
    colKey: 'op_object',
    ellipsis: true,
    cell: (h, { row }: { row: IAuditLog }) => {
      return (
        <span>{ row.op_object || '--' }</span>
      );
    },
  },
  {
    title: t('操作类型'),
    colKey: 'op_type',
    ellipsis: true,
    cell: (h, { row }: { row: IAuditLog }) => {
      return (
        <span>{ getOpTypeText(row.op_type) || '--' }</span>
      );
    },
    filter: {
      type: 'single',
      showConfirmAndReset: true,
      popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
      list: accessLogStore.auditOptions.OPType.map((item: Record<string, string>) => ({
        ...item,
        label: item.name,
      })),
    },
  },
  {
    title: t('操作状态'),
    colKey: 'op_status',
    ellipsis: true,
    cell: (h, { row }: { row: IAuditLog }) => {
      return (
        <div class="flex items-center">
          <span class={['mr-5px ag-dot', row.op_status]} />
          <span class="status-text">{ getStatusText(row.op_status) }</span>
        </div>
      );
    },
    filter: {
      type: 'single',
      showConfirmAndReset: true,
      popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
      list: auditLogStore.operateStatus.map((item: Record<string, string>) => ({
        ...item,
        label: item.name,
      })),
    },
  },
  {
    title: t('操作人'),
    colKey: 'username',
    ellipsis: true,
    cell: (h, { row }: { row: IAuditLog }) =>
      !featureFlagStore.isEnableDisplayName
        ? <span>{row.username}</span>
        : <span><bk-user-display-name user-id={row.username} /></span>,
  },
  {
    title: t('操作时间'),
    colKey: 'op_time',
    ellipsis: true,
  },
  {
    title: t('描述'),
    colKey: 'comment',
    ellipsis: true,
  },
]);

const getList = () => tableRef.value?.fetchData(filterData.value, { resetPage: true });

const getTableData = async (params: Record<string, any> = {}) => {
  const results = await getAuditLogList(apigwId.value, params);
  return results ?? [];
};

const handleClearFilter = () => {
  filterData.value = cloneDeep(defaultSearchData.value);
  searchValue.value = [];
  handleClear();
  dateKey.value = String(+new Date());
};

// 处理表头筛选联动搜索框
const handleFilterChange: PrimaryTableProps['onFilterChange'] = (filterItem: FilterValue) => {
  handleTableFilterChange({
    filterItem,
    filterData,
    searchOptions: searchData,
    searchParams: searchValue,
  });
  getList();
};

const handlePickSuccess = () => {
  handleConfirm();
  getList();
};

const handlePickClear = () => {
  handleClear();
  getList();
};

const getMenuList = async (item: { id: string }, keyword: string) => {
  if (!featureFlagStore.isTenantMode) {
    return undefined;
  }

  if (item.id === 'username' && keyword && featureFlagStore.isEnableDisplayName) {
    const list = await getTenantUsers({ keyword }, userInfoStore.info.tenant_id) as {
      bk_username: string
      display_name: string
    }[];
    return list.map(user => ({
      id: user.bk_username,
      name: user.display_name,
      value: user.bk_username,
    }));
  }
  return searchData.value.find(set => set.id === item.id)?.children;
};

watch(
  () => searchValue.value,
  (newVal: ISearchSelect[]) => {
    if (!newVal.length) {
      filterData.value = Object.assign(
        {},
        cloneDeep(defaultSearchData.value),
        {
          order_by: orderBy.value,
          time_start: filterData.value.time_start,
          time_end: filterData.value.time_end,
        },
      );
    }
    else {
      const textItem = searchValue.value.find(val => val.type === 'text');
      if (textItem) {
        filterData.value.keyword = textItem.name || '';
      }
      searchValue.value.forEach((item) => {
        if (item.values) {
          filterData.value[item.id] = item.values[0].id;
        }
      });
    }

    getList();
  },
  { deep: true },
);

</script>

<style lang="scss" scoped>
.audit-log-content {
  min-height: calc(100vh - 208px);

  .ag-top-header {
    position: relative;
    min-height: 32px;
    margin-bottom: 20px;

    :deep(.audit-log-header) {
      display: flex;
      width: 100% !important;
      max-width: 100% !important;

      .bk-form-item {
        display: inline-flex;
        margin-bottom: 0;
        margin-left: 8px;
        vertical-align: middle;

        &:first-child {
          margin-left: 0;
        }

        .bk-form-label {
          display: inline-block;
          width: auto !important;
          min-width: 75px;
          padding: 0 15px 0 0;
          line-height: 32px;

          span {
            display: inline-block;
            line-height: 20px;
          }
        }

        .bk-form-content {
          margin-left: 0 !important;
        }
      }

      .ag-form-item-inline {
        margin-top: 0 !important;
        margin-left: 8px !important;

        .bk-form-content {
          display: flex !important;
          font-size: unset;
        }

        .suffix {
          margin-left: 4px;
        }
      }

      .ag-form-item-datepicker {

        .bk-form-content {
          max-width: 320px;
        }
      }

      .ag-form-item-search {
        width: calc(100% - 320px);

        .bk-form-content {
          width: 100%;

          .audit-log-search {
            background: #fff;
          }
        }
      }
    }
  }

  .cell-field {
    display: flex;

    .label {
      flex: none;
      color: #979ba5;
    }

    .content {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      flex: 1;
    }
  }

  :deep(.ag-dot) {
    display: inline-block;
    width: 8px;
    height: 8px;
    vertical-align: middle;
    background: #c4c6cc;
    border-radius: 50%;

    &.default {
      background: #f0f1f5;
      border: 1px solid #c9cad2;
    }

    &.primary,
    &.releasing,
    &.pending {
      background: #f0f1f5;
      border: 1px solid #c9cad2;
    }

    &.success {
      background: #e5f6ea;
      border: 1px solid #3fc06d;
    }

    &.danger,
    &.failure {
      background: #ffe6e6;
      border: 1px solid #ea3636;
    }

    &.failure,
    &.fail {
      background: #ffe6e6;
      border: 1px solid #ea3636;
    }

    &.skipped,
    &.unknown {
      background: rgb(120 67 175 / 16%);
      border: 1px solid #7843af;
    }

    &.received {
      background: rgb(58 132 255 / 16%);
      border: 1px solid #3a84ff;
    }
  }
}

@media (max-width: 1660px) {

  .audit-log-header {
    width: 870px;

    :deep(.bk-form-item.top-form-item-input) {
      margin-top: 10px !important;
    }

    .top-search-button,
    .top-clear-button {
      margin-top: 10px;
    }
  }
}
</style>
