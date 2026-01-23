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
  <div class="permission-apply-container">
    <div class="flex justify-between header">
      <BkButton
        v-bk-tooltips="{ content: t('请选择要审批的权限'), disabled: selections.length }"
        theme="primary"
        :disabled="!selections.length"
        @click="handleBatchApply"
      >
        {{ t("批量审批") }}
      </BkButton>
      <BkForm
        class="flex header-filter"
        label-width="120"
      >
        <BkFormItem :label="t('蓝鲸应用ID')">
          <BkInput
            v-model="filterData.bk_app_code"
            class="w-282px"
            clearable
            :placeholder="t('请输入应用ID')"
          />
        </BkFormItem>
        <BkFormItem
          :label="t('授权维度')"
        >
          <BkSelect
            v-model="filterData.grant_dimension"
            class="w-282px"
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
            class="w-282px"
            clearable
            :placeholder="t('请输入用户')"
          />
        </BkFormItem>
        <BkFormItem
          v-else
          :label="t('申请人')"
        >
          <BkUserSelector
            v-model="filterData.applied_by"
            :api-base-url="envStore.tenantUserDisplayAPI"
            :tenant-id="userStore.info.tenant_id"
            :placeholder="t('请输入用户')"
            class="w-200px"
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
        resizable
        show-selection
        :expand-icon="false"
        :expandable="expandableConfig"
        :expanded-row-keys="expandableConfig.expandedRowKeys"
        :show-first-full-row="selections.length > 0"
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
            v-model:table-data="row.resourceList"
            size="small"
            class="ag-expand-table"
            local-page
            show-selection
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
import { Button, Form, Loading, Message, Popover } from 'bkui-vue';
import {
  getApigwResources,
  getPermissionApplyList,
  updatePermissionStatus,
} from '@/services/source/permission';
import {
  useEnv,
  useFeatureFlag,
  useGateway,
  usePermission,
  useUserInfo,
} from '@/stores';
import type { IApprovalListItem } from '@/types/permission';
import type { ITableMethod } from '@/types/common';
import { sortByKey } from '@/utils';
import { AUTHORIZATION_DIMENSION } from '@/constants';
import { APPROVAL_STATUS_MAP } from '@/enums';
import BkUserSelector from '@blueking/bk-user-selector';
import BatchApproval from '@/views/permission/apply/components/BatchApproval.vue';
import CustomHeader from '@/views/permission/apply/components/CustomHeader.vue';
import AgIcon from '@/components/ag-icon/Index.vue';
import AgTable from '@/components/ag-table/Index.vue';

const envStore = useEnv();
const gatewayStore = useGateway();
const userStore = useUserInfo();
const permissionStore = usePermission();
const featureFlagStore = useFeatureFlag();
const { t } = useI18n();

