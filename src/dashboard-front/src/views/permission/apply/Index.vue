/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
    <div class="flex items-center justify-between perm-approval-header">
      <BkButton
        v-bk-tooltips="{ content: t('请选择要审批的权限'), disabled: selections.length }"
        theme="primary"
        :disabled="!selections.length"
        class="batch-approval"
        @click="handleBatchApply"
      >
        {{ t("批量审批") }}
      </BkButton>
      <BkForm
        class="perm-approval-form"
        label-width="auto"
      >
        <BkFormItem :label="t('蓝鲸应用ID')">
          <BkInput
            v-model="filterData.bk_app_code"
            clearable
            :placeholder="t('请输入应用ID')"
          />
        </BkFormItem>
        <BkFormItem :label="t('授权维度')">
          <BkSelect
            v-model="filterData.grant_dimension"
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
          v-if="!featureFlagStore.isTenantMode"
          :label="t('申请人')"
        >
          <BkInput
            v-model="filterData.applied_by"
            clearable
            :placeholder="t('请输入用户')"
          />
        </BkFormItem>
        <BkFormItem
          v-else
          :label="t('申请人')"
        >
          <!-- @vue-expect-error BkUserSelector emits string | null -->
          <BkUserSelector
            v-model="filterData.applied_by"
            :api-base-url="envStore.tenantUserDisplayAPI"
            :tenant-id="userStore.info.tenant_id"
            :placeholder="t('请输入用户')"
          />
        </BkFormItem>
      </BkForm>
    </div>
    <div class="apply-content">
      <AgTable
        ref="permissionTableRef"
        v-model:table-data="tableData"
        v-model:selected-row-keys="selectedRowKeys"
        show-settings
        show-selection
        :expand-icon="false"
        :expandable="expandableConfig"
        :expanded-row-keys="expandableConfig.expandedRowKeys"
        :show-first-full-row="selections.length > 0"
        :disabled-check-selection="disabledSelection"
        :max-limit-config="{ allocatedHeight: 240, mode: 'tdesign'}"
        :filter-value="filterValue"
        :api-method="getTableData"
        :columns="getTableColumns"
        :row-class-name="handleSetRowClass"
        @row-click="handleRowClick"
        @filter-change="handleFilterChange"
        @selection-change="handleSelectionChange"
        @clear-filter="handleClearFilter"
        @request-done="handleRequestDone"
      >
        <template #expandedRow="{row}">
          <AgTable
            v-model:table-data="row.resources"
            size="small"
            class="ag-expand-table"
            local-page
            :show-selection="!isITSMApproval(row)"
            :max-height="378"
            :columns="childrenColumns"
            @selection-change="(selection) => handleRowSelectionChange(row, selection)"
          />
        </template>
      </AgTable>
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
    <ApprovalDialog
      v-model:dialog-config="applyActionDialogConf"
      v-model:form-data="curAction"
      :cur-permission="curPermission"
      @approved="handleSubmitApprove"
    />
  </div>
</template>

<script lang="tsx" setup>
import { cloneDeep } from 'lodash-es';
import { Button, Form, Loading, Message, Popover } from 'bkui-vue';
import type { TableRowData } from '@blueking/tdesign-ui';
import {
  getApigwResources,
  getPermissionApplyList,
  updatePermissionStatus,
} from '@/services/source/permission';
import {
  useEnv,
  useFeatureFlag,
  usePermission,
  useUserInfo,
} from '@/stores';
import type { IApprovalListItem, IResource } from '@/types/permission';
import type { ITableMethod } from '@/types/common';
import type { IApplyStatus, IFomDataQuery } from '@/services/types/query/personal-workbench.ts';
import type { IAppPermissionApplyApprovalInputSLZ } from '@/services/types/body/post/gateways.ts';
import type { IResourceListPageOutput } from '@/services/types/responses/gateways.ts';
import { sortByKey } from '@/utils';
import { AUTHORIZATION_DIMENSION } from '@/constants';
import { APPROVAL_STATUS_MAP } from '@/enums';
import BkUserSelector from '@blueking/bk-user-selector';
import BatchApproval from '@/views/permission/apply/components/BatchApproval.vue';
import CustomHeader from '@/views/permission/apply/components/CustomHeader.vue';
import ApprovalDialog from '@/views/permission/apply/components/ApprovalDialog.vue';
import AgTable from '@/components/ag-table/Index.vue';

// 扩展 IApprovalListItem，补充运行时动态添加的字段
interface IApprovalListItemExt extends IApprovalListItem {
  id: number
  grant_dimension: string
  selectionTip: string
  isExpand?: boolean
  resources?: IResource[]
  selection?: IResource[]
  isSelectAll?: boolean
}

interface IProps { gatewayId?: number }

