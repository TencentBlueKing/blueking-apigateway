<template>
  <div class="app-content apigw-access-manager-wrapper">
    <div class="wrapper">
      <div class="f14 ag-table-header">
        <p class="ag-table-change">
          {{ t('请确认以下组件对应网关资源的变更：') }}
          <!-- eslint-disable-next-line vue/no-v-html -->
          <span v-html="addInfo"></span>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <span v-html="updateInfo"></span>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <span v-html="deleteInfo"></span>
        </p>
        <bk-input
          :clearable="true"
          v-model="pathUrl"
          :placeholder="t('请输入组件名称、请求路径，按Enter搜索')"
          :right-icon="'bk-icon icon-search'"
          style="width: 328px;"
          @enter="filterData"
        />
      </div>

      <bk-loading :loading="isLoading">
        <bk-table
          ref="componentRef"
          border="outer"
          style="margin-top: 16px;"
          :data="componentList"
          size="small"
          :pagination="pagination"
          @select="handlerChange"
          @select-all="handlerAllChange"
          remote-pagination
          @page-value-change="handlePageChange"
          @page-limit-change="handlePageLimitChange"
          @filter-change="handleFilterChange">
          <bk-table-column :label="t('系统名称')" prop="system_name">
            <template #default="{ data }">
              {{data?.system_name || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('组件名称')" prop="component_name">
            <template #default="{ data }">
              {{data?.component_name || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('组件请求方法')"
            :filters="methodFilters"
            :filter-multiple="true"
            column-key="component_method"
            prop="component_method">
            <template #default="{ data }">
              {{data?.component_method || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('组件请求路径')" prop="component_path" :min-width="200">
            <template #default="{ data }">
              {{data?.component_path || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('资源')" prop="resource_id" :show-overflow-tooltip="false">
            <template #default="{ data }">
              <span
                v-if="data?.resource_name"
                :class="['text-resource', { 'resource-disabled': !data?.resource_id }]"
                v-bk-tooltips.top="{ content: data?.resource_id ? data?.resource_name : t('资源不存在') }"
                @click.stop="handleEditResource(data, data?.resource_id)">{{ data?.resource_name }}</span>
              <template v-else>
                --
              </template>
            </template>
          </bk-table-column>
          <bk-table-column :label="t('组件ID')" prop="component_id">
            <template #default="{ data }">
              {{data?.component_id || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('操作类型')" width="150"
            :filters="statusFilters"
            :filter-multiple="true"
            column-key="status"
            prop="status">
            <template #default="{ data }">
              <span style="color: #2DCB56;" v-if="!data?.resource_id"> {{ t('新建') }} </span>
              <span style="color: #ffb400;" v-if="data?.resource_id && data?.component_path"> {{ t('更新') }} </span>
              <span style="color: #EA3536;" v-if="data?.resource_id && !data?.component_path"> {{ t('删除') }} </span>
            </template>
          </bk-table-column>
          <template #empty>
            <TableEmpty
              :keyword="tableEmptyConf.keyword"
              :abnormal="tableEmptyConf.isAbnormal"
              @reacquire="getComponents"
              @clear-filter="handleClearFilterKey"
            />
          </template>
        </bk-table>
      </bk-loading>
      <div class="mt20">
        <bk-pop-confirm
          ref="resourcePopconfirm"
          :is-show="confirmSyncShow"
          trigger="click"
          ext-cls="import-resource-popconfirm-wrapper"
          v-if="componentList.length">
          <template #content>
            <div>
              <div class="content-text"> {{ t('将组件配置同步到网关 bk-esb，创建网关的资源版本并发布到网关所有环境') }} </div>
              <div class="btn-wrapper">
                <bk-button
                  size="small"
                  theme="primary"
                  class="btn"
                  :disabled="confirmIsLoading"
                  @click="confirm">
                  {{ t('确认') }}
                </bk-button>
                <bk-button
                  size="small"
                  class="btn"
                  @click="confirmSyncShow = false">
                  {{ t('取消') }}
                </bk-button>
              </div>
            </div>
          </template>

          <bk-button
            class="mr10"
            theme="primary"
            type="button"
            :title="t('下一步')"
            @click="confirmSyncShow = true"
            :loading="confirmIsLoading">
            {{ t('确认同步') }}
          </bk-button>
        </bk-pop-confirm>
        <bk-button
          v-else
          class="mr10"
          theme="primary"
          type="button"
          :disabled="true">
          {{ t('确认同步') }}
        </bk-button>
        <bk-button
          type="button"
          :title="t('取消')"
          :disabled="isLoading"
          @click="goBack">
          {{ t('取消') }}
        </bk-button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { isTableFilter } from '@/common/util';
import { checkSyncComponent, syncReleaseData, getEsbGateway } from '@/http';
import { useCommon } from '@/store';
import TableEmpty from '@/components/table-empty.vue';

const { t } = useI18n();
const router = useRouter();
const common = useCommon();

const resourcePopconfirm = ref();
const componentRef = ref();

const componentList = ref<any>([]);
const pagination = reactive({
  current: 1,
  count: 0,
  limit: 10,
});

const confirmSyncShow = ref<boolean>(false);
const isLoading = ref<boolean>(false);
const pathUrl = ref<string>('');
const esb = ref<any>({});
const filterList = ref<any>({});
const allData = ref<any>([]);
const displayData = ref<any>([]);
const curSelectList = ref<any>([]);
const requestQueue = reactive<any>(['component']);
const tableEmptyConf = ref<{keyword: string, isAbnormal: boolean}>({
  keyword: '',
  isAbnormal: false,
});
const statusFilters = reactive<any>([
  { value: 'delete', text: t('删除') },
  { value: 'update', text: t('更新') },
  { value: 'create', text: t('新建') }]);

const createNum = computed(() => {
  const results = allData.value?.filter((item: any) => !item?.resource_id);
  return results?.length;
});

const updateNum = computed(() => {
  const results = allData.value?.filter((item: any) => item?.resource_id && item?.component_path);
  return results?.length;
});

const deleteNum = computed(() => {
  const results = allData.value?.filter((item: any) => item?.resource_id && !item?.component_path);
  return results?.length;
});

const addInfo = computed(() => t('新建 <strong style="color: #2DCB56;"> {createNum} </strong> 条，', { createNum: createNum.value }));

const updateInfo = computed(() => t('更新 <strong style="color: #ffb400;"> {updateNum} </strong> 条，', { updateNum: updateNum.value }));

const deleteInfo = computed(() => t('删除 <strong style="color: #EA3536;"> {deleteNum} </strong> 条', { deleteNum: deleteNum.value }));

const confirmIsLoading = computed(() => isLoading.value);

const methodFilters = computed(() => {
  return common.methodList?.map((item: any) => {
    return {
      value: item.id,
      text: item.id,
    };
  });
});

const getDataByPage = (page?: any) => {
  if (!page) {
    page = 1;
    pagination.current = 1;
  }
  let startIndex = (page - 1) * pagination.limit;
  let endIndex = page * pagination.limit;
  if (startIndex < 0) {
    startIndex = 0;
  }
  if (endIndex > displayData.value?.length) {
    endIndex = displayData.value?.length;
  }
  updateTableEmptyConfig();
  return displayData.value?.slice(startIndex, endIndex);
};

const getComponents = async () => {
  isLoading.value = true;
  try {
    const res = await checkSyncComponent();
    allData.value = Object.freeze(res);
    displayData.value = res;
    pagination.count = displayData.value?.length;
    componentList.value = getDataByPage();
    tableEmptyConf.value.isAbnormal = false;
  } catch (e) {
    tableEmptyConf.value.isAbnormal = true;
    console.log(e);
  } finally {
    if (requestQueue?.length > 0) {
      requestQueue?.shift();
    }
    isLoading.value = false;
  }
};

const handlerChange = (payload: any) => {
  curSelectList.value = [...payload];
};

const handlerAllChange = (payload: any) => {
  curSelectList.value = [...payload];
};

const confirm = () => {
  checkReleaseData();
  confirmSyncShow.value = false;
};

const checkReleaseData = async () => {
  try {
    await syncReleaseData();
    router.push({
      path: '/components/access',
    });
  } catch (e) {
    console.log(e);
  }
};

const handlePageLimitChange = (limit: number) => {
  pagination.limit = limit;
  pagination.current = 1;
  handlePageChange(pagination.current);
};

const handlePageChange = (page: number) => {
  pagination.current = page;
  const data = getDataByPage(page);
  componentList.value?.splice(0, componentList.value?.length, ...data);
};

const goBack = () => {
  router.back();
};

const filterData = () => {
  displayData.value = allData.value?.filter((e: any) => {
    return (e?.component_path?.includes(pathUrl.value)) || (e?.component_name?.includes(pathUrl.value));
  });
  componentList.value = getDataByPage();
  pagination.count = displayData.value?.length;
};

const handleFilterChange = (filters: any) => {
  filterList.value = filters;
  if (filters?.component_method?.length) {
    displayData.value = allData.value?.filter((item: any) => {
      return filters?.component_method?.includes(item?.component_method);
    });
    componentList.value = getDataByPage();
    pagination.count = displayData.value?.length;
  } else if (filters?.status?.length) {
    const filterCriteria = filters.status;
    const filterList: any = [];
    // 过滤对应操作类型
    if (filterCriteria?.includes('delete')) {
      filterList.push(...allData.value?.filter((item: any) => item.resource_id && !item.component_path));
    }
    if (filterCriteria?.includes('create')) {
      filterList.push(...allData.value?.filter((item: any) => item.component_id && !item.resource_id));
    }
    if (filterCriteria?.includes('update')) {
      filterList.push(...allData.value?.filter((item: any) => item.resource_id && item.component_path));
    }
    displayData.value = filterList;
    componentList.value = getDataByPage();
    pagination.count = displayData.value?.length;
  } else {
    getComponents();
  }
};

const getEsbGatewayData = async () => {
  try {
    const res = await getEsbGateway();
    esb.value = res;
  } catch (e) {
    console.log(e);
  }
};

const handleEditResource = (data: any, resourceId: any) => {
  if (!resourceId) {
    return false;
  }
  const routeData = router.resolve({
    path: `/${esb.value?.gateway_id}/resource/${data.resource_id}/edit`,
    params: {
      id: esb.value?.gateway_id,
      resourceId: data?.resource_id,
    },
  });
  window.open(routeData.href, '_blank');
};

const updateTableEmptyConfig = () => {
  const isFilter = isTableFilter(filterList.value);
  if (pathUrl.value || isFilter) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const handleClearFilterKey = async () => {
  pathUrl.value = '';
  await getComponents();
};

const init = () => {
  getComponents();
  getEsbGatewayData();
};

init();

watch(
  () => pathUrl.value,
  (value) => {
    if (!value) {
      displayData.value = allData.value;
      pagination.count = displayData.value?.length;
      componentList.value = getDataByPage();
    }
  },
);
</script>

<style lang="scss" scoped>
.apigw-access-manager-wrapper {
  .wrapper {
    padding: 24px;
  }
  .search-wrapper {
    display: flex;
    justify-content: space-between;
  }
  .ag-table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    .ag-table-change {
      color: #313238;
    }
  }
  .bk-table {
    .api-name,
    .docu-link {
      max-width: 200px;
      display: inline-block;
      word-break: break-all;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
      vertical-align: bottom;
    }
    .copy-icon {
      font-size: 14px;
      cursor: pointer;
      &:hover {
        color: #3a84ff;
      }
    }
  }
}
.apigw-access-manager-slider-cls {
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
  .timeout-append {
    width: 36px;
    font-size: 12px;
    text-align: center;
  }
}

.ag-flex {
  display: flex;
}
.ag-auto-text {
  vertical-align: middle;
}
.ag-tag.success {
  width: 44px;
}

.text-resource {
  color: #3a84ff;
  cursor: pointer;
}

.resource-disabled {
  color: #dcdee5;
  cursor: not-allowed;
  user-select: none;
}
</style>

<style lang="scss">
.import-resource-popconfirm-wrapper.bk-popover {
  padding: 16px;
  .bk-pop-confirm {
    .btn-wrapper {
      padding-top: 10px;
      position: relative;
      height: 26px;
      .btn {
        min-width: 50px;
        padding: 0 6px;
        position: absolute;
        &:nth-child(1) {
          right: 100px;
        }
        &:nth-child(2) {
          right: 35px;
        }
      }
    }
    .bk-pop-confirm-footer {
      display: none !important;
    }
  }
}
</style>
