/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
          :placeholder="t('请输入 SDK 版本号，资源版本或语言')"
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
          :max-limit-config="{ allocatedHeight: 267, mode: 'tdesign'}"
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
import {
  getSDKList,
  retrySDKGenerationItem,
} from '@/services/source/sdks';
import type {
  IGatewaySDKListOutput,
  SDKGenerationStatus,
} from '@/services/types/responses/gateways';
import { copy } from '@/utils';
import {
  useFeatureFlag,
  useResourceVersion,
} from '@/stores';
import CreateSDK from './CreateSDK.vue';
import type { PrimaryTableProps, TableRowData } from '@blueking/tdesign-ui';
import AgTable from '@/components/ag-table/Index.vue';
import EditMember from '@/views/basic-info/components/EditMember.vue';
import TenantUserSelector from '@/components/tenant-user-selector/Index.vue';
import { Message } from 'bkui-vue';

interface IEmits {
  'on-show-version': [version: string]
}

type ISDKTableRow = IGatewaySDKListOutput & TableRowData;

const emits = defineEmits<IEmits>();

const { t } = useI18n();
const route = useRoute();
const featureFlagStore = useFeatureFlag();
const resourceVersionStore = useResourceVersion();

const tableRef = ref();
const keyword = ref('');
const createSdkRef = ref();
const retryingItemId = ref<number | null>(null);
const filterData = ref({
  keyword: '',
  resource_version_id: '',
});
const pollingInterval = 2000;
let pollingTimer: ReturnType<typeof setTimeout> | undefined;
let requestSequence = 0;
let isUnmounted = false;

const apigwId = computed(() => +route.params.id);

const columns = computed<PrimaryTableProps['columns']>(() => [
  {
    title: t('SDK 版本号'),
    colKey: 'version_number',
    ellipsis: true,
  },
  {
    title: t('SDK 名称'),
    colKey: 'name',
    width: 200,
    ellipsis: true,
  },
  {
    title: t('资源版本'),
    colKey: 'resource_version',
    ellipsis: true,
    cell: (h: any, { row }: any) => (
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
    title: t('状态'),
    colKey: 'status',
    width: 240,
    cell: (h: any, { row }: { row: TableRowData }) => {
      const sdkRow = row as ISDKTableRow;
      return (
        <div class="sdk-status">
          <span class={['status-label', sdkRow.status]}>{ getGenerationStatusText(sdkRow.status) }</span>
          {
            sdkRow.status === 'failed' && sdkRow.error?.message
              ? <span class="status-error" title={sdkRow.error.message}>{ sdkRow.error.message }</span>
              : null
          }
          {
            sdkRow.status === 'success' && sdkRow.native_status === 'failed'
              ? (
                <span class="native-error" title={sdkRow.native_error?.message || ''}>
                  { t('原生仓库发布失败') }
                  { sdkRow.native_error?.message ? `：${sdkRow.native_error.message}` : '' }
                </span>
              )
              : null
          }
        </div>
      );
    },
  },
  {
    title: t('创建人'),
    colKey: 'created_by',
    cell: (h: any, { row }: any) => (
      <div>
        {
          !featureFlagStore.isEnableDisplayName
            ? (
              <EditMember
                mode="detail"
                width="600px"
                field="created_by"
                content={[row?.created_by]}
              />
            )
            : (
              <TenantUserSelector
                mode="detail"
                width="600px"
                field="created_by"
                content={[row?.created_by]}
              />
            )
        }
      </div>
    ),
  },
  {
    title: t('生成时间'),
    colKey: 'created_time',
    width: 180,
    ellipsis: true,
  },
  {
    title: t('操作'),
    colKey: 'operate',
    width: 160,
    cell: (h: any, { row }: { row: TableRowData }) => {
      const sdkRow = row as ISDKTableRow;
      if (
        sdkRow.status === 'failed'
        && sdkRow.generation_task_id !== null
        && sdkRow.generation_item_id !== null
      ) {
        return (
          <bk-button
            loading={retryingItemId.value === sdkRow.generation_item_id}
            text
            theme="primary"
            onClick={() => handleRetry(sdkRow)}
          >
            { t('重试') }
          </bk-button>
        );
      }

      if (sdkRow.status !== 'success') {
        return <span>--</span>;
      }

      return (
        <div class="flex gap-10px">
          <bk-button
            disabled={!sdkRow.download_url}
            text
            theme="primary"
            onClick={() => handleCopy(sdkRow)}
          >
            { t('复制地址') }
          </bk-button>
          <bk-button
            v-bk-tooltips={{
              content: !sdkRow.download_url ? t('暂无下载地址') : '',
              disabled: sdkRow.download_url,
            }}
            disabled={!sdkRow.download_url}
            text
            theme="primary"
            class="px-10px"
            onClick={() => handleDownload(sdkRow)}
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
  tableRef.value?.fetchData(filterData.value);
}, { deep: true });

const stopPolling = () => {
  if (pollingTimer !== undefined) {
    clearTimeout(pollingTimer);
    pollingTimer = undefined;
  }
};

const schedulePolling = (rows: IGatewaySDKListOutput[]) => {
  stopPolling();
  if (!isUnmounted && rows.some(row => row.status === 'pending' || row.status === 'running')) {
    pollingTimer = setTimeout(() => {
      pollingTimer = undefined;
      tableRef.value?.refresh();
    }, pollingInterval);
  }
};

const getTableData = async (params: Record<string, any> = {}) => {
  const currentRequest = ++requestSequence;
  stopPolling();
  const result = await getSDKList(apigwId.value, params);
  if (currentRequest === requestSequence) {
    schedulePolling(result.results);
  }
  return result;
};

const getGenerationStatusText = (status: SDKGenerationStatus) => {
  const labels: Record<SDKGenerationStatus, string> = {
    pending: t('等待生成'),
    running: t('生成中'),
    success: t('生成成功'),
    failed: t('生成失败'),
  };
  return labels[status];
};

const handleKeywordChange = () => {
  filterData.value.resource_version_id = '';
  filterData.value.keyword = keyword.value;
};

// 下载单个
const handleCopy = (row: IGatewaySDKListOutput) => {
  if (row.download_url) {
    copy(row.download_url);
  }
};

const handleDownload = (row: IGatewaySDKListOutput) => {
  const { download_url } = row;
  if (download_url) {
    window.open(download_url);
  }
};

const handleRetry = async (row: IGatewaySDKListOutput) => {
  if (row.generation_task_id === null || row.generation_item_id === null) {
    return;
  }
  retryingItemId.value = row.generation_item_id;
  try {
    await retrySDKGenerationItem(apigwId.value, row.generation_task_id, row.generation_item_id);
    Message({
      message: t('SDK 重试任务已提交'),
      theme: 'success',
    });
    refresh();
  }
  finally {
    retryingItemId.value = null;
  }
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
  requestSequence += 1;
  stopPolling();
  tableRef.value?.refresh();
};

onBeforeUnmount(() => {
  isUnmounted = true;
  requestSequence += 1;
  stopPolling();
});
</script>

<style lang="scss" scoped>
.sdk-status {
  display: flex;
  flex-direction: column;
  gap: 2px;

  .status-label {
    &.pending,
    &.running {
      color: #3a84ff;
    }

    &.success {
      color: #2dcb56;
    }

    &.failed {
      color: #ea3636;
    }
  }

  .status-error,
  .native-error {
    overflow: hidden;
    color: #ea3636;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .native-error {
    color: #ff9c01;
  }
}
</style>
