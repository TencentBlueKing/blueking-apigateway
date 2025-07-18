<template>
  <div class="resource-container page-wrapper-padding">
    <bk-alert
      v-if="!tableData?.length && !commonStore.isProgrammableGateway"
      theme="warning"
      :title="t(`如需生成新版本，请前往'资源配置'页面操作`)"
      class="mb20"
    />
    <div class="operate flex-row justify-content-between mb15">
      <div class="flex-1 flex-row align-items-center">
        <div class="mr10">
          <bk-button theme="primary" @click="handleShowDiff" :disabled="diffDisabled">
            {{ t('版本对比') }}
          </bk-button>
        </div>
      </div>
      <div class="flex-1 flex-row justify-content-end">
        <bk-input
          class="ml10 mr10 operate-input"
          :placeholder="t('请输入版本号')"
          v-model="filterData.keyword"
        ></bk-input>
      </div>
    </div>
    <div class="flex-row resource-content">
      <div class="left-wraper" style="width: 100%;">
        <bk-loading :loading="isLoading">
          <bk-table
            class="edition-table table-layout"
            ref="bkTableRef"
            :data="tableData"
            remote-pagination
            :pagination="pagination"
            show-overflow-tooltip
            @page-limit-change="handlePageSizeChange"
            @page-value-change="handlePageChange"
            @selection-change="handleSelectionChange"
            @select-all="handleSelecAllChange"
            :cell-class="getCellClass"
            row-hover="auto"
            border="outer"
          >
            <bk-table-column width="80" type="selection" align="center" />
            <bk-table-column :label="t('版本号')">
              <template #default="{ data }">
                <bk-button text theme="primary" @click="handleShowInfo(data.id)">
                  {{ data?.version }}
                </bk-button>
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('生效环境')"
              prop="released_stages"
            >
              <template #default="{ data }">
                {{ data?.released_stages?.map((item: any) => item.name).join(", ") }}
              </template>
            </bk-table-column>
            <bk-table-column :label="t('生成时间')" prop="created_time">
            </bk-table-column>
            <bk-table-column :label="t('SDK')">
              <template #default="{ data }">
                <bk-button
                  text
                  theme="primary"
                  v-if="data?.sdk_count > 0"
                  @click="jumpSdk(data)"
                >
                  {{ data?.sdk_count }}
                </bk-button>
                <span v-else>
                  {{ data?.sdk_count }}
                </span>
              </template>
            </bk-table-column>
            <bk-table-column :label="t('创建者')" prop="created_by">
              <template #default="{ row }">
                <span><bk-user-display-name :user-id="row.created_by" /></span>
              </template>
            </bk-table-column>
            <bk-table-column :label="t('操作')" width="200">
              <template #default="{ data }">
                <bk-button
                  text
                  theme="primary"
                  @click="openCreateSdk(data.id)"
                  v-if="user.featureFlags?.ALLOW_UPLOAD_SDK_TO_REPOSITORY"
                >
                  {{ t('生成 SDK') }}
                </bk-button>
                <bk-dropdown
                  v-if="!commonStore.isProgrammableGateway"
                  :is-show="!!data?.isReleaseMenuShow"
                  trigger="click"
                >
                  <bk-button
                    text
                    theme="primary"
                    class="pl10 pr10"
                    @click="showRelease(data)"
                  >
                    {{ t('发布至环境') }}
                  </bk-button>
                  <template #content>
                    <bk-dropdown-menu>
                      <bk-dropdown-item
                        v-for="item in stageList"
                        :key="item.id"
                        @click="!item.publish_validate_msg ? handleClickStage(item, data) : ''"
                        :class="{ 'menu-item-disabled': !!item.publish_validate_msg }"
                        v-bk-tooltips="{ content: item.publish_validate_msg, disabled: !item.publish_validate_msg }"
                      >
                        {{ item.name }}
                      </bk-dropdown-item>
                    </bk-dropdown-menu>
                  </template>
                </bk-dropdown>
                <bk-button
                  text
                  theme="primary"
                  @click.stop="handleShowExport(data)"
                >
                  {{ t('导出') }}
                </bk-button>
              </template>
            </bk-table-column>
            <template #empty>
              <TableEmpty
                :keyword="tableEmptyConf.keyword"
                :abnormal="tableEmptyConf.isAbnormal"
                @reacquire="getList"
                @clear-filter="handleClearFilterKey"
              />
            </template>
          </bk-table>
        </bk-loading>
      </div>
    </div>

    <!-- 生成sdk弹窗 -->
    <create-sdk
      :version-list="tableData"
      :resource-version-id="String(resourceVersionId)"
      @done="changeTab"
      ref="createSdkRef"
    />

    <!-- 资源详情 -->
    <resource-detail
      :id="resourceVersionId"
      :is-show="resourceDetailShow"
      ref="resourceDetailRef"
      @hidden="handleHidden"
    />

    <!-- 版本对比 -->
    <bk-sideslider
      v-model:is-show="diffSidesliderConf.isShow"
      :title="diffSidesliderConf.title"
      :width="diffSidesliderConf.width"
      :quick-close="true"
    >
      <template #default>
        <div class="p20">
          <version-diff ref="diffRef" :source-id="diffSourceId" :target-id="diffTargetId">
          </version-diff>
        </div>
      </template>
    </bk-sideslider>

    <!-- 发布资源 -->
    <release-sideslider
      :current-assets="stageData"
      :version="versionData"
      ref="releaseSidesliderRef"
      @hidden="getList()"
      @release-success="getList()"
    />

    <!-- 资源版本导出 -->
    <ExportResourceDialog
      class="resource-version-export-dialog"
      v-model:dialog-config="exportDialogConfig"
      v-model:dialog-params="exportParams"
      @confirm="handleExportDownload"
    />
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  onMounted,
  onUnmounted,
  reactive,
  ref,
  watch,
} from 'vue';
import { useI18n } from 'vue-i18n';
import { Message } from 'bkui-vue';
import { useRoute } from 'vue-router';
import dayjs from 'dayjs';

