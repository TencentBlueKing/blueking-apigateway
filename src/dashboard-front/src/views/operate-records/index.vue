<template>
  <div class="page-wrapper-padding operate-records-content">
    <div class="ag-top-header">
      <bk-form class="search-form">
        <bk-form-item :label="t('选择时间')" class="ag-form-item-datepicker top-form-item-time">
          <bk-date-picker
            ref="topDatePicker"
            style="width: 320px"
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
        </bk-form-item>
        <bk-form-item class="ag-form-item-search">
          <bk-search-select
            style="width: 100%"
            v-model="searchValue"
            unique-select
            class="operate-records-search"
            :data="searchData"
            :placeholder="t('请输入关键字或选择条件搜索')"
            :clearable="false"
            :value-split-code="'+'"
            :value-behavior="'need-key'"
          />
        </bk-form-item>
      </bk-form>
    </div>
    <bk-loading :loading="isLoading" :z-index="100">
      <bk-table
        size="small"
        ref="tableRef"
        class="audit-table"
        border="outer"
        :data="tableData"
        :pagination="pagination"
        :remote-pagination="true"
        :show-overflow-tooltip="true"
        @column-sort="handleSortChange"
        @page-value-change="handlePageChange"
        @page-limit-change="handlePageSizeChange"
      >
        <bk-table-column
          :label="renderObjectLabel"
        >
          <template #default="{ row }">
            <div class="cell-field">
              <!-- <span class="label"> {{ t("类型") }}： </span> -->
              <span class="content">{{ getOpObjectTypeText(row.op_object_type) }}</span>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column :label="t('实例')" prop="op_object" :show-overflow-tooltip="true" />
        <bk-table-column :label="renderTypeLabel">
          <template #default="{ row }">
            {{ getOpTypeText(row.op_type) || '--'}}
          </template>
        </bk-table-column>
        <bk-table-column :label="renderStatusLabel">
          <template #default="{ row }">
            <span :class="['ag-dot', row.op_status]"></span>
            <span class="status-text">{{ getStatusText(row.op_status) }}</span>
          </template>
        </bk-table-column>
        <bk-table-column :label="t('操作人')" prop="username" />
        <bk-table-column :label="t('操作时间')" prop="op_time" />
        <bk-table-column :label="t('描述')" prop="comment" />
        <template #empty>
          <TableEmpty
            :keyword="tableEmptyConf.keyword"
            :abnormal="tableEmptyConf.isAbnormal"
            @reacquire="getAuditLogList"
            @clear-filter="handleClearFilterKey"
          />
        </template>
      </bk-table>
    </bk-loading>
  </div>
</template>

<script lang="ts" setup>
import i18n from '@/language/i18n';
import TableEmpty from '@/components/table-empty.vue';
import RenderCustomColumn from '@/components/custom-table-header-filter';
import { ref, shallowRef, reactive, watch, h } from 'vue';
import { cloneDeep } from 'lodash';
import { useQueryList } from '@/hooks';
import { useAccessLog, useOperateRecords } from '@/store';
import {
  DefaultSearchParamsInterface,
  TableEmptyConfType,
} from './common/type';
import { fetchApigwAuditLogs } from '@/http';
import { Message } from 'bkui-vue';

const { t } = i18n.global;
const AccessLogStore = useAccessLog();
const OperateRecords = useOperateRecords();

const defaultSearchData = ref<DefaultSearchParamsInterface>({
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
const defaultFilterData = ref<DefaultSearchParamsInterface>({
  op_type: 'ALL',
  op_object_type: 'ALL',
  op_status: 'ALL',
});
const tableKey = ref(-1);
const curSelectData = ref<{[key: string]: any}>(cloneDeep(defaultFilterData));
const filterData = ref<{[key: string]: any}>(cloneDeep(defaultSearchData));
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList(fetchApigwAuditLogs, filterData);

const topDatePicker = ref(null);
const dateKey = ref('dateKey');
const orderBy = ref('');
const shortcutSelectedIndex = shallowRef(-1);
const dateTimeRange = ref([]);
const members = ref([]);
const curPagination = ref(cloneDeep(pagination));
const tableEmptyConf = reactive<TableEmptyConfType>({
  keyword: '',
  isAbnormal: false,
});
const OperateRecordObjectType =  ref(AccessLogStore.auditOptions.OPObjectType.map((item: Record<string, string>) => {
  return {
    ...item,
    ...{ id: item.value },
  };
}));
const OperateRecordType =  ref(AccessLogStore.auditOptions.OPType.map((item: Record<string, string>) => {
  return {
    ...item,
    ...{ id: item.value },
  };
}));
const OperateRecordStatus =  ref(OperateRecords.operateStatus.map((item: Record<string, string>) => {
  return {
    ...item,
    ...{ id: item.value },
  };
}));
const searchValue = ref([]);
const searchData = shallowRef([
  {
    name: t('模糊查询'),
    id: 'keyword',
    placeholder: t('请输入实例，操作人'),
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
  },
  {
    name: t('操作人'),
    id: 'username',
    placeholder: t('请输入操作人'),
  },
]);

const handleFilterData = (payload: Record<string, string>, curData: Record<string, string>) => {
  const { id, name } = payload;
  filterData.value[curData.id] = payload.id;
  const hasMethodData = searchValue.value.find((item: Record<string, any>) => [curData.id].includes(item.id));
  if (hasMethodData) {
    hasMethodData.values = [{
      id,
      name,
    }];
  } else {
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
    searchValue.value = searchValue.value.filter((item: Record<string, any>) => ![curData.id].includes(item.id));
  }
  // refreshTableData();
};

const renderObjectLabel = () => {
  return h('div', { class: 'operate-records-custom-label' }, [
    h(
      RenderCustomColumn,
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
          handleFilterData(payload, curData);
        },
      },
    ),
  ]);
};

