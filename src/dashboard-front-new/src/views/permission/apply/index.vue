<template>
  <div class="permission-apply-container p20">
    <div class="header flex-row justify-content-between">
      <span>
        <bk-button theme="primary">
          {{ t('批量审批') }}
        </bk-button>
      </span>
      <bk-form class="flex-row">
        <bk-form-item :label="t('授权维度')" class="mb10" label-width="108">
          <bk-select v-model="filterData.grant_dimension" class="w150">
            <bk-option v-for="option of dimensionList" :key="option.id" :id="option.id" :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="t('蓝鲸应用ID')" class="mb10" label-width="119">
          <bk-input clearable v-model="filterData.bk_app_code" :placeholder="t('请输入应用ID')" class="w150">
          </bk-input>
        </bk-form-item>
        <bk-form-item :label="t('申请人')" class="mb10" label-width="90">
          <bk-input clearable v-model="filterData.applied_by" :placeholder="t('请输入用户')" class="w150">
          </bk-input>
        </bk-form-item>
      </bk-form>
    </div>
    <div class="apply-content">
      <bk-loading :loading="isLoading">
        <bk-table
          class="table-layout" :data="tableData" remote-pagination :pagination="pagination" show-overflow-tooltip
          @page-limit-change="handlePageSizeChange" @page-value-change="handlePageChange"
          @selection-change="handleSelectionChange" @row-mouse-enter="handleMouseEnter" row-hover="auto">
          <bk-table-column width="80" type="selection" align="center" />
          <bk-table-column :label="t('蓝鲸应用ID')" prop="bk_app_code"></bk-table-column>
          <bk-table-column :label="t('授权维度')" prop="grant_dimension_display">
            <template #default="{ data }">
              {{ data?.grant_dimension_display || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column width="120" :label="t('权限期限')" prop="expire_days_display">
            <template #default="{ data }">
              {{ data?.expire_days_display || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('申请理由')" prop="reason">
            <template #default="{ data }">
              {{ data?.reason || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('申请人')" prop="applied_by"></bk-table-column>
          <bk-table-column :label="t('申请时间')" prop="created_time"></bk-table-column>
          <bk-table-column :label="t('审批状态')" prop="status">
            <template #default="{ data }">
              <round-loading v-if="data?.status === 'pending'" />
              <span v-else :class="['dot', data?.status]"></span>
              {{ statusMap[data?.status as keyof typeof statusMap] }}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('操作')" width="200">
            <template #default="{ data }">
              <bk-popover
                :content="t('请选择资源')" v-if="expandRows.includes(data?.id)
                  && data?.selection.length === 0
                  && data?.grant_dimension !== 'api'">
                <bk-button class="mr10 is-disabled" theme="primary" text> {{ t('全部通过') }} </bk-button>
              </bk-popover>
              <bk-button class="mr10" v-else theme="primary" text>
                {{ data?.isSelectAll ? t('全部通过') : t('部分通过') }}
              </bk-button>
              <bk-button theme="primary" text> {{ t('全部驳回') }}</bk-button>
            </template>
          </bk-table-column>
        </bk-table>
      </bk-loading>

    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { getPermissionApplyList } from '@/http';
import { useCommon } from '@/store';
import { useQueryList, useSelection } from '@/hooks';
const { t } = useI18n();
const common = useCommon();

const { apigwId } = common; // 网关id

const filterData = ref({ bk_app_code: '', applied_by: '', grant_dimension: '' });
const expandRows = ref([]);
const dimensionList = reactive([
  { id: 'api', name: t('按网关') },
  { id: 'resource', name: t('按资源') },
]);
const statusMap = reactive({
  approved: t('通过'),
  rejected: t('驳回'),
  pending: t('未审批'),
});


// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  // getList,
} = useQueryList(getPermissionApplyList, filterData);

// checkbox hooks
const {
  // selections,
  handleSelectionChange,
  // resetSelections,
} = useSelection();


// 鼠标进入
const handleMouseEnter = (e: any, row: any) => {
  console.log('row', row);
};

const init = () => {
  console.log(tableData);
  console.log(apigwId);
};
init();
</script>

<style lang="scss" scoped>
.w150 {
  width: 150px;
}

.apply-content {
  height: calc(100% - 90px);
  min-height: 600px;
}
</style>