import { getStatus } from '@/common/util';
import {
  exportVersion,
  getResourceVersionsList,
  getStageList,
} from '@/http';
import {
  useQueryList,
  useSelection,
} from '@/hooks';
import createSdk from '../components/createSdk.vue';
import resourceDetail from '../components/resourceDetail.vue';
import versionDiff from '@/components/version-diff/index.vue';
import {
  useCommon,
  useResourceVersion,
  useUser,
} from '@/store';
import {
  IExportDialog,
  IExportParams,
} from '@/types';
import releaseSideslider from '@/views/stage/overview/comps/release-sideslider.vue';
import TableEmpty from '@/components/table-empty.vue';
import ExportResourceDialog from '@/components/export-resource-dialog/index.vue';
import { orderBy } from 'lodash';

const props = defineProps({
  version: {
    type: String,
    default: '',
  },
});

const route = useRoute();
const { t } = useI18n();
const resourceVersionStore = useResourceVersion();
const commonStore = useCommon();
const user = useUser();

const apigwId = computed(() => +route.params.id);

const filterData = ref({ keyword: props.version });
const diffDisabled = ref<boolean>(true);
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
const exportParams = reactive<IExportParams & { id?: number}>({
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
} = useQueryList(getResourceVersionsList, filterData);

// 列表多选
const {
  selections,
  bkTableRef,
  handleSelectionChange,
  handleSelecAllChange,
  resetSelections,
} = useSelection();

// 当前操作的行
const resourceVersionId = ref();
const createSdkRef = ref(null);
const resourceDetailRef = ref(null);

// 该网关下的环境列表
const stageList = ref<any>([]);
// 选择发布的环境
const stageData = ref();
const versionData = ref();
const releaseSidesliderRef = ref(null);
const tableEmptyConf = ref<{ keyword: string; isAbnormal: boolean }>({
  keyword: '',
  isAbnormal: false,
});

// 生成sdk
const openCreateSdk = (id: number) => {
  resourceVersionId.value = id;
  createSdkRef.value?.showCreateSdk();
};

// 版本对比抽屉
const diffSidesliderConf = reactive({
  isShow: false,
  width: 1040,
  title: t('版本资源对比'),
});
const diffSourceId = ref();
const diffTargetId = ref();
const resourceDetailShow = ref(false);

// 版本对比
const handleShowDiff = () => {
  diffSidesliderConf.width = window.innerWidth <= 1280 ? 1040 : 1280;

  // 调整展示顺序，旧的版本(id 较小的那个)放左边，新的版本放右边
  const selectedResources = orderBy(selections.value, 'id');
  // 选中一项，与最近版本对比；选中两项，则二者对比
  const [diffSource, diffTarget] = selectedResources;
  diffSourceId.value = diffSource?.id;
  diffTargetId.value = diffTarget?.id || '';

  diffSidesliderConf.isShow = true;
  resetSelections();
};

// 版本导出
const handleShowExport = ({ id }: { id: number}) => {
  exportDialogConfig.isShow = true;
  exportParams.id = id;
};

// 版本导出下载
const handleExportDownload = async () => {
  const params = { ...exportParams };
  delete params.export_type;
  exportDialogConfig.loading = true;
  try {
    const res = await exportVersion(apigwId.value, params);
    if (res.success) {
      Message({
        message: t('导出成功'),
        theme: 'success',
        width: 'auto',
      });
    }
    exportDialogConfig.isShow = false;
  } catch (e) {
    const error = e as Error;
    Message({
      message: error?.message || t('导出失败'),
      theme: 'error',
      width: 'auto',
    });
  } finally {
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
    } else {
      Message({
        theme: 'warning',
        message: t('请先添加环境！'),
      });
    }
  } catch (e) {
    Message({
      theme: 'warning',
      message: t('获取环境列表失败，请稍后再试！'),
    });
    console.log(e);
  }
};

