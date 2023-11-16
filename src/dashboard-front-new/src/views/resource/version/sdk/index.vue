<template>
  <div class="resource-container p20">
    <div class="operate flex-row justify-content-between mt10 mb10">
      <div class="flex-1 flex-row align-items-center">
        <div class="mr10">
          <bk-button theme="primary" @click="openCreateSdk">
            {{ t("生成SDK") }}
          </bk-button>
          <bk-button @click="handleBatchDownload">
            {{ t("批量下载") }}
          </bk-button>
        </div>
      </div>
      <div class="flex-1 flex-row justify-content-end">
        <bk-input
          class="ml10 mr10 operate-input"
          placeholder="请输入关键字或选择条件查询"
          v-model="filterData.query"
        ></bk-input>
      </div>
    </div>
    <div class="flex-row resource-content">
      <div class="left-wraper" style="width: '100%'">
        <bk-loading :loading="isLoading">
          <bk-table
            class="table-layout"
            :data="tableData"
            remote-pagination
            :pagination="pagination"
            show-overflow-tooltip
            @page-limit-change="handlePageSizeChange"
            @page-value-change="handlePageChange"
            @selection-change="handleSelectionChange"
            row-hover="auto"
          >
            <bk-table-column width="80" type="selection" />
            <bk-table-column :label="t('SDK版本号')" min-width="120">
              <template #default="{ data }">
                <bk-button
                  text
                  theme="primary"
                  @click="handleShowInfo(data.id)"
                >
                  {{ data?.version_number }}
                </bk-button>
              </template>
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
            <bk-table-column
              :label="t('创建人')"
              prop="created_by"
              min-width="120"
            >
            </bk-table-column>
            <bk-table-column
              :label="t('生成时间')"
              prop="created_time"
              min-width="120"
            >
            </bk-table-column>
            <bk-table-column :label="t('操作')" min-width="140">
              <template #default="{ data }">
                <bk-button text theme="primary" @click="copy(data.name)">
                  {{ t("复制地址") }}
                </bk-button>
                <bk-button text theme="primary" class="pl10 pr10">
                  {{ t("下载") }}
                </bk-button>
              </template>
            </bk-table-column>
          </bk-table>
        </bk-loading>
      </div>
    </div>

    <!-- 生成sdk弹窗 -->
    <create-sdk
      @done="getList()"
      ref="createSdkRef"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useI18n } from 'vue-i18n';
import { useQueryList, useSelection } from '@/hooks';
import { getSdksList } from '@/http';
import { copy } from '@/common/util';
import createSdk from '../components/createSdk.vue';

const { t } = useI18n();

const createSdkRef = ref(null);
const filterData = ref({ query: '' });

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
const { selections, handleSelectionChange, resetSelections } = useSelection();

// 批量下载
const handleBatchDownload = () => {};

// 展示详情
const handleShowInfo = (id: string) => {};

// 显示生成sdk弹窗
const openCreateSdk = () => {
  createSdkRef.value?.showCreateSdk();
};
</script>