const renderTypeLabel = () => {
  return h('div', { class: 'operate-records-custom-label' }, [
    h(
      RenderCustomColumn,
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
          handleFilterData(payload, curData);
        },
      },
    ),
  ]);
};

const renderStatusLabel = () => {
  return h('div', { class: 'operate-records-custom-label' }, [
    h(
      RenderCustomColumn,
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
          handleFilterData(payload, curData);
        },
      },
    ),
  ]);
};

const handleSortChange = ({ column, type }: Record<string, any>) => {
  const typeMap: Record<string, Function> = {
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
};

const getAuditLogList = async () => {
  setSearchTimeRange();
  getList();
  updateTableEmptyConfig();
};

const getStatusText = (type: string) => {
  return (OperateRecords.operateStatus.find((item: Record<string, string>) => item.value === type) || {})?.name || '';
};

const getOpTypeText = (type: string) => {
  return (
    (
      AccessLogStore.auditOptions.OPType.find((item: Record<string, string>) => item.value === type) || {}
    )?.name || ''
  );
};

const getOpObjectTypeText = (type: string) => {
  return (
    (
      AccessLogStore.auditOptions.OPObjectType.find((item: Record<string, string>) => item.value === type) || {}
    )?.name || ''
  );
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

const handleShortcutChange = (value: Record<string, any>, index: number) => {
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
  if (!curPagination.value.count) {
    tableEmptyConf.keyword = 'placeholder';
    return;
  }
  tableEmptyConf.keyword = '';
};

const refreshTableData = async () => {
  await getList();
  updateTableEmptyConfig();
};

watch(
  () => searchValue.value,
  async (newVal: any[]) => {
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
      curSelectData.value =  cloneDeep(defaultFilterData.value);
      tableKey.value = +new Date();
      await refreshTableData();
      return;
    }

    let notRefresh = false;

    Object.keys(filterData.value).forEach((filterDataKey: string) => {
      const hasData = newVal.find((v: Record<string, any>) => v.id === filterDataKey);
      let ret = '';
      if (hasData) {
        if (!['op_object_type', 'op_type', 'op_status'].includes(hasData.id)) {
          ret = hasData.values[0].id || '';
        } else {
          const alterSearchDataItem: any = searchData.value.find(sd => sd.id === hasData.id) || {};
          const alterSearchDataItemChildren = alterSearchDataItem.children || [];
          if (!alterSearchDataItemChildren.every((child: any) => child.id !== hasData.values[0].id)) {
            ret = hasData.values[0].id || '';
          } else {
            // op_object_type, op_type, op_status 三种搜索项，如果没有采用下拉框的备选项而是自己随意输入时，则替换成下拉框的第一个备选项
            notRefresh = true;
            searchValue.value.forEach((v: any) => {
              if (v.id === filterDataKey) {
                v.values = [alterSearchDataItemChildren[0]];
              }
            });
          }
        }
      }
      if (filterDataKey !== 'time_start' && filterDataKey !== 'time_end') {
        filterData.value[filterDataKey] = ret;
        curSelectData.value[filterDataKey] = ret;
      }
    });
    filterData.value.order_by = orderBy;
    tableKey.value = +new Date();
    if (!notRefresh) {
      await refreshTableData();
    }
  },
  { deep: true },
);
</script>

<style lang="scss" scoped>
.operate-records-content {
  min-height: calc(100vh - 208px);

  .audit-table {
    :deep(.bk-table-head) {
      scrollbar-color: transparent transparent;
    }
    :deep(.bk-table-body) {
      scrollbar-color: transparent transparent;
    }
  }

  .ag-top-header {
    min-height: 32px;
    margin-bottom: 20px;
    position: relative;

    :deep(.search-form) {
      width: 100% !important;
      max-width: 100% !important;
      display: flex;

      .bk-form-item {
        display: inline-flex;
        margin-bottom: 0;
        margin-left: 8px;
        vertical-align: middle;

        &:first-child {
          margin-left: 0;
        }

        .bk-form-label {
          width: auto !important;
          line-height: 32px;
          display: inline-block;
          min-width: 75px;
          padding: 0 15px 0 0;

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
        margin-left: 8px !important;
        margin-top: 0px !important;

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
          .operate-records-search {
            background: #ffffff;
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
      flex: 1;
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
    }
  }

  .ag-dot {
    width: 8px;
    height: 8px;
    display: inline-block;
    vertical-align: middle;
    background: #C4C6CC;
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
        background: #E5F6EA;
        border: 1px solid #3FC06D;
    }

    &.danger,
    &.failure {
        background: #FFE6E6;
        border: 1px solid #EA3636;
    }

    &.failure,
    &.fail {
        background: #FFE6E6;
        border: 1px solid #EA3636;
    }

    &.skipped,
    &.unknown {
        background: rgba(120, 67, 175, .16);
        border: 1px solid #7843AF;
    }

    &.received {
        background: rgba(58, 132, 255, .16);
        border: 1px solid #3A84FF;
    }
  }
}

@media (max-width: 1660px) {
  .search-form {
    width: 870px;

    :deep(.bk-form-item.top-form-item-input) {
      margin-top: 10px !important;
    }

    .top-search-button,
    .top-clear-button {
      margin-top: 10px;
    }

    // .ag-form-item-search {
    //   .operate-records-search {
    //     width: calc(100vh - 144px);
    //   }
    // }
  }
}
</style>
