<template>
  <div class="table-page">
    <BkAlert
      class="mb-16px"
      theme="info"
      :title="t('支持按名称、描述快速检索，点击列设置可自定义展示字段。')"
    />

    <!-- 工具栏 -->
    <div class="flex items-center justify-between mb-16px">
      <BkButton
        theme="primary"
        @click="handleCreate"
      >
        {{ t('新建') }}
      </BkButton>

      <div class="flex items-center gap-12px">
        <BkRadioGroup
          v-model="activeStatus"
          type="capsule"
          @change="handleSearch"
        >
          <BkRadioButton label="all">
            {{ t('全部') }}
          </BkRadioButton>
          <BkRadioButton label="enabled">
            {{ t('启用') }}
          </BkRadioButton>
          <BkRadioButton label="disabled">
            {{ t('停用') }}
          </BkRadioButton>
        </BkRadioGroup>

        <BkInput
          v-model="keyword"
          class="w-280px"
          :placeholder="t('搜索名称、描述')"
          clearable
          @enter="handleSearch"
          @clear="handleSearch"
        >
          <template #suffix>
            <span
              class="flex items-center pr-8px cursor-pointer color-#979ba5"
              @click="handleSearch"
            >
              <Search />
            </span>
          </template>
        </BkInput>
      </div>
    </div>

    <!-- 泛型业务表格 -->
    <AgTable
      ref="tableRef"
      v-model:table-data="tableData"
      cache-identifier="ExampleListPage"
      show-settings
      resizable
      :filter-value="filterData"
      :sort="sortData"
      :api-method="getTableData"
      :columns="columns"
      @filter-change="handleFilterChange"
      @sort-change="handleSortChange"
      @clear-filter="handleClearFilter"
    />

    <!-- 新建/编辑弹窗 -->
    <BkDialog
      v-model:is-show="dialogVisible"
      :title="isEdit ? t('编辑') : t('新建')"
      :width="600"
      :is-loading="submitting"
      @confirm="handleConfirm"
      @closed="handleDialogClosed"
    >
      <BkForm
        ref="formRef"
        :model="formData"
        :rules="formRules"
        form-type="vertical"
      >
        <BkFormItem
          :label="t('名称')"
          property="name"
          required
        >
          <BkInput
            v-model="formData.name"
            :placeholder="t('请输入名称')"
          />
        </BkFormItem>
        <BkFormItem
          :label="t('描述')"
          property="description"
        >
          <BkInput
            v-model="formData.description"
            type="textarea"
            :placeholder="t('请输入描述')"
          />
        </BkFormItem>
      </BkForm>
    </BkDialog>
  </div>
</template>

<script setup lang="tsx">
import { Button, type Form, Switcher, Tag } from 'bkui-vue';
import { Search } from 'bkui-vue/lib/icon';
import AgTable, {
  type FilterValue,
  type IAgTableInstance,
  type ITableColumn,
  type ITableQuery,
  type TableSort,
} from '@/components/base/ag-table';
import type { ICountAndResults } from '@/services/types/utils';

interface IExampleRow {
  id: number
  name: string
  source: 'builtin' | 'custom'
  description: string
  updated_by: string
  updated_time: string
  enabled: boolean
}

interface IExampleForm {
  id: number
  name: string
  description: string
}

const { t } = useI18n();

const tableRef = useTemplateRef<IAgTableInstance<IExampleRow>>('tableRef');
const formRef = useTemplateRef<InstanceType<typeof Form>>('formRef');

// 列表与筛选状态
const activeStatus = shallowRef<'all' | 'enabled' | 'disabled'>('all');
const keyword = shallowRef('');
const tableData = ref<IExampleRow[]>([]);
const filterData = ref<FilterValue>({});
const sortData = shallowRef<TableSort | undefined>(undefined);

