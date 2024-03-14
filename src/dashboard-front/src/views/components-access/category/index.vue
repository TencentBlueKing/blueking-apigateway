<template>
  <div class="page-wrapper-padding category-container">
    <div class="ag-top-header">
      <!-- 新建文档分类操作 -->
      <!-- <bk-button theme="primary" @click="handleCreate"> {{ t('新建文档分类') }} </bk-button> -->
      <bk-input
        class="fr"
        :clearable="true"
        v-model="keyword"
        :placeholder="t('请输入文档分类名称，按Enter搜索')"
        :right-icon="'bk-icon icon-search'"
        style="width: 240px"
        @enter="handleSearch"
      ></bk-input>
    </div>
    <bk-loading :loading="isLoading">
      <bk-table
        style="margin-top: 15px"
        :data="docCategoryList"
        size="small"
        :pagination="pagination"
        ext-cls="ag-stage-table"
        @page-limit-change="handlePageLimitChange"
        @page-value-change="handlePageChange"
        border="outer"
      >
        <!-- <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getDocCategoryList(true)"
          @clear-filter="clearFilterKey"
        />
      </div> -->
        <template #empty>
          <TableEmpty
            :keyword="tableEmptyConf.keyword"
            :abnormal="tableEmptyConf.isAbnormal"
            @reacquire="getDocCategoryList(true)"
            @clear-filter="clearFilterKey"
          />
        </template>
        <bk-table-column :label="t('名称')">
          <template #default="{ row }">
            {{ row.name }}
            <template v-if="row.is_official">
              <span class="official">{{ t('官方') }}</span>
            </template>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('优先级')"
          prop="priority"
          :show-overflow-tooltip="true"
        >
          <template #default="props">
            <template v-if="props.row.priority">
              <span>{{ props.row.priority }}</span>
            </template>
            <template v-else>--</template>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('关联系统数量')"
          :show-overflow-tooltip="true"
        >
          <template #default="props">
            {{ props.row.system_count }}
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('更新时间')"
          prop="updated_time"
        >
          <template #default="props">
            {{ props.row.updated_time }}
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('操作')"
          width="150"
        >
          <template #default="{ row }">
            <bk-button
              class="mr10"
              text
              theme="primary"
              @click="handleEdit(row)"
            >
              {{ t('编辑') }}
            </bk-button>
            <bk-button
              class="mr10"
              text
              theme="primary"
              :disabled="row.is_official || row.system_count !== 0"
              @click="handleDelete(row)"
            >
              <template v-if="row.is_official">
                <span v-bk-tooltips="t('官方文档分类，不可删除')">{{ t('删除') }}</span>
              </template>
              <template v-else-if="row.system_count !== 0">
                <span v-bk-tooltips="t('存在关联系统，不可删除')">{{ t('删除') }}</span>
              </template>
              <template v-else>
                {{ t('删除') }}
              </template>
            </bk-button>
          </template>
        </bk-table-column>
      </bk-table>
    </bk-loading>

    <bk-dialog
      :is-show="docCategoryDialog.visiable"
      :title="docCategoryDialog.title"
      :header-position="docCategoryDialog.headerPosition"
      :loading="docCategoryDialog.loading"
      :width="docCategoryDialog.width"
      :mask-close="false"
      @after-leave="docCategoryDialog.categoryName = ''"
      @confirm="handleConfirm"
      @closed="closeDocCategoryDialog"
    >
      <bk-form
        :label-width="90"
        :model="docCategoryDialog"
        :rules="rules"
        ref="validateFormRef"
        form-type="vertical"
      >
        <bk-form-item
          :label="t('名称')"
          :required="true"
          :property="'name'"
          :error-display-type="'normal'"
        >
          <bk-input
            v-model="docCategoryDialog.name"
            :placeholder="t('请输入分类名称')"
            :disabled="curDocCategory.is_official"
          ></bk-input>
        </bk-form-item>
        <bk-form-item
          :label="t('优先级')"
          :required="true"
          :property="'priority'"
          :error-display-type="'normal'"
        >
          <bk-input
            v-model="docCategoryDialog.priority"
            :placeholder="t('请输入优先级，范围1 - 9999')"
            type="number"
            :max="9999"
            :min="1"
            :show-controls="true"
          ></bk-input>
          <p class="ag-tip mt10">
            <i class="apigateway-icon icon-ag-info"></i>
            {{ t('文档展示时，将按照优先级从大到小排序') }}
          </p>
        </bk-form-item>
      </bk-form>
    </bk-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import { Message, InfoBox } from 'bkui-vue';
import { useI18n } from 'vue-i18n';

import TableEmpty from '@/components/table-empty.vue';
import {
  getDocCategorys,
  addDocCategory,
  updateDocCategory,
  deleteDocCategory,
} from '@/http';

const { t } = useI18n();

