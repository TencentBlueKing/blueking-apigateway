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
          v-for="item in panels"
          :key="item.name"
          :name="item.name"
        >
          <template #label>
            <div class="flex items-center">
              {{ item.label }}
              <div class="count">
                <div
                  v-if="item.name === 'unprocessed' && lastCount > 0"
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
        <div class="search-wrapper">
          <BkForm class="flex">
            <BkFormItem
              :label="t('蓝鲸应用ID')"
              class="mb-20px flex-grow-1"
              label-width="100"
              label-position="left"
            >
              <BkInput
                v-model="filterData.bk_app_code"
                clearable
                type="search"
                :placeholder="t('请输入应用ID')"
              />
            </BkFormItem>
            <BkFormItem
              label="MCP Server"
              class="mb-20px flex-grow-1"
              label-width="140"
            >
              <BkSelect
                v-model="filterData.mcp_server_id"
                clearable
              >
                <BkOption
                  v-for="option of mcpList"
                  :id="option.id"
                  :key="option.id"
                  :name="option.name"
                />
              </BkSelect>
            </BkFormItem>
            <BkFormItem
              v-if="!featureFlagStore.isTenantMode"
              :label="t('申请人')"
              class="mb-20px flex-grow-1"
              label-width="100"
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
        </div>

        <AgTable
          ref="tableRef"
          v-model:table-data="tableData"
          v-model:settings="settings"
          show-settings
          :filter-value="filterData"
          :api-method="getTableData"
          :columns="tableColumns"
          :no-search-fields="['state']"
          :table-empty-type="tableEmptyType"
          @filter-change="handleFilterChange"
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
</template>

<script lang="tsx" setup>
import { Button, Loading, Message } from 'bkui-vue';
import type { FilterValue, PrimaryTableProps, TableRowData } from '@blueking/tdesign-ui';
import type { ITableEmptyType, ITableMethod } from '@/types/common';
import { useFeatureFlag } from '@/stores';
import {
  getMcpAppPermissionApply,
  getMcpPermissionsApplicant,
  updateMcpPermissions,
} from '@/services/source/mcp-market.ts';
import { getServers } from '@/services/source/mcp-server';
import type { IGatewaysMcpServersAppPermissionApplyListQuery } from '@/services/types/query/gateways.ts';
import { filterSimpleEmpty } from '@/utils/filterEmptyValues';
import EditMember from '@/views/basic-info/components/EditMember.vue';
import TenantUserSelector from '@/components/tenant-user-selector/Index.vue';
import AgTable from '@/components/ag-table/Index.vue';

interface IProps { gatewayId?: number }

interface IFilterValue {
  bk_app_code: string
  applied_by: string
  mcp_server_id: string | number
  state: string
}

interface IApplyAction {
  id: number
  mcp_server_id: number | string
  status: 'approved' | 'rejected' | ''
  comment: string
}

const { gatewayId = 0 } = defineProps<IProps>();

const { t } = useI18n();
const featureFlagStore = useFeatureFlag();
const route = useRoute();

