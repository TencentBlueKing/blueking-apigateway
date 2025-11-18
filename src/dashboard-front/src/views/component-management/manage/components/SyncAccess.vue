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
      <div class="m-b-16px flex items-center justify-between text-14px">
        <p class="color-#313238">
          {{ t('请确认以下组件对应网关资源的变更：') }}
          <i18n-t
            keypath="新建 {0} 条，更新 {1} 条，删除 {2} 条"
            tag="span"
          >
            <strong class="color-#2dcb56">{{ createNum }}</strong>
            <strong class="color-#ffb400">{{ updateNum }}</strong>
            <strong class="color-#EA3536">{{ deleteNum }}</strong>
          </i18n-t>
        </p>
        <BkInput
          v-model="pathUrl"
          clearable
          :placeholder="t('请输入组件名称、请求路径，按Enter搜索')"
          :right-icon="'bk-icon icon-search'"
          style="width: 328px;"
          @enter="handleSearch"
          @clear="handleClearFilter"
        />
      </div>
      <BkLoading :loading="isLoading">
        <AgTable
          ref="tableRef"
          v-model:table-data="componentList"
          table-row-key="component_id"
          show-settings
          resizable
          local-page
          :max-limit-config="{ allocatedHeight: 300, mode: 'tdesign'}"
          :columns="tableColumns"
          :table-empty-type="tableEmptyType"
          @clear-filter="handleClearFilter"
        />
      </BkLoading>

      <div class="pt-20px">
        <BkPopConfirm
          v-if="componentList.length"
          trigger="click"
          ext-cls="import-resource-popconfirm-wrapper"
          :content="t('将组件配置同步到网关 bk-esb，创建网关的资源版本并发布到网关所有环境')"
          @confirm="handleConfirmSync"
        >
          <BkButton
            theme="primary"
            :loading="confirmIsLoading"
          >
            {{ t('确认同步') }}
          </BkButton>
        </BkPopConfirm>
        <BkButton
          v-else
          theme="primary"
          disabled
        >
          {{ t('确认同步') }}
        </BkButton>
        <BkButton
          class="ml-10px"
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
import { delay } from 'lodash-es';
import type { ITableMethod } from '@/types/common';
import {
  type ISyncApigwItem,
  checkSyncComponent,
  getEsbGateway,
  getSyncReleaseData,
} from '@/services/source/componentManagement';
import AgTable from '@/components/ag-table/Index.vue';

const { t } = useI18n();
const router = useRouter();

const tableRef = useTemplateRef<InstanceType<typeof AgTable> & ITableMethod>('tableRef');
const tableColumns = ref([
  {
    title: t('系统名称'),
    colKey: 'system_name',
    ellipsis: true,
    cell: (h, { row }: { row?: Partial<ISyncApigwItem> }) => {
      return (
        <span>
          {row?.system_name || '--' }
        </span>
      );
    },
  },
  {
    title: t('组件名称'),
    colKey: 'component_name',
    ellipsis: true,
    cell: (h, { row }: { row?: Partial<ISyncApigwItem> }) => {
      return (
        <span>
          { row?.component_name || '--' }
        </span>
      );
    },
  },
  {
    title: t('组件请求方法'),
    colKey: 'component_method',
    ellipsis: true,
    cell: (h, { row }: { row?: Partial<ISyncApigwItem> }) => {
      return (
        <span>
          { row?.component_method || '--' }
        </span>
      );
    },
  },
  {
    title: t('组件请求路径'),
    colKey: 'component_path',
    ellipsis: true,
    cell: (h, { row }: { row?: Partial<ISyncApigwItem> }) => {
      return (
        <span>
          { row?.component_path || '--' }
        </span>
      );
    },
  },
  {
    title: t('资源'),
    colKey: 'resource_id',
    cell: (h, { row }: { row?: Partial<ISyncApigwItem> }) => {
      if (row.resource_name) {
        return (
          <div
            v-bk-tooltips={{
              content: row?.resource_id ? row?.resource_name : t('资源不存在'),
              placement: 'top',
              disabled: !row.isOverflow,
            }}
            class={[
              'truncate color-#3a84ff cursor-pointer',
              { 'color-#dcdee5 cursor-not-allowed': !row?.resource_id },
            ]}
            onMouseenter={e => tableRef.value?.handleCellEnter({
              e,
              row,
            })}
            onMouseLeave={e => tableRef.value?.handleCellLeave({
              e,
              row,
            })}
            onClick={() => handleEditResource(row, row?.resource_id)}
          >
            { row?.resource_name }
          </div>
        );
      }
      return '--';
    },
  },
  {
    title: t('组件ID'),
    colKey: 'component_id ',
    ellipsis: true,
    cell: (h, { row }: { row?: Partial<ISyncApigwItem> }) => {
      return (
        <span>
          { row?.component_id || '--' }
        </span>
      );
    },
  },
  {
    title: t('操作类型'),
    colKey: 'status ',
    width: 120,
    cell: (h, { row }: { row?: Partial<ISyncApigwItem> }) => {
      if (!row.resource_id || ['POST'].includes(row?.component_method)) {
        return (
          <span class="color-#2dcb56">
            { t('新建') }
          </span>
        );
      }
      if (row.resource_id && row?.component_method) {
        if (['DELETE'].includes(row?.component_method)) {
          return (
            <span class="color-#ea3536">
              { t('删除') }
            </span>
          );
        }
        if (['PUT', 'PATCH'].includes(row?.component_method)) {
          return (
            <span class="color-#ffb400">
              { t('更新') }
            </span>
          );
        }
        return (
          <span class="color-#3a84ff">
            { t('查询') }
          </span>
        );
      }
      return '--';
    },
  },
]);
const componentList = ref([]);
const tableEmptyType = ref<'empty' | 'search-empty'>('empty');
const pagination = reactive({
  current: 1,
  count: 0,
  limit: 10,
});
const isLoading = ref(false);
const pathUrl = ref('');
const esb = ref({});
const allData = ref([]);
const displayData = ref([]);
const requestQueue = reactive(['component']);

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

const setDelay = (duration: number) => {
  isLoading.value = true;
  delay(() => {
    isLoading.value = false;
  }, duration);
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
  setDelay(500);
  return displayData.value?.slice(startIndex, endIndex);
};

const getComponents = async () => {
  isLoading.value = true;
  try {
    const res = await checkSyncComponent();
    const results = Object.freeze(res || []);
    [allData.value, displayData.value, componentList.value] = [results, results, results];
    pagination.count = displayData.value.length;
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

const goBack = () => {
  router.back();
};

const handleSearch = () => {
  isLoading.value = true;
  tableEmptyType.value = 'search-empty';
  displayData.value = allData.value?.filter((item: ISyncApigwItem) => {
    return (item?.component_path?.includes(pathUrl.value)) || (item?.component_name?.includes(pathUrl.value));
  });
  pagination.count = displayData.value?.length;
  componentList.value = getDataByPage();
  setDelay(500);
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

const handleClearFilter = () => {
  pathUrl.value = '';
  tableEmptyType.value = 'empty';
  getComponents();
};

const init = () => {
  getComponents();
  getEsbGatewayData();
};
init();
</script>
