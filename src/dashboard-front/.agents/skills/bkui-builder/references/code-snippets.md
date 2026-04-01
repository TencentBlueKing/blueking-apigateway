# 常用代码片段

> 按需获取，用于快速复制粘贴

---

## Tab 按钮组样式

当 Tab 外观类似按钮组（有外边框包围、选中项高亮）时：

```vue
<bk-tab v-model:active="activeTab" type="card" class="filter-tab">
  <bk-tab-panel name="all" :label="`全部 (${totalCount})`" />
  <bk-tab-panel name="enabled" :label="`启用 (${enabledCount})`" />
  <bk-tab-panel name="disabled" :label="`停用 (${disabledCount})`" />
</bk-tab>

<style scoped>
.filter-tab :deep(.bk-tab-header) {
  border: 1px solid #dcdee5;
  border-radius: 2px;
  background: #fff;
}
.filter-tab :deep(.bk-tab-header-item) {
  border: none;
  background: transparent;
}
.filter-tab :deep(.bk-tab-header-item.is-active) {
  background: #e1ecff;
  color: #3a84ff;
}
</style>
```

---

## 表格列配置详解

```typescript
// 典型的管理页表格列配置
const columns = [
  // 基础文本列
  { label: '名称', field: 'name', width: 150 },

  // 带排序的列 (设计稿有 ↑↓ 图标)
  { label: '更新人', field: 'updatedBy', width: 100, sort: true },
  { label: '更新时间', field: 'updatedAt', width: 170, sort: { value: 'desc' } },

  // 带筛选的列 (设计稿有漏斗图标)
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

  // 长文本溢出省略
  { label: '定义', field: 'definition', showOverflowTooltip: true },

  // 自定义渲染列 (Tag/Switcher/操作)
  { label: '来源', field: 'source', width: 100 },  // 用 #source 插槽
  { label: '启停', field: 'enabled', width: 80 },  // 用 #enabled 插槽
  { label: '操作', field: 'operation', width: 120 } // 用 #operation 插槽
];
```

## 表格自定义列插槽示例

```vue
<bk-table :data="tableData" :columns="columns">
  <!-- Tag 列 -->
  <template #source="{ row }">
    <bk-tag :theme="row.source === 'builtin' ? 'info' : 'success'">
      {{ row.source === 'builtin' ? '内置' : '自定义' }}
    </bk-tag>
  </template>

  <!-- Switcher 列 -->
  <template #enabled="{ row }">
    <bk-switcher
      v-model="row.enabled"
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
```

## 工具栏布局示例

```vue
<!-- 左侧新建按钮 + 右侧 Tab 筛选和搜索框 -->
<div class="toolbar">
  <bk-button theme="primary" @click="handleCreate">
    <Add class="mr5" />
    新建
  </bk-button>

  <div class="toolbar-right">
    <!-- Tab 筛选 -->
    <bk-tab v-model:active="activeTab" type="unborder-card">
      <bk-tab-panel name="all" :label="`全部(${totalCount})`" />
      <bk-tab-panel name="enabled" :label="`启用(${enabledCount})`" />
      <bk-tab-panel name="disabled" :label="`停用(${disabledCount})`" />
    </bk-tab>

    <!-- 搜索框 -->
    <bk-input
      v-model="searchKey"
      placeholder="搜索 名称、描述、更新人、定义"
      :clearable="true"
      style="width: 280px"
    >
      <template #suffix>
        <Search class="search-icon" @click="handleSearch" />
      </template>
    </bk-input>
  </div>
</div>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
</style>
```
