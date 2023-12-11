<template>
  <div class="system-container">
    <div class="ag-top-header">
      <bk-alert
        type="info"
        :title="t('请将新系统的接口，直接接入 API 网关')"
      ></bk-alert>
      <!-- 新建系統接口，直接接入 API 网关 -->
      <!-- <bk-button
        theme="primary"
        @click="handleCreateSys"
      >
        {{ t('新建系统') }}
      </bk-button> -->
      <div
        class="mt10"
        style="overflow: hidden"
      >
        <bk-input
          class="fr"
          :clearable="true"
          v-model="keyword"
          :placeholder="t('请输入系统名称、描述，按Enter搜索')"
          :right-icon="'bk-icon icon-search'"
          style="width: 370px"
          @enter="handleSearch"
        ></bk-input>
      </div>
    </div>
    <bk-loading :loading="isLoading">
      <bk-table
        ext-cls="ag-stage-table"
        :data="systemList"
        remote-pagination
        :pagination="pagination"
        show-overflow-tooltip
        @page-limit-change="handlePageLimitChange"
        @page-value-change="handlePageChange"
        @filter-change="handleFilterChange"
      >
        <bk-table-column :label="t('名称')">
          <template #default="{ row }">
            {{ row.name }}
            <template v-if="row.is_official">
              <span class="official">{{ t('官方') }}</span>
            </template>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('描述')"
          prop="description"
          :show-overflow-tooltip="true"
        >
          <template #default="props">
            <template v-if="props.row.description">
              <span>{{ props.row.description }}</span>
            </template>
            <template v-else>--</template>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('系统负责人')"
          :show-overflow-tooltip="true"
          :render-header="$renderHeader"
        >
          <template #default="props">
            <template v-if="props.row.maintainers?.length > 0">
              <span>{{ props.row.maintainers.join('；') }}</span>
            </template>
            <template v-else>--</template>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('文档分类')"
          column-key="doc_category"
          prop="doc_category_id"
          :render-header="$renderHeader"
          :filters="classifyFilters"
          :filter-method="classifyFilterMethod"
          :filter-multiple="true"
        >
          <template #default="props">
            {{ props.row.doc_category_name }}
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
              @click="handleEditSys(row)"
            >
              {{ t('编辑') }}
            </bk-button>
            <bk-button
              text
              theme="primary"
              :disabled="row.is_official"
              @click="handleDeleteSys(row)"
            >
              <template v-if="row.is_official">
                <span v-bk-tooltips="t('官方系统，不可删除')">{{ t('删除') }}</span>
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
      width="540"
      :is-show="deleteDialogConf.visiable"
      :title="deleteDialogTitle"
      :theme="'primary'"
      header-position="center"
      :mask-close="false"
      ext-cls="delete-system-dialog-cls"
    >
      <div>
        <div
          class="ft13"
          style="margin: 8px 0"
          v-html="systemDelTips"
        ></div>
        <bk-input v-model="formRemoveConfirmCode" />
        <div class="mt10 ft13">
          {{ t('注意：删除系统，将删除该系统下所有组件API') }}，
          <strong>{{ t('不可恢复') }}</strong>
        </div>
      </div>
      <template #footer>
        <bk-button
          theme="primary"
          :loading="deleteDialogConf.loading"
          :disabled="formRemoveConfirmCode !== curSystem.name"
          @click="handleDeleteSystem"
        >
          {{ t('确定') }}
        </bk-button>
        <bk-button @click="deleteDialogConf.visiable = false">{{ t('取消') }}</bk-button>
      </template>
    </bk-dialog>

    <bk-sideslider
      v-model:isShow="isSliderShow"
      :width="750"
      :title="sliderTitle"
      quick-close
      @hidden="handleHidden"
    >
      <div style="padding: 20px; height: calc(100vh - 107px);">
        <bk-loading :loading="detailLoading">
          <bk-form
            :label-width="160"
            :rules="rules"
            ref="formRef"
            :model="formData"
            v-show="!detailLoading"
          >
            <bk-form-item
              :label="t('名称')"
              :required="true"
              property="name"
              :error-display-type="'normal'"
            >
              <bk-input
                v-model="formData.name"
                :placeholder="t('由英文字母、下划线(_)或数字组成，并且以字母开头，长度小于64个字符')"
                :disabled="isDisabled"
              ></bk-input>
              <p class="tips">
                <i class="apigateway-icon icon-ag-info"></i>
                {{ t('系统唯一标识') }}
              </p>
            </bk-form-item>
            <bk-form-item
              :label="t('描述')"
              :required="true"
              property="description"
              :error-display-type="'normal'"
            >
              <bk-input
                :disabled="isDisabled"
                :maxlength="128"
                v-model="formData.description"
                :placeholder="t('不超过128个字符')"
              ></bk-input>
            </bk-form-item>
            <bk-form-item
              :label="t('文档分类')"
              :required="true"
              property="doc_category_id"
              :error-display-type="'normal'"
            >
              <template v-if="isDisabled">
                <bk-input
                  v-model="curSystem.doc_category_name"
                  disabled
                ></bk-input>
              </template>
              <bk-select
                v-else
                :loading="categoryLoading"
                searchable
                :clearable="false"
                v-model="formData.doc_category_id"
              >
                <bk-option
                  v-for="option in categoryList"
                  :key="option.id"
                  :id="option.id"
                  :name="option.name"
                ></bk-option>
                <template #extension>
                  <div
                    class="create-doc-category"
                    style="cursor: pointer"
                    @click="handleCreateCategory"
                  >
                    <i class="paasng-icon paasng-plus-circle"></i>
                    <span style="margin-left: 4px">{{ t('新建文档分类') }}</span>
                  </div>
                </template>
              </bk-select>
            </bk-form-item>
            <bk-form-item :label="t('系统负责人')">
              <!-- <user v-model="formData.maintainers" ref="userRef"></user> -->
              <!-- 暂时使用 tag -->
              <bk-tag-input
                ref="userRef"
                v-model="formData.maintainers"
                allow-create
                has-delete-icon
                allow-auto-match
              />
            </bk-form-item>
            <bk-form-item :label="t('超时时长')">
              <bk-input
                type="number"
                :max="600"
                :min="1"
                :precision="0"
                v-model="formData.timeout"
              >
                <template #suffix>
                  <section class="timeout-append">
                    <div>{{ t('秒') }}</div>
                  </section>
                </template>
              </bk-input>
              <p class="tips">
                <i class="apigateway-icon icon-ag-info"></i>
                {{ t('未设置时，使用默认值30秒，最大600秒') }}
              </p>
            </bk-form-item>
            <bk-form-item :label="t('备注')">
              <bk-input
                type="textarea"
                :disabled="isDisabled"
                v-model="formData.comment"
                :placeholder="t('请输入备注')"
              ></bk-input>
            </bk-form-item>
          </bk-form>
        </bk-loading>
      </div>
      <template #footer>
        <div style="padding-left: 90px">
          <bk-button
            theme="primary"
            :loading="submitLoading"
            @click="handleSubmit"
          >
            {{ t('保存') }}
          </bk-button>
          <bk-button
            style="margin-left: 6px"
            @click="handleCancel"
          >
            {{ t('取消') }}
          </bk-button>
        </div>
      </template>
    </bk-sideslider>

    <bk-dialog
      :is-show="docuCategoryDialog.visible"
      :title="t('新建文档分类')"
      :header-position="docuCategoryDialog.headerPosition"
      :width="docuCategoryDialog.width"
      :mask-close="false"
      @after-leave="docuCategoryDialog.categoryName = ''"
    >
      <div
        class="category-label"
        style="margin-bottom: 5px"
      >
        {{ t('分类名称') }}
      </div>
      <bk-input
        v-model="docuCategoryDialog.categoryName"
        @input.stop
        style="margin-bottom: 15px"
      ></bk-input>
      <template #footer>
        <div>
          <bk-button
            :disabled="docuCategoryDialog.categoryName === ''"
            theme="primary"
            :loading="docuCategoryDialog.loading"
            @click="handleConfirm"
          >
            {{ t('确定') }}
          </bk-button>
          <bk-button
            style="margin-left: 6px"
            @click="docuCategoryDialog.visible = false"
          >
            {{ t('取消') }}
          </bk-button>
        </div>
      </template>
    </bk-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { Message } from 'bkui-vue';
