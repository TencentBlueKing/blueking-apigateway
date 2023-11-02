<template>
  <div class="resource-info">
    <bk-input
      v-model="searchValue"
      style="width: 520px"
      clearable
      type="search"
      :placeholder="t('请输入后端服务名称、资源名称、请求路径或选择条件搜索')"
      @enter="handleSearch"
    />
    <bk-loading :loading="isLoading">
      <bk-table
        class="table-layout mt15"
        :data="curPageData"
        remote-pagination
        :pagination="pagination"
        show-overflow-tooltip
        row-hover="auto"
        border="outer"
        settings
        @page-limit-change="handlePageSizeChange"
        @page-value-change="handlePageChange"
      >
        <bk-table-column :label="t('后端服务')">
          <template #default="{ data }">
            {{ data?.backend?.name }}
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('资源名称')"
          prop="name"
          sort
        ></bk-table-column>
        <bk-table-column
          :label="t('前端请求方法')"
          prop="method"
        >
          <template #default="{ row }">
            <span class="ag-tag" :class="row.method?.toLowerCase()">{{row.method}}</span>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('前端请求路径')"
          prop="path"
          sort
        ></bk-table-column>
        <bk-table-column :label="t('标签')">
          <template #default="{ row }">
            <template v-if="row.api_labels && row.api_labels?.length">
              {{ row.api_labels.join('，') }}
            </template>
            <template v-else>--</template>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('生效的插件')"
          prop="name"
        ></bk-table-column>
        <bk-table-column
          :label="t('是否公开')"
          prop="is_public"
        >
          <template #default="{ row }">
            <span :style="{ color: row.is_public ? '#FE9C00' : '#63656e' }">
              {{ row.is_public ? t('是') : t('否') }}
            </span>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('操作')"
          prop="name"
        >
          <bk-button
            text
            theme="primary"
            class="mr10"
          >
            查看资源详情
          </bk-button>
          <bk-button
            text
            theme="primary"
          >
            复制资源地址
          </bk-button>
        </bk-table-column>
      </bk-table>
    </bk-loading>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useQueryList } from '@/hooks';
import { getResourceVersionsInfo } from '@/http';
import { useStage, useCommon } from '@/store';
import { IPagination } from '@/types';
import error from 'bkui-vue/lib/icon/error';


const { t } = useI18n();
const common = useCommon();
const stageStore = useStage();

const props = defineProps<{
  versionId: number;
  stageId: number
}>();

const searchValue = ref('');

const isReload = ref(false);

const filterData = ref({ query: '' });

// 网关id
const { apigwId } = common;
const isLoading = ref(false);
const initPagination: IPagination = {
  current: 1,
  limit: 10,
  count: 0,
};
const pagination = ref(initPagination);

// 资源信息
const resourceVersionList = ref([]);

watch(
  () => props.versionId,
  () => {
    if (isReload.value) {
      // 页面强制刷新 versionId 为空处理
      getResourceVersionsData();
    }
  },
);

// 获取资源信息数据
const getResourceVersionsData = async () => {
  isLoading.value = true;
  if (props.versionId === undefined) {
    isReload.value = true;
    return;
  }
  // 没有版本无需请求
  if (props.versionId === 0) {
    isLoading.value = false;
    return;
  }
  try {
    const res = await getResourceVersionsInfo(apigwId, props.versionId);
    pagination.value.count = res.data.length;
    resourceVersionList.value = res.data || [];
  } catch (e) {
    // 接口404处理
    resourceVersionList.value = [];
    console.error(e);
  } finally {
    isLoading.value = false;
    isReload.value = false;
  }
};
getResourceVersionsData();

// 当前页数据
const curPageData = computed(() => {
  // 当前页数
  const page = pagination.value.current;
  // limit 页容量
  let startIndex = (page - 1) * pagination.value.limit;
  let endIndex = page * pagination.value.limit;
  if (startIndex < 0) {
    startIndex = 0;
  }
  if (endIndex > resourceVersionList.value.length) {
    endIndex = resourceVersionList.value.length;
  }
  return resourceVersionList.value.slice(startIndex, endIndex);
});

// 页码变化发生的事件
const handlePageChange = (current: number) => {
  isLoading.value = true;
  pagination.value.current = current;
  setTimeout(() => {
    isLoading.value = false;
  }, 200);
};

// 条数变化发生的事件
const handlePageSizeChange = (limit: number) => {
  isLoading.value = true;
  pagination.value.limit = limit;
  setTimeout(() => {
    isLoading.value = false;
  }, 200);
};

const handleSearch = () => {
  console.log('enter');
};
</script>

<style lang="scss" scoped></style>
