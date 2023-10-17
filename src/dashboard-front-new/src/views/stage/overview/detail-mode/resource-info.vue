<template>
  <div class="resource-info">
    <bk-input
      v-model="searchValue"
      style="width: 520px"
      clearable
      type="search"
      @enter="handleSearch"
    />
    <bk-loading
      :loading="isLoading"
    >
      <bk-table
        class="table-layout mt15"
        :data="tableData"
        remote-pagination
        :pagination="pagination"
        show-overflow-tooltip
        row-hover="auto"
        border="outer"
        settings
        @page-limit-change="handlePageSizeChange"
        @page-value-change="handlePageChange"
      >
        <bk-table-column
          :label="t('后端服务')"
        >
          <template #default="{ data }">
            {{data?.backend?.name}}
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('资源名称')"
          prop="name"
          sort
        >
        </bk-table-column>
        <bk-table-column
          :label="t('前端请求方法')"
          prop="method"
        >
        </bk-table-column>
        <bk-table-column
          :label="t('前端请求路径')"
          prop="path"
          sort
        >
        </bk-table-column>
        <bk-table-column
          :label="t('标签')"
        >
          <template #default="{ row }">
            <template v-if="row.api_labels && row.api_labels?.length">
              {{ row.api_labels.join('，') }}
            </template>
            <template v-else>
              --
            </template>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('生效的插件')"
          prop="name"
        >
        </bk-table-column>
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
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useQueryList } from '@/hooks';
import { getResourceVersionsInfo } from '@/http';
const { t } = useI18n();

const searchValue = ref('');

const filterData = ref({ query: '' });

// 获取版本资源信息
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
} = useQueryList(getResourceVersionsInfo, filterData, 1);

const handleSearch = () => {
  console.log('enter');
};

</script>

<style lang="scss" scoped></style>
