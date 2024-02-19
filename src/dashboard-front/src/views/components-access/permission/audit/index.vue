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
      <bk-form class="fr bk-search-form">
        <bk-form-item :label="t('授权维度')">
          <bk-select
            v-model="searchParams.dimension"
            style="width: 150px;">
            <bk-option
              v-for="option of dimensionList"
              :key="option.id"
              :id="option.id"
              :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
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
          <!-- <user
            style="width: 300px;"
            :max-data="1"
            v-model="searchParams.operator">
          </user> -->
        </bk-form-item>
      </bk-form>
    </div>
    <bk-table
      style="margin-top: 15px;"
      border="outer"
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
          @reacquire="getApigwPermissionApplyData"
          @clear-filter="clearFilterKey"
        />
      </div> -->
      <bk-table-column type="selection" width="60" align="center"></bk-table-column>
      <bk-table-column type="expand" width="30" class="ag-expand-cell">
        <template #default="props">
          <div
            class="bk-alert m20 bk-alert-error"
            v-if="props?.row?.grant_dimension === 'api'"
            style="display: block; text-align: center; line-height: 60px;">
            <div class="bk-alert-wraper">
              <i class="bk-icon icon-info" style="display: inline-block; margin-right: 1px;"></i>
              <div class="bk-alert-content" style="display: inline-block;">
                <div class="bk-alert-title">
                  {{ t('将申请网关下所有资源的权限，包括未来新创建的资源，请谨慎审批') }}
                </div>
              </div>
            </div>
          </div>
          <bk-table
            v-else
            :ref="el => setRefs(el, `permissionDetail_${props?.row?.id}`)"
            :max-height="378"
            :size="'small'"
            :key="props?.row?.id"
            :data="props?.row?.resourceList"
            :outer-border="false"
            :header-cell-style="{ background: '#fafbfd', borderRight: 'none' }"
            ext-cls="ag-expand-table"
            @selection-change="handleRowSelectionChange"
          >
            <!-- <div slot="empty">
              <table-empty empty />
            </div> -->
            <bk-table-column type="index" label="" width="60"></bk-table-column>
            <bk-table-column type="selection" width="50"></bk-table-column>
            <bk-table-column prop="name" :label="t('资源名称')"></bk-table-column>
            <bk-table-column prop="path" :label="t('请求路径')"></bk-table-column>
            <bk-table-column prop="method" :label="t('请求方法')"></bk-table-column>
          </bk-table>
        </template>
      </bk-table-column>
      <bk-table-column :label="t('蓝鲸应用ID')" prop="bk_app_code"></bk-table-column>
      <bk-table-column :label="t('授权维度')" prop="grant_dimension_display">
        <template #default="props">
          <span>{{props?.row?.grant_dimension_display || '--'}}</span>
        </template>
      </bk-table-column>
      <bk-table-column :label="t('权限期限')" prop="expire_days_display">
        <template #default="props">
          <span>{{props?.row?.expire_days_display || '--'}}</span>
        </template>
      </bk-table-column>
      <bk-table-column :label="t('申请理由')" prop="reason">
        <template #default="props">
          <span>{{props?.row?.reason || '--'}}</span>
        </template>
      </bk-table-column>
      <bk-table-column :label="t('申请人')" prop="applied_by"></bk-table-column>
      <bk-table-column :label="t('申请时间')" prop="created_time"></bk-table-column>
      <bk-table-column :label="t('审批状态')" prop="status">
        <template #default="props">
          <round-loading v-if="props?.row['status'] === 'pending'" />
          <span v-else :class="['dot', props?.row['status']]"></span>
          {{statusMap[props?.row['status']]}}
        </template>
      </bk-table-column>
      <bk-table-column :label="t('操作')" width="200" :key="renderTableIndex">
        <template #default="props">
          <!-- 按网关，不需要选择对应资源 -->
          <bk-popover
            :content="t('请选择资源')"
            v-if="expandRows.includes(props?.row?.id)
              && props?.row?.selection.length === 0
              && props?.row?.grant_dimension !== 'api'">
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
            v-else
            theme="primary"
            text
            @click.stop.prevent="handleApplyApprove(props)">{{props?.row?.isSelectAll ? t('全部通过') : t('部分通过')}}
          </bk-button>
          <bk-button
            theme="primary"
            text
            @click.stop.prevent="handleApplyReject(props?.row)">
            {{ t('全部驳回') }}
          </bk-button>
        </template>
      </bk-table-column>
    </bk-table>

    <bk-dialog
      v-model="batchApplyDialogConf.isShow"
      theme="primary"
      :mask-close="false"
      :width="670"
      :loading="batchApplyDialogConf.isLoading"
      :title="batchApplyDialogConfTitle">
      <template #footer>
        <bk-button
          theme="primary"
          @click="batchApprovePermission"
          :loading="curAction.status === 'approved' && batchApplyDialogConf.isLoading">
          {{ t('全部通过') }}
        </bk-button>
        <bk-button
          theme="default"
          @click="batchRejectPermission"
          :loading="curAction.status === 'rejected' && batchApplyDialogConf.isLoading">
          {{ t('全部驳回') }}
        </bk-button>
        <bk-button
          theme="default"
          @click="batchApplyDialogConf.isShow = false">
          {{ t('取消') }}
        </bk-button>
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
          <bk-table-column
            width="250"
            :label="t('蓝鲸应用ID')"
            prop="bk_app_code"
          >
          </bk-table-column>
          <bk-table-column :label="t('申请人')" prop="applied_by"></bk-table-column>
          <bk-table-column :label="t('申请时间')" prop="created_time"></bk-table-column>
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
          <bk-alert class="mb10" :type="alertType" :title="approveFormMessage"></bk-alert>
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

    <bk-sideslider
      :quick-close="true"
      :title="detailSliderConf.title"
      :width="600"
      v-model:is-show="detailSliderConf.isShow">
      <template #default>
        <div class="p30">
          <section class="ag-kv-list" style="margin-bottom: 70px;">
            <div class="item">
              <div class="key"> {{ t('蓝鲸应用ID：') }} </div>
              <div class="value">{{curApply.bk_app_code}}</div>
            </div>
            <div class="item">
              <div class="key"> {{ t('申请人：') }} </div>
              <div class="value">{{curApply.applied_by}}</div>
            </div>
            <div class="item">
              <div class="key"> {{ t('申请时间：') }} </div>
              <div class="value">{{curApply.created_time}}</div>
            </div>
            <div class="item">
              <div class="key"> {{ t('审批状态：') }} </div>
              <div class="value">{{statusMap[curApply['status']]}}</div>
            </div>
            <div class="item">
              <div class="key"> {{ t('资源信息：') }} </div>
              <div class="value" style="line-height: 22px; padding-top: 10px">
                <bk-table
                  style="margin-top: 5px;"
                  :data="curApply.resourceList"
                  :size="'small'">
                  <!-- <div slot="empty">
                    <table-empty empty />
                  </div> -->
                  <bk-table-column :label="t('请求路径')" prop="path"></bk-table-column>
                  <bk-table-column :label="t('请求方法')" prop="method"></bk-table-column>
                </bk-table>
                <div
                  class="ag-alert warning mt10"
                  v-if="curApply.resourceList.length
                    && curApply.resourceList.length > curApply.resource_ids.length"
                >
                  <i class="apigateway-icon icon-ag-info"></i>
                  <p> {{ t('部分资源已被删除') }} </p>
                </div>
                <div class="ag-alert warning mt10" v-if="!curApply.resourceList.length && curApply.resource_ids.length">
                  <i class="apigateway-icon icon-ag-info"></i>
                  <p> {{ t('资源已被删除') }} </p>
                </div>
              </div>
            </div>
          </section>

          <div class="bk-sideslider-footer">
            <bk-button theme="primary" class="mr15" @click="handleApplyApprove(curApply)"> {{ t('通过') }} </bk-button>
            <bk-button @click="handleApplyReject(curApply)"> {{ t('驳回') }} </bk-button>
          </div>
        </div>
      </template>
    </bk-sideslider>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { useCommon } from '@/store';
