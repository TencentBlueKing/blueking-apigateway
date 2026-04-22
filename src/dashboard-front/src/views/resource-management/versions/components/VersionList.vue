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
    <BkAlert
      v-if="!tableData?.length && !gatewayStore.isProgrammableGateway"
      theme="warning"
      :title="t(`如需生成新版本，请前往'资源配置'页面操作`)"
      class="mb-20px"
    />
    <BkAlert
      :theme="versionCountAlert.theme"
      :title="versionCountAlert.title"
      class="mb-16px"
    />
    <div class="flex justify-between mb-15px">
      <div class="flex grow-1 items-center">
        <div class="mr-10px">
          <BkButton
            theme="primary"
            :disabled="diffDisabled"
            @click="handleShowDiff"
          >
            {{ t('版本对比') }}
          </BkButton>
          <BkButton
            v-bk-tooltips="{ content: t('无法批量删除，因为勾选了无法删除的版本'), disabled: !batchDeleteDisabled }"
            class="ml-12px"
            :disabled="batchDeleteDisabled || selections.length < 2"
            @click="handleBatchDelete"
          >
            {{ t('批量删除') }}
          </BkButton>
        </div>
      </div>
      <div class="flex grow-1 justify-end">
        <BkInput
          v-model="filterData.keyword"
          :placeholder="t('搜索版本号')"
        />
      </div>
    </div>
    <div class="flex resource-content">
      <div class="w-full">
        <AgTable
          ref="tableRef"
          v-model:table-data="tableData"
          :immediate="false"
          resizable
          show-settings
          show-selection
          :show-first-full-row="selections.length > 0"
          :max-limit-config="{ allocatedHeight: 267, mode: 'tdesign'}"
          :api-method="getTableData"
          :columns="columns"
          @clear-filter="handleClearFilterKey"
          @selection-change="handleSelectionChange"
          @request-done="handleRequestDone"
        />
      </div>
    </div>

    <!-- 生成sdk弹窗 -->
    <CreateSDK
      ref="createSdkRef"
      :version-list="tableData"
      :resource-version-id="String(resourceVersionId)"
      @done="changeTab"
    />

    <!-- 资源详情 -->
    <ResourceDetail
      :id="resourceVersionId"
      ref="resourceDetailRef"
      :is-show="resourceDetailShow"
      @hidden="handleHidden"
    />

    <!-- 版本对比 -->
    <BkSideslider
      v-model:is-show="diffSliderConf.isShow"
      :title="diffSliderConf.title"
      :width="diffSliderConf.width"
      quick-close
    >
      <template #default>
        <div class="p-20px">
          <VersionDiff
            :source-id="diffSourceId"
            :target-id="diffTargetId"
          />
        </div>
      </template>
    </BkSideslider>

    <!-- 发布资源 -->
    <ReleaseStage
      ref="releaseSidesliderRef"
      :current-assets="stageData"
      :version="versionData"
      @hidden="refresh"
      @release-success="refresh"
    />

    <!-- 资源版本导出 -->
    <ExportResourceDialog
      v-model:dialog-config="exportDialogConfig"
      v-model:dialog-params="exportParams"
      class="resource-version-export-dialog"
      @confirm="handleExportDownload"
    />
  </div>
</template>

<script setup lang="tsx">
import { InfoBox, Message } from 'bkui-vue';
import { getStageStatus } from '@/utils';
import {
  batchDeleteResourceVersions,
  deleteResourceVersion,
  exportVersion,
  getVersionList,
} from '@/services/source/resource.ts';
import { getStageList } from '@/services/source/stage';
import CreateSDK from './CreateSDK.vue';
import ResourceDetail from './ResourceDetail.vue';
import VersionDiff from '@/components/version-diff/Index.vue';
import {
  useFeatureFlag,
  useGateway,
  useResourceVersion,
} from '@/stores';
import {
  type IExportDialog,
  type IExportParams,
} from '@/types/common';
import ReleaseStage from '@/components/release-stage/Index.vue';
import ExportResourceDialog from '../../components/ExportResourceDialog.vue';
import { orderBy } from 'lodash-es';
import type { PrimaryTableProps } from '@blueking/tdesign-ui';
import AgTable from '@/components/ag-table/Index.vue';
import EditMember from '@/views/basic-info/components/EditMember.vue';
import TenantUserSelector from '@/components/tenant-user-selector/Index.vue';

interface IProps { version?: string }

