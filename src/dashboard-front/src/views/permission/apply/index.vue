<template>
  <div class="permission-apply-container page-wrapper-padding">
    <div class="header flex-row justify-content-between mb5">
      <span v-bk-tooltips="{ content: t('请选择要审批的权限'), disabled: selections.length }">
        <bk-button theme="primary" :disabled="!selections.length" @click="handleBatchApply">
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
        <bk-form-item v-if="!user.featureFlags?.ENABLE_MULTI_TENANT_MODE" :label="t('申请人')" class="mb10" label-width="90">
          <bk-input clearable v-model="filterData.applied_by" :placeholder="t('请输入用户')" class="w150">
          </bk-input>
        </bk-form-item>
        <bk-form-item v-else :label="t('申请人')" class="mb10" label-width="90">
          <bk-user-selector
            v-model="filterData.applied_by"
            :api-base-url="user.apiBaseUrl"
            :tenant-id="user.user.tenant_id"
            :placeholder="t('请输入用户')"
            style="min-width: 200px;"
          />
        </bk-form-item>
      </bk-form>
    </div>
    <div class="apply-content">
      <bk-loading :loading="isLoading">
        <bk-table
          ref="permissionTableRef"
          class="perm-apply-table"
          :data="permissionApplyList"
          :columns="permissionData.headers"
          :remote-pagination="true"
          :row-style="{ cursor: 'pointer' }"
          :pagination="pagination"
          @page-limit-change="handlePageSizeChange"
          @page-value-change="handlePageChange"
          @select-all="handleSelecAllChange"
          @selection-change="handleSelectionChange"
          @row-click="handleRowClick"
          row-hover="auto"
          border="outer">
          <template #expandRow="row">
            <div class="apply-expand-alert" v-if="['api'].includes(row.grant_dimension)">
              <bk-alert theme="error" :title="t('将申请网关下所有资源的权限，包括未来新创建的资源，请谨慎审批')" />
            </div>
            <bk-table
              v-else
              :ref="(el: HTMLElement) =>(childPermTableRef[row.id] = el)"
              :max-height="378"
              :size="'small'"
              :key="row.id"
              :data="row.resourceList"
              :outer-border="false"
              class="ag-expand-table"
              @select-all="(e: SelectionType) => handleRowSelectionAllChange(row, e)"
              @selection-change="(e: SelectionType) => handleRowSelectionChange(row, e)"
            >
              <bk-table-column type="index" label="" width="60" />
              <bk-table-column type="selection" width="50" align="center" />
              <bk-table-column prop="name" :label="t('资源名称')" />
              <bk-table-column prop="path" :label="t('请求路径')" />
              <bk-table-column prop="method" :label="t('请求方法')" />
            </bk-table>
          </template>
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
          <bk-table-column width="250" :label="t('蓝鲸应用ID')" prop="bk_app_code" />
          <bk-table-column :label="t('申请人')" prop="applied_by" />
          <bk-table-column :label="t('申请时间')" prop="created_time" :show-overflow-tooltip="true" />
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

