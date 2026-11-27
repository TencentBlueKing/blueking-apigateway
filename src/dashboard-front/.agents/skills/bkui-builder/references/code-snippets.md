# 常用代码片段

> 已按本仓 ESLint、`vue-code-style.md`、`ts-style.md`、`AgTable` 与 UnoCSS 规范编写，可直接参考复用。

---

## 1. 胶囊筛选组（Radio Capsule）

当选项之间有竖线分隔、仅用于切换筛选条件而不切换独立内容面板时，使用 `BkRadioGroup`：

```vue
<template>
  <BkRadioGroup
    v-model="activeStatus"
    type="capsule"
    @change="handleStatusChange"
  >
    <BkRadioButton label="all">
      {{ t('全部 ({count})', { count: totalCount }) }}
    </BkRadioButton>
    <BkRadioButton label="enabled">
      {{ t('启用 ({count})', { count: enabledCount }) }}
    </BkRadioButton>
    <BkRadioButton label="disabled">
      {{ t('停用 ({count})', { count: disabledCount }) }}
    </BkRadioButton>
  </BkRadioGroup>
</template>
```

---

## 2. 列表页工具栏布局

左侧主操作按钮 + 右侧筛选与搜索框，优先使用 UnoCSS 原子类：

```vue
<template>
  <div class="flex items-center justify-between mb-16px">
    <BkButton
      theme="primary"
      @click="handleCreate"
    >
      <Plus class="text-18px mr-4px" />
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
</template>

<script setup lang="ts">
import { Plus, Search } from 'bkui-vue/lib/icon';

const { t } = useI18n();

const activeStatus = shallowRef<'all' | 'enabled'>('all');
const keyword = shallowRef('');

const handleCreate = () => {
  // 打开新建侧滑抽屉或弹窗
};

const handleSearch = () => {
  // 触发列表重置页码查询
};
</script>
```

---

## 3. `<AgTable>` 典型列配置（TSX）

列表页统一使用 `<AgTable>`，列数组使用 `shallowRef<ITableColumn<IRow>[]>`（静态结构）或 `computed(() => defineTableColumns<IRow>([...]))`（动态显隐列）：

```tsx
import { Button, Switcher, Tag } from 'bkui-vue';
import type { ITableColumn } from '@/components/base/ag-table';

interface IItemRow {
  id: number
  name: string
  source: 'builtin' | 'custom'
  enabled: boolean
  updated_time: string
}

const columns = shallowRef<ITableColumn<IItemRow>[]>([
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
    title: t('更新时间'),
    colKey: 'updated_time',
    width: 180,
    sorter: true,
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
```

---

## 4. 侧滑表单（`<AgSideslider>`）与 `useTemplateRef` 校验

```vue
<template>
  <AgSideslider
    v-model:is-show="isShow"
    :title="t('新建配置')"
    :width="640"
    @closed="handleClosed"
  >
    <template #default>
      <BkForm
        ref="formRef"
        class="p-24px"
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
      </BkForm>
    </template>

    <template #footer>
      <div class="flex items-center gap-8px">
        <BkButton
          theme="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          {{ t('提交') }}
        </BkButton>
        <BkButton @click="isShow = false">
          {{ t('取消') }}
        </BkButton>
      </div>
    </template>
  </AgSideslider>
</template>

<script setup lang="ts">
import type { Form } from 'bkui-vue';
import AgSideslider from '@/components/base/ag-sideslider/Index.vue';

interface IFormModel {
  name: string
}

const isShow = defineModel<boolean>('isShow', { default: false });

const emit = defineEmits<{
  done: []
}>();

const { t } = useI18n();

const formRef = useTemplateRef<InstanceType<typeof Form>>('formRef');
const submitting = shallowRef(false);
const formData = reactive<IFormModel>({
  name: '',
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

const handleSubmit = async () => {
  await formRef.value?.validate();
  submitting.value = true;
  try {
    // 调用 src/services/source/ 对应接口
    isShow.value = false;
    emit('done');
  }
  finally {
    submitting.value = false;
  }
};

const handleClosed = () => {
  formRef.value?.clearValidate();
};
</script>
```