const { version = '' } = defineProps<IProps>();

const { t } = useI18n();
const route = useRoute();
const resourceVersionStore = useResourceVersion();
const gatewayStore = useGateway();
const featureFlagStore = useFeatureFlag();

const filterData = ref({ keyword: version });
const diffDisabled = ref(true);
const tableData = ref<any[]>([]);
const selections = ref<any[]>([]);
const versionCount = ref(0);

// 导出配置
const exportDialogConfig = reactive<IExportDialog>({
  isShow: false,
  title: t('请选择导出的格式'),
  loading: false,
  exportFileDocType: 'resource',
  hiddenExportContent: true,
  hiddenResourceTip: true,
  hiddenExportTypeLabel: true,
});

// 导出参数
const exportParams = reactive<IExportParams & { id?: number }>({
  export_type: 'all',
  file_type: 'yaml',
  id: 0,
});

// 当前操作的行
const resourceVersionId = ref();
const createSdkRef = ref();
const resourceDetailRef = ref();

// 该网关下的环境列表
const stageList = ref<any>([]);
// 选择发布的环境
const stageData = ref();
const versionData = ref();
const releaseSidesliderRef = ref();

// 版本对比抽屉
const diffSliderConf = reactive({
  isShow: false,
  width: 1040,
  title: t('版本资源对比'),
});

const tableRef = ref();
const diffSourceId = ref();
const diffTargetId = ref();
const resourceDetailShow = ref(false);

const apigwId = computed(() => gatewayStore.apigwId);

const versionCountAlert = computed(() => {
  if (versionCount.value >= 100) {
    return {
      theme: 'error' as const,
      title: t('当前已创建 {n} 个资源版本，已达到上限 100 个，无法创建新版本。请删除不再使用的旧版本以释放配额。', { n: versionCount.value }),
    };
  }
  if (versionCount.value > 80) {
    return {
      theme: 'warning' as const,
      title: t('当前已创建 {n} 个资源版本，接近上限 100 个。建议删除不再使用的旧版本以释放配额。', { n: versionCount.value }),
    };
  }
  return {
    theme: 'info' as const,
    title: t('每个网关最多可创建 100 个资源版本，当前已创建 {n} 个。', { n: versionCount.value }),
  };
});

// 批量删除按钮禁用状态：当选中项中有 deletable 为 false 的成员时禁用
const batchDeleteDisabled = computed(() => selections.value.some((item: any) => item.deletable === false));

const columns = computed<PrimaryTableProps['columns']>(() => [
  {
    colKey: 'version',
    title: t('版本号'),
    width: 120,
    ellipsis: true,
    cell: (h: any, { row }: any) => (
      <bk-button
        text
        theme="primary"
        onClick={() => handleShowInfo(row.id)}
      >
        { row.version }
      </bk-button>
    ),
  },
  {
    colKey: 'released_stages',
    title: t('生效环境'),
    ellipsis: true,
    cell: (h: any, { row }: any) =>
      <span>{ row.released_stages?.map((item: any) => item.name).join(', ') || '--' }</span>,
  },
  {
    colKey: 'created_time',
    title: t('生成时间'),
    width: 180,
    ellipsis: true,
  },
  {
    colKey: 'sdk',
    title: 'SDK',
    cell: (h: any, { row }: any) => (
      <div>
        {
          row.sdk_count > 0
            ? (
              <bk-button
                text
                theme="primary"
                onClick={() => jumpSdk(row)}
              >
                { row.sdk_count }
              </bk-button>
            )
            : <span>{ row.sdk_count }</span>
        }
      </div>
    ),
  },
  {
    colKey: 'created_by',
    title: t('创建者'),
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
    colKey: 'actions',
    title: t('操作'),
    width: 200,
    cell: (h: any, { row }: any) => (
      <div class="flex gap-10px">
        {
          featureFlagStore.flags.ALLOW_UPLOAD_SDK_TO_REPOSITORY
            ? (
              <bk-button
                text
                theme="primary"
                onClick={() => openCreateSdk(row.id)}
              >
                { t('生成 SDK') }
              </bk-button>
            )
            : ''
        }
        {
          !gatewayStore.isProgrammableGateway
            ? (
              <bk-dropdown
                isShow={!!row.isReleaseMenuShow}
                trigger="click"
              >
                {{
                  default: () => (
                    <bk-button
                      text
                      theme="primary"
                      class="px-10px"
                      onClick={() => showRelease(row)}
                    >
                      {t('发布至环境')}
                    </bk-button>
                  ),
                  content: () => (
                    <bk-dropdown-menu>
                      {
                        stageList.value.map((item: any) => (
                          <bk-dropdown-item
                            key={item.id}
                            v-bk-tooltips={{
                              content: item.publish_validate_msg,
                              disabled: !item.publish_validate_msg,
                            }}
                            class={{ 'menu-item-disabled': !!item.publish_validate_msg }}
                            onClick={() => !item.publish_validate_msg ? handleClickStage(item, row) : ''}
                          >
                            {item.name}
                          </bk-dropdown-item>
                        ))
                      }
                    </bk-dropdown-menu>
                  ),
                }}
              </bk-dropdown>
            )
            : ''
        }
        <bk-button
          text
          theme="primary"
          onClick={() => handleShowExport(row)}
        >
          {t('导出')}
        </bk-button>
        <bk-button
          disabled={row.deletable === false}
          text
          theme="primary"
          v-bk-tooltips={{
            content: t(
              '已发布到环境【{stage}】或生成了 SDK，无法删除',
              { stage: row.released_stages?.map((item: any) => item.name).join(', ') || '--' },
            ),
            disabled: row.deletable,
          }}
          onClick={() => handleDelete(row as any)}
        >
          {t('删除')}
        </bk-button>
      </div>
    ),
  },
]);