const { gatewayId = 0 } = defineProps<IProps>();

const envStore = useEnv();
const userStore = useUserInfo();
const permissionStore = usePermission();
const featureFlagStore = useFeatureFlag();
const { t } = useI18n();

const permissionTableRef = useTemplateRef<InstanceType<typeof AgTable> & ITableMethod>('permissionTableRef');
const approveForm = ref<InstanceType<typeof Form> & { validate: () => void }>();
const tableData = ref<any[]>([]);
const selections = ref<any[]>([]);
const selectedRowKeys = ref<any[]>([]);
const resourceList = ref<IResourceListPageOutput[]>([]);
const childrenColumns = shallowRef<any[]>([
  {
    title: '',
    colKey: 'serial-number',
    align: 'center',
    width: 80,
  },
  {
    title: t('资源名称'),
    colKey: 'name',
    ellipsis: true,
  },
  {
    title: t('请求路径'),
    colKey: 'path',
    ellipsis: true,
  },
  {
    title: t('请求方法'),
    colKey: 'method',
    ellipsis: true,
  },
]);
const filterData = ref<Record<string, any>>({});
const filterValue = ref<Record<string, any>>({});
const curAction = ref<IFomDataQuery>({
  ids: [],
  status: '',
  comment: '',
  part_resource_ids: {},
});
const curPermission = ref<{
  bk_app_code: string
  resources: IResource[]
  selection: IResource[]
  grant_dimension: string
  isSelectAll: boolean
  resource_ids: number[]
}>({
  bk_app_code: '',
  resources: [],
  selection: [],
  grant_dimension: '',
  isSelectAll: true,
  resource_ids: [],
});
const expandableConfig = ref({
  expandColumn: false,
  expandedRowKeys: [] as any[],
  canExpand: (row: any) => {
    return ['resource'].includes(row.grant_dimension);
  },
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

const apigwId = computed(() => gatewayId);
// 批量审批dialog的title
const batchApplyDialogConfTitle = computed(() => {
  return t(
    '将对以下{permissionSelectListTemplate}个权限申请单进行审批',
    { permissionSelectListTemplate: selections.value.length });
});

// 监听授权维度的变化
watch(
  () => filterData.value,
  () => {
    filterValue.value = Object.assign({}, filterData.value);
    handleSearch();
  },
  { deep: true },
);

const setRowResources = () => {
  tableData.value.forEach((row: any) => {
    row.isSelectAll = true;
    row.selection = [];
    row.resources = sortByKey(resourceList.value.filter((resource: IResourceListPageOutput) => row.resource_ids.includes(resource.id)), 'path');
  });
};

watch(
  resourceList,
  () => {
    setRowResources();
  },
  {
    deep: true,
    immediate: true,
  },
);

function getList() {
  permissionTableRef.value?.fetchData(filterData.value, { resetPage: true });
}

function handleSearch() {
  getList();
}

const getTableColumns = computed((): any[] => {
  return [
    {
      colKey: 'bk_app_code',
      title: t('蓝鲸应用ID'),
      ellipsis: true,
    },
    {
      colKey: 'grant_dimension',
      title: t('授权维度'),
      ellipsis: true,
      filter: {
        type: 'single',
        showConfirmAndReset: true,
        popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
        list: AUTHORIZATION_DIMENSION.map(({ name, id }) => ({
          label: name,
          value: id,
        })),
      },
      cell: (h: any, { row }: { row: Partial<IApprovalListItemExt> }) => {
        if (['resource'].includes(row.grant_dimension!)) {
          return (
            <div class="flex items-center">
              <ag-icon
                name={row.isExpand ? 'down-shape' : 'right-shape'}
                size="10"
                class="mr-4px"
              />
              {`${row.grant_dimension_display} (${row.resources?.length || '--'})`}
            </div>
          );
        }
        return row.grant_dimension_display || '--';
      },
    },
    {
      colKey: 'expire_days_display',
      title: t('权限期限'),
      ellipsis: true,
      cell: (h: any, { row }: { row: Partial<IApprovalListItemExt> }) => {
        return row.expire_days_display || '--';
      },
    },
    {
      colKey: 'reason',
      title: t('申请理由'),
      ellipsis: true,
      cell: (h: any, { row }: { row: Partial<IApprovalListItemExt> }) => {
        return row.reason || '--';
      },
    },
    {
      colKey: 'applied_by',
      title: t('申请人'),
      ellipsis: true,
      width: 160,
      cell: (_: unknown, { row }: { row: Partial<IApprovalListItemExt> }) => {
        if (!row?.applied_by) return '--';

        return featureFlagStore.isEnableDisplayName
          ? <span><bk-user-display-name user-id={row.applied_by} /></span>
          : <span>{row.applied_by}</span>;
      },
    },
    {
      colKey: 'created_time',
      title: t('申请时间'),
      width: 220,
      ellipsis: true,
    },
    {
      colKey: 'status',
      title: t('审批状态'),
      ellipsis: true,
      cell: (h: any, { row }: { row: Partial<IApprovalListItemExt> }) => {
        if (['pending'].includes(row.status!)) {
          return (
            <div class="perm-apply-dot">
              <Loading class="mr-4px" loading size="mini" mode="spin" theme="primary" />
              {APPROVAL_STATUS_MAP[row.status as keyof typeof APPROVAL_STATUS_MAP]}
            </div>
          );
        }
        else {
          return (
            <div class="perm-apply-dot">
              <span class={['dot', { [row.status!]: row.status }]} />
              {APPROVAL_STATUS_MAP[row.status as keyof typeof APPROVAL_STATUS_MAP]}
            </div>
          );
        }
      },
    },
    {
      colKey: 'operate',
      title: t('操作'),
      fixed: 'right',
      ellipsis: true,
      cell: (h: any, { row }: { row: Partial<IApprovalListItemExt> }) => {
        if (isITSMApproval(row)) {
          return (
            <Button
              text
              theme="primary"
              onClick={() => {
                window.open(row?.itsm_ticket_url);
              }}
            >
              {t('审批')}
            </Button>
          );
        }

        if (
          expandableConfig.value.expandedRowKeys.includes(row.id!)
          && !row.selection?.length
          && !['api'].includes(row.grant_dimension!)
        ) {
          return (
            <div>
              <Popover content={t('请选择资源')}>
                <Button
                  class="mr-8px is-disabled"
                  theme="primary"
                  text
                  onClick={(e: Event) => {
                    handlePrevent(e);
                  }}
                >
                  {t('全部通过')}
                </Button>
              </Popover>
              <Button
                theme="primary"
                text
                onClick={(e: Event) => {
                  handleApplyReject(e, row);
                }}
              >
                {t('全部驳回')}
              </Button>
            </div>
          );
        }

        return (
          <div>
            <Button
              class="mr-8px"
              theme="primary"
              text
              onClick={(e: Event) => {
                handleApplyApprove(e, row);
              }}
            >
              {row.isSelectAll ? t('全部通过') : t('部分通过')}
            </Button>
            <Button
              theme="primary"
              text
              onClick={(e: Event) => {
                handleApplyReject(e, row);
              }}
            >
              {t('全部驳回')}
            </Button>
          </div>
        );
      },
    },
  ];
});
const isEnabledITSMApply = computed(() => featureFlagStore?.flags?.ENABLE_ITSM4_PERMISSION_APPLY);

const getTableData = async (params: Record<string, any> = {}) => {
  const results = await getPermissionApplyList(apigwId.value, params);
  return results ?? [];
};

// 获取资源列表数据
const getResourceList = async () => {
  const pageParams: any = {
    no_page: true,
    order_by: 'name',
    offset: 0,
    limit: 10000,
  };
  const { results } = await getApigwResources(apigwId.value, pageParams);
  resourceList.value = results || [];
};

const handleRequestDone = () => {
  const pageConf = permissionTableRef.value?.getPagination();
  if (pageConf) {
    permissionStore.setCount(pageConf.total || 0);
  }
  getResourceList();
};

const isITSMApproval = (row: TableRowData) => {
  return isEnabledITSMApply.value && Boolean(row.itsm_ticket_url) && Boolean(row.itsm_ticket_id);
};

const disabledSelection = (row: TableRowData) => {
  const isDisabled = isITSMApproval(row);
  row.selectionTip = isDisabled ? t('单据接入了 ITSM，ITSM 不支持批量审批') : '';
  return isDisabled;
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

const handleSelectionChange = ({ selections: selected, selectionsRowKeys }: any) => {
  selections.value = selected;
  selectedRowKeys.value = selectionsRowKeys;
};

// 折叠table 多选发生变化触发
const handleRowSelectionChange = (row: any, rowSelections: any) => {
  const { selections } = rowSelections;
  const isSelectAll = row.resources.length === selections.length;
  row.selection = selections;
  row.isSelectAll = isSelectAll;
  curPermission.value = Object.assign(curPermission.value, {
    selection: row.selection,
    isSelectAll,
  });
};

// 处理表头筛选联动搜索框
const handleFilterChange = (filterItem: any) => {
  filterData.value = Object.assign(filterData.value, filterItem);
  filterValue.value = Object.assign({}, filterItem);
  getResourceList();
};

// 批量审批api
const updateStatus = async () => {
  let params = cloneDeep({ ...curAction.value });
  const { isSelectAll, selection } = curPermission.value;
  await approveForm.value?.validate();
  // 部分通过
  const id = params?.ids?.[0] || '';
  if (
    ['approved'].includes(params.status as IApplyStatus)
    && expandableConfig.value.expandedRowKeys.includes(id)
    && selection.length > 0
    && !isSelectAll
  ) {
    params = Object.assign(params, {
      status: 'partial_approved',
      part_resource_ids: { [id]: selection.map((item: any) => item.id) },
    });
  }
  await updatePermissionStatus(apigwId.value, params as IAppPermissionApplyApprovalInputSLZ);
  batchApplyDialogConf.isShow = false;
  applyActionDialogConf.isShow = false;
  Message({
    message: t('操作成功！'),
    theme: 'success',
  });
  handleClearSelection();
  getList();
  getResourceList();
};

// 全部通过
const handleApprovedPermission = () => {
  curAction.value = Object.assign(curAction.value, {
    status: 'approved',
    ids: selections.value.map((permission: any) => permission.id),
  });
  updateStatus();
};

// 全部驳回
const handleRejectedPermission = () => {
  curAction.value = Object.assign(curAction.value, {
    status: 'rejected',
    ids: selections.value.map((permission: any) => permission.id),
  });
  updateStatus();
};

const handlePrevent = (e: Event) => {
  e.stopPropagation();
  return false;
};

// 全部通过/部分通过
const handleApplyApprove = (e: Event, row: Partial<IApprovalListItemExt>) => {
  e.stopPropagation();
  curPermission.value = row as any;
  curAction.value = {
    ids: [row.id!],
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
const handleApplyReject = (e: Event, row: Partial<IApprovalListItemExt>) => {
  e.stopPropagation();
  curPermission.value = row as any;
  curAction.value = {
    ids: [row.id!],
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

const handleSetRowClass = ({ row }: { row: any }) => {
  if (row.grant_dimension.includes('resource')) {
    return 'cursor-pointer';
  }
  return '';
};

const handleRowClick = ({ e, row }: {
  e: Event
  row: IApprovalListItemExt
}) => {
  e.stopPropagation();
  if (row.grant_dimension.includes('resource')) {
    row.isExpand = !row.isExpand;
    expandableConfig.value.expandedRowKeys
      = expandableConfig.value.expandedRowKeys.filter((item: any) => item === row.id);
    const curExpandRow = row.isExpand ? row : {} as any;
    if (row.isExpand) {
      expandableConfig.value.expandedRowKeys.push(row.id as any);
    }
    else {
      expandableConfig.value.expandedRowKeys
        = expandableConfig.value.expandedRowKeys.filter((item: any) => item !== row.id);
    }
    tableData.value.forEach((item: any) => {
      const isExpand = item.id === curExpandRow.id;
      item.isExpand = isExpand;
      if (!isExpand) {
        item = Object.assign(item, {
          isExpand: false,
          selection: [],
          isSelectAll: true,
        });
      }
    });
  }
};

const handleClearFilter = () => {
  filterData.value = {};
};

const handleClearSelection = () => {
  permissionTableRef.value?.handleResetSelection();
  selections.value = [];
};
</script>

<style lang="scss" scoped>
.permission-apply-container {

  .apply-content {
    border: 1px solid #DCDEE5;
  }
}

.apply-expand-alert {
  padding: 20px;
  line-height: 60px;
  background-color: #fafafa;
}

.perm-approval-header {
  display: flex;
  min-height: 32px;
  margin-bottom: 16px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;

  .batch-approval {
    flex-shrink: 0;
    width: auto;
  }

  .perm-approval-form {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    flex-wrap: wrap;
    gap: 24px;
    flex: 1;
    min-width: 0;

    :deep(.bk-form-item) {
      display: flex;
      max-width: fit-content;
      min-width: 0;
      margin: 0;
      align-items: center;
      flex: 1;

      .bk-form-label {
        width: auto;
        text-align: right;
        white-space: nowrap;
      }

      .bk-form-content {
        width: 230px;

        .bk-input,
        .bk-user-selector,
        .member-selector {
          width: 100%;
        }
      }
    }
  }
}

:deep(.t-table__header) {

  .t-table__ellipsis {
    font-weight: 700 !important;
    color: #63656e !important;
  }
}

:deep(.t-table__expanded-row) {

  .t-table__row-full-element {
    padding: 0;
  }

  td,
  th {
    height: 42px !important;
    padding: 0 !important;
    cursor: default !important;
  }
}

:deep(.perm-apply-dot) {

  .dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    margin-right: 3px;
    border-radius: 50%;

    &.approved {
      background-color: #e6f6eb;
      border: 1px solid #43c472;
    }

    &.rejected {
      background-color: #ffe6e6;
      border: 1px solid #ea3636;
    }
  }
}
</style>