const columns = shallowRef<ITableColumn<IExampleRow>[]>([
  {
    title: t('名称'),
    colKey: 'name',
    ellipsis: true,
    fixed: 'left',
  },
  {
    title: t('来源'),
    colKey: 'source',
    width: 120,
    filter: {
      type: 'single',
      showConfirmAndReset: true,
      popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
      list: [
        {
          label: t('内置'),
          value: 'builtin',
        },
        {
          label: t('自定义'),
          value: 'custom',
        },
      ],
    },
    cell: (_h, { row }) => (
      <Tag theme={row.source === 'builtin' ? 'info' : 'success'}>
        {row.source === 'builtin' ? t('内置') : t('自定义')}
      </Tag>
    ),
  },
  {
    title: t('描述'),
    colKey: 'description',
    ellipsis: true,
  },
  {
    title: t('更新人'),
    colKey: 'updated_by',
    width: 120,
  },
  {
    title: t('更新时间'),
    colKey: 'updated_time',
    width: 180,
    sorter: true,
  },
  {
    title: t('启停'),
    colKey: 'enabled',
    width: 90,
    cell: (_h, { row }) => (
      <Switcher
        modelValue={row.enabled}
        theme="primary"
        size="small"
        onChange={(val: boolean) => handleToggle(row, val)}
      />
    ),
  },
  {
    title: t('操作'),
    colKey: 'operate',
    width: 140,
    fixed: 'right',
    cell: (_h, { row }) => (
      <div class="flex items-center gap-12px">
        <Button
          theme="primary"
          text
          onClick={() => handleEdit(row)}
        >
          {t('编辑')}
        </Button>
        <Button
          theme="danger"
          text
          onClick={() => handleDelete(row)}
        >
          {t('删除')}
        </Button>
      </div>
    ),
  },
]);

const getTableData = async (params: ITableQuery): Promise<ICountAndResults<IExampleRow>> => {
  // 替换为 src/services/source/ 下的实际接口调用
  const query = {
    ...params,
    keyword: keyword.value || undefined,
    status: activeStatus.value === 'all' ? undefined : activeStatus.value,
  };
  void query;
  return {
    count: 0,
    results: [],
  };
};

const handleSearch = () => {
  tableRef.value?.fetchData(filterData.value, { resetPage: true });
};

const handleFilterChange = (filterItem: FilterValue) => {
  filterData.value = {
    ...filterData.value,
    ...filterItem,
  };
  handleSearch();
};

const handleSortChange = (sort: TableSort | null | undefined) => {
  const currentSort = Array.isArray(sort) ? sort[0] : sort;
  sortData.value = currentSort ?? undefined;
  if (currentSort) {
    const { sortBy, descending } = currentSort;
    // 按后端约定映射排序参数（本仓 Django 接口通常为 -field / field）
    filterData.value.order_by = descending ? `-${sortBy}` : sortBy;
  }
  else {
    delete filterData.value.order_by;
  }
  handleSearch();
};

const handleClearFilter = () => {
  activeStatus.value = 'all';
  keyword.value = '';
  filterData.value = {};
  sortData.value = undefined;
  handleSearch();
};

const handleToggle = async (row: IExampleRow, enabled: boolean) => {
  // 调用启停接口（使用 row.id 与 enabled）成功后刷新当前页，避免乐观修改失败难以回滚
  void row;
  void enabled;
  tableRef.value?.refresh();
};

const handleDelete = async (row: IExampleRow) => {
  // 接入 usePopInfoBox 二次确认后按 row.id 调用删除接口并 refresh
  void row;
  tableRef.value?.refresh();
};

// 新建/编辑弹窗状态
const dialogVisible = shallowRef(false);
const isEdit = shallowRef(false);
const submitting = shallowRef(false);
const formData = reactive<IExampleForm>({
  id: 0,
  name: '',
  description: '',
});

const formRules = computed(() => ({
  name: [
    {
      required: true,
      message: t('请输入名称'),
      trigger: 'blur',
    },
  ],
}));

const handleCreate = () => {
  isEdit.value = false;
  Object.assign(formData, {
    id: 0,
    name: '',
    description: '',
  });
  dialogVisible.value = true;
};

const handleEdit = (row: IExampleRow) => {
  isEdit.value = true;
  Object.assign(formData, {
    id: row.id,
    name: row.name,
    description: row.description,
  });
  dialogVisible.value = true;
};

const handleConfirm = async () => {
  await formRef.value?.validate();
  submitting.value = true;
  try {
    // 调用新建或更新接口
    dialogVisible.value = false;
    tableRef.value?.refresh();
  }
  finally {
    submitting.value = false;
  }
};

const handleDialogClosed = () => {
  formRef.value?.clearValidate();
};
</script>

<style lang="scss" scoped>
.table-page {
  height: 100%;
}
</style>