watch(
  selections,
  () => {
    diffDisabled.value = ![1, 2].includes(selections.value.length);
  },
  { deep: true },
);

watch(
  filterData,
  () => {
    nextTick(() => {
      tableRef.value!.fetchData(filterData.value);
    });
  },
  {
    deep: true,
    immediate: true,
  },
);

watch(
  () => route.query,
  () => {
    if (route.query?.version) {
      filterData.value.keyword = route.query.version as string;
    }
  },
  {
    immediate: true,
    deep: true,
  },
);

const getTableData = async (params: Record<string, any> = {}) => getVersionList(apigwId.value, params);

const handleSelectionChange = (payload: any) => {
  selections.value = payload.selections;
};

// 生成sdk
const openCreateSdk = (id: number) => {
  resourceVersionId.value = id;
  createSdkRef.value?.showCreateSdk();
};

// 版本对比
const handleShowDiff = () => {
  diffSliderConf.width = window.innerWidth <= 1280 ? 1040 : 1280;

  // 调整展示顺序，旧的版本(id 较小的那个)放左边，新的版本放右边
  const selectedResources = orderBy(selections.value, 'id');
  // 选中一项，与最近版本对比；选中两项，则二者对比
  const [diffSource, diffTarget] = selectedResources;
  diffSourceId.value = diffSource?.id;
  diffTargetId.value = diffTarget?.id || '';

  diffSliderConf.isShow = true;
  selections.value = [];
  tableRef.value!.handleResetSelection();
};

// 版本导出
const handleShowExport = ({ id }: { id: number }) => {
  exportDialogConfig.isShow = true;
  exportParams.id = id;
};

// 版本导出下载
const handleExportDownload = async () => {
  const params = { ...exportParams };
  delete params.export_type;
  exportDialogConfig.loading = true;
  try {
    await exportVersion(apigwId.value, params as any);
    Message({
      message: t('导出成功'),
      theme: 'success',
      width: 'auto',
    });
    exportDialogConfig.isShow = false;
  }
  catch (e) {
    const fileReader = new FileReader();
    fileReader.readAsText(e as Blob, 'utf-8');
    fileReader.onload = function () {
      const blobError = JSON.parse(fileReader.result as string);
      Message({
        message: blobError?.error?.message || t('导出失败'),
        theme: 'error',
        width: 'auto',
      });
    };
  }
  finally {
    exportDialogConfig.loading = false;
    exportDialogConfig.isShow = false;
  }
};

// 展示详情
const handleShowInfo = (id: number) => {
  resourceVersionId.value = id;
  resourceDetailShow.value = true;
};

const handleHidden = () => {
  resourceDetailShow.value = false;
};

// 生成sdk成功，跳转列表
const changeTab = () => {
  resourceVersionStore.setTabActive('sdk');
};

// 过滤当前资源版本下的sdk
const jumpSdk = (row: any) => {
  resourceVersionStore.setResourceFilter(row);
  resourceVersionStore.setTabActive('sdk');
};

