<template>
  <PrimaryTable
    v-model:selected-row-keys="selectedRowKeys"
    :data="tableData"
    :columns="columns"
    :loading="loading"
    :pagination="pagination"
    v-bind="$attrs"
    cell-empty-content="--"
    @page-change="handlePageChange"
  >
    <slot />
    <template
      v-if="slots.expandedRow"
      #expandedRow="props"
    >
      <slot
        name="expandedRow"
        v-bind="props"
      />
    </template>
    <template #loading>
      <BkLoading />
    </template>
    <template #empty>
      <BkException type="empty" />
    </template>
  </PrimaryTable>
</template>

<script setup lang="ts">
import { PrimaryTable, type PrimaryTableProps } from '@blueking/tdesign-ui';
import { useRequest } from 'vue-request';

interface IProps {
  source: (params?: Record<string, any>) => Promise<unknown>
  columns?: PrimaryTableProps['columns']
}

const selectedRowKeys = defineModel<any[]>('selectedRowKeys', { default: () => [] });

const tableData = defineModel<any[]>('tableData', { default: () => [] });

const { source, columns = [] } = defineProps<IProps>();

const slots = defineSlots();

const pagination = ref<PrimaryTableProps['pagination']>({
  current: 1,
  pageSize: 10,
  defaultCurrent: 1,
  defaultPageSize: 10,
  total: 0,
});

let paramsMemo: Record<string, any> = {};

const offsetAndLimit = computed(() => {
  return {
    offset: pagination.value!.pageSize! * (pagination.value!.current! - 1) || 0,
    limit: pagination.value!.pageSize || 10,
  };
});

const { params, run: fetchData, loading } = useRequest(source, {
  manual: true,
  defaultParams: [offsetAndLimit.value],
  onSuccess: (response: {
    results: any[]
    count: number
  }) => {
    // console.log('ag table params:', JSON.stringify(params.value));
    paramsMemo = { ...params.value[0] };
    if (response.results) {
      tableData.value = response.results;
    }
    pagination.value!.total = response.count || 0;
  },
});

const handlePageChange = ({ current, pageSize }: {
  current: number
  pageSize: number
}) => {
  pagination.value!.current = current;
  pagination.value!.pageSize = pageSize;
  fetchData({
    ...paramsMemo,
    ...offsetAndLimit.value,
  });
};

onMounted(() => {
  fetchData({ ...offsetAndLimit.value });
});

defineExpose({
  fetchData: (params: Record<string, any> = {}, options: { resetPage?: boolean } = { resetPage: false }) => {
    if (options.resetPage) {
      pagination.value!.current = 1;
    }
    fetchData({
      ...params,
      ...offsetAndLimit.value,
    });
  },
  getPagination: () => pagination.value,
  setPagination: ({ current, pageSize }: {
    current: number
    pageSize: number
  }) => {
    handlePageChange({
      current,
      pageSize,
    });
  },
});

</script>

<style lang="scss">
.t-table {
  font-size: 12px;

  .t-table__body {
    color: #63656e;
  }

  // 默认的 loading 图标

  .t-loading svg.t-icon-loading {
    display: none !important;
  }
}
</style>
