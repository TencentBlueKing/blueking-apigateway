<template>
  <div class="resource-container p20">
    <bk-alert
      theme="warning"
      title="资源如有更新，需要“生成版本”并“发布到环境”才能生效"
    />
    <div class="operate flex-row justify-content-between mt10 mb10">
      <div class="flex-1 flex-row align-items-center">
        <div class="mr10">
          <bk-button
            theme="primary"
          >
            {{ t('新建') }}
          </bk-button>
        </div>
        <bk-dropdown trigger="click" class="mr10">
          <bk-button>{{ '批量' }}</bk-button>
          <template #content>
            <bk-dropdown-menu>
              <bk-dropdown-item
                v-for="item in dropdownList"
                :key="item"
              >
                {{ item }}
              </bk-dropdown-item>
            </bk-dropdown-menu>
          </template>
        </bk-dropdown>
        <bk-dropdown trigger="click" class="mr10">
          <bk-button>{{ '导入' }}</bk-button>
          <template #content>
            <bk-dropdown-menu>
              <bk-dropdown-item
                v-for="item in dropdownList"
                :key="item"
              >
                {{ item }}
              </bk-dropdown-item>
            </bk-dropdown-menu>
          </template>
        </bk-dropdown>
        <bk-dropdown trigger="click">
          <bk-button>{{ '导出' }}</bk-button>
          <template #content>
            <bk-dropdown-menu>
              <bk-dropdown-item
                v-for="item in dropdownList"
                :key="item"
              >
                {{ item }}
              </bk-dropdown-item>
            </bk-dropdown-menu>
          </template>
        </bk-dropdown>
      </div>
      <div class="flex-1 flex-row justify-content-end">
        <bk-input class="ml10 mr10 operate-input" placeholder="请输入网关名" v-model="filterData.query"></bk-input>
      </div>
    </div>
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
          :label="t('后端服务')"
        >
          <template #default="{ data }">
            {{data?.backend?.name}}
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('文档')"
          prop="docs"
          sort
        >
        </bk-table-column>
        <bk-table-column
          :label="t('标签')"
          prop="labels"
          sort
        >
        </bk-table-column>
        <bk-table-column
          :label="t('更新时间')"
          prop="updated_time"
          sort
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
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useQueryList } from '@/hooks';
import { getResourceListData } from '@/http';
const dropdownList = ref(['生产环境', '预发布环境', '测试环境', '正式环境', '开发环境', '调试环境']);
const { t } = useI18n();

const filterData = ref({ query: '' });

// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
} = useQueryList(getResourceListData, filterData);
</script>
<style lang="scss" scoped>
.resource-container{
  .operate{
    &-input{
      width: 450px;
    }
  }

}
</style>
