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
  <div class="auth">
    <BkAlert
      theme="info"
      class="mb-16px"
      :title="t('授权应用将会拥有这个 mcp server 工具列表对应接口的调用权限')"
    />

    <div class="flex items-center justify-between mb-16px">
      <div class="flex">
        <BkButton
          theme="primary"
          @click="showAuthorizeDia"
        >
          {{ t('主动授权') }}
        </BkButton>
        <AgDropdown
          class="ml-8px"
          placement="bottom"
          :dropdown-list="exportDropData"
          :is-disabled="!tableData.length"
          :text="t('导出')"
          @on-change="handleExportApp"
        />
      </div>

      <BkInput
        v-model="filterData.bk_app_code"
        class="w-400px"
        :placeholder="t('请输入应用 ID')"
        clearable
        type="search"
      />
    </div>

    <AgTable
      ref="tableRef"
      v-model:table-data="tableData"
      :api-method="getTableData"
      :columns="tableColumns"
      :filter-value="filterData"
      show-settings
      @filter-change="handleFilterChange"
      @sort-change="handleSortChange"
      @clear-filter="handleClearFilter"
    />

    <BkDialog
      v-model:is-show="isShowAuth"
      :title="t('主动授权')"
      width="480px"
      quick-close
      @closed="cancelAuth"
    >
      <div class="auth-dialog">
        <p>{{ t('你将对指定的蓝鲸应用添加访问资源的权限') }}</p>
        <BkForm
          ref="formRef"
          form-type="vertical"
          class="form-main"
          :model="formData"
          :rules="rules"
        >
          <BkFormItem
            :label="t('蓝鲸应用ID')"
            property="bk_app_code"
            required
          >
            <BkInput
              v-model="formData.bk_app_code"
              :placeholder="t('请输入应用 ID')"
              clearable
            />
          </BkFormItem>
        </BkForm>
      </div>
      <template #footer>
        <BkButton
          theme="primary"
          class="mr-8px"
          :loading="authLoading"
          @click="submitAuth"
        >
          {{ t('确定') }}
        </BkButton>
        <BkButton @click="cancelAuth">
          {{ t('取消') }}
        </BkButton>
      </template>
    </BkDialog>
  </div>
</template>

<script lang="tsx" setup>
import { Button, Form, Message, PopConfirm } from 'bkui-vue';
import type {
  FilterValue,
  PrimaryTableProps,
  SortInfo,
  TableRowData,
} from '@blueking/tdesign-ui';
import type { IDropList, IFormMethod } from '@/types/common';
import { useFeatureFlag, useGateway } from '@/stores';
import { useMcpPermission } from '@/hooks';
import { AUTHORIZATION_APPLICATION_OPERATE_TYPE } from '@/constants';
import { filterSimpleEmpty } from '@/utils/filterEmptyValues';
import type { IMCPServerAppPermissionListOutput } from '@/services/types/responses/gateways.ts';
import type { IGatewaysMcpServersPermissionsListQuery } from '@/services/types/query/gateways.ts';
import type { IMCPServerAppPermissionCreateInputSLZ } from '@/services/types/body/post/gateways.ts';
import {
  authMcpPermissions,
  getMcpPermissions,
} from '@/services/source/mcp-market';
import AgDropdown from '@/components/ag-dropdown/Index.vue';
import AgTable from '@/components/ag-table/Index.vue';

interface IProps { mcpServerId?: number }

const { mcpServerId = 0 } = defineProps<IProps>();

const { t } = useI18n();
const gatewayStore = useGateway();
const featureFlagStore = useFeatureFlag();
const {
  exportDropData,
  getExportDropData,
  handleDelete,
  handleExport,
} = useMcpPermission();

