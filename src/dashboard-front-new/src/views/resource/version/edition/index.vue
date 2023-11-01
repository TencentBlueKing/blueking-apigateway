<template>
  <div class="resource-container p20">
    <div class="operate flex-row justify-content-between mt10 mb10">
      <div class="flex-1 flex-row align-items-center">
        <div class="mr10">
          <bk-button theme="primary" @click="handleVersionCompare">
            {{ t("版本对比") }}
          </bk-button>
        </div>
      </div>
      <div class="flex-1 flex-row justify-content-end">
        <bk-input
          class="ml10 mr10 operate-input"
          placeholder="请输入版本号"
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
            <bk-table-column :label="t('版本号')" min-width="120">
              <template #default="{ data }">
                <bk-button
                  text
                  theme="primary"
                  @click="handleShowInfo(data.id)"
                >
                  {{ data?.version }}
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
                <bk-button text theme="primary">
                  {{ data?.sdk_count }}
                </bk-button>
              </template>
            </bk-table-column>
            <bk-table-column :label="t('操作')" min-width="140">
              <template #default="{ data }">
                <bk-button text theme="primary" @click="openCreateSdk(data.id)">
                  {{ t("生成SDK") }}
                </bk-button>
                <bk-button text theme="primary" class="pl10 pr10">
                  {{ t("发布至环境") }}
                </bk-button>
              </template>
            </bk-table-column>
          </bk-table>
        </bk-loading>
      </div>
    </div>

    <!-- 生成sdk弹窗 -->
    <create-sdk
      :version-list="tableData"
      :resource-version-id="resourceVersionId"
      @done="getList()"
      ref="createSdkRef"
    />

    <!-- 资源详情 -->
    <resource-detail :id="resourceVersionId" ref="resourceDetailRef" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useI18n } from 'vue-i18n';
import { useQueryList, useSelection } from '@/hooks';
import { getResourceVersionsList } from '@/http';
import createSdk from '../components/createSdk.vue';
import resourceDetail from '../components/resourceDetail.vue';

const { t } = useI18n();

const filterData = ref({ query: '' });

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
const { selections, handleSelectionChange, resetSelections } = useSelection();

// 当前操作的行
const resourceVersionId = ref();
const createSdkRef = ref(null);
const resourceDetailRef = ref(null);

// 生成sdk
const openCreateSdk = (id: number) => {
  resourceVersionId.value = id;
  createSdkRef.value?.showCreateSdk();
};

// 版本对比
const handleVersionCompare = () => {};

// 展示详情
const handleShowInfo = (id: number) => {
  resourceVersionId.value = id;
  resourceDetailRef.value?.showSideslider();
};
</script>
