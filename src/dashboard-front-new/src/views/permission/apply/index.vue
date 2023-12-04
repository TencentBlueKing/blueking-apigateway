<template>
  <div class="permission-apply-container p20">
    <div class="header flex-row justify-content-between mb5">
      <span v-bk-tooltips="{ content: t('请选择要审批的权限'), disabled: applySumCount !== 0 }">
        <bk-button theme="primary" :disabled="applySumCount === 0" @click="handleBatchApply">
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
          ref="permissionTable" class="table-layout" :data="tableData" remote-pagination :pagination="pagination"
          show-overflow-tooltip @page-limit-change="handlePageSizeChange" @page-value-change="handlePageChange"
          @selection-change="handleSelectionChange"
          @row-click="handleRowClick" @expand-change="handlePageExpandChange"
          row-hover="auto">
          <bk-table-column width="80" type="selection" align="center" />
          <!-- <bk-table-column type="expand" width="30" class="ag-expand-cell">
            <template #expandRow="row">
              <div class="h60" v-if="row.grant_dimension === 'api'">
                <bk-alert theme="error" :title="t('将申请网关下所有资源的权限，包括未来新创建的资源，请谨慎审批')" />
                {{ row.id }}
              </div>
              <bk-table
                v-else :ref="`permissionDetail_${row.id}`" :max-height="378" :size="'small'" :key="row.id"
                :data="row.resourceList" :outer-border="false"
                ext-cls="ag-expand-table"
                @selection-change="handleRowSelectionChange">
                <bk-table-column type="index" label="" width="60"></bk-table-column>
                <bk-table-column type="selection" width="50"></bk-table-column>
                <bk-table-column prop="name" :label="t('资源名称')"></bk-table-column>
                <bk-table-column prop="path" :label="t('请求路径')"></bk-table-column>
                <bk-table-column prop="method" :label="t('请求方法')"></bk-table-column>
              </bk-table>
            </template>
          </bk-table-column> -->
          <bk-table-column :label="t('蓝鲸应用ID')" prop="bk_app_code" width="110"></bk-table-column>
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
          <bk-table-column :label="t('申请时间')" prop="created_time" width="215"></bk-table-column>
          <bk-table-column :label="t('审批状态')" prop="status" width="150">
            <template #default="{ data }">
              <loading
                class="mr5" loading size="mini" mode="spin" theme="primary"
                v-if="data?.status === 'pending'"
              />
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
                <bk-button class="mr10 is-disabled" theme="primary" text @click.stop.prevent="handlePrevent">
                  {{ t('全部通过') }}
                </bk-button>
              </bk-popover>
              <bk-button class="mr10" v-else theme="primary" text @click.stop.prevent="handleApplyApprove(data)">
                <!-- {{ data?.isSelectAll ? t('全部通过') : t('部分通过') }} -->
                {{ t('全部通过') }}
              </bk-button>
              <bk-button theme="primary" text @click.stop.prevent="handleApplyReject(data)">
                {{ t('全部驳回') }}
              </bk-button>
            </template>
          </bk-table-column>
        </bk-table>
      </bk-loading>
    </div>

    <!-- 批量审批dialog -->
    <bk-dialog
      :is-show="batchApplyDialogConf.isShow" theme="primary" :mask-close="false" :width="670"
      :loading="batchApplyDialogConf.isLoading" :title="batchApplyDialogConfTitle">
      <template #footer>
        <bk-button
          theme="primary" @click="batchApprovePermission"
          :loading="curAction.status === 'approved' && batchApplyDialogConf.isLoading">
          {{ t('全部通过') }}
        </bk-button>
        <bk-button
          @click="batchRejectPermission"
          :loading="curAction.status === 'rejected' && batchApplyDialogConf.isLoading">
          {{ t('全部驳回') }}
        </bk-button>
        <bk-button @click="batchApplyDialogConf.isShow = false"> {{ t('取消') }} </bk-button>
      </template>
      <div>
        <bk-table :data="selections" :size="'small'" :max-height="200" :key="selections.length">
          <bk-table-column width="250" :label="t('蓝鲸应用ID')" prop="bk_app_code"></bk-table-column>
          <bk-table-column :label="t('申请人')" prop="applied_by"></bk-table-column>
          <bk-table-column :label="t('申请时间')" prop="created_time"></bk-table-column>
        </bk-table>
        <bk-form :label-width="0" :model="curAction" :rules="rules" ref="batchForm" class="mt20">
          <bk-form-item class="bk-hide-label" label="" :required="true" :property="'comment'">
            <bk-input type="textarea" :placeholder="t('请输入备注')" v-model="curAction.comment" :maxlength="100">
            </bk-input>
          </bk-form-item>
        </bk-form>
      </div>
    </bk-dialog>

    <!-- 全部通过/全部驳回操作dialog -->
    <bk-dialog
      :is-show="applyActionDialogConf.isShow"
      theme="primary"
      :width="600"
      :quick-close="false"
      :header-position="'left'"
      :title="applyActionDialogConf.title"
      :loading="applyActionDialogConf.isLoading"
      @confirm="handleSubmitApprove"
      @closed="applyActionDialogConf.isShow = false">
      <bk-form
        :label-width="90"
        :model="curAction"
        :rules="rules"
        ref="approveForm"
        class="mt10 mr20 mb30">
        <bk-form-item
          :label="t('备注')"
          :required="true"
          :property="'comment'">
          <bk-alert class="mb10" :theme="alertTheme" :title="approveFormMessage"></bk-alert>
          <bk-input
            type="textarea"
            :placeholder="t('请输入备注')"
            v-model="curAction.comment"
            :rows="4"
            :maxlength="100">
          </bk-input>
        </bk-form-item>
      </bk-form>
    </bk-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { getPermissionApplyList, updatePermissionStatus } from '@/http';