import { Message } from 'bkui-vue';
import { sortByKey } from '@/common/util';
import { updateApigwPermissionStatus, getApigwPermissionApplyList, getResourceListData } from '@/http';

const { t } = useI18n();
const common = useCommon();

const permissionTable = ref();
const approveForm = ref();
const batchForm = ref();
const keyword = ref<string>('');
const isPageLoading = ref<boolean>(true);
const isDataLoading = ref<boolean>(false);
const permissionApplyList = ref<any>([]);
const curExpandedRow = ref<any>(null);
const pagination = reactive<any>({
  current: 1,
  count: 0,
  limit: 10,
});
const batchApplyDialogConf = reactive<any>({
  isLoading: false,
  isShow: false,
});
const permissionSelectList = ref<any>([]);
const permissionTableSelection = ref<any>([]);
const permissionRowSelection = ref<any>([]);
const expandRows = ref<any>([]);
const renderTableIndex = ref<number>(0);
const curApply = ref<any>({
  bk_app_code: '',
  expire_type: 'None',
  expire_days: '',
  resource_ids: [],
  dimension: 'api',
  resourceList: [],
});
const curPermission = ref<any>({
  bk_app_code: '',
  resourceList: [],
  selection: [],
});
const rules = ref<any>({
  comment: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
});
const dimensionList = ref<any>([
  {
    id: 'api',
    name: t('按网关'),
  },
  {
    id: 'resource',
    name: t('按资源'),
  },
]);
const searchParams = ref<any>({
  dimension: '',
  bk_app_code: '',
  applied_by: '',
  operator: [],
});
const statusMap = ref<any>({
  approved: t('通过'),
  rejected: t('驳回'),
  pending: t('未审批'),
});
const applyActionDialogConf = reactive<any>({
  isShow: false,
  title: t('通过申请'),
  isLoading: false,
});
const curAction = ref<any>({
  ids: [],
  status: '',
  comment: '',
});
const detailSliderConf = reactive<any>({
  title: '',
  isShow: false,
});
const resourceList = ref<any>([]);
const tableEmptyConf = reactive<any>({
  keyword: '',
  isAbnormal: false,
});
const curExpandRow = ref<any>();
const formRefs = ref(new Map());

