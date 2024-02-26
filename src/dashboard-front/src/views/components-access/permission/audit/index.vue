<template>
  <div class="app-content">
    <div class="ag-top-header">
      <span v-bk-tooltips="{ content: t('请选择要审批的权限'), disabled: permissionTableSelection.length }">
        <bk-button
          theme="primary"
          :disabled="!permissionTableSelection.length"
          @click="handleBatchApply">
          {{ t('批量审批') }}
        </bk-button>
      </span>
      <bk-form class="fr bk-inline-form" form-type="inline">
        <bk-form-item :label="t('蓝鲸应用ID')">
          <bk-input
            :clearable="true"
            v-model="keyword"
            :placeholder="t('请输入应用ID，按Enter搜索')"
            :right-icon="'bk-icon icon-search'"
            style="width: 190px;"
            @enter="handleSearch">
          </bk-input>
        </bk-form-item>
        <bk-form-item :label="t('申请人')">
          <user
            style="width: 300px;"
            :max-data="1"
            v-model="searchParams.operator">
          </user>
        </bk-form-item>
      </bk-form>
    </div>
    <bk-loading :loading="isDataLoading">
      <bk-table
        style="margin-top: 15px;"
        ref="permissionTable"
        class="ag-apply-table"
        :data="permissionApplyList"
        :size="'medium'"
        :pagination="pagination"
        @page-limit-change="handlePageLimitChange"
        @page-change="handlePageChange"
        @select="handlePageSelect"
        @selection-change="handlePageSelectionChange"
        @expand-change="handlePageExpandChange"
        @row-click="handleRowClick">
        <!-- <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getApigwPermissionApplyList"
          @clear-filter="clearFilterKey"
        />
      </div> -->
        <bk-table-column type="selection" width="60" align="center"></bk-table-column>
        <bk-table-column type="expand" width="30" class="ag-expand-cell">
          <template #default="props">
            <bk-table
              :ref="(el) => setPermissionDetail(`permissionDetail_${props.row.id}`, el)"
              :max-height="378"
              :size="'small'"
              :key="props.row.id"
              :data="props.row.components"
              :outer-border="false"
              :header-cell-style="{ background: '#fafbfd', borderRight: 'none' }"
              ext-cls="ag-expand-table"
              @selection-change="handleRowSelectionChange">
              <!-- <div slot="empty">
              <table-empty empty />
            </div> -->
              <bk-table-column type="index" label="" width="60"></bk-table-column>
              <bk-table-column type="selection" width="50"></bk-table-column>
              <bk-table-column prop="name" :label="t('组件名称')"></bk-table-column>
              <bk-table-column prop="description" :label="t('组件描述')"></bk-table-column>
            </bk-table>
          </template>
        </bk-table-column>
        <bk-table-column :label="t('蓝鲸应用ID')" prop="bk_app_code"></bk-table-column>
        <bk-table-column :label="t('组件系统')" prop="system_name">
          <template #default="props">
            <span>{{props.row.system_name || '--'}}</span>
          </template>
        </bk-table-column>
        <bk-table-column :label="t('权限期限')" prop="expire_days_display">
          <template #default="props">
            <span>{{props.row.expire_days ? getMonths(props.row.expire_days) : '--'}}</span>
          </template>
        </bk-table-column>
        <bk-table-column :label="t('申请理由')" prop="reason">
          <template #default="props">
            <span>{{props.row.reason || '--'}}</span>
          </template>
        </bk-table-column>
        <bk-table-column :label="t('申请人')" prop="applied_by"></bk-table-column>
        <bk-table-column
          :label="t('申请时间')"
          prop="applied_time"
          width="200"
          :show-overflow-tooltip="true">
        </bk-table-column>
        <bk-table-column :label="t('审批状态')" prop="status">
          <template #default="props">
            {{ statusMap[props.row['apply_status']] }}
          </template>
        </bk-table-column>
        <bk-table-column :label="t('操作')" width="200" :key="renderTableIndex">
          <template #default="props">
            <bk-popover
              :content="t('请选择组件')"
              v-if="expandRows.includes(props.row.id) && props.row.selection.length === 0"
            >
              <bk-button
                class="mr10 is-disabled"
                theme="primary"
                text
                @click.stop.prevent="handlePrevent">
                {{ t('全部通过') }}
              </bk-button>
            </bk-popover>
            <bk-button
              class="mr10"
              theme="primary"
              v-else
              text
              @click="handleApplyApprove(props.row)">
              {{props.row.isSelectAll ? t('全部通过') : t('部分通过')}}
            </bk-button>
            <bk-button
              theme="primary"
              text
              @click="handleApplyReject(props.row)">
              {{ t('全部驳回') }}
            </bk-button>
          <!-- <bk-button
          class="mr10"
          theme="primary"
          text
           @click="handleApplyApprove(props.row)">
           {{props.row.isSelectAll ? '全部通过' : t('部分通过')}}
           </bk-button> -->
          <!-- <bk-button theme="primary" text @click="handleApplyReject(props.row)"> {{ t('全部驳回') }} </bk-button> -->
          </template>
        </bk-table-column>
      </bk-table>
    </bk-loading>
    <bk-dialog
      v-model="batchApplyDialogConf.isShow"
      theme="primary"
      :mask-close="false"
      :width="670"
      :loading="batchApplyDialogConf.isLoading"
      :title="batchApplyDialogConfTitle">
      <template #footer>
        <div>
          <bk-button
            theme="primary"
            @click="batchApprovePermission"
            :loading="curAction.status === 'approved' && batchApplyDialogConf.isLoading">
            {{ t('全部通过') }}
          </bk-button>
          <bk-button
            @click="batchRejectPermission"
            :loading="curAction.status === 'rejected' && batchApplyDialogConf.isLoading">
            {{ t('全部驳回') }}
          </bk-button>
          <bk-button
            @click="batchApplyDialogConf.isShow = false">
            {{ t('取消') }}
          </bk-button>
        </div>
      </template>

      <div>
        <bk-table
          :data="permissionSelectList"
          :size="'small'"
          :max-height="200"
          :key="permissionSelectList.length">
          <!-- <div slot="empty">
            <table-empty empty />
          </div> -->
          <bk-table-column width="250" :label="t('蓝鲸应用ID')" prop="bk_app_code"></bk-table-column>
          <bk-table-column :label="t('申请人')" prop="applied_by"></bk-table-column>
          <bk-table-column :label="t('申请时间')" prop="applied_time"></bk-table-column>
        </bk-table>
        <bk-form
          :label-width="0"
          :model="curAction"
          :rules="rules"
          ref="batchForm"
          class="mt20">
          <bk-form-item
            class="bk-hide-label"
            label=""
            :required="true"
            :property="'comment'">
            <bk-input
              type="textarea"
              :placeholder="t('请输入备注')"
              v-model="curAction.comment"
              :maxlength="100">
            </bk-input>
          </bk-form-item>
        </bk-form>
      </div>
    </bk-dialog>

    <bk-dialog
      v-model="applyActionDialogConf.isShow"
      theme="primary"
      :width="600"
      :mask-close="false"
      :header-position="'left'"
      :title="applyActionDialogConf.title"
      :loading="applyActionDialogConf.isLoading"
      @confirm="handleSubmitApprove">
      <bk-form
        :label-width="90"
        :model="curAction"
        :rules="rules"
        ref="approveForm"
        class="mt10 mr20 mb20">
        <bk-form-item
          :label="t('备注')"
          :required="true"
          :property="'comment'">
          <bk-alert class="mb10" type="warning" :title="approveFormMessage"></bk-alert>
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