import { useCommon, usePermission } from '@/store';
import { useQueryList, useSelection } from '@/hooks';
import { Message, Loading } from 'bkui-vue';
const { t } = useI18n();
const common = useCommon();
const permission = usePermission();

const { apigwId } = common; // 网关id

const filterData = ref({ bk_app_code: '', applied_by: '', grant_dimension: '' });
const expandRows = ref([]);
const batchForm = ref(null);
const approveForm = ref(null);
// const timer = ref(null);
const applySumCount = ref<number>(-1);
// const resourceList = ref([]);
const batchApplyDialogConf = reactive({
  isLoading: false,
  isShow: false,
});
const applyActionDialogConf = reactive({
  isShow: false,
  title: t('通过申请'),
  isLoading: false,
});
const curAction = ref({
  ids: [],
  status: '',
  comment: '',
});
const curPermission = ref({
  bk_app_code: '',
  resourceList: [],
  selection: [],
  grant_dimension: '',
  isSelectAll: true,
  resource_ids: [],
});
const dimensionList = reactive([
  { id: 'api', name: t('按网关') },
  { id: 'resource', name: t('按资源') },
]);
const statusMap = reactive({
  approved: t('通过'),
  rejected: t('驳回'),
  pending: t('未审批'),
});
const rules = reactive({
  comment: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
});

// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList(getPermissionApplyList, filterData);

// checkbox hooks
const {
  selections,
  handleSelectionChange,
  resetSelections,
} = useSelection();


// 监听授权维度的变化
watch(
  () => filterData.value,
  () => {
    resetSelections();
  },
  {  deep: true },
);
// 监听多选的变化
watch(
  () => selections.value,
  (v: number[]) => {
    applySumCount.value = v.length;
  },
  { immediate: true, deep: true },
);
// 监听总数量的变化
watch(
  () => pagination.value,
  (v: any) => {
    permission.setCount(v.count);
    console.log('newValue', v);
  },
  { deep: true },
);