import { useI18n } from 'vue-i18n';
// import User from '@/components/user';
import {
  getDocCategorys,
  addDocCategory,
  getSystems,
  getSystemDetail,
  addSystem,
  updateSystem,
  deleteSystem,
} from '@/http';

const { t } = useI18n();

const getDefaultData = () => {
  return {
    name: '',
    description: '',
    comment: '',
    maintainers: [],
    timeout: 0,
    doc_category_id: '',
  };
};

const keyword = ref('');
const systemList = ref([]);
const pagination = ref({
  offset: 0,
  limit: 10,
  count: 0,
});
const curSystem = ref({
});
const deleteDialogConf = ref({
  visiable: false,
  loading: false,
});
const isSliderShow = ref(false);
const formData = ref(getDefaultData()); // Assuming getDefaultData is a function returning data
const categoryList = ref([]);
const submitLoading = ref(false);
const categoryLoading = ref(false);
const allData = ref([]);
const displayData = ref([]);
const classifyFilters = ref([]);
const isLoading = ref(false);
const formRemoveConfirmCode = ref('');
const docuCategoryDialog = ref({
  visible: false,
  width: 480,
  headerPosition: 'left',
  categoryName: '',
  loading: false,
});
const detailLoading = ref(false);
const tableEmptyConf = ref({
  keyword: '',
  isAbnormal: false,
});
const filterDocCategory = ref([]);
const isFilter = ref(false);
const rules = ref({
  name: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  description: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  doc_category_id: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
});