// 展示发布弹窗
const handleClickStage = (stage: any, row: any) => {
  if (getStatus(stage) === 'doing') {
    return Message({
      theme: 'warning',
      message: t('该环境正在发布资源，请稍后再试'),
    });
  }
  stageData.value = stage;
  versionData.value = row;
  releaseSidesliderRef.value.showReleaseSideslider();
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

const getCellClass = (_column: any, _index: number, row: any, _rowIndex: number) => {
  const targetTime = dayjs(row.created_time); // 目标时间
  const curTime = dayjs();
  let isWithin24Hours = false;
  if (targetTime.isBefore(curTime) || targetTime.isSame(curTime)) {
    const addOneDay = targetTime.add(1, 'day');
    isWithin24Hours = curTime.isBefore(addOneDay) || curTime.isSame(addOneDay);
  }
  return isWithin24Hours ? 'last24hours' : '';
};

watch(
  () => filterData.value,
  () => {
    updateTableEmptyConfig();
  },
  {
    deep: true,
  },
);

watch(
  () => selections.value,
  (sel) => {
    if (sel?.length === 1 || sel?.length === 2) {
      diffDisabled.value = false;
    } else {
      diffDisabled.value = true;
    }
  },
  {
    deep: true,
  },
);

let timeId: any = null;
onMounted(() => {
  timeId = setInterval(async () => {
    await getList(getResourceVersionsList, false);
    tableData.value.forEach((item: Record<string, any>) => {
      if (selections.value.find(sel => sel.id === item.id)) {
        bkTableRef.value?.toggleRowSelection(item, true);
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
    table tbody tr td.last24hours {
      background-color: #f2fcf5;
    }
  }
  :deep(.bk-table-head) {
    scrollbar-color: transparent transparent;
  }
  :deep(.bk-table-body) {
    scrollbar-color: transparent transparent;
  }
}
:deep(.menu-item-disabled) {
  background-color: #dcdee5;
  color: #fff;
  cursor: not-allowed;
  &:hover {
    background-color: #dcdee5;
    color: #fff;
    cursor: not-allowed;
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
