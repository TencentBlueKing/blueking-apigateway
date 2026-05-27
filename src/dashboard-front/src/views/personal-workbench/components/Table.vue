/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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
  <div :class="`p-16px personal-workbench-table ${applyStatus}`">
    <BasicForm
      ref="basicFormRef"
      v-model:form-data="filterData"
      :selected-rows="selectedRows"
      :is-show-selection="isShowSelection"
      :is-show-applicant="!['applied'].includes(applyStatus)"
      @batch-approval="handleBatchApproval"
    />
    <AgTable
      ref="tableRef"
      v-model:table-data="tableData"
      v-model:selected-row-keys="selectedRowKeys"
      v-model:settings="settings"
      show-settings
      :show-selection="isShowSelection"
      :table-empty-type="tableEmptyType"
      :expand-icon="false"
      :expandable="expandableConfig"
      :expanded-row-keys="expandableConfig.expandedRowKeys"
      :show-first-full-row="selectedRows.length > 0"
      :max-limit-config="{ allocatedHeight: 240, mode: 'tdesign' }"
      :filter-value="filterData"
      :api-method="getTableData"
      :columns="tableColumns"
      :row-class-name="getRowClass"
      @row-click="handleRowClick"
      @filter-change="handleFilterChange"
      @selection-change="handleSelectionChange"
      @clear-filter="handleClearFilter"
    >
      <template #cellEmptyContent="{ col }">
        <template v-if="!col.fixed">
          <span class="empty-placeholder">--</span>
        </template>
        <template v-else />
      </template>
      <template #expandedRow="{row}">
        <BkLoading :loading="row?.isLoading">
          <AgTable
            v-model:table-data="row.resources"
            v-model:selected-row-keys="curPermission.resource_ids"
            size="small"
            class="ag-expand-table"
            local-page
            :max-height="378"
            :show-first-full-row="isShowSelection && curPermission.resource_ids?.length > 0"
            :show-selection="isShowSelection"
            :columns="childrenColumns"
            @selection-change="(selection) => handleChildSelectionChange(row, selection)"
          />
        </BkLoading>
      </template>
    </AgTable>
  </div>

  <!-- 审批详情 -->
  <ApprovalDetailSlider
    v-model:approval-slider-conf="approvalSliderConf"
    :active-tab="activeTab"
    :approval-detail="approvalSliderDetail"
  />

  <!-- 批量审批 -->
  <BatchApproval
    v-model:dialog-params="batchApplyDialogConf"
    v-model:action-params="curAction"
    :title="batchApplyDialogConfTitle"
    :selections="selectedRows"
    @approved="handleApprovedPermission"
    @rejected="handleRejectedPermission"
  />

  <!-- 全部通过/全部驳回操作 -->
  <ApprovalDialog
    v-model:dialog-config="applyActionDialogConf"
    v-model:form-data="curAction"
    :is-gateway="isGateway"
    :cur-permission="curPermission"
    @approved="handleSubmitApprove"
  />
</template>

<script setup lang="tsx">
import { Button, Loading, Message, Popover } from 'bkui-vue';
import { t } from '@/locales';
import type { FilterValue, PrimaryTableProps, TableRowData } from '@blueking/tdesign-ui';
import type { ITableEmptyType, ITableMethod } from '@/types/common';
import type { ICountAndResults } from '@/services/types/utils.ts';
import type {
  IApplyStatus,
  IApprovalStatus,
  IFomDataQuery,
  IPermission,
  IPersonalWorkbenchListQuery,
  IPersonalWorkbenchUIState,
  ITabKey,
} from '@/services/types/query/personal-workbench.ts';
import type {
  IPersonalWorkbenchFilterOptionResponse,
  IPersonalWorkbenchListResponse,
  IResources,
} from '@/services/types/responses/personal-workbench.ts';
import type { IAppPermissionApplyApprovalInputSLZ } from '@/services/types/body/post/gateways.ts';
import type { IMCPServerAppPermissionApplyUpdateInputSLZ } from '@/services/types/body/patch/gateways.ts';
import {
  getGatewayFilterOptions,
  getMcpGatewayFilterOptions,
  getMcpServerFilterOptions,
} from '@/services/source/personal-workbench.ts';
import { updatePermissionStatus } from '@/services/source/permission.ts';
import { updateMcpPermissions } from '@/services/source/mcp-market.ts';
import { useFeatureFlag } from '@/stores';
import { APPROVAL_HISTORY_STATUS_MAP, APPROVAL_STATUS_MAP } from '@/enums';
import { filterSimpleEmpty } from '@/utils/filterEmptyValues';
import BatchApproval from '@/views/permission/apply/components/BatchApproval.vue';
import ApprovalDialog from '@/views/permission/apply/components/ApprovalDialog.vue';
import ApprovalDetailSlider from '@/views/mcp-server/permission/components/ApprovalDetailSlider.vue';
import BasicForm from '@/views/personal-workbench/components/Form.vue';
import AgTable from '@/components/ag-table/Index.vue';
import RenderTagOverflow from '@/components/render-tag-overflow/Index.vue';