// refs
const formRef = ref(null);
const systemRef = ref(null);
const userRef = ref(null);

const isEdit = computed(() => {
  return Object.keys(curSystem.value).length > 0;
});

const isDisabled = computed(() => {
  return curSystem.value.is_official;
});

const sliderTitle = computed(() => {
  return isEdit.value ? t('编辑系统') : t('新建系统');
});

const systemDelTips = computed(() => {
  // 使用标识符
  // return t('DeleteSystemTitle', { name: curSystem.value.name });
  return `请完整输入 <code class="system-del-tips">${curSystem.value.name}</code> 来确认删除系统！`;
});

const deleteDialogTitle = computed(() => {
  return `${t('确认删除系统')}【${curSystem.value.name}】？`;
});

watch(keyword, (newVal, oldVal) => {
  if (oldVal && !newVal && isFilter) {
    isFilter.value = false;
    pagination.value.offset = 1;
    pagination.value.limit = 10;
    displayData.value = allData.value;
    systemList.value = getDataByPage();
  }
});

const init = () => {
  console.log('init');
  getSystemList();
};

const handleCreateCategory = () => {
  docuCategoryDialog.value.visible = true;
};

const handleConfirm = async () => {
  docuCategoryDialog.value.loading = true;
  try {
    const res = await addDocCategory(docuCategoryDialog.value.categoryName);
    categoryList.value.push({
      id: res.data.id,
      name: docuCategoryDialog.value.categoryName,
    });
    formData.value.doc_category_id = res.data.id;
    docuCategoryDialog.value.visible = false;
  } catch (e) {
    // catchErrorHandler(e, this);
    console.error(e);
  } finally {
    docuCategoryDialog.value.loading = false;
  }
};

const handleHidden = () => {
  curSystem.value = {};
  categoryList.value = [];
  formData.value = Object.assign({}, getDefaultData());
};

const handleAfterLeave = () => {
  curSystem.value = {};
  formRemoveConfirmCode.value = '';
};

const handleCancel = () => {
  isSliderShow.value = false;
};

const handleSubmit = async () => {
  formRef.value?.validate().then(
    async () => {
      submitLoading.value = true;
      const tempData = { ...formData.value };
      if (!tempData.timeout) {
        tempData.timeout = null;
      }
      try {
        isEdit.value ? await updateSystem(curSystem.value.id, tempData) : await addSystem(tempData);
        isSliderShow.value = false;
        getSystemList(true);
      } catch (e) {
        // catchErrorHandler(e, this);
        console.error(e);
      } finally {
        submitLoading.value = false;
      }
    },
    async (validator) => {
      console.error(validator);
    },
  );
};