const setRefs = (el: any, name: string) => {
  if (el) {
    formRefs.value?.set(name, el);
  }
};

const apigwId = computed(() => common.apigwId);
const approveFormMessage = computed(() => {
  const selectLength = curPermission.value?.selection?.length;
  const resourceLength = curPermission.value?.resourceList?.length;
  if (curPermission.value?.grant_dimension === 'api') {
    if (curAction.value?.status === 'approved') {
      return `${t('应用将申请网关下所有资源的权限，包括未来新创建的资源，请谨慎审批')}`;
    }
    return `${t('应用将按网关申请全部驳回')}`;
  }
  if (curAction.value?.status === 'approved') {
    if (selectLength && selectLength < resourceLength) {
      const rejectLength = resourceLength - selectLength;
      return t('应用{appCode} 申请{applyForLength}个权限，通过{selectLength}个，驳回{rejectLength}个', { appCode: curPermission.value.bk_app_code, applyForLength: curPermission.value.resourceList.length, selectLength, rejectLength });
    }
    return t('应用{appCode} 申请{applyForLength}个权限，全部通过', { appCode: curPermission.value.bk_app_code, applyForLength: curPermission.value.resourceList.length });
  }
  return t('应用{appCode} 申请{applyForLength}个权限，全部驳回', { appCode: curPermission.value.bk_app_code, applyForLength: curPermission.value.resourceList.length });
});
const batchApplyDialogConfTitle = computed(() => t('将对以下{permissionSelectListTemplate}个权限申请单进行审批', { permissionSelectListTemplate: permissionSelectList.value?.length }));
const alertType = computed(() => {
  if (curPermission.value?.grant_dimension === 'api') {
    return curAction.value.status === 'approved' ? 'warning' : 'error';
  }
  return 'warning';
});

const updateTableEmptyConfig = () => {
  if (keyword.value || searchParams.value?.operator?.length || searchParams.value?.dimension) {
    tableEmptyConf.keyword = 'Placeholder';
    return;
  }
  tableEmptyConf.keyword = '';
};

// const clearFilterKey = () => {
//   keyword.value = '';
//   searchParams.value.operator = [];
//   searchParams.value.dimension = '';
// };

// const handleDimensionChange = () => {
//   handleSearch();
// };

const handleRowClick = (row: any) => {
  permissionTable.value?.toggleRowExpansion(row);
  curExpandedRow.value = row;
};

const handleRowSelectionChange = (row: any, rowSelections: any) => {
  permissionRowSelection.value = rowSelections;
  row.selection = rowSelections;
  if (rowSelections?.length) {
    row.isSelectAll = row.resourceList.length === rowSelections.length;
  } else {
    row.isSelectAll = true;
  }
  permissionRowSelection.value.isSelectAll = row.isSelectAll;
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
    permissionTable.value?.toggleRowExpansion(curExpandRow.value, false);
  }
  curExpandRow.value = row;
  nextTick(() => {
    const table = formRefs.value?.get(`permissionDetail_${row.id}`);
    table?.toggleAllSelection();
  });
};

// const handleShowRecord = (data: any) => {
//   curApply.value = data;
//   detailSliderConf.title = `${t('申请应用：')}${data.bk_app_code}`;
//   curApply.value.resourceList = [];

//   const results = [];

