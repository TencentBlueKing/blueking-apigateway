<template>
  <div class="publish-container p20">
    <bk-loading
      :loading="isLoading"
    >
      <bk-table
        class="table-layout"
        :data="tableData"
        remote-pagination
        :pagination="pagination"
        show-overflow-tooltip
        @page-limit-change="handlePageSizeChange"
        @page-value-change="handlePageChange"
        row-hover="auto"
      >
        <bk-table-column
          :label="t('已发布的环境')"
          prop="stage.name"
        >
        </bk-table-column>
        <bk-table-column
          :label="t('类型')"
        >
          <template #default="{ data }">
            {{ publishSourceEnum[data?.source] }}
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('版本号')"
          prop="resource_version_display"
        >
        </bk-table-column>
        <bk-table-column
          :label="t('操作状态')"
        >
          <template #default="{ data }">
            {{ publishStatusEnum[data?.status] }}
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('操作时间')"
          prop="created_time"
        >
        </bk-table-column>
        <bk-table-column
          :label="t('操作人')"
          prop="created_by"
        >
        </bk-table-column>
        <bk-table-column
          :label="t('耗时')"
          prop="duration"
        >
        </bk-table-column>
        <bk-table-column
          :label="t('操作')"
        >
        </bk-table-column>
      </bk-table>
    </bk-loading>
  </div>
</template>

<script setup lang="ts">
import { useQueryList } from '@/hooks';
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { PublishSourceEnum, PublishStatusEnum } from '@/types';
import {
  getReleaseHistories,
} from '@/http';
const { t } = useI18n();
const filterData = ref({ query: '' });
const publishSourceEnum: any = ref(PublishSourceEnum);
const publishStatusEnum: any = ref(PublishStatusEnum);
// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
} = useQueryList(getReleaseHistories, filterData);
</script>

<style lang="scss" scoped>

</style>
