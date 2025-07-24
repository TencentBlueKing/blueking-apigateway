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
  <div class="page-wrapper-padding system-container">
    <div class="ag-top-header">
      <BkAlert
        type="info"
        :title="t('请将新系统的接口，直接接入 API 网关')"
      />
      <div class="flex mt-16px mb-16px">
        <BkInput
          v-model="keyword"
          clearable
          class="w-370px system-search"
          :placeholder="t('请输入系统名称、描述，按Enter搜索')"
          :right-icon="'bk-icon icon-search'"
          @enter="handleSearch"
        />
      </div>
    </div>

    <BkLoading :loading="isLoading">
      <BkTable
        ext-cls="ag-stage-table"
        :data="systemList"
        :pagination="pagination"
        :columns="tableColumns"
        :max-height="clientHeight"
        remote-pagination
        show-overflow-tooltip
        @page-limit-change="handlePageLimitChange"
        @page-value-change="handlePageChange"
      >
        <template #empty>
          <TableEmpty
            :is-loading="isLoading"
            :empty-type="tableEmptyConf.emptyType"
            :abnormal="tableEmptyConf.isAbnormal"
            @refresh="getSystemList"
            @clear-filter="handleClearFilterKey"
          />
        </template>
      </BkTable>
    </BkLoading>

    <!-- 编辑系统 -->
    <AddSystemSlider
      v-model:slider-params="sliderConfig"
      v-model:detail-data="formData"
      :init-data="initData"
      :category-list="categoryList"
      @create-category="handleCreateCategory"
      @done="handleSubmit"
    />

    <BkDialog
      :width="540"
      :is-show="deleteDialogConf.visible"
      :title="deleteDialogTitle"
      :theme="'primary'"
      header-position="center"
      :mask-close="false"
      ext-cls="delete-system-dialog-cls"
    >
      <div>
        <div
          v-dompurify-html="systemDelTips"
          class="text-[13px] m-t-8px m-b-8px"
        />
        <BkInput v-model="formRemoveConfirmCode" />
        <div class="m-t-10px text-[13px]">
          {{ t('注意：删除系统，将删除该系统下所有组件API') }}，
          <strong>{{ t('不可恢复') }}</strong>
        </div>
      </div>
      <template #footer>
        <BkButton
          theme="primary"
          :loading="deleteDialogConf.loading"
          :disabled="formRemoveConfirmCode !== curSystem.name"
          @click="handleDeleteSystem"
        >
          {{ t('确定') }}
        </BkButton>
        <BkButton @click="deleteDialogConf.visible = false">
          {{ t('取消') }}
        </BkButton>
      </template>
    </BkDialog>

    <BkDialog
      :is-show="docCategoryDialog.visible"
      :title="t('新建文档分类')"
      :header-position="docCategoryDialog.headerPosition"
      :width="docCategoryDialog.width"
      :mask-close="false"
      @after-leave="docCategoryDialog.categoryName = ''"
    >
      <div class="m-b-5px category-label">
        {{ t('分类名称') }}
      </div>
      <BkInput
        v-model="docCategoryDialog.categoryName"
        class="m-b-16px"
        @input.stop
      />
      <template #footer>
        <div>
          <BkButton
            :disabled="docCategoryDialog.categoryName === ''"
            theme="primary"
            :loading="docCategoryDialog.loading"
            @click="handleConfirm"
          >
            {{ t('确定') }}
          </BkButton>
          <BkButton
            class="m-l-4px"
            @click="docCategoryDialog.visible = false"
          >
            {{ t('取消') }}
          </BkButton>
        </div>
      </template>
    </BkDialog>
  </div>
</template>

<script lang="tsx" setup>
import {
  cloneDeep,
  delay,
  sortBy,
  sortedUniq,
} from 'lodash-es';
import { Message } from 'bkui-vue';
import { useMaxTableLimit } from '@/hooks';
import {
  addDocCategory,
  getDocCategory,
} from '@/services/source/category';
import {
  type ISystemItem,
  deleteSystem,
  getSystemDetail,
  getSystems,
} from '@/services/source/system';
import AddSystemSlider from './components/AddSystemSlider.vue';
import TableEmpty from '@/components/table-empty/Index.vue';

