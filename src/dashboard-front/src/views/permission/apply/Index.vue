/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */
<template>
  <CustomHeader />
  <div class="permission-apply-container page-wrapper-padding">
    <div class="flex justify-between header">
      <BkButton
        v-bk-tooltips="{ content: t('请选择要审批的权限'), disabled: selections.length }"
        theme="primary"
        :disabled="!selections.length"
        @click="handleBatchApply"
      >
        {{ t("批量审批") }}
      </BkButton>
      <BkForm class="flex header-filter">
        <BkFormItem
          :label="t('授权维度')"
          label-width="108"
        >
          <BkSelect
            v-model="filterData.grant_dimension"
            class="w-150px"
          >
            <BkOption
              v-for="option of AUTHORIZATION_DIMENSION"
              :id="option.id"
              :key="option.id"
              :name="option.name"
            />
          </BkSelect>
        </BkFormItem>
        <BkFormItem
          :label="t('蓝鲸应用ID')"
          label-width="119"
        >
          <BkInput
            v-model="filterData.bk_app_code"
            class="w-150px"
            clearable
            :placeholder="t('请输入应用ID')"
          />
        </BkFormItem>
        <BkFormItem
          v-if="!userStore.isTenantMode"
          :label="t('申请人')"
          label-width="90"
        >
          <BkInput
            v-model="filterData.applied_by"
            class="w-150px"
            clearable
            :placeholder="t('请输入用户')"
          />
        </BkFormItem>
        <BkFormItem
          v-else
          :label="t('申请人')"
          label-width="90"
        >
          <BkUserSelector
            v-model="filterData.applied_by"
            :api-base-url="userStore.apiBaseUrl"
            :tenant-id="userStore.tenant_id"
            :placeholder="t('请输入用户')"
            style="min-width: 200px"
          />
        </BkFormItem>
      </BkForm>
    </div>
    <div class="apply-content">
      <BkLoading :loading="isLoading">
        <BkTable
          ref="permissionTableRef"
          class="perm-apply-table"
          :data="permissionApplyList"
          :columns="permissionData.headers"
          remote-pagination
          :row-style="{ cursor: 'pointer' }"
          :pagination="pagination"
          :max-height="clientHeight"
          row-hover="auto"
          border="outer"
          show-overflow-tooltip
          @page-limit-change="handlePageSizeChange"
          @page-value-change="handlePageChange"
          @select-all="handleSelectAllChange"
          @selection-change="handleSelectionChange"
          @row-click="handleRowClick"
        >
          <template #expandRow="row">
            <BkTable
              :ref="(el: HTMLElement) =>(childPermTableRef[row.id] = el)"
              :key="row.id"
              :max-height="378"
              size="small"
              :data="row.resourceList"
              :columns="childrenColumns"
              :outer-border="false"
              show-overflow-tooltip
              :cell-style="{ background: '#fafbfd' }"
              class="ag-expand-table"
              @select-all="(selection: SelectionType) => handleRowSelectionAllChange(row, selection)"
              @selection-change="(selection: SelectionType) => handleRowSelectionChange(row, selection)"
            />
          </template>
          <template #empty>
            <TableEmpty
              :is-loading="isLoading"
              :empty-type="tableEmptyConf.emptyType"
              :abnormal="tableEmptyConf.isAbnormal"
              @refresh="getList"
              @clear-filter="handleClearFilterKey"
            />
          </template>
        </BkTable>
      </BkLoading>
    </div>

    <!-- 批量审批 -->
    <BatchApproval
      v-model:dialog-params="batchApplyDialogConf"
      v-model:action-params="curAction"
      :title="batchApplyDialogConfTitle"
      :selections="selections"
      @approved="handleApprovedPermission"
      @rejected="handleRejectedPermission"
    />

    <!-- 全部通过/全部驳回操作 -->
    <BkDialog
      :is-show="applyActionDialogConf.isShow"
      theme="primary"
      :width="600"
      :quick-close="false"
      :header-position="'left'"
      :title="applyActionDialogConf.title"
      :loading="applyActionDialogConf.isLoading"
      :rules="rules"
      @confirm="handleSubmitApprove"
      @closed="applyActionDialogConf.isShow = false"
    >
      <BkForm
        ref="approveForm"
        :label-width="90"
        :model="curAction"
        :rules="rules"
        class="m-t-10px m-r-20px m-b-30px"
      >
        <BkFormItem
          :label="t('备注')"
          :property="'comment'"
          required
        >
          <BkAlert
            class="m-b-10px"
            :theme="alertTheme"
            :title="approveFormMessage"
          />
          <BkInput
            v-model="curAction.comment"
            type="textarea"
            :placeholder="t('请输入备注')"
            :rows="4"
            :maxlength="100"
          />
        </BkFormItem>
      </BkForm>
    </BkDialog>
  </div>
