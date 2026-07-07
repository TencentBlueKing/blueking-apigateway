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
  <div class="page-wrapper-padding">
    <div class="permission">
      <BkTab
        v-model:active="filterData.state"
        type="unborder-card"
        class="tab"
        @change="handleTabChange"
      >
        <BkTabPanel
          v-for="item of panels"
          :key="item.name"
          :name="item.name"
        >
          <template #label>
            <div class="flex items-center">
              {{ item.label }}
              <div
                v-if="item.name === 'unprocessed' && lastCount > 0"
                class="count"
              >
                <div
                  class="text"
                  :class="[filterData.state === item.name ? 'on' : 'off']"
                >
                  {{ lastCount }}
                </div>
              </div>
            </div>
          </template>
        </BkTabPanel>
      </BkTab>

      <div class="main">
        <div class="mcp-permission-header">
          <BkForm
            class="flex-grow-1 flex-wrap permission-filter-form"
          >
            <BkFormItem
              label="MCP Server"
              label-width="110"
            >
              <BkSelect
                v-model="filterData.mcp_server_id"
                clearable
                filterable
                :placeholder="t('请选择 MCP Server')"
                :scroll-loading="scrollLoading"
                :remote-method="handleMcpServerSearch"
                @toggle="handleMcpToggle"
                @scroll-end="handleMcpServerScrollEnd"
              >
                <BkOption
                  v-for="option of mcpList"
                  :id="option.id"
                  :key="option.id"
                  :name="renderMcpDisplayName(option)"
                />
              </BkSelect>
            </BkFormItem>
            <BkFormItem
              :label="t('蓝鲸应用ID')"
              label-width="140"
            >
              <BkInput
                v-model="filterData.bk_app_code"
                clearable
                type="search"
                :placeholder="t('请输入应用ID')"
              />
            </BkFormItem>
            <BkFormItem
              v-if="!featureFlagStore.isTenantMode && !isAppPerm"
              :label="t('申请人')"
            >
              <BkSelect
                v-model="filterData.applied_by"
                clearable
                :placeholder="t('请选择用户')"
              >
                <BkOption
                  v-for="option of applicantList"
                  :id="option"
                  :key="option"
                  :name="option"
                />
              </BkSelect>
            </BkFormItem>
          </BkForm>

          <div
            v-if="isAppPerm"
            class="export-dropdown"
          >
            <AgDropdown
              class="flex-shrink-0 mr-0!"
              placement="bottom"
              :dropdown-list="exportDropData"
              :is-disabled="!tableData.length"
              :text="t('导出')"
              @on-change="handleExportApp"
            />
          </div>
        </div>

        <AgTable
          ref="tableRef"
          v-model:table-data="tableData"
          v-model:settings="settings"
          show-settings
          :filter-value="filterData"
          :api-method="getTableData"
          :columns="tableColumns"
          :cache-identifier="cacheIdentifier"
          :no-search-fields="['state']"
          :table-empty-type="tableEmptyType"
          @filter-icon-click="handleFilterIconClick"
          @filter-change="handleFilterChange"
          @sort-change="handleSortChange"
          @clear-filter="handleClearFilter"
        />
      </div>
    </div>
  </div>

  <BkDialog
    theme="primary"
    :width="600"
    :quick-close="false"
    :header-position="'left'"
    :title="applyActionDialogConf.title"
    :is-show="applyActionDialogConf.isShow"
    @closed="applyActionDialogConf.isShow = false"
  >
    <BkForm
      ref="approveForm"
      :label-width="90"
      :model="curAction"
      :rules="rules"
      class="mt-10px mr-20px mb-30px"
    >
      <BkFormItem
        :label="t('备注')"
        required
        :property="'comment'"
      >
        <BkInput
          v-model="curAction.comment"
          type="textarea"
          :placeholder="t('请输入备注')"
          :rows="4"
          :maxlength="100"
        />
      </BkFormItem>
    </BkForm>
    <template #footer>
      <BkButton
        theme="primary"
        :disabled="applyActionDialogConf.isLoading"
        :loading="applyActionDialogConf.isLoading"
        class="mr-8px"
        @click="handleSubmitApprove"
      >
        {{ t('确定') }}
      </BkButton>
      <BkButton @click="applyActionDialogConf.isShow = false">
        {{ t('取消') }}
      </BkButton>
    </template>
  </BkDialog>

  <ApprovalDetailSlider
    v-model:approval-slider-conf="approvalSliderConf"
    :approval-detail="approvalSliderDetail"
  />