//   curApply.value.resource_ids.forEach((resourceId: any) => {
//     resourceList.value.forEach((item: any) => {
//       if (item.id === resourceId) {
//         results.push(item);
//       }
//     });
//   });
//   curApply.value.resourceList = sortByKey(results, 'path');
//   detailSliderConf.isShow = true;
// };

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
  const id = data.ids[0];
  if (data.status === 'approved' && expandRows.value.includes(id) && permissionRowSelection.value.length && !permissionRowSelection.value.isSelectAll) {
    data.part_resource_ids = {};
    data.status = 'partial_approved';
    data.part_resource_ids[id] = permissionRowSelection.value.map((item: any) => item.id);
  }

  try {
    await updateApigwPermissionStatus(apigwId.value, data);

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
    detailSliderConf.isShow = false;
    getApigwPermissionApplyData();
  } catch (e) {
    console.error(e);
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
    permissionRowSelection.value.isSelectAll = true;
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
    permissionRowSelection.value.isSelectAll = true;
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

const handleApplyApprove = (props: any) => {
  const data = props.row;
  curPermission.value = data;
  curAction.value = {
    ids: [data.id],
    status: 'approved',
    comment: t('全部通过'),
  };
  if (!curPermission.value.isSelectAll) {
    curAction.value.comment = t('部分通过');
  }
  applyActionDialogConf.title = t('通过申请');
  applyActionDialogConf.isShow = true;
  approveForm.value?.clearError();
};

const handleSearch = () => {
  searchParams.value.bk_app_code = keyword;
};

const handlePageChange = (newPage: any) => {
  pagination.current = newPage;
  getApigwPermissionApplyData(newPage);
};

const handlePageLimitChange = (limit: any) => {
  pagination.limit = limit;
  pagination.current = 1;
  getApigwPermissionApplyData(pagination.current);
};

const getApigwResources = async (callback: any) => {
  const pageParams = {
    offset: 0,
    limit: 10000,
    order_by: 'name',
  };

  try {
    const res = await getResourceListData(apigwId.value, pageParams);
    resourceList.value = res.data.results;
    callback?.();
  } catch (e) {
    console.error(e);
  }
};

const handlePrevent = () => {
  return false;
};

const initReourceList = (permissionApplyList: any[] = []) => {
  permissionApplyList.forEach((applyItem) => {
    const results: any = [];
    applyItem.resourceList = [];
    applyItem.isSelectAll = true;
    applyItem.selection = [];
    applyItem.resource_ids.forEach((resourceId: any) => {
      resourceList.value.forEach((item: any) => {
        if (item.id === resourceId) {
          results.push(item);
        }
      });
    });
    applyItem.resourceList = sortByKey(results, 'path');
  });
  return permissionApplyList;
};

const getApigwPermissionApplyData = async (page?: any) => {
  const curPage = page || pagination.current;
  const pageParams = {
    limit: pagination.limit,
    offset: pagination.limit * (curPage - 1),
    bk_app_code: searchParams.value.bk_app_code,
    applied_by: searchParams.value.applied_by,
    grant_dimension: searchParams.value.dimension,
  };

  isDataLoading.value = true;
  try {
    const res = await getApigwPermissionApplyList(apigwId.value, pageParams);
    res.data.results.forEach((item: any) => {
      item.updated_time = item.updated_time || '--';
    });

    permissionApplyList.value = initReourceList(res.data.results);
    pagination.count = res.data.count;
    updateTableEmptyConfig();
    tableEmptyConf.isAbnormal = false;
  } catch (e) {
    tableEmptyConf.isAbnormal = true;
    console.error(e);
  } finally {
    isPageLoading.value = false;
    isDataLoading.value = false;
    // $store.commit('setMainContentLoading', false);
  }
};

const init = async () => {
  getApigwResources(() => {
    getApigwPermissionApplyData();
  });
};


onMounted(() => {
  init();
});

watch(
  () => keyword.value,
  (newVal, oldVal) => {
    if (oldVal && !newVal) {
      handleSearch();
    }
  },
);

watch(
  () => searchParams.value,
  () => {
    pagination.current = 1;
    pagination.count = 0;
    searchParams.value.applied_by = searchParams.value.operator.join(';');
    getApigwPermissionApplyData();
  },
  {
    deep: true,
  },
);
</script>

<style lang="scss" scoped>
.app-content {
  padding: 24px;
  .ag-top-header {
    min-height: 32px;
    margin-bottom: 20px;
    position: relative;
  }
}
.ag-resource-radio {
  label {
    display: block;
    margin-bottom: 10px;
  }
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

.bk-search-form.bk-form {
 :deep(.bk-form-item) {
  display: inline-block;
 }
}
</style>
