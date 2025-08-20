<template>
  <PrimaryTable
    v-model:selected-row-keys="selectedRowKeys"
    :data="localTableData"
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
      <BkException
        v-bind="exceptionAttrs"
        class="ag-table-exception"
      >
        <BkButton
          v-if="exceptionAttrs.type === 500"
          text
          theme="primary"
          @click="handleRefresh"
        >
          {{ t("刷新") }}
        </BkButton>
        <div
          v-if="exceptionAttrs.type === 'search-empty'"
          class="flex items-center gap-4px"
        >
          <span class="color-#979ba5">{{ t("可以尝试 调整关键词 或") }}</span>
          <BkButton
            text
            theme="primary"
            @click="emit('clear-queries')"
          >
            <span class="line-height-22px">{{ t("清空搜索条件") }}</span>
          </BkButton>
        </div>
      </BkException>
    </template>
  </PrimaryTable>
</template>

<script setup lang="ts">
import { PrimaryTable, type PrimaryTableProps } from '@blueking/tdesign-ui';
import { useRequest } from 'vue-request';
import { cloneDeep } from 'lodash-es';

interface IProps {
  source?: (params?: Record<string, any>) => Promise<unknown>
  columns?: PrimaryTableProps['columns']
  immediate?: boolean
  local?: boolean
  frontendSearch?: boolean
}

const selectedRowKeys = defineModel<any[]>('selectedRowKeys', { default: () => [] });

const tableData = defineModel<any[]>('tableData', { default: () => [] });

const {
  source = undefined,
  columns = [],
  immediate = true,
  local = false,
  frontendSearch = false,
} = defineProps<IProps>();

const emit = defineEmits<{ 'clear-queries': [void] }>();

const slots = defineSlots();

const { t } = useI18n();

const localTableData = ref<any[]>([]);

const pagination = ref<PrimaryTableProps['pagination']>({
  current: 1,
  pageSize: 10,
  defaultCurrent: 1,
  defaultPageSize: 10,
  total: 0,
  theme: 'default',
  showPageSize: true,
});

let paramsMemo: Record<string, any> = {};

const offsetAndLimit = computed(() => {
  return {
    offset: pagination.value!.pageSize! * (pagination.value!.current! - 1) || 0,
    limit: pagination.value!.pageSize || 10,
  };
});

const { params, loading, error, refresh, run: fetchData } = useRequest(source, {
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

const exceptionAttrs = computed(() => {
  if (error.value) {
    return {
      type: 500,
      title: t('数据获取异常'),
    };
  }

  const queries = cloneDeep(params.value?.[0] || {});
  delete queries.limit;
  delete queries.offset;

  if (Object.keys(queries).length || frontendSearch) {
    return {
      type: 'search-empty',
      title: t('搜索结果为空'),
    };
  }

  return {
    type: 'empty',
    title: t('暂无数据'),
  };
});

watch(tableData, () => {
  localTableData.value = cloneDeep(tableData.value || []);
  if (local) {
    pagination.value!.current = 1;
    pagination.value!.total = localTableData.value.length;
  }
}, {
  immediate: true,
  deep: true,
});

const handlePageChange = ({ current, pageSize }: {
  current: number
  pageSize: number
}) => {
  pagination.value!.current = current;
  pagination.value!.pageSize = pageSize;
  if (!local) {
    fetchData({
      ...paramsMemo,
      ...offsetAndLimit.value,
    });
  }
};

const handleRefresh = () => {
  refresh();
};

onMounted(() => {
  if (immediate && !local) {
    fetchData({ ...offsetAndLimit.value });
  }
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
  setPaginationTheme: ({ theme, showPageSize }: {
    theme: 'default' | 'simple'
    showPageSize?: boolean
  }) => {
    Object.assign(pagination.value!, {
      theme,
      showPageSize: showPageSize ?? true,
    });
  },
  resetPaginationTheme: () => {
    pagination.value!.theme = 'default';
    pagination.value!.showPageSize = true;
  },
  refresh,
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

.ag-table-exception {

  .bk-exception-img {
    width: 200px;
    height: 100px;
  }

  .bk-exception-title {
    margin-top: 8px;
    font-size: 12px;
    color: #979ba5;
  }

  .bk-exception-footer {
    margin-top: 8px;
    font-size: 12px;
  }
}
</style>
