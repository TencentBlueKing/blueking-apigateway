<template>
  <div class="resource-container page-wrapper-padding">
    <div class="operate flex-row justify-content-between mb15">
      <div class="flex-1 flex-row align-items-center">
        <div class="mr10">
          <bk-button theme="primary" @click="handleShowDiff" :disabled="diffDisabled">
            {{ t("版本对比") }}
          </bk-button>
        </div>
      </div>
      <div class="flex-1 flex-row justify-content-end">
        <bk-input
          class="ml10 mr10 operate-input"
          placeholder="请输入版本号"
          v-model="filterData.keyword"
        ></bk-input>
      </div>
    </div>
    <div class="flex-row resource-content">
      <div class="left-wraper" style="width: '100%'">
        <bk-loading :loading="isLoading">
          <bk-table
            class="table-layout"
            ref="bkTableRef"
            :data="tableData"
            remote-pagination
            :pagination="pagination"
            show-overflow-tooltip
            @page-limit-change="handlePageSizeChange"
            @page-value-change="handlePageChange"
            @selection-change="handleSelectionChange"
            @select-all="handleSelecAllChange"
            row-hover="auto"
          >
            <bk-table-column width="80" type="selection" align="center" />
            <bk-table-column :label="t('版本号')" min-width="120">
              <template #default="{ data }">
                <bk-button
                  text
                  theme="primary"
                  @click="handleShowInfo(data.id)"
                >
                  {{ data?.version }}--id {{ data?.id }}
                </bk-button>
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('生效环境')"
              prop="released_stages"
              min-width="120"
            >
              <template #default="{ data }">
                {{ data?.released_stages?.map((item) => item.name).join(", ") }}
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('生成时间')"
              prop="created_time"
              min-width="120"
            >
            </bk-table-column>
            <bk-table-column min-width="120" :label="t('SDK')">
              <template #default="{ data }">
                <bk-button text theme="primary" v-if="data?.sdk_count > 0" @click="jumpSdk(data)">
                  {{ data?.sdk_count }}
                </bk-button>
                <span v-else>
                  {{ data?.sdk_count }}
                </span>
              </template>
            </bk-table-column>
            <bk-table-column :label="t('操作')" min-width="140">
              <template #default="{ data }">
                <bk-button
                  text
                  theme="primary"
                  @click="openCreateSdk(data.id)"
                  v-if="user.featureFlags?.ALLOW_UPLOAD_SDK_TO_REPOSITORY">
                  {{ t("生成SDK") }}
                </bk-button>
                <bk-dropdown trigger="click" :is-show="!!data?.isReleaseMenuShow">
                  <bk-button text theme="primary" class="pl10 pr10" @click="showRelease(data)">
                    {{ t("发布至环境") }}
                  </bk-button>
                  <template #content>
                    <bk-dropdown-menu>
                      <bk-dropdown-item
                        v-for="item in stageList"
                        :key="item.id"
                        @click="handleClickStage(item, data)"
                      >
                        {{ item.name }}
                      </bk-dropdown-item>
                    </bk-dropdown-menu>
                  </template>
                </bk-dropdown>
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
      :resource-version-id="resourceVersionId"
      @done="changeTab"
      ref="createSdkRef"
    />

    <!-- 资源详情 -->
    <resource-detail
      :id="resourceVersionId" :is-show="resourceDetailShow" ref="resourceDetailRef"
      @hidden="handleHidden" />

    <!-- 版本对比 -->
    <bk-sideslider
      v-model:isShow="diffSidesliderConf.isShow"
      :title="diffSidesliderConf.title"
      :width="diffSidesliderConf.width"
      :quick-close="true">
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
      @release-success="getList()" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { getStatus } from '@/common/util';
import { useQueryList, useSelection } from '@/hooks';
import { getResourceVersionsList, getStageList } from '@/http';
import createSdk from '../components/createSdk.vue';
import resourceDetail from '../components/resourceDetail.vue';
import versionDiff from '@/components/version-diff';
import { useResourceVersion, useUser } from '@/store';
import { Message } from 'bkui-vue';
import { useRoute } from 'vue-router';
import releaseSideslider from '@/views/stage/overview/comps/release-sideslider.vue';
import TableEmpty from '@/components/table-empty.vue';
const user = useUser();

const route = useRoute();
const { t } = useI18n();
const resourceVersionStore = useResourceVersion();

const apigwId = computed(() => +route.params.id);

const filterData = ref({ keyword: '' });
const diffDisabled = ref<boolean>(true);

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
const { selections, bkTableRef, handleSelectionChange, handleSelecAllChange, resetSelections } = useSelection();

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
const tableEmptyConf = ref<{keyword: string, isAbnormal: boolean}>({
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

// 版本对比
const handleShowDiff = () => {
  diffSidesliderConf.width = window.innerWidth <= 1280 ? 1040 : 1280;

  // 选中一项，与最近版本对比；选中两项，则二者对比
  const [diffSource, diffTarget] = selections.value;
  diffSourceId.value = diffSource?.id;
  diffTargetId.value = diffTarget?.id || '';

  diffSidesliderConf.isShow = true;
  resetSelections();
};

const resourceDetailShow = ref(false);

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
  resourceVersionStore.setResourceFilter(row?.version);
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
  if (filterData.value.keyword || !tableData.value.length) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (filterData.value.keyword) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

watch(() => filterData.value, () => {
  updateTableEmptyConfig();
}, {
  deep: true,
});

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
    await getList();
    tableData.value.forEach((item) => {
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
