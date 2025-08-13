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
        <BkFormItem
          :label="t('选择时间')"
          class="ag-form-item-datepicker top-form-item-time h-32px! flex items-center"
        >
          <BkDatePicker
            :key="dateKey"
            v-model="dateTimeRange"
            type="datetimerange"
            class="w-320px!"
            :placeholder="t('选择日期时间范围')"
            :shortcuts="accessLogStore.datepickerShortcuts"
            shortcut-close
            use-shortcut-text
            :shortcut-selected-index="shortcutSelectedIndex"
            @shortcut-change="handleShortcutChange"
            @change="handleTimeChange"
            @pick-success="handleTimeChange"
            @clear="handleTimeClear"
          />
        </BkFormItem>
        <BkFormItem class="ag-form-item-search">
          <BkSearchSelect
            v-if="!userInfoStore.isTenantMode"
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

    <BkLoading
      :loading="isLoading"
      :z-index="100"
    >
      <BkTable
        size="small"
        class="audit-table"
        border="outer"
        :data="tableData"
        :pagination="pagination"
        :max-height="clientHeight"
        :columns="getTableColumns()"
        remote-pagination
        show-overflow-tooltip
        @column-sort="handleSortChange"
        @page-value-change="handlePageChange"
        @page-limit-change="handlePageSizeChange"
      >
        <template #empty>
          <TableEmpty
            :empty-type="tableEmptyConfig.emptyType"
            :abnormal="tableEmptyConfig.isAbnormal"
            @refresh="getAuditLogList"
            @clear-filter="handleClearFilterKey"
          />
        </template>
      </BkTable>
    </BkLoading>
  </div>
</template>

<script lang="tsx" setup>
import { cloneDeep } from 'lodash-es';
import { t } from '@/locales';
import type { ISearchSelect, ReturnRecordType } from '@/types/common';
import { useMaxTableLimit, useQueryList } from '@/hooks';
import {
  useAccessLog,
  useAuditLog,
  useFeatureFlag,
  useUserInfo,
} from '@/stores';
import { getTenantUsers } from '@/services/source/basic';
import {
  type IAuditLog,
  getAuditLogList,
} from '@/services/source/auditLog';
import TableHeaderFilter from '@/components/table-header-filter';
import TableEmpty from '@/components/table-empty/Index.vue';
import dayjs from 'dayjs';

const accessLogStore = useAccessLog();
const auditLogStore = useAuditLog();
const userInfoStore = useUserInfo();
const featureFlagStore = useFeatureFlag();

const shortcutSelectedIndex = shallowRef(-1);
const tableKey = ref(-1);
const orderBy = ref('');
const dateKey = ref('dateKey');
const members = ref([]);
const searchValue = ref([]);
const dateTimeRange = ref([]);
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
const defaultFilterData = ref<Record<string, string>>({
  op_type: 'ALL',
  op_object_type: 'ALL',
  op_status: 'ALL',
});
const curSelectData = ref<Record<string, string>>(cloneDeep(defaultFilterData));
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
const tableEmptyConfig = reactive({
  emptyType: '',
  isAbnormal: false,
});

