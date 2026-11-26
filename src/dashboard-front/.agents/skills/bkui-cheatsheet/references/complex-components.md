# 高级组件避坑指南

> 本仓 `bkui-vue` 3.0 复杂组件高频坑点，示例已遵循本仓 PascalCase、`<script setup lang="ts">`、`useTemplateRef`、`I` 前缀与国际化规范。

## Select / SearchSelect

### 多选 Tag 模式

- **`BkSelect`**：必须显式设置 `multiple-mode="tag"`，否则默认是文本拼接。
- **`BkSearchSelect`**：使用布尔简写 `display-tag`。

```vue
<template>
  <BkSelect
    v-model="selectedValues"
    multiple
    multiple-mode="tag"
  >
    <BkOption
      value="1"
      :label="t('选项 1')"
    />
  </BkSelect>

  <BkSearchSelect
    v-model="searchValues"
    :data="searchOptions"
    display-tag
  />
</template>
```

### 默认键名差异

| 组件 | `id-key` 默认值 | `display-key` 默认值 |
| --- | --- | --- |
| `BkSelect` | `value` | `label` |
| `BkSearchSelect` | `id` | `name` |

### 远程搜索

必须配合 `filterable` 与 `:remote-method`：

```vue
<template>
  <BkSelect
    v-model="selectedId"
    filterable
    :remote-method="handleSearch"
    :loading="loading"
  >
    <BkOption
      v-for="item in filteredList"
      :key="item.id"
      :value="item.id"
      :label="item.name"
    />
  </BkSelect>
</template>
```

---

## DatePicker 日期选择

> 本仓列表页的日期范围筛选应优先使用 `useDatePicker(filter, { presets, defaultPreset })` 并配合 `@/utils/time-range` 转换秒级时间戳；网关仪表盘、统计报表使用 `@blueking/date-picker` + `@/utils/date-picker-range`。以下为直接使用 `<BkDatePicker>` 时的底层避坑点。

### 快捷方式 `value` 必须是函数

```typescript
interface IDateShortcut {
  text: string
  value: () => [Date, Date]
}

// 正确：每次点击动态计算当前时间（静态数组只会计算一次）
const shortcuts = computed<IDateShortcut[]>(() => [
  {
    text: t('今天'),
    value: () => {
      const now = new Date();
      return [now, now];
    },
  },
  {
    text: t('最近 7 天'),
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(start.getDate() - 7);
      return [start, end];
    },
  },
]);
```

### 范围类型名称无连字符

| 错误 | 正确 |
| --- | --- |
| `datetime-range` | `datetimerange` |
| `date-range` | `daterange` |

```vue
<template>
  <BkDatePicker
    v-model="dateRange"
    type="datetimerange"
    :shortcuts="shortcuts"
  />
</template>
```

---

## Upload 文件上传

### 响应码判断

默认仅认 `res.code === 0`；若接口返回 `result: true`，需自定义 `:handle-res-code`：

```vue
<template>
  <BkUpload
    :url="uploadUrl"
    :size="10"
    :handle-res-code="(res: { result?: boolean }) => res.result === true"
  />
</template>
```

> `size` 属性单位为 **MB**。

### `files` 为单向绑定初始值，不要用 `v-model`

```vue
<template>
  <!-- 正确 -->
  <BkUpload
    :files="fileList"
    @change="handleFileChange"
  />
</template>
```

---

## Tree 树形组件

- 推荐显式设置 `node-key="id"`；
- 默认开启虚拟滚动，需传 `:height="500"` 或确保父容器有明确高度；
- 替换 `data` 后如需重置内部状态，通过 `useTemplateRef` 在 `nextTick` 后调用 `reset()`：

```vue
<template>
  <BkTree
    ref="treeRef"
    :data="treeData"
    node-key="id"
    :height="500"
  />
</template>

<script setup lang="ts">
import type { Tree } from 'bkui-vue';

interface ITreeNode {
  id: string
  name: string
  children?: ITreeNode[]
}

const treeRef = useTemplateRef<InstanceType<typeof Tree>>('treeRef');
const treeData = shallowRef<ITreeNode[]>([]);

const refreshTree = async (nextData: ITreeNode[]) => {
  treeData.value = [...nextData];
  await nextTick();
  treeRef.value?.reset();
};
</script>
```

---

## Form 表单验证

### 异步验证

`validator` 支持返回 `Promise<boolean | string>`：

```typescript
const rules = computed(() => ({
  username: [
    {
      validator: async (value: string) => {
        const exists = await checkUsernameExists(value);
        return exists ? t('用户名已存在') : true;
      },
      trigger: 'blur',
    },
  ],
}));
```

### 动态表单项（稳定 `:key` + 索引 `property`）

动态增删的表单项中，**`:key` 必须使用稳定唯一标识（如 `item.uid`）而非 `index`**，避免删除中间项时输入框状态与校验信息错位；同时 `property` 仍按数组下标路径拼接，供 `BkForm` 定位字段：

```vue
<template>
  <BkFormItem
    v-for="(item, index) in formData.list"
    :key="item.uid"
    :label="t('项目 {index}', { index: index + 1 })"
    :property="`list.${index}.value`"
    :rules="itemRules"
  >
    <BkInput v-model="item.value" />
  </BkFormItem>
</template>

<script setup lang="ts">
interface IDynamicItem {
  uid: string
  value: string
}

const { t } = useI18n();

const formData = reactive<{ list: IDynamicItem[] }>({
  list: [
    {
      uid: crypto.randomUUID(),
      value: '',
    },
  ],
});

const itemRules = computed(() => [
  {
    required: true,
    message: t('必填项'),
    trigger: 'blur',
  },
]);
</script>
```