</template>

<script lang="tsx" setup>
import { cloneDeep } from 'lodash-es';
import { Loading, Message } from 'bkui-vue';
import {
  getApigwResources,
  getPermissionApplyList,
  updatePermissionStatus,
} from '@/services/source/permission';
import {
  useGateway,
  usePermission,
  useUserInfo,
} from '@/stores';
import {
  type SelectionType,
  useMaxTableLimit,
  useQueryList,
  useSelection,
} from '@/hooks';
import type { IApprovalListItem } from '@/types/permission';
import { sortByKey } from '@/utils';
import { AUTHORIZATION_DIMENSION } from '@/constants';
import { APPROVAL_STATUS_MAP } from '@/enums';
import BkUserSelector from '@blueking/bk-user-selector';
import BatchApproval from '@/views/permission/apply/components/BatchApproval.vue';
import CustomHeader from '@/views/permission/apply/components/CustomHeader.vue';
import AgIcon from '@/components/ag-icon/Index.vue';
import TableEmpty from '@/components/table-empty/Index.vue';

const { t } = useI18n();
const gatewayStore = useGateway();
const userStore = useUserInfo();
const permissionStore = usePermission();
const {
  selections,
  handleSelectionChange,
  handleSelectAllChange,
  resetSelections,
} = useSelection();
const { maxTableLimit, clientHeight } = useMaxTableLimit();

const approveForm = ref<InstanceType<typeof BkForm> & { validate: () => void }>();
const permissionTableRef = ref<InstanceType<typeof BkTable> & { setRowExpand: () => void }>();
const renderTableIndex = ref(0);
const expandRows = ref([]);
const childPermTableRef = ref([]);
const resourceList = ref([]);
const permissionData = ref({ headers: [] });
const filterData = ref({
  bk_app_code: '',
  applied_by: '',
  grant_dimension: '',
});
const curAction = ref({
  ids: [],
  status: '',
  comment: '',
  part_resource_ids: {},
});
const curPermission = ref({
  bk_app_code: '',
  resourceList: [],
  selection: [],
  grant_dimension: '',
  isSelectAll: true,
  resource_ids: [],
});
const curExpandRow = ref({});
const permissionApplyList = ref([]);
const childrenColumns = shallowRef([
  {
    label: '',
    type: 'index',
    width: 60,
  },
  {
    label: '',
    type: 'selection',
    width: 50,
    align: 'center',
  },
  {
    label: t('资源名称'),
    field: 'name',
  },
  {
    label: t('请求路径'),
    field: 'path',
  },
  {
    label: t('请求方法'),
    field: 'method',
  },
]);
const tableEmptyConf = ref<{
  emptyType: string
  isAbnormal: boolean
}>({
  emptyType: '',
  isAbnormal: false,
});
const batchApplyDialogConf = reactive({
  isLoading: false,
  isShow: false,
});
let applyActionDialogConf = reactive({
  isShow: false,
  title: t('通过申请'),
  isLoading: false,
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

const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList({
  apiMethod: getPermissionApplyList,
  filterData,
  initialPagination: {
    limitList: [
      maxTableLimit,
      10,
      20,
      50,
      100,
    ],
    limit: maxTableLimit,
  },
});

const apigwId = computed(() => gatewayStore.apigwId);
// 批量审批dialog的title
const batchApplyDialogConfTitle = computed(() => {
  return t(
    '将对以下{permissionSelectListTemplate}个权限申请单进行审批',
    { permissionSelectListTemplate: selections.value.length });
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
      return t(
        `应用${appCode} 申请${resourceLength}个权限，通过${selectLength}个，驳回${rejectLength}个`,
      );
    }
    return t(`应用${appCode} 申请${resourceLength}个权限，全部通过`);
  }
  return t(`应用${appCode} 申请${resourceLength}个权限，全部驳回`);
});

