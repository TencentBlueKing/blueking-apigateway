<template>
  <div class="table-page">
    <!-- 提示信息 -->
    <bk-alert theme="info" class="mb16">
      <template #title>平台按优先级从大到小匹配，可直接编辑优先级数值。</template>
    </bk-alert>

    <!-- 工具栏 -->
    <div class="toolbar mb16">
      <!-- 左侧：新建按钮 -->
      <bk-button theme="primary" @click="handleCreate">新建</bk-button>

      <!-- 右侧：Tab 筛选 + 搜索框 -->
      <div class="toolbar-right">
        <!-- Tab 筛选 -->
        <bk-tab v-model:active="activeTab" type="card" class="filter-tab" @change="handleTabChange">
          <bk-tab-panel name="all" :label="`全部 (${totalCount})`" />
          <bk-tab-panel name="enabled" :label="`启用 (${enabledCount})`" />
          <bk-tab-panel name="disabled" :label="`停用 (${disabledCount})`" />
        </bk-tab>

        <!-- 搜索框 -->
        <bk-input
          v-model="searchKey"
          placeholder="搜索 名称、描述、更新人、定义"
          :clearable="true"
          style="width: 280px"
          @enter="handleSearch"
        >
          <template #suffix>
            <Search class="search-icon" @click="handleSearch" />
          </template>
        </bk-input>
      </div>
    </div>

    <!-- 表格 -->
    <bk-table
      :data="tableData"
      :columns="columns"
      :pagination="pagination"
      :remote-pagination="true"
      :settings="true"
      @page-value-change="handlePageChange"
      @page-limit-change="handleLimitChange"
      @filter-change="handleFilterChange"
      @sort-change="handleSortChange"
    >
      <!-- 来源列：Tag -->
      <template #source="{ row }">
        <bk-tag :theme="row.source === 'builtin' ? 'info' : 'success'">
          {{ row.source === 'builtin' ? '内置' : '自定义' }}
        </bk-tag>
      </template>

      <!-- 启停列：Switcher -->
      <template #enabled="{ row }">
        <bk-switcher
          v-model="row.enabled"
          theme="primary"
          size="small"
          @change="(val) => handleToggle(row, val)"
        />
      </template>

      <!-- 操作列 -->
      <template #operation="{ row }">
        <bk-button text theme="primary" @click="handleEdit(row)">编辑</bk-button>
        <bk-button text theme="danger" @click="handleDelete(row)">删除</bk-button>
      </template>
    </bk-table>

    <!-- 新建/编辑弹窗 -->
    <!-- ⚠️ 注意: 使用 v-model:isShow，不是 v-model -->
    <bk-dialog
      v-model:isShow="dialogVisible"
      :title="dialogTitle"
      width="600"
      @confirm="handleConfirm"
    >
      <bk-form ref="formRef" :model="formData" :rules="formRules" label-width="100">
        <bk-form-item label="名称" property="name" required>
          <bk-input v-model="formData.name" placeholder="请输入名称" />
        </bk-form-item>
        <bk-form-item label="定义" property="definition" required>
          <bk-input v-model="formData.definition" placeholder="请输入定义" />
        </bk-form-item>
        <bk-form-item label="描述" property="description">
          <bk-input v-model="formData.description" type="textarea" placeholder="请输入描述" />
        </bk-form-item>
      </bk-form>
    </bk-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
// ⚠️ 正确导入方式：从 bkui-vue/lib/icon 导入
import { Search } from 'bkui-vue/lib/icon';

interface RowData {
  id: number;
  name: string;
  source: 'builtin' | 'custom';
  definition: string;
  description: string;
  updatedBy: string;
  updatedAt: string;
  enabled: boolean;
}

// Tab 筛选
const activeTab = ref('all');
const totalCount = ref(24);
const enabledCount = ref(10);
const disabledCount = ref(14);

// 搜索
const searchKey = ref('');

// 表格配置
const columns = [
  { label: '名称', field: 'name', width: 150 },
  {
    label: '来源',
    field: 'source',
    width: 100,
    filter: {
      list: [
        { text: '内置', value: 'builtin' },
        { text: '自定义', value: 'custom' }
      ]
    }
  },
  { label: '定义', field: 'definition', showOverflowTooltip: true },
  { label: '描述', field: 'description', showOverflowTooltip: true },
  {
    label: '更新人',
    field: 'updatedBy',
    width: 100,
    filter: {
      list: [] // 动态填充
    }
  },
  {
    label: '更新时间',
    field: 'updatedAt',
    width: 170,
    sort: { value: 'desc' }
  },
  { label: '启停', field: 'enabled', width: 80 },
  { label: '操作', field: 'operation', width: 120 }
];

const tableData = ref<RowData[]>([]);
const pagination = reactive({
  current: 1,
  count: 198,
  limit: 10,
  showTotalCount: true,
  location: 'left'
});

// 弹窗
const dialogVisible = ref(false);
const dialogTitle = ref('新建');
const formRef = ref();
const formData = reactive({
  id: 0,
  name: '',
  definition: '',
  description: ''
});

const formRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  definition: [{ required: true, message: '请输入定义', trigger: 'blur' }]
};

// 方法
const handleTabChange = (tab: string) => {
  activeTab.value = tab;
  pagination.current = 1;
  fetchData();
};

const handleSearch = () => {
  pagination.current = 1;
  fetchData();
};

const handlePageChange = (page: number) => {
  pagination.current = page;
  fetchData();
};

const handleLimitChange = (limit: number) => {
  pagination.limit = limit;
  pagination.current = 1;
  fetchData();
};

const handleFilterChange = (filters: Record<string, any>) => {
  console.log('Filter changed:', filters);
  fetchData();
};

const handleSortChange = ({ column, prop, order }: any) => {
  console.log('Sort changed:', { column, prop, order });
  fetchData();
};

const handleToggle = (row: RowData, enabled: boolean) => {
  console.log('Toggle:', row.id, enabled);
  // TODO: 调用启停 API
};

const handleCreate = () => {
  dialogTitle.value = '新建';
  Object.assign(formData, { id: 0, name: '', definition: '', description: '' });
  dialogVisible.value = true;
};

const handleEdit = (row: RowData) => {
  dialogTitle.value = '编辑';
  Object.assign(formData, row);
  dialogVisible.value = true;
};

const handleDelete = async (row: RowData) => {
  // TODO: 调用删除 API
  console.log('Delete:', row.id);
};

const handleConfirm = async () => {
  await formRef.value?.validate();
  // TODO: 调用保存 API
  dialogVisible.value = false;
  fetchData();
};

const fetchData = async () => {
  // TODO: 调用列表 API
  console.log('Fetch data:', { tab: activeTab.value, searchKey: searchKey.value, ...pagination });
};

// 初始化
fetchData();
</script>

<style scoped>
.table-page {
  height: 100%;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* Tab 按钮组样式 */
.filter-tab :deep(.bk-tab-header) {
  border: 1px solid #dcdee5;
  border-radius: 2px;
  background: #fff;
}

.filter-tab :deep(.bk-tab-header-item) {
  border: none;
  background: transparent;
  padding: 0 16px;
}

.filter-tab :deep(.bk-tab-header-item.is-active) {
  background: #e1ecff;
  color: #3a84ff;
}

.search-icon {
  cursor: pointer;
}

.mb16 {
  margin-bottom: 16px;
}
</style>
