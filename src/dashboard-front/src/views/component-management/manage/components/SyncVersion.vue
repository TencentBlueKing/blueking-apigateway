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
      <div class="flex mb-16px">
        <BkInput
          v-model="pathUrl"
          clearable
          :placeholder="t('请输入组件名称、请求路径，按Enter搜索')"
          :right-icon="'bk-icon icon-search'"
          class="sync-version-search"
          @enter="handleSearch"
          @clear="handleClearFilter"
        />
      </div>
      <BkLoading :loading="isLoading">
        <AgTable
          ref="tableRef"
          v-model:table-data="displayData"
          table-row-key="component_id"
          show-settings
          resizable
          local-page
          :table-empty-type="tableEmptyType"
          :max-limit-config="{ allocatedHeight: 260, mode: 'tdesign'}"
          :columns="tableColumns"
          @clear-filter="handleClearFilter"
        />
      </BkLoading>
    </div>
  </div>
</template>

<script lang="tsx" setup>
import { delay } from 'lodash-es';
import { PERMISSION_LEVEL_MAP } from '@/enums';
import type { ITableMethod } from '@/types/common';
import { type ISyncApigwItem, getSyncVersion } from '@/services/source/component-management.ts';
import AgTable from '@/components/ag-table/Index.vue';

const { t } = useI18n();
const route = useRoute();

const tableRef = ref<InstanceType<typeof AgTable> & ITableMethod>();
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
    title: t('资源ID'),
    colKey: 'resource_id',
    ellipsis: true,
    cell: (h, { row }: { row?: Partial<ISyncApigwItem> }) => {
      return (
        <span>
          { row?.resource_id || '--'}
        </span>
      );
    },
  },
  {
    title: t('组件ID'),
    colKey: 'component_id',
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
    title: t('权限级别'),
    colKey: 'component_permission_level',
    ellipsis: true,
    cell: (h, { row }: { row?: Partial<ISyncApigwItem> }) => {
      return (
        <span>
          { PERMISSION_LEVEL_MAP[row?.component_permission_level] ?? '--' }
        </span>
      );
    },
  },
]);
let pagination = reactive({});
const requestQueue = reactive(['component']);
const allData = ref([]);
const displayData = ref([]);
const isLoading = ref(false);
const pathUrl = ref('');
const tableEmptyType = ref<'empty' | 'search-empty'>('empty');

const historyId = computed(() => route.query.id);

const getComponents = async () => {
  isLoading.value = true;
  try {
    const res = await getSyncVersion(historyId.value);
    [displayData.value, allData.value] = [Object.freeze(res), Object.freeze(res)];
    pagination.total = displayData.value?.length;
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
getComponents();

const handleClearFilter = async () => {
  pathUrl.value = '';
  await getComponents();
};

const handleSearch = () => {
  isLoading.value = true;
  tableEmptyType.value = pathUrl.value ? 'search-empty' : 'empty';
  displayData.value = allData.value?.filter((item: IISyncApigwItem) => {
    return (item?.component_path?.includes(pathUrl.value)) || (item?.component_name?.includes(pathUrl.value));
  });
  pagination.total = displayData.value?.length;
  delay(() => isLoading.value = false, 100);
};

onMounted(() => {
  pagination = tableRef.value?.getPagination();
});
</script>

<style lang="scss" scoped>
.apigw-access-manager-wrapper {

  .sync-version-search {
    width: 328px;
    margin-left: auto;
  }
}
</style>
