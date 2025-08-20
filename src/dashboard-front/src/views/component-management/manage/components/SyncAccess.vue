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
    <div class="p-24px">
      <div class="m-b-16px flex items-center justify-between ag-table-header">
        <p class="ag-table-change">
          {{ t('请确认以下组件对应网关资源的变更：') }}
          <i18n-t
            keypath="新建 {0} 条，更新 {1} 条，删除 {2} 条"
            tag="span"
          >
            <strong style="color: #2DCB56;">{{ createNum }}</strong>
            <strong style="color: #ffb400;">{{ updateNum }}</strong>
            <strong style="color: #EA3536;">{{ deleteNum }}</strong>
          </i18n-t>
        </p>
        <BkInput
          v-model="pathUrl"
          clearable
          :placeholder="t('请输入组件名称、请求路径，按Enter搜索')"
          :right-icon="'bk-icon icon-search'"
          style="width: 328px;"
          @enter="handleSearch"
        />
      </div>

      <BkLoading :loading="isLoading">
        <BkTable
          border="outer"
          :data="componentList"
          size="small"
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

      <div class="p-t-20px">
        <BkPopConfirm
          v-if="componentList.length"
          trigger="click"
          ext-cls="import-resource-popconfirm-wrapper"
          :content="t('将组件配置同步到网关 bk-esb，创建网关的资源版本并发布到网关所有环境')"
          @confirm="handleConfirmSync"
        >
          <BkButton
            class="m-r-10px"
            theme="primary"
            type="button"
            :loading="confirmIsLoading"
          >
            {{ t('确认同步') }}
          </BkButton>
        </BkPopConfirm>
        <BkButton
          v-else
          class="m-r-10px"
          theme="primary"
          type="button"
          disabled
        >
          {{ t('确认同步') }}
        </BkButton>
        <BkButton
          type="button"
          :title="t('取消')"
          :disabled="isLoading"
          @click="goBack"
        >
          {{ t('取消') }}
        </BkButton>
      </div>
    </div>
  </div>
</template>

<script lang="tsx" setup>
import {
  delay,
  sortBy,
  sortedUniq,
} from 'lodash-es';
import {
  type ISyncApigwItem,
  checkSyncComponent,
  getEsbGateway,
  getSyncReleaseData,
} from '@/services/source/componentManagement';
import { useMaxTableLimit } from '@/hooks';
import TableEmpty from '@/components/table-empty/Index.vue';

const { t } = useI18n();
const { maxTableLimit, clientHeight } = useMaxTableLimit({ allocatedHeight: 242 });
const router = useRouter();

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
    label: t('资源'),
    field: 'resource_id',
    showOverflowTooltip: false,
    render: ({ row }: { row?: Partial<ISyncApigwItem> }) => {
      if (row.resource_name) {
        return (
          <span
            v-bk-tooltips={{
              content: row?.resource_id ? row?.resource_name : t('资源不存在'),
              placement: 'top',
            }}
            class={['resource-text', { 'resource-text-disabled': !row?.resource_id }]}
            onClick={() => handleEditResource(row, row?.resource_id)}
          >
            { row?.resource_name }
          </span>
        );
      }
      return '--';
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
    label: t('操作类型'),
    field: 'status ',
    width: 100,
    render: ({ row }: { row?: Partial<ISyncApigwItem> }) => {
      if (!row.resource_id) {
        return (
          <span style="color: #2DCB56;">
            { t('新建') }
          </span>
        );
      }
      if (row.resource_id && row?.component_path) {
        return (
          <span style="color: #ffb400;">
            { t('更新') }
          </span>
        );
      }
      if (row.resource_id && row?.component_path) {
        return (
          <span style="color: #ea3536;">
            { t('删除') }
          </span>
        );
      }
      return '--';
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
const isLoading = ref(false);
const pathUrl = ref('');
const esb = ref({});
const filterList = ref({});
const allData = ref([]);
const displayData = ref([]);
const requestQueue = reactive(['component']);
const tableEmptyConf = ref<{
  emptyType: string
  isAbnormal: boolean
}>({
  emptyType: '',
  isAbnormal: false,
});

const createNum = computed(() => {
  const results = allData.value?.filter(item => !item?.resource_id);
  return results?.length;
});
const updateNum = computed(() => {
  const results = allData.value?.filter(item => item?.resource_id && item?.component_path);
  return results?.length;
});
const deleteNum = computed(() => {
  const results = allData.value?.filter(item => item?.resource_id && !item?.component_path);
  return results?.length;
});

const confirmIsLoading = computed(() => isLoading.value);

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
  delay(() => isLoading.value = false, 100);
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
  }
  catch {
    tableEmptyConf.value.isAbnormal = true;
  }
  finally {
    if (requestQueue?.length > 0) {
      requestQueue?.shift();
    }
    isLoading.value = false;
  }
};

const handleConfirmSync = async () => {
  await getSyncReleaseData();
  router.push({ name: 'ComponentsManage' });
};

const handlePageLimitChange = (limit: number) => {
  pagination.limit = limit;
  pagination.current = 1;
  handlePageChange(pagination.current);
};

const handlePageChange = (page: number) => {
  isLoading.value = true;
  pagination.current = page;
  const data = getDataByPage(page);
  componentList.value?.splice(0, componentList.value?.length, ...data);
};

const goBack = () => {
  router.back();
};

const handleSearch = () => {
  isLoading.value = true;
  displayData.value = allData.value?.filter((item: ISyncApigwItem) => {
    return (item?.component_path?.includes(pathUrl.value)) || (item?.component_name?.includes(pathUrl.value));
  });
  componentList.value = getDataByPage();
  pagination.count = displayData.value?.length;
};

const getEsbGatewayData = async () => {
  const res = await getEsbGateway();
  esb.value = res;
};

const handleEditResource = (data: ISyncApigwItem, resourceId: number) => {
  if (!resourceId) {
    return;
  }
  const routeData = router.resolve({
    name: 'ResourceEdit',
    params: {
      id: esb.value?.gateway_id,
      resourceId: data?.resource_id,
    },
  });
  window.open(routeData.href, '_blank');
};

const updateTableEmptyConfig = () => {
  const isFilter = Object.values(filterList.value).filter(item => item !== '');
  if (pathUrl.value || isFilter) {
    tableEmptyConf.value.emptyType = 'searchEmpty';
    return;
  }
  tableEmptyConf.value.emptyType = '';
};

const handleClearFilterKey = () => {
  pathUrl.value = '';
  getComponents();
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

  .ag-table-header {
    font-size: 14px;

    .ag-table-change {
      color: #313238;
    }
  }

  :deep(.resource-text) {
    color: #3a84ff;
    cursor: pointer;

    &.resource-text-disabled {
      color: #dcdee5;
      cursor: not-allowed;
      user-select: none;
    }
  }
}

</style>

<style lang="scss">
.import-resource-popconfirm-wrapper.bk-popover {

  .bk-pop-confirm {

    .bk-pop-confirm-footer {
      margin-right: 48px;
    }
  }
}
</style>