const searchData = computed(() => {
  const isTenantMode = userInfoStore.featureFlags?.ENABLE_MULTI_TENANT_MODE || false;
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

const { maxTableLimit, clientHeight } = useMaxTableLimit();

const getFilterData = (payload: Record<string, string>, curData: Record<string, string>) => {
  const { id, name } = payload;
  filterData.value[curData.id] = payload.id;
  const hasMethodData = searchValue.value.find((item: ISearchSelect) => [curData.id].includes(item.id));
  if (hasMethodData) {
    hasMethodData.values = [{
      id,
      name,
    }];
  }
  else {
    searchValue.value.push({
      id: curData.id,
      name: curData.name,
      values: [{
        id,
        name,
      }],
    });
  }
  if (['ALL'].includes(payload.id)) {
    delete filterData.value[curData.id];
    searchValue.value = searchValue.value.filter((item: ISearchSelect) => ![curData.id].includes(item.id));
  }
  // refreshTableData();
};

const renderObjectLabel = () => {
  return h('div', { class: 'audit-log-custom-label' }, [
    h(
      TableHeaderFilter,
      {
        key: tableKey.value,
        hasAll: true,
        columnLabel: t('操作对象'),
        selectValue: curSelectData.value.op_object_type,
        list: OperateRecordObjectType.value,
        onSelected: (payload: Record<string, string>) => {
          const curData = {
            id: 'op_object_type',
            name: t('操作对象'),
          };
          getFilterData(payload, curData);
        },
      },
    ),
  ]);
};

const renderTypeLabel = () => {
  return h('div', { class: 'audit-log-custom-label' }, [
    h(
      TableHeaderFilter,
      {
        key: tableKey.value,
        hasAll: true,
        columnLabel: t('操作类型'),
        selectValue: curSelectData.value.op_type,
        list: OperateRecordType.value,
        onSelected: (payload: Record<string, string>) => {
          const curData = {
            id: 'op_type',
            name: t('操作类型'),
          };
          getFilterData(payload, curData);
        },
      },
    ),
  ]);
};

const renderStatusLabel = () => {
  return h('div', { class: 'audit-log-custom-label' }, [
    h(
      TableHeaderFilter,
      {
        key: tableKey.value,
        hasAll: true,
        columnLabel: t('操作状态'),
        selectValue: curSelectData.value.op_status,
        list: OperateRecordStatus.value,
        onSelected: (payload: Record<string, string>) => {
          const curData = {
            id: 'op_status',
            name: t('操作状态'),
          };
          getFilterData(payload, curData);
        },
      },
    ),
  ]);
};

const handleSortChange = ({ column, type }: Record<string, any>) => {
  const typeMap: ReturnRecordType<string, string> = {
    asc: () => {
      orderBy.value = column.field;
    },
    desc: () => {
      orderBy.value = `-${column.field}`;
    },
    null: () => {
      orderBy.value = '';
    },
  };
  typeMap[type]();
  refreshTableData();
};

const formatDatetime = (timeRange: number[]) => {
  return [+new Date(`${timeRange[0]}`) / 1000, +new Date(`${timeRange[1]}`) / 1000];
};

const setSearchTimeRange = () => {
  // 选择了同一天，则需要把开始时间的时分秒设置为 00:00:00
  if (dayjs(dateTimeRange.value[0]).isSame(dateTimeRange.value[1])) {
    dateTimeRange.value[0].setHours(0, 0, 0);
  }
  let timeRange = dateTimeRange.value;
  // 选择的是时间快捷项，需要实时计算时间值
  if (shortcutSelectedIndex.value !== -1) {
    timeRange = accessLogStore.datepickerShortcuts[shortcutSelectedIndex.value].value();
  }
  const formatTimeRange = formatDatetime(timeRange);
  filterData.value = Object.assign(filterData.value, {
    time_start: formatTimeRange[0] || '',
    time_end: formatTimeRange[1] || '',
  });
};

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

const getTableColumns = () => {
  return [
    {
      label: renderObjectLabel,
      field: 'op_object_type',
      render: ({ row }: { row?: IAuditLog }) => {
        return (
          <div class="cell-field">
            <span class="content">{ getOpObjectTypeText(row.op_object_type) }</span>
          </div>
        );
      },
    },
    {
      label: t('实例'),
      field: 'op_object',
      render: ({ row }: { row?: IAuditLog }) => {
        return (
          <span>{ row.op_object || '--' }</span>
        );
      },
    },
    {
      label: renderTypeLabel,
      field: 'op_type',
      render: ({ row }: { row?: IAuditLog }) => {
        return (
          <span>{ getOpTypeText(row.op_type) || '--' }</span>
        );
      },
    },
    {
      label: renderStatusLabel,
      field: 'op_status',
      render: ({ row }: { row?: IAuditLog }) => {
        return (
          <div class="flex items-center">
            <span class={['mr-5px ag-dot', row.op_status]} />
            <span class="status-text">{ getStatusText(row.op_status) }</span>
          </div>
        );
      },
    },
    {
      label: t('操作人'),
      field: 'username',
      render: ({ row }: { row: IAuditLog }) =>
        !featureFlagStore.isTenantMode
          ? <span>{row.username}</span>
          : <span><bk-user-display-name user-id={row.username} /></span>,
    },
    {
      label: t('操作时间'),
      field: 'op_time',
    },
    {
      label: t('描述'),
      field: 'comment',
    },
  ];
};

const handleTimeChange = () => {
  setSearchTimeRange();
};

const handleTimeClear = () => {
  shortcutSelectedIndex.value = -1;
  dateTimeRange.value = [];
  setSearchTimeRange();
};

const handleShortcutChange = (shortcut: {
  text: string
  value?: () => void
}, index: number) => {
  shortcutSelectedIndex.value = index;
  updateTableEmptyConfig();
};

const handleClearFilterKey = () => {
  isLoading.value = true;
  members.value = [];
  filterData.value = cloneDeep(defaultSearchData.value);
  searchValue.value = [];
  handleTimeClear();
  dateKey.value = String(+new Date());
};

const updateTableEmptyConfig = () => {
  const searchParams = { ...filterData.value };
  const list = Object.values(searchParams).filter(item => item !== '');
  if (list.length || shortcutSelectedIndex.value > -1) {
    tableEmptyConfig.emptyType = 'searchEmpty';
    return;
  }
  tableEmptyConfig.emptyType = 'empty';
};

const refreshTableData = async () => {
  await getList();
  updateTableEmptyConfig();
};

const getMenuList = async (item: { id: string }, keyword: string) => {
  if (!userInfoStore.isTenantMode) {
    return undefined;
  }

  if (item.id === 'username' && keyword) {
    const list = await getTenantUsers({ keyword }, userInfoStore.userInfoStore.tenant_id) as {
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
      curSelectData.value = cloneDeep(defaultFilterData.value);
      // tableKey.value = +new Date();
      refreshTableData();
      return;
    }
    let notRefresh = false;
    Object.keys(filterData.value).forEach((filterDataKey: string) => {
      const hasData = newVal.find((sv: ISearchSelect) => sv.id === filterDataKey);
      let ret = '';
      if (hasData) {
        if (!['op_object_type', 'op_type', 'op_status'].includes(hasData.id)) {
          ret = hasData.values[0].id || '';
        }
        else {
          const alterSearchDataItem = searchData.value.find(sd => sd.id === hasData.id) ?? {};
          const alterSearchDataItemChildren = alterSearchDataItem.children || [];
          if (!alterSearchDataItemChildren.every((child: {
            name: string
            id: number
          }) => child.id !== hasData.values[0].id)) {
            ret = hasData.values[0].id || '';
          }
          else {
            // op_object_type, op_type, op_status三种搜索项，如果没有采用下拉框的备选项而是自己随意输入时，则替换成下拉框的第一个备选项
            notRefresh = true;
            searchValue.value.forEach((sv: ISearchSelect) => {
              if (sv.id === filterDataKey) {
                sv.values = [alterSearchDataItemChildren[0]];
              }
            });
          }
        }
      }
      if (!['time_start', 'time_end'].includes(filterDataKey)) {
        filterData.value[filterDataKey] = ret;
        curSelectData.value[filterDataKey] = ret;
      }
    });
    // tableKey.value = +new Date();
    if (!notRefresh) {
      refreshTableData();
    }
  },
  { deep: true },
);

const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList({
  apiMethod: getAuditLogList,
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
