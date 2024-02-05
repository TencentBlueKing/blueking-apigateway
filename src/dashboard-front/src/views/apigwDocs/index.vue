<template>
  <div class="docs-main">
    <div class="top-bar">
      <bk-input
        type="search"
        :placeholder="t('请输入网关名称或描述')"
        v-model="filterData.keyword"
        clearable
        style="width: 500px"
      />
      <!-- <bk-button
        theme="primary"
        @click="handleGoApigw"
      >
        {{ t('网关管理') }}
      </bk-button> -->
    </div>
    <div class="docs-list">
      <bk-loading :loading="isLoading">
        <bk-table
          :data="tableData"
          remote-pagination
          :pagination="pagination"
          show-overflow-tooltip
          @page-limit-change="handlePageSizeChange"
          @page-value-change="handlePageChange"
          :border="['outer']"
        >
          <bk-table-column
            :label="t('网关名称')"
            field="name"
          >
            <template #default="{ data }">
              <span class="link-name" @click="gotoDetails(data)">{{data?.name || '--'}}</span>
              <bk-tag theme="success" v-if="data?.is_official">
                {{ t('官方') }}
              </bk-tag>
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('网关描述')"
            field="description"
          >
            <template #default="{ data }">
              {{ data?.description || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('网关负责人')"
            field="maintainers"
          >
            <template #default="{ data }">
              {{ data?.maintainers?.join(', ') || '--' }}
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
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue';
import { useQueryList } from '@/hooks';
import { useI18n } from 'vue-i18n';
import { getGatewaysDocs } from '@/http';
import { useRouter } from 'vue-router';
import TableEmpty from '@/components/table-empty.vue';

const { t } = useI18n();
const router = useRouter();

const filterData = ref({ keyword: '' });

const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList(getGatewaysDocs, filterData);


// const handleGoApigw = () => {
//   window.open(window.BK_DASHBOARD_URL);
// };
const tableEmptyConf = ref<{keyword: string, isAbnormal: boolean}>({
  keyword: '',
  isAbnormal: false,
});

const gotoDetails = (data: any) => {
  router.push({
    name: 'apigwAPIDetailIntro',
    params: {
      apigwId: data?.name,
    },
  });
};

const handleClearFilterKey = () => {
  filterData.value = { keyword: '' };
  getList();
  updateTableEmptyConfig();
};

const updateTableEmptyConfig = () => {
  const searchParams = {
    ...filterData.value,
  };
  const list = Object.values(searchParams).filter(item => item !== '');
  tableEmptyConf.value.isAbnormal = pagination.value.abnormal;
  if (list.length && !tableData.value.length) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (list.length) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

watch(
  () => tableData.value, () => {
    updateTableEmptyConfig();
  },
  {
    deep: true,
  },
);

</script>

<style lang="scss" scoped>
.docs-main {
  width: 90%;
  min-width: 1000px;
  max-width: 1200px;
  margin: auto;
  padding: 28px 0;
  .top-bar {
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .link-name {
    color: #3A84FF;
    cursor: pointer;
  }
}
</style>
