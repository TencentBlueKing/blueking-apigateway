<template>
  <div class="resource-container page-wrapper-padding">
    <div class="operate flex-row justify-content-between mb15">
      <div class="flex-1 flex-row align-items-center">
        <div class="mr10">
          <bk-button theme="primary" @click="openCreateSdk">
            {{ t('生成 SDK') }}
          </bk-button>
        </div>
      </div>
      <div class="flex-1 flex-row justify-content-end">
        <bk-input
          class="ml10 mr10 operate-input"
          placeholder="请输入关键字或选择条件查询"
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
            row-hover="auto"
            border="outer"
          >
            <!-- <bk-table-column width="80" type="selection" align="center" /> -->
            <bk-table-column
              :label="t('SDK版本号')"
              min-width="120"
              prop="version_number"
            >
            </bk-table-column>
            <bk-table-column :label="t('SDK名称')" prop="name" min-width="120">
            </bk-table-column>
            <bk-table-column
              :label="t('资源版本')"
              prop="resource_version"
              min-width="120"
            >
              <template #default="{ data }">
                {{ data?.resource_version?.version }}
              </template>
            </bk-table-column>
            <bk-table-column min-width="120" prop="language" :label="t('语言')">
            </bk-table-column>
            <bk-table-column :label="t('创建人')" prop="created_by" min-width="120">
            </bk-table-column>
            <bk-table-column :label="t('生成时间')" prop="created_time" min-width="120">
            </bk-table-column>
            <bk-table-column :label="t('操作')" min-width="140">
              <template #default="{ row, data }">
                <bk-button text theme="primary" @click="copy(data.download_url)">
                  {{ t('复制地址') }}
                </bk-button>
                <bk-button
                  text
                  theme="primary"
                  class="pl10 pr10"
                  v-bk-tooltips="{
                    content: !row.download_url ? $t('暂无下载地址') : '',
                    disabled: row.download_url,
                  }"
                  :disabled="!row.download_url"
                  @click="handleDownload(data)"
                >
                  {{ t('下载') }}
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
    <create-sdk @done="getList()" ref="createSdkRef" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useQueryList, useSelection } from '@/hooks';
import { getSdksList } from '@/http';
import { copy } from '@/common/util';
import { useResourceVersion } from '@/store';
import createSdk from '../components/createSdk.vue';
import TableEmpty from '@/components/table-empty.vue';

const { t } = useI18n();
const resourceVersionStore = useResourceVersion();

const createSdkRef = ref(null);
const filterData = ref({ keyword: '' });
const tableEmptyConf = ref<{ keyword: string; isAbnormal: boolean }>({
  keyword: '',
  isAbnormal: false,
});

// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList(getSdksList, filterData);

// 列表多选
const { bkTableRef, handleSelectionChange } = useSelection();

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
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
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
  () => resourceVersionStore.getResourceFilter,
  (value: string) => {
    filterData.value.keyword = value;
  },
  {
    immediate: true,
  }
);
</script>