// 监听授权维度的变化
watch(
  () => filterData.value,
  () => {
    updateTableEmptyConfig();
    resetSelections(permissionTableRef.value);
  },
  { deep: true },
);

// 监听总数量的变化
watch(
  () => pagination.value,
  (v) => {
    permissionStore.setCount(v.count);
    resetSelections(permissionTableRef.value);
  },
  { deep: true },
);

const setTableHeader = () => {
  permissionData.value.headers = [
    {
      type: 'selection',
      width: 60,
      minWidth: 60,
      align: 'center',
      showOverflowTooltip: false,
    },
    {
      field: 'bk_app_code',
      label: t('蓝鲸应用ID'),
    },
    {
      field: 'grant_dimension_display',
      label: t('授权维度'),
      render: ({ row }: { row?: Partial<IApprovalListItem> }) => {
        if (['resource'].includes(row.grant_dimension)) {
          return (
            <div class="flex items-center">
              <AgIcon
                name={row.isExpand ? 'down-shape' : 'right-shape'}
                size="10"
                class="m-r-5px"
              />
              {`${row.grant_dimension_display} (${row.resource_ids?.length || '--'})`}
            </div>
          );
        }
        return row.grant_dimension_display || '--';
      },
    },
    {
      field: 'expire_days_display',
      label: t('权限期限'),
      render: ({ row }: { row?: Partial<IApprovalListItem> }) => {
        return row?.expire_days_display || '--';
      },
    },
    {
      field: 'reason',
      label: t('申请理由'),
      render: ({ row }: { row?: Partial<IApprovalListItem> }) => {
        return row?.reason || '--';
      },
    },
    {
      field: 'applied_by',
      label: t('申请人'),
      render: ({ row }: { row?: Partial<IApprovalListItem> }) => (
        <span>
          <bk-user-display-name user-id={row.applied_by} />
        </span>
      ),
    },
    {
      field: 'created_time',
      width: 215,
      label: t('申请时间'),
    },
    {
      field: 'status',
      width: 150,
      label: t('审批状态'),
      render: ({ row }: { row?: Partial<IApprovalListItem> }) => {
        if (['pending'].includes(row?.status)) {
          return (
            <div class="perm-apply-dot">
              <Loading class="m-r-5px" loading size="mini" mode="spin" theme="primary" />
              {APPROVAL_STATUS_MAP[row?.status as keyof typeof APPROVAL_STATUS_MAP]}
            </div>
          );
        }
        else {
          return (
            <div class="perm-apply-dot">
              <span class={['dot', { [row.status]: row?.status }]} />
              {APPROVAL_STATUS_MAP[row?.status as keyof typeof APPROVAL_STATUS_MAP]}
            </div>
          );
        }
      },
    },
    {
      field: 'operate',
      width: 220,
      label: t('操作'),
      key: renderTableIndex.value,
      render: ({ row }: { row?: Partial<IApprovalListItem> }) => {
        if (
          expandRows.value.includes(row.id)
          && row?.selection.length === 0
          && !['api'].includes(row?.grant_dimension)
        ) {
          return (
            <div>
              <BkPopover content={t('请选择资源')}>
                <BkButton
                  class="m-r-10px is-disabled"
                  theme="primary"
                  text
                  onClick={(e: Event) => {
                    handlePrevent(e, row);
                  }}
                >
                  {t('全部通过')}
                </BkButton>
              </BkPopover>
              <BkButton
                theme="primary"
                text
                onClick={(e: Event) => {
                  handleApplyReject(e, row);
                }}
              >
                {t('全部驳回')}
              </BkButton>
            </div>
          );
        }
        else {
          return (
            <div>
              <BkButton
                class="m-r-10px"
                theme="primary"
                text
                onClick={(e: Event) => {
                  handleApplyApprove(e, row);
                }}
              >
                {row?.isSelectAll ? t('全部通过') : t('部分通过')}
              </BkButton>
              <BkButton
                theme="primary"
                text
                onClick={(e: Event) => {
                  handleApplyReject(e, row);
                }}
              >
                {t('全部驳回')}
              </BkButton>
            </div>
          );
        }
      },
    },
  ];
};