// 选择要发布的环境
const showRelease = async (row: any) => {
  try {
    const res = await getStageList(apigwId.value);
    if (res?.length) {
      stageList.value = res;
      row.isReleaseMenuShow = true;
    }
    else {
      Message({
        theme: 'warning',
        message: t('请先添加环境！'),
      });
    }
  }
  catch {
    Message({
      theme: 'warning',
      message: t('获取环境列表失败，请稍后再试！'),
    });
  }
};

// 展示发布弹窗
const handleClickStage = (stage: any, row: any) => {
  if (getStageStatus(stage) === 'doing') {
    return Message({
      theme: 'warning',
      message: t('该环境正在发布资源，请稍后再试'),
    });
  }
  stageData.value = stage;
  versionData.value = row;
  releaseSidesliderRef.value?.showReleaseSideslider();
  row.isReleaseMenuShow = false;
};

// 删除资源版本
const handleDelete = (
  { id, version }: {
    id: number
    version: string
  },
) => {
  InfoBox({
    title: t('是否删除该版本？'),
    subTitle: (
      <div>
        <div class="pb-16px text-align-left">{t('版本：{v}', { v: version })}</div>
        <div class="py-12px px-16px text-align-left bg-#f5f7fa">{t('删除该版本后将无法恢复，请谨慎操作')}</div>
      </div>
    ),
    confirmText: t('删除'),
    cancelText: t('取消'),
    confirmButtonTheme: 'danger',
    onConfirm: async () => {
      await deleteResourceVersion(apigwId.value, id);
      Message({
        message: t('删除成功'),
        theme: 'success',
      });
      selections.value = [];
      tableRef.value!.handleResetSelection();
      refresh();
    },
  });
};

const handleBatchDelete = () => {
  InfoBox({
    width: 480,
    class: 'version-remove-info',
    title: t('确定删除选中版本？'),
    confirmText: t('删除'),
    cancelText: t('取消'),
    confirmButtonTheme: 'danger',
    content: () => (
      <div class="info-content">
        <div class="remove-tip">
          {t('删除选中版本后将无法恢复，请谨慎操作')}
        </div>
        <div class="remove-version-list-wrapper">
          <div class="remove-version-counter">
            <span innerHTML={t('已选择以下 {0} 个版本', [`<strong>${selections.value.length}</strong>`])}></span>
          </div>
          <div class="detail-list">
            {
              selections.value.map((row: any) => (
                <div class="detail-item">{row.version}</div>
              ))
            }
          </div>
        </div>
      </div>
    ),
    onConfirm: async () => {
      const ids = selections.value.map((item: any) => item.id);
      await batchDeleteResourceVersions(apigwId.value, { ids });
      Message({
        message: t('删除成功'),
        theme: 'success',
      });
      selections.value = [];
      tableRef.value!.handleResetSelection();
      refresh();
    },
  });
};

const handleRequestDone = () => {
  const pagination = tableRef.value?.getPagination();
  versionCount.value = pagination?.total ?? 0;
};

const handleClearFilterKey = () => {
  filterData.value.keyword = '';
};

const refresh = () => {
  tableRef.value!.refresh();
};

</script>

<style lang="scss" scoped>

:deep(.menu-item-disabled) {
  color: #fff;
  cursor: not-allowed;
  background-color: #dcdee5;

  &:hover {
    color: #fff;
    cursor: not-allowed;
    background-color: #dcdee5;
  }
}

</style>

<style lang="scss">
.resource-version-export-dialog {

  .bk-form-item {

    .bk-form-content {
      margin-left: 0 !important;
    }
  }
}

.version-remove-info {

  .info-content {
    font-size: 14px;
    text-align: left;

    .remove-tip {
      padding: 12px 16px;
      margin-top: 16px;
      background: #f5f6fa;
      border-radius: 2px;
    }

    .remove-version-list-wrapper {
      margin-top: 16px;

      .remove-version-counter {
        display: flex;
        align-items: center;
        height: 32px;
        padding-left: 16px;
        color: #313238;
        background: #f0f1f5;
        border-bottom: 1px solid #dcdee5;
      }

      .detail-list {
        max-height: 160px;
        overflow-y: auto;

        .detail-item {
          display: flex;
          height: 32px;
          padding-left: 16px;
          font-size: 12px;
          align-items: center;
          border-bottom: 1px solid #dcdee5;

          &:nth-child(even) {
            background-color: #fafbfd;
          }
        }
      }
    }
  }
}

</style>
