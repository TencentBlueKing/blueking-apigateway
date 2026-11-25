---
id: bkui-cheatsheet
name: bkui-cheatsheet
category: engineering
description: BKUI 3.0 组件属性速查表与本仓避坑指南（PascalCase、AgTable/UserSelector 衔接）
tags: [bkui, cheatsheet, props, pitfalls]
---

# BKUI 3.0 组件属性速查表

在 `src/dashboard-front/` 使用 `bkui-vue` 时，严格遵守以下属性映射与本仓规范（模板使用 **PascalCase**、布尔属性简写、文案使用 `t('...')`），**严禁套用 ElementUI / AntD 属性名**。

## 高频易错属性速查

| 组件 | 错误写法 | 正确写法 |
| --- | --- | --- |
| `BkButton` | `type="primary"` | `theme="primary"` |
| `BkInput` | `prefix-icon="xx"` | `<template #prefix>` / `<template #suffix>` |
| 图标 | `import { Plus } from '@bkui-vue/icon'` | 优先 `<AgIcon name="..." />`；BKUI 内置图标从 `bkui-vue/lib/icon` 导入 |
| `BkDialog` | `v-model="show"` | `v-model:is-show="show"`（或 `v-model:isShow`） |
| `BkTab` | `v-model="activeTab"` | `v-model:active="activeTab"` |
| `BkDatePicker` | `shortcuts.value: []` / `type="datetime-range"` | `shortcuts.value: () => []` / `type="datetimerange"`（列表筛选优先复用 `useDatePicker`） |
| 数据表格 | 业务列表页裸写 `<BkTable>` | 统一使用 `@/components/base/ag-table` 的泛型 `<AgTable>`；极简静态表用 `<BkTable>` 时远程分页需加 `remote-pagination` |
| 人员选择 | 在页面里自行判断 `isTenantMode` | 统一使用 `@/components/user/user-selector/Index.vue`（`<UserSelector>`） |

## 基础组件速查

```vue
<template>
  <!-- Button -->
  <BkButton theme="primary">
    {{ t('主要') }}
  </BkButton>
  <BkButton
    theme="primary"
    text
  >
    {{ t('编辑') }}
  </BkButton>

  <!-- Input + 内置图标 -->
  <BkInput
    v-model="keyword"
    clearable
  >
    <template #prefix>
      <Search />
    </template>
  </BkInput>
</template>

<script setup lang="ts">
import { Search } from 'bkui-vue/lib/icon';

const { t } = useI18n();
const keyword = shallowRef('');
</script>
```

## 极简静态表格（仅无分页/筛选/列设置场景）

> 业务列表页请直接使用 `<AgTable>`，完整用法见 [AgTable 指南](../../../src/components/base/ag-table/README.md)。

```vue
<template>
  <BkTable
    :data="list"
    :pagination="pagination"
    remote-pagination
  >
    <BkTableColumn
      :label="t('名称')"
      prop="name"
    />
    <BkTableColumn :label="t('操作')">
      <template #default="{ row }">
        <BkButton
          theme="primary"
          text
          @click="handleEdit(row)"
        >
          {{ t('编辑') }}
        </BkButton>
      </template>
    </BkTableColumn>
  </BkTable>
</template>
```

> `BkTable` 分页对象字段为 `{ current, limit, count }`。

## 按需加载资源

- `./references/complex-components.md` — `BkSelect` / `BkSearchSelect` / `BkDatePicker` / `BkUpload` / `BkTree` / `BkForm` 详细避坑