const { t } = useI18n();
const { maxTableLimit, clientHeight } = useMaxTableLimit({ allocatedHeight: 240 });

const getDefaultData = () => {
  return {
    name: '',
    description: '',
    description_en: '',
    comment: '',
    maintainers: [],
    timeout: 0,
    doc_category_name: '',
    doc_category_id: '',
    is_official: false,
  };
};

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
    label: t('描述'),
    field: 'description',
    render: ({ row }: { row?: Partial<ISystemItem> }) => {
      return (
        <span>
          {row?.description || '--' }
        </span>
      );
    },
  },
  {
    label: t('系统负责人'),
    field: 'maintainers',
    render: ({ row }: { row?: Partial<ISystemItem> }) => {
      return (
        <span>
          {row?.maintainers?.length ? row.maintainers.join('；') : '--' }
        </span>
      );
    },
  },
  {
    label: t('文档分类'),
    field: 'doc_category_id',
    render: ({ row }: { row?: Partial<ISystemItem> }) => {
      return (
        <span>
          {row?.doc_category_name || '--' }
        </span>
      );
    },
  },
  {
    label: t('操作'),
    field: 'operate',
    fixed: 'right',
    width: 150,
    render: ({ row }: { row?: Partial<ISystemItem> }) => {
      return (
        <div>
          <BkButton
            class="m-r-10px"
            theme="primary"
            text
            onClick={() => handleEditSys(row)}
          >
            { t('编辑') }
          </BkButton>
          <BkButton
            theme="primary"
            text
            disabled={row.is_official}
            onClick={() => handleDeleteSys(row)}
          >
            {
              row.is_official
                ? (
                  <span v-bk-tooltips={{ content: t('官方系统，不可删除') }}>
                    { t('删除') }
                  </span>
                )
                : t('删除')
            }
          </BkButton>
        </div>
      );
    },
  },
]);
const systemList = ref([]);
const initData = ref({});
const pagination = ref({
  offset: 0,
  limit: maxTableLimit,
  count: 0,
  limitList: sortedUniq(sortBy([10, 20, 50, 100, maxTableLimit])),
});
const curSystem = ref({});
const deleteDialogConf = ref({
  visible: false,
  loading: false,
});
const isLoading = ref(false);
const isFilter = ref(false);
const formData = ref(getDefaultData());
const categoryList = ref([]);
const allData = ref([]);
const displayData = ref([]);
const formRemoveConfirmCode = ref('');
const sliderConfig = ref({
  isShow: false,
  title: '',
});
const docCategoryDialog = ref({
  visible: false,
  width: 480,
  headerPosition: 'left',
  categoryName: '',
  loading: false,
});
const tableEmptyConf = ref({
  emptyType: '',
  isAbnormal: false,
});

const isEdit = computed(() => {
  return Object.keys(curSystem.value).length > 0;
}); ;
const systemDelTips = computed(() => {
  // 使用标识符
  return `请完整输入 <code class="system-del-tips">${curSystem.value.name}</code> 来确认删除系统！`;
});
const deleteDialogTitle = computed(() => {
  return `${t('确认删除系统')}【${curSystem.value.name}】？`;
});

watch(
  () => keyword.value,
  (newVal, oldVal) => {
    if (oldVal && !newVal && isFilter) {
      isFilter.value = false;
      pagination.value = Object.assign(pagination.value, {
        offset: 0,
        limit: maxTableLimit,
      });
      displayData.value = allData.value;
      systemList.value = getDataByPage();
    }
  },
);

const init = () => {
  getSystemList(true);
  getCategories();
};

const handleClearFilterKey = () => {
  keyword.value = '';
  getSystemList(true);
};

const handleCreateCategory = () => {
  docCategoryDialog.value.visible = true;
};

const handleConfirm = async () => {
  docCategoryDialog.value.loading = true;
  try {
    const res = await addDocCategory(docCategoryDialog.value.categoryName);
    categoryList.value.push({
      id: res.data.id,
      name: docCategoryDialog.value.categoryName,
    });
    formData.value.doc_category_id = res.data.id;
    docCategoryDialog.value.visible = false;
  }
  finally {
    docCategoryDialog.value.loading = false;
  }
};

const handleSubmit = () => {
  getSystemList(true);
};