interface IProps {
  activeTab?: ITabKey
  applyStatus?: IApprovalStatus
  remoteMethod?: (params: IPersonalWorkbenchListQuery) => Promise<ICountAndResults<IPersonalWorkbenchListResponse>>
}

const {
  applyStatus = 'pending',
  activeTab = 'gateway',
  remoteMethod = undefined,
} = defineProps<IProps>();

const featureFlagStore = useFeatureFlag();

const basicFormRef = useTemplateRef<InstanceType<typeof BasicForm>>('basicFormRef');
const tableRef = useTemplateRef<InstanceType<typeof AgTable> & ITableMethod>('tableRef');
const tableData = ref<IPersonalWorkbenchListResponse[]>([]);
const selectedRows = ref<IPersonalWorkbenchUIState[]>([]);
const selectedRowKeys = ref<(string | number)[]>([]);
const settings = ref(null);
const tableEmptyType = ref<ITableEmptyType>('empty');
const applyActionDialogConf = ref({
  isShow: false,
  isLoading: false,
  title: t('通过申请'),
});
const batchApplyDialogConf = ref({
  isLoading: false,
  isShow: false,
});
const approvalSliderConf = ref({
  isShow: false,
  title: '',
});
const approvalSliderDetail = ref<Partial<IPersonalWorkbenchListResponse> | null>(null);
const filterData = ref<FilterValue | IPersonalWorkbenchListQuery>({
  time_start: '',
  time_end: '',
  keyword: '',
  bk_app_code: '',
  applied_by: [],
  gateway_id: '',
  mcp_server_id: '',
  grant_dimension: '',
});
const expandableConfig = ref({
  expandColumn: false,
  expandedRowKeys: [] as number[],
  canExpand: (row: TableRowData) => {
    return ['resource'].includes(row.grant_dimension);
  },
});
const curAction = ref<IFomDataQuery>({
  status: '',
  ids: [],
  part_resource_ids: {},
});
const curPermission = ref<IPermission>({
  bk_app_code: '',
  grant_dimension: '',
  resources: [],
  selection: [],
  resource_ids: [],
  isSelectAll: true,
});
// 缓存上一个展开行
const lastExpandRow = ref<IPersonalWorkbenchUIState | TableRowData | null>(null);
const gatewayList = ref<IPersonalWorkbenchFilterOptionResponse[]>([]);
const mcpServerList = ref<IPersonalWorkbenchFilterOptionResponse[]>([]);
const childrenColumns = shallowRef<PrimaryTableProps['columns']>([
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

const isEnabledITSMApply = computed(() => featureFlagStore?.flags?.ENABLE_ITSM4_PERMISSION_APPLY);
const isGateway = computed(() => ['gateway'].includes(activeTab));
const isPending = computed(() => ['pending'].includes(applyStatus));
const isShowSelection = computed(() => isGateway.value && isPending.value);
// 批量审批dialog的title
const batchApplyDialogConfTitle = computed(() => {
  return t(
    '将对以下{permissionSelectListTemplate}个权限申请单进行审批',
    { permissionSelectListTemplate: selectedRows.value.length });
});
const approvalStatusMap = computed(() => isGateway.value ? APPROVAL_HISTORY_STATUS_MAP : APPROVAL_STATUS_MAP);
const approvalStatusList = computed(() =>
  Object.entries(approvalStatusMap.value)
    .map(([value, label]) => ({
      value,
      label,
    })).filter(item => applyStatus !== 'handled' || item.value !== 'pending'),
);
const tableColumns = computed(() => {
  const gatewayAppCodeColumn: PrimaryTableProps['columns'] = [
    {
      title: t('网关'),
      colKey: 'gateway_id',
      ellipsis: true,
      width: 200,
      fixed: 'left' as const,
      filter: {
        type: 'single' as const,
        showConfirmAndReset: true,
        popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
        list: gatewayList.value.map((item: IPersonalWorkbenchFilterOptionResponse) => ({
          label: item.name,
          value: item.id,
        })),
      },
      cell: (_: unknown, { row }: { row: TableRowData }) => {
        return row.gateway_name || row?.mcp_server?.gateway_name || '--';
      },
    },
    {
      title: t('蓝鲸应用ID'),
      colKey: 'bk_app_code',
      ellipsis: true,
    },
  ];

  const columns: PrimaryTableProps['columns'] = [
    {
      colKey: 'applied_by',
      title: t('申请人'),
      ellipsis: true,
      width: 160,
      cell: (_: unknown, { row }: { row: TableRowData }) => {
        if (!row?.applied_by) return '--';

        return featureFlagStore.isEnableDisplayName
          ? <span><bk-user-display-name user-id={row.applied_by} /></span>
          : <span>{row.applied_by}</span>;
      },
    },
    {
      title: t('申请时间'),
      colKey: 'applied_time',
      ellipsis: true,
      width: 220,
      cell: (_: unknown, { row }: { row: TableRowData }) => {
        return row?.applied_time || row?.created_time || '--';
      },
    },
    {
      colKey: 'approvers',
      title: t('审批人'),
      ellipsis: true,
      cell: (_: unknown, { row }: { row: TableRowData }) => {
        if (!row?.approvers?.length && !row?.handled_by) return '--';

        return (
          <div class="w-full">
            <RenderTagOverflow
              data={row.approvers || [row?.handled_by]}
              is-member
            />
          </div>
        );
      },
    },
    {
      title: t('审批状态'),
      colKey: 'status',
      ellipsis: true,
      filter: {
        type: 'single' as const,
        showConfirmAndReset: true,
        popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
        list: approvalStatusList.value.map(({ label, value }) => ({
          label,
          value,
        })),
      },
      cell: (_: unknown, { row }: { row: TableRowData }) => {
        const statusKey = row?.status as keyof typeof approvalStatusMap.value;
        const status = approvalStatusMap.value[statusKey] ?? '--';

        if (['pending'].includes(row.status)) {
          return (
            <div class="perm-apply-dot">
              <Loading class="mr-4px" loading size="mini" mode="spin" theme="primary" />
              {status}
            </div>
          );
        }
        else {
          return (
            <div class="perm-apply-dot">
              <span class={['mr-4px ag-dot', { [row.status]: row.status }]} />
              {status}
            </div>
          );
        }
      },
    },
    {
      title: t('操作'),
      colKey: 'operate',
      fixed: 'right' as const,
      width: isPending.value ? 200 : 80,
      cell: (_: unknown, { row }: { row: TableRowData }) => {
        const isItsm = isEnabledITSMApply.value && Boolean(row?.itsm_ticket_url) && Boolean(row?.itsm_ticket_id);

        if (isPending.value) {
          if (isItsm) {
            return (
              <Button
                text
                theme="primary"
                onClick={() => {
                  window.open(row?.itsm_ticket_url);
                }}
              >
                {t('跳转到 ITSM')}
              </Button>
            );
          }

          if (isGateway.value) {
            // 是否展开了资源行
            const isExpandResource = expandableConfig.value.expandedRowKeys.includes(row.id) && !['api'].includes(row.grant_dimension);

            // 当前行自己的选中数量
            const selectedLen = row.selection?.length ?? 0;
            const totalLen = row.resources?.length ?? 0;

            // 没展开 → 全部通过
            // 已展开未选中 → 全部通过
            if (!isExpandResource || (isExpandResource && selectedLen < 1)) {
              row.isSelectAll = true;
            }
            else {
              // 选中 == 总数 → 全部通过
              // 选中 != 总数 → 部分通过
              row.isSelectAll = (isExpandResource && selectedLen < 1) || (totalLen > 0 && selectedLen === totalLen);
            }

            // 展开了 + 一个都没选 → 才 disabled
            const disabled = isExpandResource && selectedLen === 0;

            return (
              <div class="flex">
                <Popover content={t('请选择资源')} disabled={!disabled}>
                  <Button
                    class="mr-8px"
                    theme="primary"
                    text
                    disabled={disabled}
                    onClick={(e: MouseEvent) => {
                      handleShowGatewayApprove(e, row);
                    }}
                  >
                    {row.isSelectAll ? t('全部通过') : t('部分通过')}
                  </Button>
                </Popover>
                <Button
                  theme="primary"
                  text
                  onClick={(e: MouseEvent) => {
                    handleShowGatewayReject(e, row);
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
                text
                theme="primary"
                class="mr-8px"
                onClick={(e: MouseEvent) => {
                  handleShowMcpApprove(row, 'approved', e);
                }}
              >
                { t('通过') }
              </Button>
              <Button
                text
                theme="primary"
                onClick={(e: MouseEvent) => {
                  handleShowMcpApprove(row, 'rejected', e);
                }}
              >
                { t('驳回') }
              </Button>
            </div>
          );
        }
        else {
          return (
            <Button
              text
              theme="primary"
              onClick={(e: MouseEvent) => {
                e?.stopPropagation();
                if (isItsm) {
                  window.open(row?.itsm_ticket_url);
                  return;
                }
                approvalSliderConf.value = {
                  isShow: true,
                  title: `${t('申请应用：')}${row.bk_app_code}`,
                };
                approvalSliderDetail.value = { ...row } as IPersonalWorkbenchUIState;
              }}
            >
              {t('详情')}
            </Button>
          );
        }
      },
    },
  ].filter((col) => {
    if (['applied_by'].includes(col.colKey) && ['applied'].includes(applyStatus)) {
      return false;
    }

    if (['handled_by'].includes(col.colKey) && !['applied'].includes(applyStatus)) {
      return false;
    }

    return true;
  });

  const gatewayColumns: PrimaryTableProps['columns'] = [
    ...gatewayAppCodeColumn!,
    {
      title: t('授权维度'),
      colKey: 'grant_dimension',
      ellipsis: true,
      width: 120,
      filter: {
        type: 'single' as const,
        showConfirmAndReset: true,
        popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
        list: [
          {
            label: t('按网关'),
            value: 'api',
          },
          {
            label: t('按资源'),
            value: 'resource',
          },
        ],
      },
      cell: (_: unknown, { row }: { row: TableRowData }) => {
        if (['resource'].includes(row.grant_dimension)) {
          return (
            <div class="flex items-center">
              <ag-icon
                name={row.isExpand ? 'down-shape' : 'right-shape'}
                size="10"
                class="mr-4px"
              />
              {`${row.grant_dimension_display} (${row.resources?.length || 0})`}
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
      width: 100,
    },
    {
      colKey: 'reason',
      title: t('申请理由'),
      ellipsis: true,
      width: 100,
    },
    ...columns!,
  ];

  const mcpColumns: PrimaryTableProps['columns'] = [
    ...gatewayAppCodeColumn!,
    {
      title: 'MCP Server',
      colKey: 'mcp_server_id',
      ellipsis: true,
      filter: {
        type: 'single' as const,
        showConfirmAndReset: true,
        popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
        list: mcpServerList.value.map((item: IPersonalWorkbenchFilterOptionResponse) => ({
          label: item.name,
          value: item.id,
        })),
      },
      cell: (_: unknown, { row }: { row: TableRowData }) => {
        return row?.mcp_server?.name || '--';
      },
    },
    ...columns!,
  ];

  return isGateway.value ? gatewayColumns : mcpColumns;
});

const getList = () => {
  const params = {
    ...filterData.value,
    applied_by: filterData.value.applied_by.join(),
  };
  return tableRef.value?.fetchData(filterSimpleEmpty(params), { resetPage: true });
};

const getTableData = async (params: {
  offset: number
  limit: number
}) => {
  // 触发表格组件watch
  settings.value = null;
  const queryParams: IPersonalWorkbenchListQuery = {
    ...params,
    ...filterData.value,
    applied_by: filterData.value.applied_by.join(),
  };
  const res = await remoteMethod?.(filterSimpleEmpty(queryParams));
  return res ?? {
    count: 0,
    results: [],
  };
};

const fetchGatewayFilterOptions = async () => {
  try {
    const requestList = isGateway.value
      ? getGatewayFilterOptions({ type: applyStatus })
      : getMcpGatewayFilterOptions({ type: applyStatus });

    const res = await requestList;
    gatewayList.value = Array.isArray(res) ? res : [];
  }
  catch {
    gatewayList.value = [];
  }
};

const fetchMcpServerFilterOptions = async () => {
  try {
    const res = await getMcpServerFilterOptions({ type: applyStatus });
    mcpServerList.value = res ?? [];
  }
  catch {
    mcpServerList.value = [];
  }
};
fetchMcpServerFilterOptions();

// 批量网关审批提交
const handleGatewayApproveReject = async () => {
  try {
    let params = { ...curAction.value };
    const { isSelectAll, selection } = curPermission.value;

    const id = params?.ids?.[0] || '';

    // 部分通过逻辑
    if (
      ['approved'].includes(params.status as IApplyStatus)
      && expandableConfig.value.expandedRowKeys.includes(id as number)
      && !!selection?.length
      && !isSelectAll
    ) {
      params = Object.assign(params, {
        status: 'partial_approved',
        part_resource_ids: { [id]: selection?.map((item: IResources) => item.id) },
      });
    }
    let gatewayIdList: number[] = [curAction.value.gateway_id!];

    if (batchApplyDialogConf.value.isShow) {
      gatewayIdList = selectedRows.value.map(item => item.gateway_id ?? 0);
    }

    const validUniqueIds = [...new Set(gatewayIdList.filter(id => id && !isNaN(id)))];

    const requestPromises = validUniqueIds.map(agId =>
      updatePermissionStatus(agId as number, params as IAppPermissionApplyApprovalInputSLZ),
    );

    await Promise.all(requestPromises);

    batchApplyDialogConf.value.isShow = false;
    applyActionDialogConf.value.isShow = false;

    Message({
      message: t('操作成功'),
      theme: 'success',
    });

    handleClearSelection();
    getList();
  }
  catch (e: unknown) {
    const err = e as { error?: { message?: string } };
    Message({
      message: err?.error?.message,
      theme: 'error',
    });
  }
};

//  MCP审批提交
const handleMcpApproveReject = async () => {
  try {
    applyActionDialogConf.value.isLoading = true;

    const { id, gateway_id, mcp_server_id } = curAction.value;

    await updateMcpPermissions(
      gateway_id as number,
      mcp_server_id as number,
      id as number,
      curAction.value as IMCPServerAppPermissionApplyUpdateInputSLZ,
    );

    Message({
      message: t('操作成功'),
      theme: 'success',
    });
    getList();
    applyActionDialogConf.value.isShow = false;
  }
  catch (e: unknown) {
    const err = e as { error?: { message?: string } };
    Message({
      message: err?.error?.message,
      theme: 'error',
    });
  }
  finally {
    applyActionDialogConf.value.isLoading = false;
  }
};

const handleFilterChange: PrimaryTableProps['onFilterChange'] = (filterItem: FilterValue) => {
  filterData.value = { ...filterItem };
};

const handleRowClick = async ({ e, row }: {
  e: MouseEvent
  row: TableRowData
}) => {
  e.stopPropagation();

  if (!row?.grant_dimension?.includes('resource')) return;

  const newIsExpand = !row.isExpand;

  row.isLoading = true;

  // 重置上一个展开行
  if (lastExpandRow.value && lastExpandRow.value !== row) {
    Object.assign(lastExpandRow.value, {
      isExpand: false,
      selection: [],
      resource_ids: [],
    });
  }

  // 更新当前行状态
  row.isExpand = newIsExpand;
  expandableConfig.value.expandedRowKeys = newIsExpand ? [Number(row.id)] : [];
  lastExpandRow.value = newIsExpand ? row : null;

  // 初始化选中数据
  if (newIsExpand) {
    row.selection ??= [];
    row.resource_ids = row.selection.map((item: IResources) => item.id) as number[];
  }
  else {
    Object.assign(row, {
      selection: [],
      resource_ids: [],
    });
  }

  setTimeout(() => {
    row.isLoading = false;
  }, 300);
};

const handleSelectionChange = ({
  selections,
  selectionsRowKeys,
}: {
  selections: TableRowData[]
  selectionsRowKeys: (string | number)[]
}) => {
  selectedRows.value = selections as IPersonalWorkbenchUIState[];
  selectedRowKeys.value = selectionsRowKeys;
};

const handleChildSelectionChange = (
  row: TableRowData,
  {
    selections,
    selectionsRowKeys,
  }: {
    selections: TableRowData[]
    selectionsRowKeys: (string | number)[]
  }) => {
  // 保存当前行选中项
  row.selection = selections as IResources[];
  row.resource_ids = selectionsRowKeys;

  // 是否全选
  const total = row.resources?.length || 0;
  row.isSelectAll = total > 0 && selections.length === total;

  // 更新全局审批数据
  curPermission.value = {
    ...curPermission.value,
    selection: row.selection,
    resource_ids: selectionsRowKeys as number[],
    isSelectAll: row.isSelectAll,
  };
};

// 全部通过/部分通过 Dialog
const handleShowGatewayApprove = (e: MouseEvent, row: TableRowData) => {
  e.stopPropagation();
  curPermission.value = row as IPersonalWorkbenchUIState;
  curAction.value = {
    ids: [row.id],
    gateway_id: row.gateway_id as number,
    status: 'approved',
    comment: t('全部通过'),
    part_resource_ids: {},
  };
  if (!curPermission.value.isSelectAll) {
    curAction.value.comment = t('部分通过');
  }
  applyActionDialogConf.value = Object.assign(applyActionDialogConf.value, {
    isShow: true,
    title: t('通过申请'),
  });
};

// 全部驳回 Dialog
const handleShowGatewayReject = (e: MouseEvent, row: TableRowData) => {
  e.stopPropagation();
  curPermission.value = row as IPersonalWorkbenchUIState;
  curAction.value = {
    ids: [row.id!],
    gateway_id: row.gateway_id as number,
    status: 'rejected',
    comment: t('全部驳回'),
    part_resource_ids: {},
  };
  applyActionDialogConf.value = Object.assign(applyActionDialogConf.value, {
    isShow: true,
    title: t('驳回申请'),
  });
};

// Mcp审批 Dialog
const handleShowMcpApprove = (row: TableRowData, status: string, e: MouseEvent) => {
  e?.stopPropagation();
  curAction.value = {
    id: row.id as number,
    mcp_server_id: row?.mcp_server?.id as number,
    gateway_id: row?.mcp_server?.gateway_id as number,
    status: status as IApplyStatus,
    comment: status === 'approved' ? t('通过') : t('驳回'),
  };
  if (status === 'approved') {
    applyActionDialogConf.value.title = t('通过申请');
  }
  else {
    applyActionDialogConf.value.title = t('驳回申请');
  }
  applyActionDialogConf.value.isShow = true;
};

// 网关全部通过/部分通过/全部驳回、MCP审批
const handleSubmitApprove = () => {
  if (isGateway.value) {
    handleGatewayApproveReject();
  }
  else {
    handleMcpApproveReject();
  }
};

// 全部通过
const handleApprovedPermission = () => {
  curAction.value = Object.assign(curAction.value, {
    status: 'approved',
    ids: selectedRows.value.map((permission: IPersonalWorkbenchUIState) => permission.id),
  });
  handleGatewayApproveReject();
};

// 全部驳回
const handleRejectedPermission = () => {
  curAction.value = Object.assign(curAction.value, {
    status: 'rejected',
    ids: selectedRows.value.map((permission: IPersonalWorkbenchUIState) => permission.id),
  });
  handleGatewayApproveReject();
};

// 批量审批
const handleBatchApproval = () => {
  curAction.value = Object.assign({}, {
    ids: [] as number[],
    status: '' as IApplyStatus,
    comment: '',
    part_resource_ids: {} as Record<string, unknown>,
  });
  batchApplyDialogConf.value.isShow = true;
};

const handleClearSelection = () => {
  tableRef.value?.handleResetSelection();
  selectedRows.value = [];
  selectedRowKeys.value = [];
  curPermission.value = Object.assign(curPermission.value, {
    selection: [],
    resource_ids: [],
  });
};

const handleClearFilter = () => {
  filterData.value = Object.assign(filterData.value ?? {}, {
    time_start: '',
    time_end: '',
    keyword: '',
    bk_app_code: '',
    applied_by: [],
    gateway_id: '',
    mcp_server_id: '',
    grant_dimension: '',
  });
  basicFormRef.value?.handleResetFormData();
  handleClearSelection();
};

const getRowClass = ({ row }: { row: TableRowData }) => {
  if (row?.grant_dimension?.includes('resource')) {
    return 'hover:cursor-pointer';
  }
  return '';
};

watch(() => filterData, () => {
  tableEmptyType.value = Object.keys(filterSimpleEmpty(filterData.value))?.length > 0 ? 'searchEmpty' : 'empty';
  getList();
}, { deep: true });

watch(isGateway, () => {
  fetchGatewayFilterOptions();
}, { immediate: true });

defineExpose({
  handleClearFilter,
});
</script>

<style lang="scss" scoped>
.personal-workbench-table {
  box-sizing: border-box;

  &.pending {

    :deep(.t-table__th-status) {

      .t-table__filter-icon-wrap {
        display: none;
      }
    }
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

:deep(.is-exist-member) {

  .tag-input-item {
    display: none !important;
  }
}
 </style>
