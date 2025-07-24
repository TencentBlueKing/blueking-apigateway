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
  <div class="apigw-access-manager-wrapper">
    <div class="p-24px wrapper">
      <BkInput
        v-model="pathUrl"
        clearable
        :placeholder="t('请输入组件名称、请求路径，按Enter搜索')"
        :right-icon="'bk-icon icon-search'"
        class="sync-version-search"
        @enter="filterData"
      />
      <BkLoading
        :loading="isLoading"
        :opacity="1"
      >
        <BkTable
          size="small"
          :data="componentList"
          :pagination="pagination"
          :columns="tableColumns"
          :max-height="clientHeight"
          remote-pagination
          show-overflow-tooltip
          @page-value-change="handlePageChange"
          @page-limit-change="handlePageLimitChange"
        >
          <template #empty>
            <TableEmpty
              :is-loading="isLoading"
              :empty-type="tableEmptyConf.emptyType"
              :abnormal="tableEmptyConf.isAbnormal"
              @refresh="getComponents"
              @clear-filter="handleClearFilterKey"
            />
          </template>
        </BkTable>
      </BkLoading>
    </div>
  </div>
</template>

<script lang="tsx" setup>
import {
  sortBy,
  sortedUniq,
} from 'lodash-es';
import { PERMISSION_LEVEL_MAP } from '@/enums';
import { useMaxTableLimit } from '@/hooks';
import { type ISyncApigwItem, getSyncVersion } from '@/services/source/componentManagement';
import TableEmpty from '@/components/table-empty/Index.vue';

const { t } = useI18n();
const { maxTableLimit, clientHeight } = useMaxTableLimit({ allocatedHeight: 220 });
const route = useRoute();

const tableColumns = ref([
  {
    label: t('系统名称'),
    field: 'system_name',
    render: ({ row }: { row?: Partial<ISyncApigwItem> }) => {
      return (
        <span>
          {row?.system_name || '--' }
        </span>
      );
    },
  },
  {
    label: t('组件名称'),
    field: 'component_name',
    render: ({ row }: { row?: Partial<ISyncApigwItem> }) => {
      return (
        <span>
          { row?.component_name || '--' }
        </span>
      );
    },
  },
  {
    label: t('组件请求方法'),
    field: 'component_method',
    render: ({ row }: { row?: Partial<ISyncApigwItem> }) => {
      return (
        <span>
          { row?.component_method || '--' }
        </span>
      );
    },
  },
  {
    label: t('组件请求路径'),
    field: 'component_path',
    render: ({ row }: { row?: Partial<ISyncApigwItem> }) => {
      return (
        <span>
          { row?.component_path || '--' }
        </span>
      );
    },
  },
  {
    label: t('资源ID'),
    field: 'resource_id',
    showOverflowTooltip: false,
    render: ({ row }: { row?: Partial<ISyncApigwItem> }) => {
      return (
        <span>
          { row?.resource_id || '--'}
        </span>
      );
    },
  },
  {
    label: t('组件ID'),
    field: 'component_id ',
    render: ({ row }: { row?: Partial<ISyncApigwItem> }) => {
      return (
        <span>
          { row?.component_id || '--' }
        </span>
      );
    },
  },
  {
    label: t('权限级别'),
    field: 'component_permission_level ',
    width: 100,
    render: ({ row }: { row?: Partial<ISyncApigwItem> }) => {
      return (
        <span>
          { PERMISSION_LEVEL_MAP[row?.component_permission_level] ?? '--' }
        </span>
      );
    },
  },
]);
const componentList = ref([]);
const pagination = reactive({
  current: 1,
  count: 0,
  limit: maxTableLimit,
  limitList: sortedUniq(sortBy([10, 20, 50, 100, maxTableLimit])),
});
const requestQueue = reactive(['component']);
const allData = ref([]);
const displayData = ref([]);
const displayDataLocal = ref([]);
const isLoading = ref(false);
const pathUrl = ref('');
const tableEmptyConf = reactive({
  emptyType: '',
  isAbnormal: false,
});

const historyId = computed(() => route.query.id);

const getComponents = async () => {
  isLoading.value = true;
  try {
    const res = await getSyncVersion(historyId.value);
    allData.value = Object.freeze(res);
    displayData.value = res;
    displayDataLocal.value = res;
    pagination.count = displayData.value?.length;
    componentList.value = getDataByPage();
    tableEmptyConf.isAbnormal = false;
  }
  catch {
    tableEmptyConf.isAbnormal = true;
  }
  finally {
    if (requestQueue?.length > 0) {
      requestQueue.shift();
    }
    setTimeout(() => {
      isLoading.value = false;
    }, 500);
  }
};

const updateTableEmptyConfig = () => {
  if (pathUrl.value && !componentList.value.length) {
    tableEmptyConf.emptyType = 'searchEmpty';
    return;
  }
  tableEmptyConf.emptyType = '';
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
  displayData.value = displayDataLocal.value?.filter((item: IISyncApigwItem) => {
    return (item?.component_path?.includes(pathUrl.value)) || (item?.component_name?.includes(pathUrl.value));
  });
  componentList.value = getDataByPage();
  pagination.count = displayData.value?.length;
};

const init = () => {
  getComponents();
};

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
  .sync-version-search {
    width: 328px;
    margin-bottom: 16px;
    float: right;
  }
}
</style>
