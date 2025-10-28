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
          @clear="handleClearFilter"
        />
      </div>
    </div>
    <BkLoading :loading="isLoading">
      <AgTable
        ref="tableRef"
        v-model:table-data="displayData"
        show-settings
        resizable
        local-page
        :table-empty-type="tableEmptyType"
        :max-limit-config="{ allocatedHeight: 300, mode: 'tdesign'}"
        :columns="tableColumns"
        @clear-filter="handleClearFilter"
      />
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
import { Button, Message } from 'bkui-vue';
import type { ITableMethod } from '@/types/common';
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
import AgTable from '@/components/ag-table/Index.vue';
import AddSystemSlider from './components/AddSystemSlider.vue';

const { t } = useI18n();

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

const tableRef = useTemplateRef<InstanceType<typeof AgTable> & ITableMethod>('tableRef');
const isLoading = ref(false);
const keyword = ref('');
const tableEmptyType = ref<'empty' | 'search-empty'>('empty');
const tableColumns = ref([
  {
    title: t('名称'),
    colKey: 'name',
    ellipsis: true,
    cell: (h, { row }: { row?: Partial<ISystemItem> }) => {
      return (
        <div class="flex-row">
          <div
            v-bk-tooltips={{
              content: row.name,
              placement: 'top',
              disabled: !row.isOverflow,
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
    title: t('描述'),
    colKey: 'description',
    ellipsis: true,
    cell: (h, { row }: { row?: Partial<ISystemItem> }) => {
      return (
        <span>
          {row?.description || '--' }
        </span>
      );
    },
  },
  {
    title: t('系统负责人'),
    colKey: 'maintainers',
    ellipsis: true,
    cell: (h, { row }: { row?: Partial<ISystemItem> }) => {
      return (
        <span>
          {row?.maintainers?.length ? row.maintainers.join('；') : '--' }
        </span>
      );
    },
  },
  {
    title: t('文档分类'),
    colKey: 'doc_category_id',
    ellipsis: true,
    cell: (h, { row }: { row?: Partial<ISystemItem> }) => {
      return (
        <span>
          {row?.doc_category_name || '--' }
        </span>
      );
    },
  },
  {
    title: t('操作'),
    colKey: 'operate',
    fixed: 'right',
    width: 150,
    cell: (h, { row }: { row?: Partial<ISystemItem> }) => {
      return (
        <div>
          <Button
            class="mr-10px"
            theme="primary"
            text
            onClick={() => handleEditSys(row)}
          >
            { t('编辑') }
          </Button>
          <Button
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
          </Button>
        </div>
      );
    },
  },
]);
const initData = ref({});
const pagination = ref({
  offset: 0,
  limit: 10,
  count: 0,
  limitList: sortedUniq(sortBy([10, 20, 50, 100])),
});
const curSystem = ref({});
const deleteDialogConf = ref({
  visible: false,
  loading: false,
});
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

const getCategories = async () => {
  const res = await getDocCategory();
  categoryList.value = res;
};

// 获取系统列表
const getSystemList = async (loading = false) => {
  isLoading.value = loading;
  try {
    const res = await getSystems();
    const results = Object.freeze(res || []);
    [allData.value, displayData.value] = [results, results];
    pagination.value.count = displayData.value.length;
  }
  finally {
    setDelay(1000);
  }
};

const init = () => {
  getCategories();
  getSystemList();
};
init();

const handleClearFilter = () => {
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
  tableEmptyType.value = payload ? 'search-empty' : 'empty';
  if (!payload) {
    return;
  }
  isLoading.value = true;
  pagination.value = Object.assign(pagination.value, {
    offset: 0,
    limit: 10,
  });
  displayData.value = allData.value.filter((item) => {
    const reg = new RegExp(`(${payload})`, 'gi');
    return item.name.match(reg) || item.description.match(reg);
  });
  pagination.value.count = displayData.value.length;
  setDelay(500);
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

const setDelay = (duration: number) => {
  delay(() => {
    isLoading.value = false;
  }, duration);
};
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