const initResourceList = (resourceArr: IApprovalListItem[]) => {
  resourceArr.forEach((applyItem) => {
    const results = [];
    applyItem.resource_ids.forEach((resourceId: number) => {
      resourceList.value.forEach((item) => {
        if (item.id === resourceId) {
          results.push(item);
        }
      });
    });
    applyItem = Object.assign(applyItem, {
      isSelectAll: true,
      selection: [],
      resourceList: sortByKey(results, 'path'),
    });
  });
  return resourceArr;
};

// 获取资源列表数据
const getResourceList = async () => {
  const pageParams = {
    no_page: true,
    order_by: 'name',
    offset: 0,
    limit: 10000,
  };
  const { results } = await getApigwResources(apigwId.value, pageParams);
  resourceList.value = results || [];
  permissionApplyList.value = initResourceList(tableData.value);
};

// 批量审批
const handleBatchApply = () => {
  curAction.value = {
    ids: [],
    status: '',
    comment: '',
    part_resource_ids: {},
  };
  batchApplyDialogConf.isShow = true;
};

// 折叠table 多选发生变化触发
const handleRowSelectionChange = (payload: Record<string, unknown>, rowSelections: SelectionType) => {
  const { checked, row } = rowSelections;
  if (checked) {
    payload.selection.push(row);
  }
  else {
    payload.selection = payload.selection.filter((item: Partial<IApprovalListItem>) => item.id !== row.id);
  }
  const isSelectAll = payload.resourceList.length === payload.selection.length;
  payload.isSelectAll = isSelectAll;
  curPermission.value = Object.assign(curPermission.value, {
    selection: payload.selection,
    isSelectAll,
  });
  renderTableIndex.value++;
  setTableHeader();
};

const handleRowSelectionAllChange = (payload: Record<string, unknown>, rowSelections: SelectionType) => {
  const { checked, data } = rowSelections;
  if (checked) {
    payload = Object.assign(payload, {
      selection: data,
      isSelectAll: true,
    });
    curPermission.value = Object.assign(curPermission.value, {
      selection: data,
      isSelectAll: true,
    });
  }
  else {
    payload = Object.assign(payload, {
      selection: [],
      isSelectAll: false,
    });
    curPermission.value = Object.assign(curPermission.value, {
      selection: [],
      isSelectAll: false,
    });
  }
};

// 批量审批api
const updateStatus = async () => {
  let params = cloneDeep({ ...curAction.value });
  const { isSelectAll, selection } = curPermission.value;
  await approveForm.value?.validate();
  try {
    // 部分通过
    const id = params?.ids?.[0] || '';
    if (
      ['approved'].includes(params.status)
      && expandRows.value.includes(id)
      && selection.length > 0
      && !isSelectAll
    ) {
      params.part_resource_ids = {};
      params = Object.assign(params, {
        status: 'partial_approved',
        [part_resource_ids[id]]: selection.map(item => item.id),
      });
    }
    await updatePermissionStatus(apigwId.value, params);
    batchApplyDialogConf.isShow = false;
    applyActionDialogConf.isShow = false;
    getList();
    Message({
      message: t('操作成功！'),
      theme: 'success',
    });
    resetSelections(permissionTableRef.value);
  }
  catch (e) {
    Message({
      message: e?.message || e?.error?.message,
      theme: 'error',
    });
  }
};

// 全部通过
const handleApprovedPermission = () => {
  curAction.value = Object.assign(curAction.value, {
    status: 'approved',
    ids: selections.value.map(permission => permission.id),
  });
  updateStatus();
};