const classifyFilterMethod = (value, row, column) => {
  const { property } = column;
  return row[property] === value;
};

const handleFilterChange = (filters) => {
  filterDocCategory.value = filters.doc_category || [];
  // updateTableEmptyConfig();
};

const getCategories = async () => {
  categoryLoading.value = true;
  try {
    const res = await getDocCategorys();
    categoryList.value = res;
  } catch (e) {
    // catchErrorHandler(e, this);
    console.error(e);
  } finally {
    categoryLoading.value = false;
  }
};

// 获取系统列表
const getSystemList = async (loading = false, curPage = 1) => {
  isLoading.value = loading;
  try {
    const res = await getSystems();
    allData.value = Object.freeze(res) || [];
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
    systemList.value = getDataByPage(curPage);
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

// 改变页码
const handlePageChange = (page) => {
  pagination.value.offset = page;
  const data = getDataByPage(page);
  systemList.value.splice(0, systemList.value.length, ...data);
};

// 前端分页
const getDataByPage = (page = 1) => {
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
  // updateTableEmptyConfig();
  return displayData.value.slice(startIndex, endIndex);
};

const handleCreateSys = async () => {
  curSystem.value = {};
  formData.value.timeout = 30;
  isSliderShow.value = true;
  await getCategories();
  // initSidebarFormData(formData.value);
};

const handleDeleteSystem = async () => {
  deleteDialogConf.value.loading = true;
  try {
    await deleteSystem(curSystem.value.id);
    deleteDialogConf.value.visiable = false;
    Message({
      limit: 1,
      theme: 'success',
      message: t('删除成功！'),
    });
    // 页码存储
    getSystemList(true, pagination.value.offset);
  } catch (e) {
    // catchErrorHandler(e, this);
    console.error(e);
  } finally {
    deleteDialogConf.value.loading = false;
  }
};

// 搜索
const handleSearch = (payload) => {
  if (payload === '') {
    return;
  }
  pagination.value.offset = 1;
  pagination.value.limit = 10;
  isFilter.value = true;
  displayData.value = allData.value.filter((item) => {
    const reg = new RegExp(`(${payload})`, 'gi');
    return item.name.match(reg) || item.description.match(reg);
  });
  systemList.value = getDataByPage();
};

const handleEditSys = async (data) => {
  curSystem.value = data;
  isSliderShow.value = true;
  getCategories();
  detailLoading.value = true;
  try {
    const res = await getSystemDetail(data.id);
    const { name, description, maintainers, comment, timeout } = res;
    formData.value.name = name;
    formData.value.description = description;
    formData.value.maintainers = [...maintainers];
    formData.value.doc_category_id = data.doc_category_id;
    formData.value.comment = comment;
    formData.value.timeout = timeout;
  } catch (e) {
    // catchErrorHandler(e, this)
    console.error(e);
  } finally {
    detailLoading.value = false;
  }
};

const handleDeleteSys = (data) => {
  curSystem.value = data;
  deleteDialogConf.value.visiable = true;
};

// const clearFilterKey = () => {
//   keyword.value = '';
//   filterDocCategory.value = [];
//   systemRef.value.clearFilter();
//   if (systemRef.value?.$refs.tableHeader) {
//     clearFilter(this.$refs.systemRef.$refs.tableHeader);
//   }
// };

// const updateTableEmptyConfig = () => {
//   if (keyword.value || filterDocCategory.value.length) {
//     tableEmptyConf.value.keyword = 'placeholder';
//     return;
//   }
//   tableEmptyConf.value.keyword = '';
// };

// 表单型弹窗关闭验证
const handleBeforeClose = async () => {
  return true;
  // userRef.value?.handleBlur();
  // return this.$isSidebarClosed(JSON.stringify(this.formData));
};

init();
</script>

<style lang="scss" scoped>
.system-container {
  padding: 24px;
}
span.official {
  margin-left: 2px;
  padding: 2px;
  background: #dcffe2;
  font-size: 12px;
  color: #2dcb56;
}

.timeout-append {
  width: 32px;
  color: #63656e;
  text-align: center;
  background: #fafbfd;
  border-left: 1px solid #c4c6cc;
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
.create-doc-category {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  cursor: pointer;
}
</style>
<style>
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
