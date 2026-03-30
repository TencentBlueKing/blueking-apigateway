# 高级组件避坑指南

> 详细的复杂组件使用说明

## Select / SearchSelect

### 多选 Tag 模式
- **Select**: 必须显式设置 `multiple-mode="tag"`，否则默认是文本拼接
- **SearchSelect**: 使用 `display-tag` 属性

```vue
<!-- Select -->
<bk-select v-model="value" multiple multiple-mode="tag">
  <bk-option value="1" label="选项1" />
</bk-select>

<!-- SearchSelect -->
<bk-search-select v-model="value" :data="list" display-tag />
```

### 键名配置差异

**重要**：两者默认值不同！

| 组件 | id-key 默认值 | display-key 默认值 |
|------|--------------|-------------------|
| Select | `value` | `label` |
| SearchSelect | `id` | `name` |

```typescript
// Select 数据格式
const selectOptions = [
  { value: '1', label: '选项1' }
];

// SearchSelect 数据格式
const searchOptions = [
  { id: '1', name: '选项1' }
];
```

### 远程搜索

必须配合 `filterable` 和 `remote-method`：

```vue
<bk-select
  v-model="value"
  filterable
  :remote-method="handleSearch"
  :loading="loading"
>
  <bk-option
    v-for="item in filteredList"
    :key="item.id"
    :value="item.id"
    :label="item.name"
  />
</bk-select>
```

## DatePicker 日期选择

### 快捷方式陷阱

`shortcuts` 的 `value` **必须是函数**，不能是静态值！

```javascript
// ❌ 错误：静态值
const shortcuts = [
  {
    text: '今天',
    value: [new Date(), new Date()] // 只会计算一次
  }
];

// ✅ 正确：函数
const shortcuts = [
  {
    text: '今天',
    value: () => {
      const now = new Date();
      return [now, now];
    }
  },
  {
    text: '最近7天',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(start.getDate() - 7);
      return [start, end];
    }
  }
];
```

### 类型名称陷阱

范围类型是**一个单词**，中间没有连字符：

| 错误 | 正确 |
|------|------|
| `datetime-range` | `datetimerange` |
| `date-range` | `daterange` |

```vue
<bk-date-picker
  v-model="dateRange"
  type="datetimerange"
  :shortcuts="shortcuts"
/>
```

## Upload 文件上传

### 响应码判断

默认只认 `res.code === 0`，如果后端返回 `result: true`，需要自定义：

```vue
<bk-upload
  :url="uploadUrl"
  :handle-res-code="(res) => res.result === true"
/>
```

### 大小限制单位

`size` 属性单位是 **MB**：

```vue
<!-- 限制 10MB -->
<bk-upload :size="10" />
```

### 文件数组绑定

`files` 是**单向绑定**的初始值，不要用 v-model：

```vue
<!-- ❌ 错误 -->
<bk-upload v-model:files="fileList" />

<!-- ✅ 正确 -->
<bk-upload
  :files="fileList"
  @change="handleFileChange"
/>
```

## Tree 树形组件

### 唯一标识

推荐显式设置 `node-key`：

```vue
<bk-tree
  :data="treeData"
  node-key="id"
/>
```

### 虚拟滚动高度

默认开启虚拟滚动，必须设置高度：

```vue
<bk-tree
  :data="treeData"
  :height="500"
/>
```

或者确保父容器有明确高度：

```css
.tree-container {
  height: 500px;
}
```

### 数据刷新

修改 `data` 数组后，建议手动重置：

```typescript
const treeRef = ref();

const refreshTree = () => {
  treeData.value = [...newData];
  nextTick(() => {
    treeRef.value?.reset();
  });
};
```

## Form 表单验证

### 验证时机

- `trigger: 'blur'` - 失焦时验证
- `trigger: 'change'` - 值改变时验证
- 手动验证：`formRef.value.validate()`

### 异步验证

validator 可以返回 Promise：

```typescript
const rules = {
  username: [
    {
      validator: async (value) => {
        const exists = await checkUsernameExists(value);
        if (exists) {
          return '用户名已存在';
        }
        return true;
      },
      trigger: 'blur'
    }
  ]
};
```

### 动态表单项

使用 `v-for` 生成的表单项，`property` 必须用数组语法：

```vue
<bk-form-item
  v-for="(item, index) in list"
  :key="index"
  :label="`项目${index + 1}`"
  :property="`list.${index}.value`"
  :rules="[{ required: true }]"
>
  <bk-input v-model="list[index].value" />
</bk-form-item>
```