<script lang="ts" setup>
import { ref, reactive, computed, watch, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { Message } from 'bkui-vue';
import { applyRecordsHandle, applyRecordsPending } from '@/http';
// import User from '@/components/user';

const { t } = useI18n();

const keyword = ref<string>('');
const isPageLoading = ref<boolean>(true);
const isDataLoading = ref<boolean>(false);
const permissionApplyList = ref<any>([]);
const pagination = reactive<any>({
  current: 1,
  count: 0,
  limit: 10,
});
const permissionTable = ref();
const batchApplyDialogConf = reactive<any>({
  isLoading: false,
  isShow: false,
});
const permissionSelectList = ref<any>([]);
const permissionTableSelection = ref<any>([]);
const permissionRowSelection = ref<any>([]);
const curExpandRow = ref<any>();
const renderTableIndex = ref<number>(0);
const expandRows = ref<any>([]);
const curPermission = ref<any>({
  bk_app_code: '',
  selection: [],
  components: [],
});
const approveForm = ref();
const batchForm = ref();
const searchParams = reactive<any>({
  bk_app_code: '',
  applied_by: '',
  operator: [],
});
const applyActionDialogConf = reactive({
  isShow: false,
  title: t('通过申请'),
  isLoading: false,
});
const curAction = ref<any>({
  ids: [],
  status: '',
  comment: '',
});
const tableEmptyConf = reactive({
  keyword: '',
  isAbnormal: false,
});
const statusMap = ref<any>({
  approved: t('通过'),
  rejected: t('驳回'),
  pending: t('未审批'),
});
const rules = ref({
  comment: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
});

const permissionDetailRefs = ref<Map<String, any>>();
const setPermissionDetail = (name: string, el: any) => {
  permissionDetailRefs.value?.set(name, el);
};


const approveFormMessage = computed(() => {
  const selectLength = curPermission.value.selection.length;
  const resourceLength = curPermission.value.components.length;
  if (curAction.value.status === 'approved') {
    if (selectLength && selectLength < resourceLength) {
      const rejectLength = resourceLength - selectLength;
      return t('应用{appCode} 申请{applyForLength}个权限，通过{selectLength}个，驳回{rejectLength}个', { appCode: curPermission.value.bk_app_code, applyForLength: curPermission.value.components.length, selectLength, rejectLength });
    }
    return t('应用{appCode} 申请{applyForLength}个权限，全部通过', { appCode: curPermission.value.bk_app_code, applyForLength: curPermission.value.components.length });
  }
  return t('应用{appCode} 申请{applyForLength}个权限，全部驳回', { appCode: curPermission.value.bk_app_code, applyForLength: curPermission.value.components.length });
});

const batchApplyDialogConfTitle = computed(() => t('将对以下{permissionSelectListTemplate}个权限申请单进行审批', { permissionSelectListTemplate: permissionSelectList.value?.length }));

const updateTableEmptyConfig = () => {
  if (keyword.value || searchParams.operator.length) {
    tableEmptyConf.keyword = 'placeholder';
    return;
  }
  tableEmptyConf.keyword = '';
};

// const clearFilterKey = () => {
//   keyword.value = '';
//   searchParams.operator = [];
// };

const handleRowClick = (row: any) => {
  permissionTable.value?.toggleRowExpansion(row);
  curExpandRow.value = row;
};

const handleRowSelectionChange = (row: any, index: number, checked: any) => {
  permissionRowSelection.value = checked;
  row.selection = checked;
  if (checked.length) {
    row.isSelectAll = row.components.length === checked.length;
  } else {
    row.isSelectAll = true;
  }
  renderTableIndex.value += 1;
};

const handlePageSelectionChange = (selection: any) => {
  permissionTableSelection.value = selection;
};

const handlePageExpandChange = (row: any, expandedRows: any) => {
  expandRows.value = expandedRows.map((item: any) => {
    return item.id;
  });
  if (curExpandRow.value !== row) {
    permissionTable.value?.toggleRowExpansion(curExpandRow, false);
  }
  curExpandRow.value = row;
  nextTick(() => {
    const table = permissionDetailRefs.value?.get(`permissionDetail_${row.id}`);
    if (table) {
      table?.toggleAllSelection();
    }
  });
};

const handleSubmitApprove = () => {
  if (applyActionDialogConf.isLoading) {
    return false;
  }
  applyActionDialogConf.isLoading = true;
  approveForm.value?.validate().then(() => {
    updatePermissionStatus();
  })
    .catch(() => {
      nextTick(() => {
        applyActionDialogConf.isLoading = false;
      });
    });
};

const updatePermissionStatus = async () => {
  const data: any = { ...curAction };

  // 部分通过
  if (data.status === 'approved' && permissionRowSelection.value.length && !curPermission.value.isSelectAll) {
    const id = data.ids[0];
    data.part_component_ids = {};
    data.status = 'partial_approved';
    data.part_component_ids[id] = permissionRowSelection.value.map((item: any) => item.id);
  }

  try {
    await applyRecordsHandle(data);

    // 当前页只有一条数据
    if (permissionApplyList.value.length === 1 && pagination.current > 1) {
      pagination.current -= 1;
    }

    Message({
      theme: 'success',
      message: t('操作成功！'),
    });

    applyActionDialogConf.isShow = false;
    batchApplyDialogConf.isShow = false;
    getApigwPermissionApplyList();
  } catch (e) {
    console.log(e);
  } finally {
    applyActionDialogConf.isLoading = false;
    batchApplyDialogConf.isLoading = false;
  }
};

const batchRejectPermission = async () => {
  if (batchApplyDialogConf.isLoading) {
    return false;
  }
  batchApplyDialogConf.isLoading = true;
  batchForm.value?.validate().then(() => {
    curAction.value.ids = permissionSelectList.value?.map((permission: any) => permission.id);
    curAction.value.status = 'rejected';
    updatePermissionStatus();
  })
    .catch(() => {
      nextTick(() => {
        batchApplyDialogConf.isLoading = false;
      });
    });
};

const batchApprovePermission = async () => {
  if (batchApplyDialogConf.isLoading) {
    return false;
  }
  batchApplyDialogConf.isLoading = true;
  batchForm.value?.validate().then(() => {
    curAction.value.ids = permissionSelectList.value?.map((permission: any) => permission.id);
    curAction.value.status = 'approved';
    updatePermissionStatus();
  })
    .catch(() => {
      nextTick(() => {
        batchApplyDialogConf.isLoading = false;
      });
    });
};

const handlePageSelect = (selection: any) => {
  permissionTableSelection.value = selection;
};

const handleBatchApply = () => {
  curAction.value = {
    ids: [],
    status: '',
    comment: '',
  };
  if (!permissionTableSelection.value.length) {
    Message({
      theme: 'error',
      message: t('请选择要审批的权限'),
    });
    return false;
  }

  permissionSelectList.value = permissionTableSelection;
  batchForm.value?.clearError();
  batchApplyDialogConf.isShow = true;
};

const handleApplyReject = (data: any) => {
  curPermission.value = data;
  curAction.value = {
    ids: [data.id],
    status: 'rejected',
    comment: t('全部驳回'),
  };
  applyActionDialogConf.title = t('驳回申请');
  applyActionDialogConf.isShow = true;
  approveForm.value?.clearError();
};

const handlePrevent = () => {
  return false;
};

const handleApplyApprove = (data: any) => {
  curPermission.value = data;
  curAction.value = {
    ids: [data.id],
    status: 'approved',
    comment: t('全部通过'),
    part_component_ids: {},
  };
  if (!curPermission.value.isSelectAll) {
    curAction.value.comment = t('部分通过');
  } else {
    curAction.value.part_component_ids[data.id] = curPermission.value.components.map((item: any) => item.id);
  }
  applyActionDialogConf.title = t('通过申请');
  applyActionDialogConf.isShow = true;
  approveForm.value?.clearError();
};

const handleSearch = () => {
  searchParams.bk_app_code = keyword;
};

const handlePageChange = (newPage: number) => {
  pagination.current = newPage;
  getApigwPermissionApplyList(newPage);
};

const handlePageLimitChange = (limit: number) => {
  pagination.limit = limit;
  pagination.current = 1;
  getApigwPermissionApplyList(pagination.current);
};

const getMonths = (payload: any) => {
  return `${Math.ceil(payload / 30)} ${t('个月')}`;
};

const initReourceList = (permissionApplyList: any[] = []) => {
  permissionApplyList.forEach((applyItem) => {
    applyItem.isSelectAll = true;
    applyItem.selection = [];
  });
  return permissionApplyList;
};

const getApigwPermissionApplyList = async (page?: number) => {
  const curPage = page || pagination.current;
  const pageParams = {
    limit: pagination.limit,
    offset: pagination.limit * (curPage - 1),
    bk_app_code: searchParams.bk_app_code,
    applied_by: searchParams.applied_by,
  };
  isDataLoading.value = true;
  try {
    const res = await applyRecordsPending(pageParams);
    permissionApplyList.value = initReourceList(res.data.results);
    pagination.count = res.data.count;
    updateTableEmptyConfig();
    tableEmptyConf.isAbnormal = false;
  } catch (e) {
    tableEmptyConf.isAbnormal = true;
    console.log(e);
  } finally {
    isPageLoading.value = false;
    isDataLoading.value = false;
  }
};

const init = async () => {
  await getApigwPermissionApplyList();
};

init();

watch(
  () => keyword.value,
  (newVal, oldVal) => {
    if (oldVal && !newVal) {
      handleSearch();
    }
  },
);

watch(
  () => searchParams,
  () => {
    pagination.current = 1;
    pagination.count = 0;
    searchParams.applied_by = searchParams.operator.join(';');
    getApigwPermissionApplyList();
  },
  {
    deep: true,
  },
);
</script>

<style lang="scss" scoped>
.app-content {
  padding: 24px;
}
.ag-resource-radio {
  label {
    display: block;
    margin-bottom: 10px;
  }
}

:deep(.bk-table-medium .cell) {
  -webkit-line-clamp: 1 !important;
}

.ag-transfer-box {
  padding: 20px;
  background: #FAFBFD;
  border: 1px solid #F0F1F5;
  border-radius: 2px;
}

.ag-dl {
  padding: 15px 40px 5px 30px;
}

.ag-user-type {
  width: 560px;
  height: 80px;
  background: #FAFBFD;
  border-radius: 2px;
  border: 1px solid #DCDEE5;
  padding: 17px 20px 0 20px;
  position: relative;
  overflow: hidden;

  .apigateway-icon {
    font-size: 80px;
    position: absolute;
    color: #ECF2FC;
    top: 15px;
    right: 20px;
    z-index: 0;
  }

  strong {
    font-size: 14px;
    margin-bottom: 10px;
    line-height: 1;
    display: block;
  }

  p {
    font-size: 12px;
    color: #63656E;
  }
}

.bk-inline-form.bk-form {
  :deep(.bk-form-item) {
    display: inline-block;
    vertical-align: middle;
  }
}
</style>