</template>

<script lang="tsx" setup>
import { Button, Form, Loading, Message, PopConfirm } from 'bkui-vue';
import { cloneDeep, debounce } from 'lodash-es';
import type { FilterValue, PrimaryTableProps, SortInfo, TableRowData } from '@blueking/tdesign-ui';
import type { IDropList, IFormMethod, ITableEmptyType, ITableMethod } from '@/types/common';
import { AUTHORIZATION_APPLICATION_OPERATE_TYPE } from '@/constants';
import { useFeatureFlag } from '@/stores';
import { useMcpPermission } from '@/hooks';
import {
  type IPermissionApprovalAction,
  type IPermissionApprovalFilterValue,
  getMcpAppPermissionApply,
  getMcpPermissions,
  getMcpPermissionsApplicant,
  updateMcpPermissions,
} from '@/services/source/mcp-market.ts';
import { getServers } from '@/services/source/mcp-server';
import type { IGatewaysMcpServersAppPermissionApplyListQuery } from '@/services/types/query/gateways.ts';
import type { IMCPServerAppPermissionApplyListOutput, IMCPServerListOutput } from '@/services/types/responses/gateways.ts';
import { filterSimpleEmpty } from '@/utils/filterEmptyValues';
import ApprovalDetailSlider from '@/views/mcp-server/permission/components/ApprovalDetailSlider.vue';
import AgDropdown from '@/components/ag-dropdown/Index.vue';
import AgTable from '@/components/ag-table/Index.vue';

interface IProps { gatewayId?: number }

const { gatewayId = 0 } = defineProps<IProps>();

const { t } = useI18n();
const route = useRoute();
const featureFlagStore = useFeatureFlag();
const {
  exportDropData,
  getExportDropData,
  handleDelete,
  handleExport,
} = useMcpPermission();

const tableRef = useTemplateRef<InstanceType<typeof AgTable> & ITableMethod>('tableRef');
const tableEmptyType = ref<ITableEmptyType>('empty');
const filterData = ref<FilterValue | IPermissionApprovalFilterValue>({
  bk_app_code: '',
  applied_by: '',
  order_by: '',
  mcp_server_id: '',
  state: 'unprocessed',
});
const scrollLoading = ref(false);
const mcpServerName = ref('');
const defaultPagination = ref({
  limit: 10,
  current: 1,
  count: 0,
  hasNoMore: false,
});
const mcpServerPagination = ref(cloneDeep(defaultPagination.value));
const tableData = ref([]);
const settings = ref(null);
const lastCount = ref(0);
const panels = ref([
  {
    name: 'unprocessed',
    label: t('待审批'),
  },
  {
    name: 'processed',
    label: t('已审批'),
  },
  {
    name: 'appPerm',
    label: t('应用权限'),
  },
]);
const statusMap = reactive({
  approved: t('通过'),
  rejected: t('驳回'),
  pending: t('未审批'),
});
const mcpList = ref<IMCPServerListOutput[]>([]);
const applicantList = ref<string[]>([]);
const approveForm = ref<InstanceType<typeof Form> & IFormMethod>();
const applyActionDialogConf = reactive({
  isShow: false,
  isLoading: false,
  title: t('通过申请'),
});
const approvalSliderConf = ref({
  isShow: false,
  title: '',
});
const approvalSliderDetail = ref<IMCPServerAppPermissionApplyListOutput>({
  id: 0,
  bk_app_code: '',
  applied_by: '',
  applied_time: '',
  status: '',
  itsm_ticket_id: '',
  itsm_ticket_url: '',
  mcp_server: {
    id: 0,
    name: '',
    title: '',
  },
});
const curAction = ref<IPermissionApprovalAction>({
  id: 0,
  mcp_server_id: '',
  status: '',
  comment: '',
});
const cacheIdentifier = ref('permission-apply-unprocessed');

let filterTimer: number | null = null;
const filterFields = ['bk_app_code', 'mcp_server_id', 'grant_type'] as string[];
const rules = {
  comment: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
};