const permissionTableRef = useTemplateRef<InstanceType<typeof AgTable> & ITableMethod>('permissionTableRef');
const approveForm = ref<InstanceType<typeof Form> & { validate: () => void }>();
const tableData = ref([]);
const selections = ref([]);
const selectedRowKeys = ref([]);
const resourceList = ref([]);
const childrenColumns = shallowRef([
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
const filterData = ref({});
const filterValue = ref({});
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
const expandableConfig = ref({
  expandColumn: false,
  expandedRowKeys: [],
  canExpand: (row) => {
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
const rules = reactive({
  comment: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
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
    filterValue.value = Object.assign({}, filterData.value);
    handleSearch();
  },
  { deep: true },
);

const setRowResources = () => {
  tableData.value.forEach((row) => {
    row.isSelectAll = true;
    row.selection = [];
    row.resourceList = sortByKey(resourceList.value.filter(resource => row.resource_ids.includes(resource.id)), 'path');
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
};

const getTableColumns = computed(() => {
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
      cell: (h, { row }: { row?: Partial<IApprovalListItem> }) => {
        if (['resource'].includes(row.grant_dimension)) {
          return (
            <div class="flex items-center">
              <AgIcon
                name={row.isExpand ? 'down-shape' : 'right-shape'}
                size="10"
                class="mr-4px"
              />
              {`${row.grant_dimension_display} (${row.resourceList?.length || '--'})`}
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
      cell: (h, { row }: { row?: Partial<IApprovalListItem> }) => {
        return row?.expire_days_display || '--';
      },
    },
    {
      colKey: 'reason',
      title: t('申请理由'),
      ellipsis: true,
      cell: (h, { row }: { row?: Partial<IApprovalListItem> }) => {
        return row?.reason || '--';
      },
    },
    {
      colKey: 'applied_by',
      title: t('申请人'),
      ellipsis: true,
      cell: (h, { row }: { row?: Partial<IApprovalListItem> }) =>
        featureFlagStore.isEnableDisplayName
          ? <span><bk-user-display-name user-id={row.applied_by} /></span>
          : <span>{row.applied_by}</span>,
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
      cell: (h, { row }: { row?: Partial<IApprovalListItem> }) => {
        if (['pending'].includes(row?.status)) {
          return (
            <div class="perm-apply-dot">
              <Loading class="mr-4px" loading size="mini" mode="spin" theme="primary" />
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
      colKey: 'operate',
      title: t('操作'),
      fixed: 'right',
      ellipsis: true,
      cell: (h, { row }: { row?: Partial<IApprovalListItem> }) => {
        if (
          expandableConfig.value.expandedRowKeys.includes(row.id)
          && !row?.selection?.length
          && !['api'].includes(row?.grant_dimension)
        ) {
          return (
            <div>
              <Popover content={t('请选择资源')}>
                <Button
                  class="m-r-10px is-disabled"
                  theme="primary"
                  text
                  onClick={(e: Event) => {
                    handlePrevent(e, row);
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
        else {
          return (
            <div>
              <Button
                class="mr-10px"
                theme="primary"
                text
                onClick={(e: Event) => {
                  handleApplyApprove(e, row);
                }}
              >
                {row?.isSelectAll ? t('全部通过') : t('部分通过')}
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
        }
      },
    },
  ];
});

const getTableData = async (params: Record<string, any> = {}) => {
  const results = await getPermissionApplyList(apigwId.value, params);
  return results ?? [];
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
};

const handleRequestDone = () => {
  const pageConf = permissionTableRef.value?.getPagination();
  if (pageConf) {
    permissionStore.setCount(pageConf.total || 0);
  }
  getResourceList();
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

const handleSelectionChange: PrimaryTableProps['onSelectChange'] = ({ selections: selected, selectionsRowKeys }) => {
  selections.value = selected;
  selectedRowKeys.value = selectionsRowKeys;
};

// 折叠table 多选发生变化触发
const handleRowSelectionChange = (row: Partial<IApprovalListItem>, rowSelections) => {
  const { selections } = rowSelections;
  const isSelectAll = row.resourceList.length === selections.length;
  row.selection = selections;
  row.isSelectAll = isSelectAll;
  curPermission.value = Object.assign(curPermission.value, {
    selection: row.selection,
    isSelectAll,
  });
};

// 处理表头筛选联动搜索框
const handleFilterChange: PrimaryTableProps['onFilterChange'] = (filterItem: FilterValue) => {
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
    ['approved'].includes(params.status)
    && expandableConfig.value.expandedRowKeys.includes(id)
    && selection.length > 0
    && !isSelectAll
  ) {
    params = Object.assign(params, {
      status: 'partial_approved',
      part_resource_ids: { [id]: selection.map(item => item.id) },
    });
  }
  await updatePermissionStatus(apigwId.value, params);
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

const handleSetRowClass = ({ row }) => {
  if (row.grant_dimension.includes('resource')) {
    return 'cursor-pointer';
  }
  return '';
};

const handleRowClick = ({ e, row }: {
  e: Event
  row: IApprovalListItem
}) => {
  e.stopPropagation();
  if (row.grant_dimension.includes('resource')) {
    row.isExpand = !row.isExpand;
    expandableConfig.value.expandedRowKeys
      = expandableConfig.value.expandedRowKeys.filter(item => item === row.id);
    const curExpandRow = row.isExpand ? row : {};
    if (row.isExpand) {
      expandableConfig.value.expandedRowKeys.push(row.id);
    }
    else {
      expandableConfig.value.expandedRowKeys
        = expandableConfig.value.expandedRowKeys.filter(item => item !== row.id);
    }
    tableData.value.forEach((item) => {
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
  tableRef.value.handleResetSelection();
  selections.value = [];
};
</script>

<style lang="scss" scoped>
.permission-apply-container {
  margin: 16px;
  background-color: #fff;
  padding: 16px 16px 34px;
  .apply-content {
    border: 1px solid #DCDEE5;
  }
}
.apply-expand-alert {
  padding: 20px;
  line-height: 60px;
  background-color: #fafafa;
}

.header-filter {

  .bk-form-item {
    margin-bottom: 16px;

    :deep(.bk-form-content) {
      line-height: 30px;

      .form-item-label {
        padding: 5px 7px;
        overflow: hidden;
        line-height: 20px;
        color: #4d4f56;
        text-align: center;
        text-overflow: ellipsis;
        white-space: nowrap;
        background-color: #fafbfd;
        border: 1px solid #c4c6cc;
        border-radius: 2px 0 0 2px;
      }

      .form-item-value {
        margin-left: -1px;
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