<script setup lang="tsx">
import { reactive, ref, watch, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { getPermissionApplyList, getApigwResources, updatePermissionStatus } from '@/http';
import {
  useCommon,
  usePermission,
  useUser,
} from '@/store';
import { useQueryList, useSelection } from '@/hooks';
import type { SelectionType }  from '@/hooks';
import { Message, Loading } from 'bkui-vue';
import { sortByKey } from '@/common/util'
import TableEmpty from '@/components/table-empty.vue';
import { cloneDeep } from 'lodash';
import BkUserSelector from '@blueking/bk-user-selector';

const { t } = useI18n();
const common = useCommon();
const permission = usePermission();

const { apigwId } = common; // 网关id

const filterData = ref({ bk_app_code: '', applied_by: '', grant_dimension: 'resource' });
const expandRows = ref([]);
const batchForm = ref(null);
const approveForm = ref(null);
const permissionTableRef = ref(null);
const renderTableIndex = ref(0)
const childPermTableRef = ref([]);
const resourceList = ref([]);
const batchApplyDialogConf = reactive({
  isLoading: false,
  isShow: false,
});
const applyActionDialogConf = reactive({
  isShow: false,
  title: t('通过申请'),
  isLoading: false,
});
const permissionData = ref({
  headers: [],
});
const curAction = ref({
  ids: [],
  status: '',
  comment: '',
  part_resource_ids: {}
});
const curPermission = ref({
  bk_app_code: '',
  resourceList: [],
  selection: [],
  grant_dimension: '',
  isSelectAll: true,
  resource_ids: [],
});
const curExpandRow = ref({}) as any;
const tableEmptyConf = ref<{keyword: string, isAbnormal: boolean}>({
  keyword: '',
  isAbnormal: false,
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
const permissionApplyList = ref([]);

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
  handleSelecAllChange,
  resetSelections,
} = useSelection();

const user = useUser();

const setTableHeader = () => {
  const columns =  [
    {
      type: 'selection',
      width: 60,
      minWidth: 60,
      align: 'center',
      showOverflowTooltip: false,
    },
    {
      type: 'expand',
      width: 30,
      minWidth: 30,
      showOverflowTooltip: false
    },
    { field: 'bk_app_code', label: t('蓝鲸应用ID') },
    {
      field: 'grant_dimension_display',
      label: t('授权维度'),
      render: ({ data }: Record<string, any>) => {
        return data?.grant_dimension_display || '--';
      },
    },
    {
      field: 'expire_days_display',
      label: t('权限期限'),
      render: ({ data }: Record<string, any>) => {
        return data?.expire_days_display || '--';
      },
    },
    {
      field: 'reason',
      label: t('申请理由'),
      render: ({ data }: Record<string, any>) => {
        return data?.reason || '--';
      },
    },
    {
      field: 'applied_by',
      label: t('申请人'),
      render: ({ data }: Record<string, any>) =>
        user.featureFlags?.ENABLE_MULTI_TENANT_MODE
        ? <span><bk-user-display-name user-id={data.applied_by} /></span>
        : <span>{ data.applied_by }</span>
    },
    { field: 'created_time', width: 215, label: t('申请时间') },
    {
      field: 'status',
      width: 150,
      label: t('审批状态'),
      render: ({ data }: Record<string, any>) => {
        if(['pending'].includes(data?.status)) {
          return (
            <div class="perm-apply-dot">
              <Loading class="mr5" loading size="mini" mode="spin" theme="primary" />
              {statusMap[data?.status as keyof typeof statusMap]}
            </div>
          )
        } else {
          return (
            <div class="perm-apply-dot">
              <span class={[
                'dot',
                {[data.status]: data?.status}
              ]}
              />
              {statusMap[data?.status as keyof typeof statusMap]}
            </div>
          )
        }
      }
    },
    {
      field: 'operate',
      width: 220,
      label: t('操作'),
      key: renderTableIndex.value,
      render: ({ data }: Record<string, any>) => {
        if(expandRows.value.includes(data.id) && data?.selection.length === 0 && data?.grant_dimension !== 'api') {
          return (
            <div>
              <bk-popover content={t('请选择资源')}>
                  <bk-button class="mr10 is-disabled" theme="primary" text onClick={(e:Event) => { handlePrevent(e, data) }}>
                    { t('全部通过') }
                  </bk-button>
              </bk-popover>
              <bk-button theme="primary" text onClick={(e:Event) => { handleApplyReject(e, data) }}>
                  { t('全部驳回') }
              </bk-button>
            </div>
          )
        } else {
          return (
            <div>
              <bk-button class="mr10" theme="primary" text onClick={(e:Event) => { handleApplyApprove(e, data)}}>
                { data?.isSelectAll ? t('全部通过') : t('部分通过') }
              </bk-button>
              <bk-button theme="primary" text onClick={(e:Event) => { handleApplyReject(e, data) }}>
                  { t('全部驳回') }
              </bk-button>
            </div>
          )
        }
      },
    },
  ];
  permissionData.value.headers = columns;
};

// 获取资源列表数据
 (async () => {
  const { apigwId } = common;
  const pageParams = {
    no_page: true,
    order_by: 'name',
    offset: 0,
    limit: 10000
  };
  try {
    const { results} = await getApigwResources(apigwId, pageParams);
    resourceList.value = results || [];
    permissionApplyList.value = initResourceList(tableData.value)
  } catch (e) {
    console.log(e);
  }
})();

const initResourceList = (payload:any[]) => {
  payload.forEach((applyItem) => {
    const results = []
    applyItem.resourceList = []
    applyItem.isSelectAll = true
    applyItem.selection = []
    applyItem.resource_ids.forEach((resourceId:number) => {
      resourceList.value.forEach((item) => {
        if (item.id === resourceId) {
          results.push(item)
        }
      })
    })
    applyItem.resourceList = sortByKey(results, 'path')
  })
  return payload
}

// 监听授权维度的变化
watch(
  () => filterData.value,
  () => {
    updateTableEmptyConfig();
    resetSelections();
  },
  {  deep: true },
);

// 监听总数量的变化
watch(
  () => pagination.value,
  (v: any) => {
    permission.setCount(v.count);
  },
  { deep: true },
);

watch(
  () => tableData.value,
  async (value: any[]) => {
    permissionApplyList.value = await initResourceList(value);
    updateTableEmptyConfig();
  },
  { immediate: true },
);

// 批量审批dialog的title
const batchApplyDialogConfTitle = computed(() => {
  return t('将对以下{permissionSelectListTemplate}个权限申请单进行审批', { permissionSelectListTemplate: selections.value.length })
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
    part_resource_ids: {}
  };
  batchApplyDialogConf.isShow = true;
};

// 折叠table 多选发生变化触发
const handleRowSelectionChange = (payload: any, rowSelections: SelectionType) => {
  const { checked, row } = rowSelections
  if(checked) {
    payload.selection.push(row)
  } else {
    payload.selection = payload.selection.filter((item:Record<string, string | any[]>) => item.id !== row.id)
  }
  payload.isSelectAll = payload.resourceList.length === payload.selection.length
  curPermission.value = Object.assign(curPermission.value, { selection: payload.selection, isSelectAll: true })
  renderTableIndex.value++
  setTableHeader()
}

const handleRowSelectionAllChange= (payload: any, rowSelections: SelectionType) => {
  const { checked, data } = rowSelections;
  if(checked) {
    payload = Object.assign(payload, { selection: data, isSelectAll: true })
    curPermission.value = Object.assign(curPermission.value, { selection: data, isSelectAll: true })
  } else {
    payload = Object.assign(payload, { selection: [], isSelectAll: false })
    curPermission.value = Object.assign(curPermission.value, { selection: [], isSelectAll: false })
  }
}

// 批量审批api
const updateStatus = async () => {
  let data = cloneDeep({ ...curAction.value });
  const { isSelectAll, selection } = curPermission.value;
  await batchForm.value?.validate();
  await approveForm.value?.validate();
  try {
     // 部分通过
    const id = data?.ids?.[0] || '';
    if (data.status === 'approved' && expandRows.value.includes(id) && selection.length > 0 && !isSelectAll) {
      data.part_resource_ids = {};
      data.status = 'partial_approved';
      data.part_resource_ids[id] = selection.map(item => item.id);
    }
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
const handlePrevent = (e: Event, data: any) => {
  e.stopPropagation();
  return false;
};
// 全部通过/部分通过 btn
const handleApplyApprove = (e: Event, data: any) => {
  e.stopPropagation();
  curPermission.value = data;
  curAction.value = {
    ids: [data.id],
    status: 'approved',
    comment: t('全部通过'),
    part_resource_ids: {}
  };
  if (!curPermission.value.isSelectAll) {
   curAction.value.comment = t('部分通过');
  }
  applyActionDialogConf.title = t('通过申请');
  applyActionDialogConf.isShow = true;
};
// 全部驳回 btn
const handleApplyReject = (e: Event, data: any) => {
  e.stopPropagation();
  curPermission.value = data;
  curAction.value = {
    ids: [data.id],
    status: 'rejected',
    comment: t('全部驳回'),
    part_resource_ids: {}
  };
  applyActionDialogConf.title = t('驳回申请');
  applyActionDialogConf.isShow = true;
};

// 全部通过/部分通过/全部驳回 操作dialog
const handleSubmitApprove = () => {
  updateStatus();
};

const handleRowClick = (e:Event, row:any) => {
  e.stopPropagation();
  row.isExpand = !row.isExpand;
  expandRows.value = expandRows.value.filter((item) => item.id === row.id);
  if(row.isExpand) {
    curExpandRow.value = row;
    expandRows.value.push(row.id);
  } else {
    curExpandRow.value = {};
    expandRows.value = expandRows.value.filter((item) => item.id === row.id);
  }
  setTimeout(() => {
    permissionApplyList.value.forEach((item) => {
      if(item.id === curExpandRow.value.id) {
        item.selection = cloneDeep(item.resourceList);
        permissionTableRef.value.setRowExpand(row, row.isExpand);
        childPermTableRef.value[row.id]?.toggleAllSelection();
      } else {
        item = Object.assign(item, { isExpand: false, selection: [], isSelectAll: true });
        permissionTableRef.value.setRowExpand(item, false);
      }
    })
  }, 0)
};

const handleClearFilterKey = () => {
  filterData.value = { bk_app_code: '', applied_by: '', grant_dimension: '' };
  getList();
  updateTableEmptyConfig();
};

const updateTableEmptyConfig = () => {
  const list = Object.values(filterData.value).filter((item) => item !== '');
  if (list.length && !permissionApplyList.value.length) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (list.length) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const init = async () => {
  setTableHeader();
};

onMounted(() => {
  init();
});
</script>

<style lang="scss" scoped>
.w150 {
  width: 150px;
}
.h60 {
  height: 60px;
}
.apply-content {
  height: calc(100% - 90px);
  min-height: 600px;
}

.apply-expand-alert {
  padding: 20px;
  line-height: 60px;
  background-color: #fafafa;
}

.perm-apply-table,
.ag-expand-table {
  :deep(tr) {
    background-color: #fafbfd;
  }
  :deep(th) {
    .head-text {
      font-weight: bold !important;
      color: #63656E !important;
    }
  }
  :deep(.bk-table-head) {
    scrollbar-color: transparent transparent;
  }
  :deep(.bk-table-body) {
    scrollbar-color: transparent transparent;
  }
}
:deep(.ag-expand-table) {
  .bk-table-body {
    border-bottom: 0 !important;
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

:deep(.perm-apply-dot) {
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 3px;
    &.approved {
      background: #e6f6eb;
      border: 1px solid #43c472;
    }
    &.rejected {
      background: #FFE6E6;
      border: 1px solid #EA3636;
    }
  }
}

:deep(.bk-table-expanded-cell) {
    padding: 0 !important;

    &:hover {
      cursor: pointer;
    }

    .bk-table {
      border: 0;
    }
  }
</style>