// 批量审批dialog的title
const batchApplyDialogConfTitle = computed(() => {
  return t(`将对以下${selections.value.length}个权限申请单进行审批`);
});
// 审批操作alter的theme
const alertTheme = computed(() => {
  if (curPermission.value.grant_dimension === 'api') {
    return curAction.value.status === 'approved' ? 'warning' : 'error';
  }
  return 'warning';
});
// 审批操作alter的title
const approveFormMessage = computed(() => {
  const selectLength = curPermission.value.selection?.length;
  // const resourceLength = curPermission.value.resourceList?.length;
  const resourceLength = curPermission.value.resource_ids?.length;
  const appCode = curPermission.value.bk_app_code;
  if (curPermission.value.grant_dimension === 'api') {
    if (curAction.value.status === 'approved') {
      return `${t('应用将申请网关下所有资源的权限，包括未来新创建的资源，请谨慎审批')}`;
    }
    return `${t('应用将按网关申请全部驳回')}`;
  }
  if (curAction.value.status === 'approved') {
    if (selectLength && selectLength < resourceLength) {
      const rejectLength = resourceLength - selectLength;
      return t(`应用${appCode} 申请${resourceLength}个权限，通过${selectLength}个，驳回${rejectLength}个`);
    }
    return t(`应用${appCode} 申请${resourceLength}个权限，全部通过`);
  }
  return t(`应用${appCode} 申请${resourceLength}个权限，全部驳回`);
});


// 批量审批
const handleBatchApply = () => {
  curAction.value = {
    ids: [],
    status: '',
    comment: '',
  };
  batchApplyDialogConf.isShow = true;
};
// 折叠table 多选发生变化触发
// const handleRowSelectionChange = () => {

// };
// 折叠变化
const handlePageExpandChange = (row: any, expandedRows: any) => {
  expandRows.value = expandedRows.map((item: any) => {
    return item.id;
  });
  // if (curExpandRow !== row) {
  //   $refs.permissionTable.toggleRowExpansion(curExpandRow, false);
  // }
  // curExpandRow = row;
  // nextTick(() => {
  //   const table = $refs[`permissionDetail_${row.id}`];
  //   if (table) {
  //     table.toggleAllSelection();
  //   }
  // });
};

// 批量审批api
const updateStatus = async () => {
  const data = { ...curAction.value };
  await batchForm.value?.validate();
  await approveForm.value?.validate();
  try {
    await updatePermissionStatus(apigwId, data);
    batchApplyDialogConf.isShow = false;
    applyActionDialogConf.isShow = false;
    getList();
    Message({
      message: t('操作成功！'),
      theme: 'success',
    });
    // 清空已选 速度太快
    resetSelections();
  } catch ({ error }: any) {
    Message({
      message: error.message,
      theme: 'error',
    });
  }
};
// 全部通过 dialog btn
const batchApprovePermission =  () => {
  curAction.value.ids = selections.value.map(permission => permission.id);
  curAction.value.status = 'approved';
  updateStatus();
};
// 全部驳回 dialog btn
const batchRejectPermission = () => {
  curAction.value.ids = selections.value.map(permission => permission.id);
  curAction.value.status = 'rejected';
  updateStatus();
};


const handlePrevent = () => {
  return false;
};
// 全部通过/部分通过 btn
const handleApplyApprove = (data: any) => {
  curPermission.value = data;
  curAction.value = {
    ids: [data.id],
    status: 'approved',
    comment: t('全部通过'),
  };
  console.log(curPermission.value);

  // if (!curPermission.value.isSelectAll) {
  //   curAction.value.comment = t('部分通过');
  // }
  applyActionDialogConf.title = t('通过申请');
  applyActionDialogConf.isShow = true;
};
// 全部驳回 btn
const handleApplyReject = (data: any) => {
  curPermission.value = data;
  curAction.value = {
    ids: [data.id],
    status: 'rejected',
    comment: t('全部驳回'),
  };
  applyActionDialogConf.title = t('驳回申请');
  applyActionDialogConf.isShow = true;
};

// 全部通过/部分通过/全部驳回 操作dialog
const handleSubmitApprove = () => {
  updateStatus();
};


// 鼠标点击
const handleRowClick = (row: any) => {
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
.h60{
  height: 60px;
}
.apply-content {
  height: calc(100% - 90px);
  min-height: 600px;
}

.ag-expand-table {
  tr {
    background-color: #fafbfd;
  }

  td,
  th {
    padding: 0 !important;
    height: 42px !important;
    cursor: default !important;
  }
}
:deep(.apply-content){
  .bk-exception{
    height: 280px;
    max-height: 280px;
    justify-content: center;
  }
}
</style>
