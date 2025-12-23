/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */
<template>
  <div class="page-wrapper-padding category-container">
    <div class="ag-top-header">
      <BkInput
        v-model="keyword"
        class="float-right w-240px"
        clearable
        :placeholder="t('请输入文档分类名称，按Enter搜索')"
        :right-icon="'bk-icon icon-search'"
        @enter="handleSearch"
        @clear="handleClearFilter"
      />
    </div>

    <BkLoading :loading="isLoading">
      <AgTable
        ref="tableRef"
        v-model:table-data="displayData"
        show-settings
        resizable
        local-page
        :max-limit-config="{ allocatedHeight: 260, mode: 'tdesign'}"
        :columns="tableColumns"
        :table-empty-type="tableEmptyType"
        @clear-filter="handleClearFilter"
      />
    </BkLoading>

    <BkDialog
      :is-show="docCategoryDialog.visible"
      :title="docCategoryDialog.title"
      :header-position="docCategoryDialog.headerPosition"
      :loading="docCategoryDialog.loading"
      :width="docCategoryDialog.width"
      :mask-close="false"
      @after-leave="docCategoryDialog.categoryName = ''"
      @confirm="handleConfirm"
      @closed="closeDocCategoryDialog"
    >
      <BkForm
        ref="validateFormRef"
        :label-width="90"
        :model="docCategoryDialog"
        :rules="rules"
        form-type="vertical"
      >
        <BkFormItem
          :label="t('名称')"
          required
          :property="'name'"
          :error-display-type="'normal'"
        >
          <BkInput
            v-model="docCategoryDialog.name"
            :placeholder="t('请输入分类名称')"
            :disabled="curDocCategory.is_official"
          />
        </BkFormItem>
        <BkFormItem
          :label="t('优先级')"
          required
          :property="'priority'"
          :error-display-type="'normal'"
        >
          <BkInput
            v-model="docCategoryDialog.priority"
            :placeholder="t('请输入优先级，范围1 - 9999')"
            type="number"
            :max="9999"
            :min="1"
            show-controls
          />
          <p class="ag-tip m-t-10px">
            <i class="apigateway-icon icon-ag-info" />
            {{ t('文档展示时，将按照优先级从大到小排序') }}
          </p>
        </BkFormItem>
      </BkForm>
    </BkDialog>
  </div>
</template>

<script setup lang="tsx">
import { delay } from 'lodash-es';
import { Button, Form, Message } from 'bkui-vue';
import type { IFormMethod, ITableMethod } from '@/types/common';
import { usePopInfoBox } from '@/hooks';
import {
  type ICategoryItem,
  addDocCategory,
  deleteDocCategory,
  getDocCategory,
  updateDocCategory,
} from '@/services/source/category';
import AgTable from '@/components/ag-table/Index.vue';

const { t } = useI18n();

const tableRef = useTemplateRef<InstanceType<typeof AgTable> & ITableMethod>('tableRef');
const validateFormRef = ref<InstanceType<typeof Form> & IFormMethod>();
const keyword = ref('');
const tableColumns = ref([
  {
    title: t('名称'),
    colKey: 'name',
    cell: (h, { row }: { row?: Partial<ISystemItem> }) => {
      return (
        <div class="flex-row">
          <div
            v-bk-tooltips={{
              content: row.name,
              placement: 'top',
              disabled: !row.isOverflow,
              extCls: 'max-w-480px',
            }}
            class="truncate mr-4px"
            onMouseenter={e => tableRef.value?.handleCellEnter({
              e,
              row,
            })}
            onMouseLeave={e => tableRef.value?.handleCellLeave({
              e,
              row,
            })}
          >
            {row?.name || '--' }
          </div>
          { row.is_official && <span class="official">{ t('官方') }</span> }
        </div>
      );
    },
  },
  {
    title: t('优先级'),
    colKey: 'priority',
    ellipsis: true,
    cell: (h, { row }: { row?: Partial<ISystemItem> }) => {
      return (
        <span>
          { row.priority || '--'}
        </span>
      );
    },
  },
  {
    title: t('关联系统数量'),
    colKey: 'system_count',
    ellipsis: true,
  },
  {
    title: t('更新时间'),
    colKey: 'updated_time',
    ellipsis: true,
  },
  {
    title: t('操作'),
    colKey: 'operate',
    ellipsis: true,
    width: 150,
    cell: (h, { row }: { row?: Partial<ISystemItem> }) => {
      return (
        <div>
          <Button
            class="mr-10px"
            theme="primary"
            text
            onClick={() => handleEdit(row)}
          >
            { t('编辑') }
          </Button>
          <BkButton
            theme="primary"
            text
            disabled={row.is_official || row.system_count > 0}
            onClick={() => handleDelete(row)}
          >
            {
              row.is_official
              && (
                <span v-bk-tooltips={{ content: t('官方文档分类，不可删除') }}>
                  { t('删除') }
                </span>
              )
            }
            {
              row.system_count > 0 && !row.is_official
              && (
                <span v-bk-tooltips={{ content: t('存在关联系统，不可删除') }}>
                  { t('删除') }
                </span>
              )
            }
            { !row.is_official && row.system_count < 1 && t('删除') }
          </BkButton>
        </div>
      );
    },
  },
]);
const pagination = ref({
  offset: 1,
  count: 0,
  limit: 10,
});
const curDocCategory = ref({
  name: '',
  is_official: false,
  categoryName: '',
});
const allData = ref([]);
const displayData = ref([]);
const classifyFilters = ref([]);
const isLoading = ref(false);
const docCategoryDialog = ref({
  visible: false,
  width: 480,
  headerPosition: 'left',
  id: 0,
  name: '',
  priority: 1000,
  title: '',
  loading: false,
});
const tableEmptyType = ref<'empty' | 'search-empty'>('empty');
const rules = ref({
  name: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  priority: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
});