const tableRef = useTemplateRef<InstanceType<typeof AgTable> & ITableMethod>('tableRef');
const tableEmptyType = ref<ITableEmptyType>('empty');
const filterData = ref<FilterValue | IFilterValue>({
  bk_app_code: '',
  applied_by: '',
  mcp_server_id: '',
  state: 'unprocessed',
});
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
]);
const statusMap = reactive({
  approved: t('通过'),
  rejected: t('驳回'),
  pending: t('未审批'),
});
const mcpList = ref<any[]>([]);
const applicantList = ref<string[]>([]);
const approveForm = ref();
const applyActionDialogConf = reactive({
  isShow: false,
  isLoading: false,
  title: t('通过申请'),
});
const curAction = ref<IApplyAction>({
  id: 0,
  mcp_server_id: '',
  status: '',
  comment: '',
});

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
  const columns: PrimaryTableProps['columns'] = [
    {
      title: t('蓝鲸应用ID'),
      colKey: 'bk_app_code',
      fixed: 'left' as const,
      ellipsis: true,
    },
    {
      title: 'MCP Server',
      colKey: 'mcp_server_id',
      ellipsis: true,
      filter: {
        type: 'single',
        showConfirmAndReset: true,
        popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
        list: mcpList.value.map((item: Record<string, string>) => ({
          label: item.name,
          value: item.id,
        })),
      },
      cell: (_: unknown, { row }: { row: TableRowData }) => {
        return row?.mcp_server?.name;
      },
    },
    {
      title: t('申请人'),
      colKey: 'applied_by',
      cell: (_: unknown, { row }: { row: TableRowData }) => {
        if (featureFlagStore.isEnableDisplayName) {
          return (
            <TenantUserSelector
              mode="detail"
              field="applied_by"
              width="600px"
              content={[row.applied_by]}
            />
          );
        }

        return (
          <EditMember
            mode="detail"
            field="applied_by"
            width="600px"
            content={[row.applied_by]}
          />
        );
      },
    },
    {
      title: t('申请时间'),
      colKey: 'applied_time',
      ellipsis: true,
    },
    {
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
    },
  ];

  const operateColumn: PrimaryTableProps['columns'] = [
    {
      title: t('操作'),
      colKey: 'operate',
      fixed: 'right' as const,
      cell: (_: unknown, { row }: { row: TableRowData }) => {
        if (isEnabledITSMApply.value && Boolean(row?.itsm_ticket_url) && Boolean(row?.itsm_ticket_id)) {
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
      },
    },
  ];

  if (filterData.value.state === 'unprocessed') {
    return [
      ...columns,
      ...operateColumn,
    ];
  }

  return columns;
});
const isEnabledITSMApply = computed(() => featureFlagStore?.flags?.ENABLE_ITSM4_PERMISSION_APPLY);

const getList = () => tableRef.value?.fetchData(filterData.value, { resetPage: true });

const getTableData = async (params: {
  offset: number
  limit: number
}) => {
  // 触发表格组件watch
  settings.value = null;
  const { state } = filterData.value;
  const res = await getMcpAppPermissionApply(gatewayId, {
    ...params,
    ...filterSimpleEmpty(filterData.value),
  } as IGatewaysMcpServersAppPermissionApplyListQuery);
  if (state === 'unprocessed') {
    lastCount.value = res?.count ?? 0;
  }
  return res ?? {
    count: 0,
    results: [],
  };
};

const getMcpList = async () => {
  const page = {
    offset: 0,
    limit: 1000,
  };
  const res = await getServers(gatewayId, page);
  mcpList.value = res.results;
};
getMcpList();

const getApplicant = async () => {
  const response = await getMcpPermissionsApplicant(
    gatewayId,
    filterData.value.mcp_server_id || '-',
    {} as any,
  );
  applicantList.value = response?.applicants || [];
};

const handleTabChange = (name: string) => {
  if (name === filterData.value.state) {
    return;
  }
  filterData.value.state = name;
  handleClearFilter();
};

// 处理表头筛选联动搜索框
const handleFilterChange: PrimaryTableProps['onFilterChange'] = (filterItem: FilterValue) => {
  filterData.value = { ...filterItem };
};

const resetSearch = () => {
  filterData.value = {
    ...filterData.value,
    bk_app_code: '',
    applied_by: '',
    mcp_server_id: '',
  };
};

const handleClearFilter = () => {
  resetSearch();
};

const handleApprove = (row: any, status: string) => {
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
      curAction.value as any,
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
    if (!featureFlagStore.isTenantMode) {
      getApplicant();
    }
    filterData.value.applied_by = '';
    tableEmptyType.value = Boolean(filterData.value.mcp_server_id) ? 'searchEmpty' : 'empty';
    getList();
  },
  { immediate: true },
);

watch(
  () => [filterData.value.bk_app_code, filterData.value.applied_by],
  () => {
    getList();
  },
  { immediate: true },
);

</script>

<style lang="scss" scoped>
.permission {
  background: #FFF;
  border-radius: 2px;
  box-shadow: 0 2px 4px 0 #1919290d;

  .tab {
    padding-left: 24px;
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
      color: #4D4F56;

      // background: #C4C6CC;
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
</style>
