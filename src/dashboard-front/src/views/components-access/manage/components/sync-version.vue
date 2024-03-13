<template>
  <div class="app-content apigw-access-manager-wrapper">
    <div class="wrapper">
      <bk-input
        class="fr"
        :clearable="true"
        v-model="pathUrl"
        :placeholder="t('请输入组件名称、请求路径，按Enter搜索')"
        :right-icon="'bk-icon icon-search'"
        style="width: 328px; margin-bottom: 10px"
        @enter="filterData">
      </bk-input>
      <bk-loading :loading="isLoading">
        <bk-table
          ref="componentTableRef"
          style="margin-top: 16px;"
          :data="componentList"
          size="small"
          :pagination="pagination"
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
            :filter-multiple="false"
            column-key="component_method"
            prop="component_method">
            <template #default="{ data }">
              {{data?.component_method || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('组件请求路径')" prop="component_path">
            <template #default="{ data }">
              {{data?.component_path || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('资源ID')" prop="resource_id">
            <template #default="{ data }">
              {{data?.resource_id || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('组件ID')" prop="component_id">
            <template #default="{ data }">
              {{data?.component_id || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('权限级别')" width="150"
            :filters="levelFilters"
            :filter-multiple="false"
            column-key="component_permission_level"
            prop="component_permission_level">
            <template #default="{ data }">
              {{levelEnum[data?.component_permission_level] || '--'}}
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
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { /* clearFilter,  */ isTableFilter } from '@/common/util';
import { useCommon } from '@/store';
import { getSyncVersion } from '@/http';
import TableEmpty from '@/components/table-empty.vue';

const { t } = useI18n();
const route = useRoute();
const common = useCommon();

const componentTableRef = ref();

const componentList = ref<any>([]);
const pagination = reactive<any>({
  current: 1,
  count: 0,
  limit: 10,
});
const requestQueue = reactive<any>(['component']);
const allData = ref<any>([]);
const displayData = ref<any>([]);
const isLoading = ref<boolean>(false);
const pathUrl = ref<string>('');
const levelEnum = reactive<any>({ unlimited: t('无限制'), normal: t('普通') });
const displayDataLocal = ref<any>([]);
const levelFilters = reactive<any>([{ value: 'unlimited', text: t('无限制') }, { value: 'normal', text: t('普通') }]);
const tableEmptyConf = reactive<any>({
  keyword: '',
  isAbnormal: false,
});
const filterList = ref<any>({});

const id = computed(() => route.query.id);
const methodFilters = computed(() => {
  return common.methodList?.map((item: any) => {
    return {
      value: item.id,
      text: item.id,
    };
  });
});

const getComponents = async () => {
  isLoading.value = true;
  try {
    const res = await getSyncVersion(id.value);
    allData.value = Object.freeze(res);
    displayData.value = res;
    displayDataLocal.value = res;
    pagination.count = displayData.value?.length;
    componentList.value = getDataByPage();
    tableEmptyConf.isAbnormal = false;
  } catch (e) {
    tableEmptyConf.isAbnormal = true;
    console.log(e);
  } finally {
    if (requestQueue?.length > 0) {
      requestQueue.shift();
    }
    isLoading.value = false;
  }
};

const updateTableEmptyConfig = () => {
  const isFilter = isTableFilter(filterList.value);
  if (pathUrl.value || isFilter) {
    tableEmptyConf.keyword = 'placeholder';
    return;
  }
  tableEmptyConf.keyword = '';
};

const handleClearFilterKey = async () => {
  pathUrl.value = '';
  await getComponents();
};

const getDataByPage = (page?: number) => {
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

const handlePageChange = (page: number) => {
  pagination.current = page;
  const data = getDataByPage(page);
  componentList.value?.splice(0, componentList.value?.length, ...data);
};

const handlePageLimitChange = (limit: number) => {
  pagination.limit = limit;
  pagination.current = 1;
  handlePageChange(pagination.current);
};

const filterData = () => {
  displayData.value = displayDataLocal.value?.filter((e: any) => {
    return (e?.component_path?.includes(pathUrl.value)) || (e?.component_name?.includes(pathUrl.value));
  });
  componentList.value = getDataByPage();
  pagination.count = displayData.value?.length;
};

const handleFilterChange = ((filters: any) => {
  filterList.value = filters;
  if (filters?.component_method?.length) {
    displayData.value = displayDataLocal.value?.filter((item: any) => {
      return filters?.component_method?.includes(item?.component_method);
    });
    componentList.value = getDataByPage();
    pagination.count = displayData.value?.length;
  } else if (filters?.component_permission_level?.length) {
    displayData.value = displayDataLocal.value?.filter((item: any) => {
      return filters?.component_permission_level[0] === item?.component_permission_level;
    });
    componentList.value = getDataByPage();
    pagination.count = displayData.value?.length;
  } else {
    getComponents();
  }
});

// const clearFilterKey = () => {
//   pathUrl.value = '';
//   componentTableRef.value?.clearFilter();
//   if (componentTableRef.value?.$refs?.tableHeader) {
//     clearFilter(componentTableRef.value.$refs?.tableHeader);
//   }
// };

const init = () => {
  getComponents();
};

// watch(
//   () => requestQueue,
//   (value) => {
//     if (value.length < 1) {
//       this.$store.commit('setMainContentLoading', false);
//     }
//   },
// );

watch(
  () => pathUrl.value,
  (value) => {
    if (!value) {
      displayData.value = displayDataLocal.value;
      pagination.count = displayData.value?.length;
      componentList.value = getDataByPage();
    }
  },
);

init();

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
</style>