const keyword = ref('');
const docCategoryList = ref([]);
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
const isFilter = ref(false);
const docCategoryDialog = ref({
  visiable: false,
  width: 480,
  headerPosition: 'left',
  id: 0,
  name: '',
  priority: 1000,
  title: '',
  loading: false,
});
const tableEmptyConf = ref({
  keyword: '',
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

// rers
const validateFormRef = ref(null);

watch(keyword, (newVal, oldVal) => {
  if (oldVal && !newVal && isFilter.value) {
    isFilter.value = false;
    pagination.value.offset = 1;
    pagination.value.limit = 10;
    displayData.value = allData.value;
    pagination.value.count = displayData.value.length;
    docCategoryList.value = getDataByPage();
  }
});

const init = () => {
  getDocCategoryList();
};

const handleConfirm = async () => {
  docCategoryDialog.value.loading = true;

  validateFormRef.value?.validate().then(() => {
    if (docCategoryDialog.value.id) {
      updateDocCategoryFun();
    } else {
      createDocCategory();
    }
  })
    .catch(() => {
      nextTick(() => {
        docCategoryDialog.value.loading = false;
      });
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
      limit: 1,
      theme: 'success',
      message: t('新建成功！'),
    });
    docCategoryDialog.value.visiable = false;
  } catch (e) {
    // catchErrorHandler(e, this);
    console.error(e);
  } finally {
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
      limit: 1,
      theme: 'success',
      message: t('更新成功！'),
    });
    docCategoryDialog.value.visiable = false;
  } catch (e) {
    // catchErrorHandler(e, this);
    console.error(e);
  } finally {
    docCategoryDialog.value.loading = false;
  }
};

// 获取文档分类列表
const getDocCategoryList = async (loading = false) => {
  isLoading.value = loading;
  try {
    const res = await getDocCategorys();
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
  } catch (e) {
    tableEmptyConf.value.isAbnormal = true;
    // catchErrorHandler(e, this);
    console.error(e);
  } finally {
    if (!loading) {
      // this.$store.commit('setMainContentLoading', false);
    }
    isLoading.value = false;
  }
};

const handlePageLimitChange = (limit) => {
  pagination.value.limit = limit;
  pagination.value.offset = 1;
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
    // eslint-disable-next-line no-multi-assign
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

// 新建文档 - 暂时关闭新建文档入口
// const handleCreate = () => {
//   docCategoryDialog.value.title = t('新建文档分类');
//   curDocCategory.value = {};
//   docCategoryDialog.value.id = 0;
//   docCategoryDialog.value.name = '';
//   docCategoryDialog.value.priority = 1000;
//   docCategoryDialog.value.visiable = true;
// };

// 编辑文档
const handleEdit = (data: any) => {
  curDocCategory.value = data;
  docCategoryDialog.value.title = t('编辑文档分类');
  docCategoryDialog.value.id = data.id;
  docCategoryDialog.value.name = data.name;
  docCategoryDialog.value.priority = data.priority;
  docCategoryDialog.value.visiable = true;
};

const handleDeleteDocCategory = async (id: number) => {
  try {
    await deleteDocCategory(id);
    Message({
      limit: 1,
      theme: 'success',
      message: t('删除成功！'),
    });
    getDocCategoryList(true);
  } catch (e) {
    // catchErrorHandler(e, this);
    console.error(e);
  }
};

const handleSearch = (payload: any) => {
  if (payload === '') {
    return;
  }
  pagination.value.offset = 1;
  pagination.value.limit = 10;
  isFilter.value = true;
  displayData.value = allData.value.filter((item) => {
    const reg = new RegExp(`(${payload})`, 'gi');
    return item.name.match(reg);
  });
  pagination.value.count = displayData.value.length;
  docCategoryList.value = getDataByPage();
};

const handleDelete = (data: any) => {
  curDocCategory.value = data;
  InfoBox({
    title: t('确认删除'),
    subTitle: `${t('确定要删除文档分类')}【${data.name}】?`,
    onConfirm() {
      handleDeleteDocCategory(data.id);
    },
  });
};

const closeDocCategoryDialog = () => {
  docCategoryDialog.value.visiable = false;
  validateFormRef.value?.clearValidate();
};

const clearFilterKey = () => {
  keyword.value = '';
};

const updateTableEmptyConfig = () => {
  tableEmptyConf.value.keyword = keyword.value;
};

init();
</script>

<style lang="scss" scoped>
.category-container {
  // padding: 24px;
  .ag-top-header {
    min-height: 32px;
    margin-bottom: 20px;
    position: relative;
  }
}
span.official {
  margin-left: 2px;
  padding: 2px;
  background: #dcffe2;
  font-size: 12px;
  color: #2dcb56;
}

.timeout-append {
  width: 36px;
  font-size: 12px;
  text-align: center;
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

.ft13 {
  font-size: 13px;
}

.category-label {
  position: relative;
  margin-bottom: 5px;
  &::after {
    content: '*';
    margin-left: 2px;
    color: #ea3636;
  }
}

.tips {
  line-height: 24px;
  font-size: 12px;
  color: #63656e;
  i {
    position: relative;
    top: -1px;
    margin-right: 3px;
  }
}
</style>