const handleConfirm = () => {
  docCategoryDialog.value.loading = true;
  validateFormRef.value?.validate().then(() => {
    if (docCategoryDialog.value.id) {
      updateDocCategoryFun();
    }
    else {
      createDocCategory();
    }
  })
    .catch(() => {
      docCategoryDialog.value.loading = false;
    });
};

// 创建文档分类
const createDocCategory = async () => {
  try {
    const data = {
      name: docCategoryDialog.value.name,
      priority: docCategoryDialog.value.priority,
    };
    await addDocCategory(data);
    getDocCategoryList(true);
    Message({
      theme: 'success',
      message: t('新建成功！'),
    });
    docCategoryDialog.value.visible = false;
  }
  finally {
    docCategoryDialog.value.loading = false;
  }
};

// 更新文档分类
const updateDocCategoryFun = async () => {
  try {
    await updateDocCategory(docCategoryDialog.value.id, {
      name: docCategoryDialog.value.name,
      priority: docCategoryDialog.value.priority,
    });
    getDocCategoryList(true);
    Message({
      theme: 'success',
      message: t('更新成功！'),
    });
    docCategoryDialog.value.visible = false;
  }
  finally {
    docCategoryDialog.value.loading = false;
  }
};

const setDelay = (duration: number) => {
  isLoading.value = true;
  delay(() => {
    isLoading.value = false;
  }, duration);
};

// 获取文档分类列表
const getDocCategoryList = async (loading = false) => {
  isLoading.value = loading;
  try {
    const res = await getDocCategory();
    [allData.value, displayData.value] = [Object.freeze(res), Object.freeze(res)];
    allData.value.forEach((item) => {
      if (!classifyFilters.value.map(subItem => subItem.value).includes(item.doc_category_id)) {
        classifyFilters.value.push({
          text: item.doc_category_name,
          value: item.doc_category_id,
        });
      }
    });
    pagination.value.count = displayData.value.length;
  }
  finally {
    setDelay(500);
  }
};
getDocCategoryList(true);

const updateTableEmptyConfig = () => {
  tableEmptyType.value = keyword.value ? 'search-empty' : 'empty';
};

// 编辑文档
const handleEdit = (data: ICategoryItem) => {
  curDocCategory.value = data;
  docCategoryDialog.value = Object.assign(docCategoryDialog.value, {
    title: t('编辑文档分类'),
    id: data.id,
    name: data.name,
    priority: data.priority,
    visible: true,
  });
};

const handleDeleteDocCategory = async (id: number) => {
  await deleteDocCategory(id);
  Message({
    theme: 'success',
    message: t('删除成功！'),
  });
  getDocCategoryList(true);
};

const handleSearch = (payload: string) => {
  updateTableEmptyConfig();
  displayData.value = allData.value.filter((item) => {
    const reg = new RegExp(`(${payload})`, 'gi');
    return item.name.match(reg);
  });
  pagination.value.count = displayData.value.length;
  setDelay(500);
};

const handleDelete = (data: ICategoryItem) => {
  curDocCategory.value = data;
  usePopInfoBox({
    title: t('确认删除'),
    type: 'warning',
    subTitle: `${t('确定要删除文档分类')}【${data.name}】?`,
    confirmText: t('删除'),
    confirmButtonTheme: 'danger',
    onConfirm: () => {
      handleDeleteDocCategory(data.id);
    },
  });
};

const closeDocCategoryDialog = () => {
  docCategoryDialog.value.visible = false;
  validateFormRef.value?.clearValidate();
};

const handleClearFilter = () => {
  keyword.value = '';
  getDocCategoryList(true);
};
</script>

<style lang="scss" scoped>
.category-container {
  .ag-top-header {
    min-height: 32px;
    margin-bottom: 20px;
    position: relative;
  }
}

:deep(.official) {
  margin-left: 2px;
  padding: 2px;
  background: #dcffe2;
  font-size: 12px;
  color: #2dcb56;
}
</style>