const getCategories = async () => {
  const res = await getDocCategory();
  categoryList.value = res;
};

// 获取系统列表
const getSystemList = async (loading = false, curPage = 1) => {
  isLoading.value = loading;
  try {
    const res = await getSystems();
    allData.value = Object.freeze(res) || [];
    displayData.value = res;
    pagination.value.count = displayData.value.length;
    systemList.value = getDataByPage(curPage);
    tableEmptyConf.value.isAbnormal = false;
  }
  catch (e) {
    tableEmptyConf.value.isAbnormal = true;
    console.error(e);
  }
  finally {
    setDelay(1000);
  }
};

const handlePageLimitChange = (limit: number) => {
  pagination.value = Object.assign(pagination.value, {
    offset: 0,
    limit,
  });
  handlePageChange(pagination.value.offset);
};

// 改变页码
const handlePageChange = (page: number) => {
  isLoading.value = true;
  pagination.value.offset = page;
  const data = getDataByPage(page);
  systemList.value.splice(0, systemList.value.length, ...data);
  setDelay(1000);
};

// 前端分页
const getDataByPage = (page = 1) => {
  if (!page) {
    pagination.value.offset = 0;
    page = 1;
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

const handleDeleteSystem = async () => {
  deleteDialogConf.value.loading = true;
  try {
    await deleteSystem(curSystem.value.id);
    deleteDialogConf.value.visible = false;
    Message({
      theme: 'success',
      message: t('删除成功！'),
    });
    getSystemList(true, pagination.value.offset);
  }
  finally {
    deleteDialogConf.value.loading = false;
  }
};

const handleSearch = (payload: string) => {
  if (!payload) {
    return;
  }
  isLoading.value = true;
  pagination.value = Object.assign(pagination.value, {
    offset: 0,
    limit: maxTableLimit,
  });
  isFilter.value = true;
  displayData.value = allData.value.filter((item) => {
    const reg = new RegExp(`(${payload})`, 'gi');
    return item.name.match(reg) || item.description.match(reg);
  });
  pagination.value.count = displayData.value.length;
  systemList.value = getDataByPage();
  setDelay(1000);
};

const handleEditSys = async (data: ISystemItem) => {
  curSystem.value = data;
  sliderConfig.value = Object.assign({}, {
    isShow: true,
    title: t(isEdit.value ? '编辑系统' : '新建系统'),
    isLoading: true,
  });
  try {
    const res = await getSystemDetail(data.id);
    formData.value = Object.assign({}, res);
    initData.value = cloneDeep(formData.value);
  }
  finally {
    sliderConfig.value.isLoading = false;
  }
};

const handleDeleteSys = (data: ISystemItem) => {
  curSystem.value = data;
  deleteDialogConf.value.visible = true;
};

const updateTableEmptyConfig = () => {
  if (keyword.value || !systemList.value.length) {
    tableEmptyConf.value.emptyType = 'searchEmpty';
    return;
  }
  if (keyword.value) {
    tableEmptyConf.value.emptyType = 'empty';
    return;
  }
  tableEmptyConf.value.emptyType = '';
};

const setDelay = (duration: number) => {
  delay(() => {
    isLoading.value = false;
  }, duration);
};
init();
</script>

<style lang="scss" scoped>
.system-search {
  width: 328px;
  margin-left: auto;
}

:deep(.official) {
  margin-left: 2px;
  padding: 2px;
  background: #dcffe2;
  font-size: 12px;
  color: #2dcb56;
}

code {
  padding: 0;
  padding-top: 0.2em;
  padding-bottom: 0.2em;
  margin: 0;
  color: #c7254e;
  font-size: 85%;
  background-color: rgba(0, 0, 0, 0.04);
  border-radius: 3px;
}

.category-label {
  position: relative;

  &::after {
    content: '*';
    margin-left: 2px;
    color: #ea3636;
  }
}
</style>

<style lang="scss">
.system-del-tips {
  padding: 0;
  padding-top: 0.2em;
  padding-bottom: 0.2em;
  margin: 0;
  color: #c7254e;
  font-size: 85%;
  background-color: rgba(0, 0, 0, 0.04);
  border-radius: 3px;
}

.delete-system-dialog-cls .bk-modal-content {
  padding-bottom: 20px !important;
}
</style>
