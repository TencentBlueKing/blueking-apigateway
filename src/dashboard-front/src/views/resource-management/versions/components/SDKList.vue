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
        <BkLoading :loading="isLoading">
          <BkTable
            class="sdk-table table-layout"
            :data="tableData"
            remote-pagination
            :pagination="pagination"
            show-overflow-tooltip
            row-hover="auto"
            border="outer"
            @page-limit-change="handlePageSizeChange"
            @page-value-change="handlePageChange"
          >
            <BkTableColumn
              :label="t('SDK 版本号')"
              prop="version_number"
            />
            <BkTableColumn
              :label="t('SDK 名称')"
              prop="name"
            />
            <BkTableColumn
              :label="t('资源版本')"
              prop="resource_version"
            >
              <template #default="{ row }">
                <BkButton
                  text
                  theme="primary"
                  @click="() => goVersionList(row)"
                >
                  {{ row?.resource_version?.version }}
                </BkButton>
              </template>
            </BkTableColumn>
            <BkTableColumn
              prop="language"
              :label="t('语言')"
            />
            <BkTableColumn
              :label="t('创建人')"
              prop="created_by"
            >
              <template #default="{ row }">
                <span><bk-user-display-name :user-id="row.created_by" /></span>
              </template>
            </BkTableColumn>
            <BkTableColumn
              :label="t('生成时间')"
              prop="created_time"
            />
            <BkTableColumn :label="t('操作')">
              <template #default="{ row, data }">
                <div class="flex gap-10px">
                  <BkButton
                    text
                    theme="primary"
                    @click="() => copy(data.download_url)"
                  >
                    {{ t('复制地址') }}
                  </BkButton>
                  <BkButton
                    v-bk-tooltips="{
                      content: !row.download_url ? $t('暂无下载地址') : '',
                      disabled: row.download_url,
                    }"
                    text
                    theme="primary"
                    class="px-10px"
                    :disabled="!row.download_url"
                    @click="() => handleDownload(data)"
                  >
                    {{ t('下载') }}
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
      @done="getList"
    />
  </div>
</template>

<script setup lang="ts">
import { useQueryList } from '@/hooks';
import { getSDKList } from '@/services/source/sdks';
import { copy } from '@/utils';
import { useResourceVersion } from '@/stores';
import CreateSDK from './CreateSDK.vue';
import TableEmpty from '@/components/table-empty/index.vue';

const emits = defineEmits<{ 'on-show-version': [version: string] }>();

const { t } = useI18n();
const resourceVersionStore = useResourceVersion();

const keyword = ref('');
const createSdkRef = ref();
const filterData = ref({
  keyword: '',
  resource_version_id: '',
});
const tableEmptyConf = ref<{
  keyword: string
  isAbnormal: boolean
}>({
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
} = useQueryList({
  apiMethod: getSDKList,
  filterData,
});

watch(
  filterData,
  () => {
    updateTableEmptyConfig();
  },
  { deep: true },
);

watch(
  () => resourceVersionStore.getResourceFilter,
  (value: any) => {
    keyword.value = value?.version;
    filterData.value.resource_version_id = value?.id;
  },
  { immediate: true },
);

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
  filterData.value.resource_version_id = '';
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
  if (keyword.value) {
    tableEmptyConf.value.keyword = keyword.value;
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const goVersionList = (data: any) => {
  emits('on-show-version', data?.resource_version?.version || '');
};
</script>

<style lang="scss" scoped>
.sdk-table {

  :deep(.bk-table-head) {
    scrollbar-color: transparent transparent;
  }

  :deep(.bk-table-body) {
    scrollbar-color: transparent transparent;
  }
}
</style>
