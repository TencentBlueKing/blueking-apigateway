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
        </div>
      </div>
      <div class="flex grow-1 justify-end">
        <BkInput
          v-model="filterData.keyword"
          :placeholder="t('请输入版本号')"
        />
      </div>
    </div>
    <div class="flex resource-content">
      <div class="w-full">
        <BkLoading :loading="isLoading">
          <BkTable
            ref="tableRef"
            class="edition-table table-layout"
            :data="tableData"
            remote-pagination
            :pagination="pagination"
            show-overflow-tooltip
            :cell-class="getCellClass"
            row-hover="auto"
            border="outer"
            @page-limit-change="handlePageSizeChange"
            @page-value-change="handlePageChange"
            @selection-change="handleSelectionChange"
            @select-all="handleSelectAllChange"
          >
            <BkTableColumn
              width="80"
              type="selection"
              align="center"
            />
            <BkTableColumn :label="t('版本号')">
              <template #default="{ data }">
                <BkButton
                  text
                  theme="primary"
                  @click="() => handleShowInfo(data.id)"
                >
                  {{ data?.version }}
                </BkButton>
              </template>
            </BkTableColumn>
            <BkTableColumn
              :label="t('生效环境')"
              prop="released_stages"
            >
              <template #default="{ data }">
                {{ data?.released_stages?.map((item: any) => item.name).join(", ") || '--' }}
              </template>
            </BkTableColumn>
            <BkTableColumn
              :label="t('生成时间')"
              prop="created_time"
            />
            <BkTableColumn :label="t('SDK')">
              <template #default="{ data }">
                <BkButton
                  v-if="data?.sdk_count > 0"
                  text
                  theme="primary"
                  @click="() => jumpSdk(data)"
                >
                  {{ data?.sdk_count }}
                </BkButton>
                <span v-else>
                  {{ data?.sdk_count }}
                </span>
              </template>
            </BkTableColumn>
            <BkTableColumn
              :label="t('创建者')"
              prop="created_by"
            >
              <template #default="{ row }">
                <span><bk-user-display-name :user-id="row.created_by" /></span>
              </template>
            </BkTableColumn>
            <BkTableColumn
              :label="t('操作')"
              width="200"
            >
              <template #default="{ data }">
                <div class="flex gap-10px">
                  <BkButton
                    v-if="featureFlagStore.flags.ALLOW_UPLOAD_SDK_TO_REPOSITORY"
                    text
                    theme="primary"
                    @click="() => openCreateSdk(data.id)"
                  >
                    {{ t('生成 SDK') }}
                  </BkButton>
                  <BkDropdown
                    v-if="!gatewayStore.isProgrammableGateway"
                    :is-show="!!data?.isReleaseMenuShow"
                    trigger="click"
                  >
                    <BkButton
                      text
                      theme="primary"
                      class="px-10px"
                      @click="() => showRelease(data)"
                    >
                      {{ t('发布至环境') }}
                    </BkButton>
                    <template #content>
                      <BkDropdownMenu>
                        <BkDropdownItem
                          v-for="item in stageList"
                          :key="item.id"
                          v-bk-tooltips="{ content: item.publish_validate_msg, disabled: !item.publish_validate_msg }"
                          :class="{ 'menu-item-disabled': !!item.publish_validate_msg }"
                          @click="!item.publish_validate_msg ? handleClickStage(item, data) : ''"
                        >
                          {{ item.name }}
                        </BkDropdownItem>
                      </BkDropdownMenu>
                    </template>
                  </BkDropdown>
                  <BkButton
                    text
                    theme="primary"
                    @click.stop="() => handleShowExport(data)"
                  >
                    {{ t('导出') }}
                  </BkButton>
                </div>
              </template>
            </BkTableColumn>
            <template #empty>
              <TableEmpty
                :keyword="tableEmptyConf.keyword"
                :abnormal="tableEmptyConf.isAbnormal"
                @reacquire="getList"
                @clear-filter="handleClearFilterKey"
              />
            </template>
          </BkTable>
        </BkLoading>
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
      @hidden="getList"
      @release-success="getList"
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

<script setup lang="ts">
import { Message } from 'bkui-vue';
import dayjs from 'dayjs';
import { getStageStatus } from '@/utils';
import { exportVersion, getVersionList } from '@/services/source/resource.ts';
import { getStageList } from '@/services/source/stage';
import {
  useQueryList,
  useSelection,
} from '@/hooks';
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
import TableEmpty from '@/components/table-empty/Index.vue';
import ExportResourceDialog from '../../components/ExportResourceDialog.vue';
import { orderBy } from 'lodash-es';

interface IProps { version?: string }

const { version = '' } = defineProps<IProps>();

const { t } = useI18n();
const route = useRoute();
const resourceVersionStore = useResourceVersion();
const gatewayStore = useGateway();
const featureFlagStore = useFeatureFlag();

const filterData = ref({ keyword: version });
const diffDisabled = ref(true);

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

// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList({
  apiMethod: getVersionList,
  filterData,
});

// 列表多选
const {
  selections,
  handleSelectionChange,
  handleSelectAllChange,
  resetSelections,
} = useSelection();

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
const tableEmptyConf = ref<{
  keyword: string
  isAbnormal: boolean
}>({
  keyword: '',
  isAbnormal: false,
});

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

let timeId: any = null;

const apigwId = computed(() => +route.params.id);

watch(
  filterData,
  () => {
    updateTableEmptyConfig();
  },
  { deep: true },
);

watch(
  selections,
  () => {
    if (selections.value?.length === 1 || selections.value?.length === 2) {
      diffDisabled.value = false;
    }
    else {
      diffDisabled.value = true;
    }
  },
  { deep: true },
);

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
  resetSelections(tableRef.value);
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
    await exportVersion(apigwId.value, params);
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
  catch (e) {
    Message({
      theme: 'warning',
      message: t('获取环境列表失败，请稍后再试！'),
    });
    console.log(e);
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

const handleClearFilterKey = () => {
  filterData.value.keyword = '';
  getList();
  updateTableEmptyConfig();
};

const updateTableEmptyConfig = () => {
  tableEmptyConf.value.isAbnormal = pagination.value.abnormal;
  if (filterData.value.keyword && !tableData.value.length) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (filterData.value.keyword) {
    // tableEmptyConf.value.keyword = '$CONSTANT';
    tableEmptyConf.value.keyword = filterData.value.keyword;
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const getCellClass = (_column: any, _index: number, row: any) => {
  const targetTime = dayjs(row.created_time); // 目标时间
  const curTime = dayjs();
  let isWithin24Hours = false;
  if (targetTime.isBefore(curTime) || targetTime.isSame(curTime)) {
    const addOneDay = targetTime.add(1, 'day');
    isWithin24Hours = curTime.isBefore(addOneDay) || curTime.isSame(addOneDay);
  }
  return isWithin24Hours ? 'last24hours' : '';
};

onMounted(() => {
  timeId = setInterval(async () => {
    await getList(getVersionList, false);
    tableData.value.forEach((item: Record<string, any>) => {
      if (selections.value.find(sel => sel.id === item.id)) {
        tableRef.value?.toggleRowSelection(item, true);
      }
    });
  }, 1000 * 30);
});

onUnmounted(() => {
  clearInterval(timeId);
});
</script>

<style lang="scss" scoped>
.edition-table {

  :deep(.bk-table-body) {
    scrollbar-color: transparent transparent;

    table tbody tr td.last24hours {
      background-color: #f2fcf5;
    }
  }

  :deep(.bk-table-head) {
    scrollbar-color: transparent transparent;
  }
}

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
</style>
