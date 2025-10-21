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
  <div class="resource-container page-wrapper-padding">
    <div class="flex justify-between mb-15px">
      <div class="flex grow-1 items-center">
        <div class="mr-10px">
          <BkButton
            theme="primary"
            @click="openCreateSdk"
          >
            {{ t('生成 SDK') }}
          </BkButton>
        </div>
      </div>
      <div class="flex grow-1 justify-end">
        <BkInput
          v-model="keyword"
          class="mx-10px"
          :placeholder="t('请输入关键字或选择条件搜索')"
          @change="handleKeywordChange"
        />
      </div>
    </div>
    <div class="flex resource-content">
      <div class="w-full">
        <AgTable
          ref="tableRef"
          show-settings
          resizable
          :api-method="getTableData"
          :columns="columns"
          @clear-filter="handleClearFilterKey"
        />
      </div>
    </div>

    <!-- 生成sdk弹窗 -->
    <CreateSDK
      ref="createSdkRef"
      @done="refresh"
    />
  </div>
</template>

<script setup lang="tsx">
import { getSDKList } from '@/services/source/sdks';
import { copy } from '@/utils';
import {
  useFeatureFlag,
  useResourceVersion,
} from '@/stores';
import CreateSDK from './CreateSDK.vue';
import type { PrimaryTableProps } from '@blueking/tdesign-ui';
import AgTable from '@/components/ag-table/Index.vue';

const emits = defineEmits<{ 'on-show-version': [version: string] }>();

const { t } = useI18n();
const route = useRoute();
const featureFlagStore = useFeatureFlag();
const resourceVersionStore = useResourceVersion();

const tableRef = ref();
const keyword = ref('');
const createSdkRef = ref();
const filterData = ref({
  keyword: '',
  resource_version_id: '',
});

const apigwId = computed(() => +route.params.id);

const columns = computed<PrimaryTableProps['columns']>(() => [
  {
    title: t('SDK 版本号'),
    colKey: 'version_number',
  },
  {
    title: t('SDK 名称'),
    colKey: 'name',
  },
  {
    title: t('资源版本'),
    colKey: 'resource_version',
    cell: (h, { row }) => (
      <bk-button
        text
        theme="primary"
        onClick={() => goVersionList(row)}
      >
        { row.resource_version?.version }
      </bk-button>
    ),
  },
  {
    title: t('语言'),
    colKey: 'language',
  },
  {
    title: t('创建人'),
    colKey: 'created_by',
    cell: (h, { row }) => (
      <div>
        {
          featureFlagStore.isEnableDisplayName
            ? <span><bk-user-display-name userId={row.created_by} /></span>
            : <span>{ row.created_by }</span>
        }
      </div>
    ),
  },
  {
    title: t('生成时间'),
    colKey: 'created_time',
  },
  {
    title: t('操作'),
    colKey: 'operate',
    cell: (h, { row }) => {
      return (
        <div class="flex gap-10px">
          <bk-button
            text
            theme="primary"
            onClick={() => copy(row.download_url)}
          >
            { t('复制地址') }
          </bk-button>
          <bk-button
            v-bk-tooltips={{
              content: !row.download_url ? t('暂无下载地址') : '',
              disabled: row.download_url,
            }}
            disabled={!row.download_url}
            text
            theme="primary"
            class="px-10px"
            onClick={() => handleDownload(row)}
          >
            { t('下载') }
          </bk-button>
        </div>
      );
    },
  },
]);

watch(
  () => resourceVersionStore.getResourceFilter,
  (value: any) => {
    keyword.value = value?.version;
    filterData.value.resource_version_id = value?.id;
  },
  { immediate: true },
);

watch(filterData, () => {
  tableRef.value!.fetchData(filterData.value);
}, { deep: true });

const getTableData = async (params: Record<string, any> = {}) => getSDKList(apigwId.value, params);

const handleKeywordChange = () => {
  filterData.value.resource_version_id = '';
  filterData.value.keyword = keyword.value;
};

// 下载单个
const handleDownload = (row: any) => {
  const { download_url } = row;
  window.open(download_url);
};

// 显示生成sdk弹窗
const openCreateSdk = () => {
  createSdkRef.value?.showCreateSdk();
};

const handleClearFilterKey = () => {
  keyword.value = '';
  filterData.value = {
    keyword: '',
    resource_version_id: '',
  };
};

const goVersionList = (data: any) => {
  emits('on-show-version', data?.resource_version?.version || '');
};

const refresh = () => {
  tableRef.value!.refresh();
};
</script>
