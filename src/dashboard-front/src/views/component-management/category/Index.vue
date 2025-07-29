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
        class="float-right"
        clearable
        :placeholder="t('请输入文档分类名称，按Enter搜索')"
        :right-icon="'bk-icon icon-search'"
        style="width: 240px"
        @enter="handleSearch"
      />
    </div>
    <BkLoading :loading="isLoading">
      <BkTable
        size="small"
        class="m-t-16px"
        border="outer"
        ext-cls="ag-stage-table"
        :max-height="clientHeight"
        :columns="tableColumns"
        :data="docCategoryList"
        :pagination="pagination"
        remote-pagination
        show-overflow-tooltip
        @page-limit-change="handlePageLimitChange"
        @page-value-change="handlePageChange"
      >
        <template #empty>
          <TableEmpty
            :empty-type="tableEmptyConf.emptyType"
            :abnormal="tableEmptyConf.isAbnormal"
            @refresh="getDocCategoryList(true)"
            @clear-filter="clearFilterKey"
          />
        </template>
      </BkTable>
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
import {
  sortBy,
  sortedUniq,
} from 'lodash-es';
import { Message } from 'bkui-vue';
import { useMaxTableLimit, usePopInfoBox } from '@/hooks';
import {
  type ICategoryItem,
  addDocCategory,
  deleteDocCategory,
  getDocCategory,
  updateDocCategory,
} from '@/services/source/category';
import TableEmpty from '@/components/table-empty/Index.vue';

type IFormMethod = {
  validate: () => void
  clearValidate: () => void
};

const { t } = useI18n();
const { maxTableLimit, clientHeight } = useMaxTableLimit();

const validateFormRef = ref<InstanceType<typeof BkForm> & IFormMethod>();
const keyword = ref('');
const tableColumns = ref([
  {
    label: t('名称'),
    field: 'name',
    render: ({ row }: { row?: Partial<ISystemItem> }) => {
      return (
        <span>
          <span class="m-r-4px">{row?.name || '--' }</span>
          { row.is_official && <span class="official">{ t('官方') }</span> }
        </span>
      );
    },
  },
  {
    label: t('优先级'),
    field: 'priority',
    render: ({ row }: { row?: Partial<ISystemItem> }) => {
      return (
        <span>
          { row.priority || '--'}
        </span>
      );
    },
  },
  {
    label: t('关联系统数量'),
    field: 'system_count',
  },
  {
    label: t('更新时间'),
    field: 'updated_time',
  },
  {
    label: t('操作'),
    field: 'operate',
    width: 150,
    render: ({ row }: { row?: Partial<ISystemItem> }) => {
      return (
        <div>
          <BkButton
            class="m-r-10px"
            theme="primary"
            text
            onClick={() => handleEdit(row)}
          >
            { t('编辑') }
          </BkButton>
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
const docCategoryList = ref([]);
const pagination = ref({
  offset: 1,
  count: 0,
  limit: maxTableLimit,
  limitList: sortedUniq(sortBy([10, 20, 50, 100, maxTableLimit])),
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
const isFilter = ref(false);
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
const tableEmptyConf = ref({
  emptyType: '',
  isAbnormal: false,
});
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

watch(keyword, (newVal, oldVal) => {
  if (oldVal && !newVal && isFilter.value) {
    isFilter.value = false;
    displayData.value = allData.value;
    pagination.value = Object.assign(pagination.value, {
      offset: 0,
      limit: maxTableLimit,
      count: displayData.value.length,
    });
    docCategoryList.value = getDataByPage();
  }
});

const init = () => {
  getDocCategoryList(true);
};

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

// 获取文档分类列表
const getDocCategoryList = async (loading = false) => {
  isLoading.value = loading;
  try {
    const res = await getDocCategory();
    allData.value = Object.freeze(res);
    displayData.value = res;
    allData.value.forEach((item) => {
      if (!classifyFilters.value.map(subItem => subItem.value).includes(item.doc_category_id)) {
        classifyFilters.value.push({
          text: item.doc_category_name,
          value: item.doc_category_id,
        });
      }
    });
    pagination.value.count = displayData.value.length;
    docCategoryList.value = getDataByPage();
    tableEmptyConf.value.isAbnormal = false;
  }
  catch (e) {
    tableEmptyConf.value.isAbnormal = true;
    console.error(e);
  }
  finally {
    setTimeout(() => {
      isLoading.value = false;
    }, 500);
  }
};

const handlePageLimitChange = (limit) => {
  pagination.value = Object.assign(pagination.value, {
    offset: 0,
    limit,
  });
  handlePageChange(pagination.value.offset);
};

const handlePageChange = (page) => {
  pagination.value.offset = page;
  const data = getDataByPage(page);
  docCategoryList.value.splice(0, docCategoryList.value.length, ...data);
};

// 获取当前页数据
const getDataByPage = (page?: number) => {
  if (!page) {
    pagination.value.offset = page = 1;
  }
  let startIndex = (page - 1) * pagination.value.limit;
  let endIndex = page * pagination.value.limit;
  if (startIndex < 0) {
    startIndex = 0;
  }
  if (endIndex > displayData.value.length) {
    endIndex = displayData.value.length;
  }
  updateTableEmptyConfig();
  return displayData.value.slice(startIndex, endIndex);
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
  if (!payload) {
    return;
  }
  pagination.value = Object.assign(pagination.value, {
    offset: 0,
    limit: maxTableLimit,
  });
  isFilter.value = true;
  displayData.value = allData.value.filter((item) => {
    const reg = new RegExp(`(${payload})`, 'gi');
    return item.name.match(reg);
  });
  pagination.value.count = displayData.value.length;
  docCategoryList.value = getDataByPage();
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

const clearFilterKey = () => {
  keyword.value = '';
  getDocCategoryList(true);
};

const updateTableEmptyConfig = () => {
  tableEmptyConf.value.emptyType = keyword.value ? 'searchEmpty' : 'empty';
};

init();
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