const tableColumns = computed(() => {
  const grantTypeColumn: PrimaryTableProps['columns'] = isAppPerm.value
    ? [{
      title: t('授权类型'),
      colKey: 'grant_type',
      ellipsis: true,
      filter: {
        type: 'single',
        showConfirmAndReset: true,
        popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
        list: AUTHORIZATION_APPLICATION_OPERATE_TYPE.map((item: Record<string, string>) => ({
          label: item.name,
          value: item.id,
        })),
      },
      cell: (_: unknown, { row }: { row: TableRowData }) => {
        const grantTypeText = AUTHORIZATION_APPLICATION_OPERATE_TYPE.find(item => item.id === row.grant_type)?.name ?? '--';
        return (
          <span>
            { grantTypeText }
          </span>
        );
      },
    }]
    : [];
  const handledByEffectiveColumn: PrimaryTableProps['columns'] = isAppPerm.value
    ? [{
      title: t('操作人'),
      colKey: 'handled_by',
      cell: (_: unknown, { row }: { row: TableRowData }) => renderDisplayNameColumn(row.handled_by),
    },
    {
      title: t('生效时间'),
      colKey: 'effective_time',
      ellipsis: true,
      sorter: true,
      width: 260,
    }]
    : [];
  const appliedTimeColumn: PrimaryTableProps['columns'] = !isAppPerm.value
    ? [{
      title: t('申请时间'),
      colKey: 'applied_time',
      ellipsis: true,
      width: 260,
    }]
    : [];
  const approvalColumn: PrimaryTableProps['columns'] = !isAppPerm.value
    ? [{
      title: t('审批状态'),
      colKey: 'status',
      ellipsis: true,
      cell: (_: unknown, { row }: { row: TableRowData }) => {
        const statusLabel = statusMap[row?.status as keyof typeof statusMap];

        if (row.status === 'pending') {
          return (
            <div
              class="perm-apply-dot"
            >
              <Loading
                class="mr-4px"
                loading
                size="mini"
                mode="spin"
                theme="primary"
              />
              { statusLabel }
            </div>
          );
        }

        return (
          <div class="perm-apply-dot">
            <span class={['dot', row?.status]} />
            {statusLabel}
          </div>
        );
      },
    }]
    : [];

  const columns: PrimaryTableProps['columns'] = [
    {
      title: 'MCP Server',
      colKey: 'mcp_server_id',
      fixed: 'left' as const,
      ellipsis: true,
      className: 'need-filter-icon-handler',
      width: 360,
      filter: {
        type: 'single',
        showConfirmAndReset: true,
        popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper mcp-server-filter-popup' },
        list: mcpList.value.map((item: IMCPServerListOutput) => ({
          label: renderMcpDisplayName(item),
          value: item.id,
        })),
      },
      cell: (_: unknown, { row }: { row: TableRowData }) => {
        return row?.mcp_server?.name;
      },
    },
    {
      title: t('蓝鲸应用ID'),
      colKey: 'bk_app_code',
      ellipsis: true,
    },
    ...grantTypeColumn,
    {
      title: t('申请人'),
      colKey: 'applied_by',
      cell: (_: unknown, { row }: { row: TableRowData }) => renderDisplayNameColumn(row.applied_by),
    },
    ...appliedTimeColumn,
    ...handledByEffectiveColumn,
    ...approvalColumn,
    {
      title: t('操作'),
      colKey: 'operate',
      fixed: 'right' as const,
      cell: (_: unknown, { row }: { row: TableRowData }) => {
        if (isAppPerm.value) {
          return (
            <PopConfirm
              placement="top"
              trigger="click"
              content={t('确认删除？')}
              onConfirm={async () => {
                await handleDelete(gatewayId, row?.mcp_server?.id, row?.id);
                getList();
              }}
            >
              <Button
                text
                theme="primary"
              >
                { t('删除') }
              </Button>
            </PopConfirm>
          );
        }

        const isItsm = isEnabledITSMApply.value && Boolean(row?.itsm_ticket_url) && Boolean(row?.itsm_ticket_id);

        if (filterData.value.state === 'unprocessed') {
          if (isItsm) {
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

          return (
            <div>
              <Button
                text
                theme="primary"
                class="mr-8px"
                onClick={() => handleApprove(row, 'approved')}
              >
                { t('通过') }
              </Button>
              <Button
                text
                theme="primary"
                onClick={() => handleApprove(row, 'rejected')}
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
              onClick={() => {
                if (isItsm) {
                  window.open(row?.itsm_ticket_url);
                  return;
                }
                approvalSliderConf.value = {
                  isShow: true,
                  title: `${t('申请应用：')}${row.bk_app_code}`,
                };
                approvalSliderDetail.value = { ...row } as IMCPServerAppPermissionApplyListOutput;
              }}
            >
              {t('详情')}
            </Button>
          );
        }
      },
    },
  ];

  return columns;
});
const isEnabledITSMApply = computed(() => featureFlagStore?.flags?.ENABLE_ITSM4_PERMISSION_APPLY);
// 应用权限tab
const isAppPerm = computed(() => filterData.value.state.includes('appPerm'));

const getList = () => {
  const params = { ...filterData.value };
  if (isAppPerm.value) {
    delete params.state;
  }
  tableRef.value?.fetchData(filterData.value, { resetPage: true });
};

const getTableData = async (params: {
  offset: number
  limit: number
}) => {
  // 触发表格组件监听刷新
  settings.value = null;

  const { state } = filterData.value;

  // 定义 tab 与对应接口的映射
  const tabApiMap = {
    processed: getMcpAppPermissionApply,
    unprocessed: getMcpAppPermissionApply,
    appPerm: getMcpPermissions,
  } as const;

  // 获取当前 tab 对应的请求方法
  const remoteApi = tabApiMap[state as keyof typeof tabApiMap];
  if (!remoteApi) {
    return {
      count: 0,
      results: [],
    };
  }

  // 过滤空值参数
  const queryParams: IGatewaysMcpServersAppPermissionApplyListQuery = {
    ...params,
    ...filterSimpleEmpty(filterData.value),
  };

  if (isAppPerm.value) {
    delete queryParams.state;
  }

  const res = await remoteApi(gatewayId, queryParams);

  // 未处理状态记录数量
  if (state === 'unprocessed') {
    lastCount.value = res.count ?? 0;
  }

  return res ?? {
    count: 0,
    results: [],
  };
};

const getMcpList = async (customLimit?: number) => {
  // 如果是自定义limit, 重置分页参数
  if (customLimit) {
    mcpServerPagination.value = {
      ...defaultPagination.value,
      limit: customLimit,
    };
  }
  const { hasNoMore, current, limit } = mcpServerPagination.value;
  scrollLoading.value = true;

  if (hasNoMore) {
    scrollLoading.value = false;
    return;
  }

  try {
    const params = {
      limit,
      offset: limit * (current - 1),
      keyword: mcpServerName.value,
    };
    const res = await getServers(gatewayId, filterSimpleEmpty(params));
    const { results = [], count = 0 } = res ?? {};
    mcpList.value = current === 1 ? results : [...mcpList.value, ...results];
    mcpServerPagination.value = {
      ...mcpServerPagination.value,
      count,
      hasNoMore: mcpList.value.length >= count,
      current: current + 1,
    };
  }
  catch {
    mcpServerPagination.value = cloneDeep(defaultPagination.value);
    mcpList.value = [];
  }
  finally {
    scrollLoading.value = false;
  }
};
getMcpList();

const getApplicant = async () => {
  // 如果是多租户模式或者应用权限tab，不展示申请人筛选
  if (featureFlagStore.isTenantMode || isAppPerm.value) {
    return;
  }
  const response = await getMcpPermissionsApplicant(
    gatewayId,
    filterData.value.mcp_server_id || '-',
    {
      state: filterData.value.state,
    } as IGatewaysMcpServersAppPermissionApplyListQuery,
  );
  applicantList.value = response?.applicants || [];
};

const renderMcpDisplayName = (option: Record<string, string>) => {
  return option?.title ? `${option.title} (${option.name})` : option.name;
};

const renderDisplayNameColumn = (value: string) => {
  return featureFlagStore.isEnableDisplayName && Boolean(value)
    ? <span><bk-user-display-name user-id={value} /></span>
    : <span>{value || '--'}</span>;
};

// 搜索McpServer列表
const handleMcpServerSearch = debounce((value: string) => {
  mcpServerName.value = value;
  mcpServerPagination.value = cloneDeep(defaultPagination.value);
  getMcpList();
}, 200);

// 滚动加载MCP Server
const handleMcpServerScrollEnd = debounce(() => {
  const { hasNoMore } = mcpServerPagination.value;
  if (hasNoMore) return;
  getMcpList();
}, 200);

const handleExportApp = (payload: IDropList) => {
  handleExport(gatewayId, payload, filterData);
};

const handleTabChange = (name: string) => {
  if (name === filterData.value.state) {
    return;
  }
  cacheIdentifier.value = `permission-apply-${name}`;
  filterData.value.state = name;
  handleClearFilter();
  getApplicant();
};

const handleFilterIconClick = () => {
  mcpServerName.value = '';
  if (filterTimer) clearTimeout(filterTimer);

  // 因为popup执行机制是异步的，所以延迟执行, 这里适配表格filter无法滚动加载和搜索未抛出事件
  filterTimer = setTimeout(() => {
    const filterPopup = document.querySelector('.mcp-server-filter-popup');

    if (filterPopup) {
      const MCP_FILTER_ALL_LIMIT = 10000;
      const { count } = mcpServerPagination.value;
      const totalCount = Math.max(count, MCP_FILTER_ALL_LIMIT);

      getMcpList(totalCount);
    }

    filterTimer = null;
  }, 200);
};

const handleFilterChange: PrimaryTableProps['onFilterChange'] = (filterItem: FilterValue) => {
  filterData.value = { ...filterItem };
};

const handleSortChange: PrimaryTableProps['onSortChange'] = (sort) => {
  const sortData = sort as SortInfo;
  if (sortData) {
    const { sortBy: colKey, descending } = sortData;
    filterData.value.order_by = descending ? `-${colKey}` : colKey;
  }
  else {
    filterData.value.order_by = '';
  }
  getList();
};

const handleMcpToggle = (value: boolean) => {
  if (value) {
    mcpServerName.value = '';
    getMcpList(10);
  }
};

const handleClearFilter = () => {
  filterData.value = {
    ...filterData.value,
    bk_app_code: '',
    applied_by: '',
    order_by: '',
    mcp_server_id: '',
  };
};

const handleApprove = (row: TableRowData, status: string) => {
  curAction.value = {
    id: row.id,
    mcp_server_id: row.mcp_server.id,
    status: status as 'approved' | 'rejected',
    comment: status === 'approved' ? t('通过') : t('驳回'),
  };
  if (status === 'approved') {
    applyActionDialogConf.title = t('通过申请');
  }
  else {
    applyActionDialogConf.title = t('驳回申请');
  }
  applyActionDialogConf.isShow = true;
};

const handleSubmitApprove = async () => {
  try {
    applyActionDialogConf.isLoading = true;

    await approveForm.value?.validate();
    await updateMcpPermissions(
      gatewayId,
      curAction.value.mcp_server_id as number,
      curAction.value.id,
      curAction.value as IPermissionApprovalAction,
    );
    Message({
      message: t('操作成功'),
      theme: 'success',
    });
    getList();
    applyActionDialogConf.isShow = false;
  }
  catch (e: any) {
    Message({
      message: e?.error?.message,
      theme: 'error',
    });
  }
  finally {
    applyActionDialogConf.isLoading = false;
  }
};

watch(() => route.query.serverId as string, (value: string) => {
  if (value) {
    filterData.value.mcp_server_id = Number(value);
  }
}, {
  immediate: true,
});

watch(
  () => filterData.value.mcp_server_id,
  () => {
    getExportDropData(filterFields, filterData);
    getApplicant();
    filterData.value.applied_by = '';
    tableEmptyType.value = Boolean(filterData.value.mcp_server_id) ? 'searchEmpty' : 'empty';
    getList();
  },
  { immediate: true },
);

watch(
  () => [filterData.value.bk_app_code, filterData.value.applied_by],
  () => {
    getExportDropData(filterFields, filterData);
    getList();
  },
  { immediate: true },
);
</script>

<style lang="scss" scoped>
.permission {
  background-color: #ffffff;
  border-radius: 2px;
  box-shadow: 0 2px 4px 0 #1919290d;

  .tab {
    padding-left: 24px;

    :deep(.bk-tab-header-nav) {

       .bk-tab-header-item {

        &:nth-of-type(2) {
          padding-left: 4px;
        }
      }
    }
  }

  .main {
    padding: 6px 24px 42px;
  }
}

.count {
  display: flex;
  width: 20px;

  .text {
    padding: 2px 8px;
    margin-left: 8px;
    font-size: 12px;
    line-height: 12px;
    border-radius: 8px;

    &.on {
      color: #3A84FF;
      background: #E1ECFF;
    }

    &.off {
      color: #979ba5;
      background-color: #f0f1f5;
    }
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
      background: #e6f6eb;
      border: 1px solid #43c472;
    }

    &.rejected {
      background: #FFE6E6;
      border: 1px solid #EA3636;
    }
  }
}

:deep(.mcp-permission-header) {
  display: grid;
  align-items: flex-start;
  grid-template-columns: repeat(3, 1fr);
  column-gap: 24px;
  flex-wrap: wrap;

  .permission-filter-form {
    display: contents;

    .bk-form-item {
      min-width: 230px;
      margin-bottom: 24px;
    }
  }

  .export-dropdown {
    grid-column: 3;
    grid-row: 1;
    text-align: right;
  }
}
</style>