// 全部驳回
const handleRejectedPermission = () => {
  curAction.value = Object.assign(curAction.value, {
    status: 'rejected',
    ids: selections.value.map(permission => permission.id),
  });
  updateStatus();
};

const handlePrevent = (e: Event) => {
  e.stopPropagation();
  return false;
};

// 全部通过/部分通过
const handleApplyApprove = (e: Event, row: Partial<IApprovalListItem>) => {
  e.stopPropagation();
  curPermission.value = row;
  curAction.value = {
    ids: [row.id],
    status: 'approved',
    comment: t('全部通过'),
    part_resource_ids: {},
  };
  if (!curPermission.value.isSelectAll) {
    curAction.value.comment = t('部分通过');
  }
  applyActionDialogConf = Object.assign(applyActionDialogConf, {
    isShow: true,
    title: t('通过申请'),
  });
};

// 全部驳回
const handleApplyReject = (e: Event, row: Partial<IApprovalListItem>) => {
  e.stopPropagation();
  curPermission.value = row;
  curAction.value = {
    ids: [row.id],
    status: 'rejected',
    comment: t('全部驳回'),
    part_resource_ids: {},
  };
  applyActionDialogConf = Object.assign(applyActionDialogConf, {
    isShow: true,
    title: t('驳回申请'),
  });
};

// 全部通过/部分通过/全部驳回 操作dialog
const handleSubmitApprove = () => {
  updateStatus();
};

const handleRowClick = (e: Event, row: Record<string, unknown>) => {
  e.stopPropagation();
  if (row.grant_dimension === 'resource') {
    row.isExpand = !row.isExpand;
    expandRows.value = expandRows.value.filter(item => item.id === row.id);
    if (row.isExpand) {
      curExpandRow.value = row;
      expandRows.value.push(row.id);
    }
    else {
      curExpandRow.value = {};
      expandRows.value = expandRows.value.filter(item => item.id === row.id);
    }
    setTimeout(() => {
      permissionApplyList.value.forEach((item) => {
        if (item.id === curExpandRow.value.id) {
          permissionTableRef.value.setRowExpand(row, row.isExpand);
          childPermTableRef.value[row.id]?.toggleAllSelection();
        }
        else {
          item = Object.assign(item, {
            isExpand: false,
            selection: [],
            isSelectAll: true,
          });
          permissionTableRef.value.setRowExpand(item, false);
        }
      });
    }, 0);
  }
};

const handleClearFilterKey = () => {
  filterData.value = Object.assign({}, {
    bk_app_code: '',
    applied_by: '',
    grant_dimension: '',
  });
  getList();
  updateTableEmptyConfig();
};

const updateTableEmptyConfig = () => {
  const filterList = Object.values(filterData.value).filter(item => item !== '');
  tableEmptyConf.value.isAbnormal = pagination.value.abnormal;
  if (filterList.length && !permissionApplyList.value.length) {
    tableEmptyConf.value.emptyType = 'searchEmpty';
    return;
  }
  if (filterList.length) {
    tableEmptyConf.value.emptyType = 'empty';
    return;
  }
};

watch(
  () => tableData.value,
  async (value: IApprovalListItem[]) => {
    permissionApplyList.value = await initResourceList(value);
    updateTableEmptyConfig();
  },
  { immediate: true },
);

onMounted(() => {
  setTableHeader();
  getResourceList();
});
</script>

<style lang="scss" scoped>
.apply-expand-alert {
  padding: 20px;
  line-height: 60px;
  background-color: #fafafa;
}

.header-filter {
  .bk-form-item {
    margin-bottom: 16px;
  }
}

.perm-apply-table,
.ag-expand-table {
  :deep(tr) {
    background-color: #fafbfd;
  }

  :deep(th) {
    .head-text {
      font-weight: bold !important;
      color: #63656e !important;
    }
  }
}

:deep(.ag-expand-table) {
  td,
  th {
    padding: 0 !important;
    height: 42px !important;
    cursor: default !important;
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
      background: #ffe6e6;
      border: 1px solid #ea3636;
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