const tableRef = useTemplateRef<InstanceType<typeof AgTable>>('tableRef');
const formRef = ref<InstanceType<typeof Form> & IFormMethod>();
const tableColumns = shallowRef<PrimaryTableProps['columns']>([
  {
    title: t('蓝鲸应用ID'),
    colKey: 'bk_app_code',
    ellipsis: true,
  },
  {
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
  },
  {
    title: t('申请人'),
    colKey: 'applied_by',
    ellipsis: true,
    cell: (_: unknown, { row }: { row: TableRowData }) => renderDisplayNameColumn(row.applied_by),
  },
  {
    title: t('操作人'),
    colKey: 'handled_by',
    ellipsis: true,
    cell: (_: unknown, { row }: { row: TableRowData }) => renderDisplayNameColumn(row.handled_by),
  },
  {
    title: t('生效时间'),
    colKey: 'effective_time',
    ellipsis: true,
    sorter: true,
    width: 260,
  },
  {
    title: t('操作'),
    colKey: 'operate',
    fixed: 'right' as const,
    cell: (_: unknown, { row }: { row: TableRowData }) => {
      return (
        <PopConfirm
          placement="top"
          trigger="click"
          content={t('确认删除？')}
          onConfirm={async () => {
            await handleDelete(gatewayId.value, mcpServerId, row?.id);
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
    },
  },
]);
const tableData = ref<IMCPServerAppPermissionListOutput[]>([]);
const isShowAuth = ref(false);
const authLoading = ref(false);
const formData = ref<IMCPServerAppPermissionCreateInputSLZ>({
  bk_app_code: '',
});
const filterData = ref<FilterValue | IGatewaysMcpServersPermissionsListQuery>({
  bk_app_code: '',
  grant_type: '',
  order_by: '',
});
const curSelectData = ref<IGatewaysMcpServersPermissionsListQuery>({
  grant_type: '',
});

const filterFields = ['bk_app_code', 'grant_type'] as string[];
const rules = {
  bk_app_code: [
    {
      required: true,
      message: t('请输入应用 ID'),
      trigger: 'blur',
    },
  ],
};

const gatewayId = computed(() => gatewayStore.currentGateway?.id ?? 0);

const getList = () => {
  const params = {
    ...filterData.value,
    mcp_server_id: mcpServerId,
  };
  return tableRef.value?.fetchData(filterSimpleEmpty(params), { resetPage: true });
};

const getTableData = async (params: {
  offset: number
  limit: number
}) => {
  const queryParams: IGatewaysMcpServersPermissionsListQuery = {
    ...params,
    ...filterData.value,
    mcp_server_id: mcpServerId,
  };
  const res = await getMcpPermissions(gatewayId.value, filterSimpleEmpty(queryParams));
  return res ?? {
    count: 0,
    results: [],
  };
};

const renderDisplayNameColumn = (value: string) => {
  return featureFlagStore.isEnableDisplayName && Boolean(value)
    ? <span><bk-user-display-name user-id={value} /></span>
    : <span>{value || '--'}</span>;
};

const handleExportApp = (payload: IDropList) => {
  handleExport(gatewayId.value, payload, filterData);
};

const showAuthorizeDia = () => {
  isShowAuth.value = true;
};

const cancelAuth = () => {
  isShowAuth.value = false;
  formData.value = { bk_app_code: '' };
};

const submitAuth = async () => {
  try {
    authLoading.value = true;

    await formRef.value?.validate();
    await authMcpPermissions(gatewayId.value, mcpServerId, formData.value);

    Message({
      theme: 'success',
      message: t('操作成功'),
    });
    cancelAuth();
    getList();
  }
  finally {
    authLoading.value = false;
  }
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
};

const resetSearch = () => {
  filterData.value = {
    bk_app_code: '',
    grant_type: '',
    order_by: '',
  };
  curSelectData.value.grant_type = '';
};

const handleClearFilter = () => {
  resetSearch();
};

watch(() => filterData, () => {
  // 是否存在筛选项
  getExportDropData(filterFields, filterData);
  getList();
}, { deep: true });
</script>

<style lang="scss" scoped>
.auth {
  padding: 16px 24px 24px;
  background: #ffffff;
}

.auth-dialog {

  p {
    font-size: 14px;
    color: #4D4F56;
  }

  .form-main {
    margin-top: 8px;
  }
}
</style>
