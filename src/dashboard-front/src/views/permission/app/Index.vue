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
  <div class="permission-app-container page-wrapper-padding">
    <div class="flex justify-between">
      <div class="flex items-center header-btn">
        <BkButton
          v-bk-tooltips="{
            content: t('没有选中可续期的权限'),
            disabled: renewableCount,
          }"
          theme="primary"
          :disabled="!renewableCount || !isBatchRenewal"
          @click="handleBatchRenew"
        >
          {{ t('批量续期') }}
        </BkButton>
        <BkButton
          v-bk-tooltips="{
            content: t('请选择待删除的权限'),
            disabled: curSelections.length,
          }"
          class="ml-8px"
          :disabled="!curSelections.length"
          @click="handleBatchDelete"
        >
          {{ t('批量删除') }}
        </BkButton>
        <BkButton
          class="ml-8px"
          :disabled="!tableData.length"
          @click="handleExport"
        >
          {{ t('导出全部') }}
        </BkButton>
        <BkButton
          class="ml-8px"
          @click="handleAuthShow"
        >
          {{ t('主动授权') }}
        </BkButton>
      </div>
      <BkForm class="flex">
        <BkFormItem
          label=""
          class="mb-0"
          label-width="10"
        >
          <BkSearchSelect
            :key="componentKey"
            v-model="filterValues"
            :data="filterConditions"
            :validate-values="validateSearchSelect"
            :placeholder="t('搜索')"
            :value-split-code="'+'"
            clearable
            unique-select
            value-behavior="need-key"
            class="w-450px bg-white"
          />
        </BkFormItem>
      </BkForm>
    </div>

    <div class="mt-24px app-content">
      <AgTable
        ref="tableRef"
        v-model:table-data="tableData"
        resizable
        show-settings
        show-selection
        :show-first-full-row="curSelections.length > 0"
        :filter-value="filterData"
        :api-method="getTableData"
        :columns="tableColumns"
        @clear-filter="handleClearFilter"
        @clear-selection="isBatchRenewal = false"
        @filter-change="handleFilterChange"
        @selection-change="handleSelectionChange"
      />
    </div>

    <!-- 主动授权 -->
    <ProactiveAuthorization
      v-model:slider-params="authSliderConf"
      v-model:auth-data="curAuthData"
      :resource-list="resourceList"
      @confirm="handleSave"
    />

    <!-- 批量续期 -->
    <BatchRenewal
      v-model:expire-date="expireDays"
      v-model:slider-params="batchApplySliderConf"
      :api-list="selectedRenewableApiPermList"
      :resource-list="selectedRenewableResourcePermList"
      :apply-count="renewableCount"
      @confirm="handleBatchRenewalConfirm"
    />

    <!-- 单个续期 -->
    <RenewalDialog
      v-model:expire-date="expireDays"
      v-model:dialog-params="applyDialogConf"
      v-model:selections="curSelections"
      :apply-count="renewableCount"
      @confirm="handleBatchRenewalConfirm"
    />

    <!-- 删除权限 -->
    <DeletePermission
      v-model:dialog-params="removeDialogConf"
      :permissions="curPermission"
      @confirm="handleRemovePermission"
    />

    <!-- 批量删除权限 -->
    <BatchRemove
      v-model:slider-params="batchRemoveSliderConf"
      :api-list="selectedApiPermList"
      :resource-list="selectedResourcePermList"
      @confirm="handleBatchRemovalConfirm"
    />
  </div>
</template>

<script lang="tsx" setup>
import { cloneDeep } from 'lodash-es';
import { Button, Message } from 'bkui-vue';
import { type ISearchItem, type ISearchValue } from 'bkui-vue/lib/search-select/utils.d';
import type { IGatewaysResourcesListQuery } from '@/services/types/query/gateways';
import { useTableFilterChange } from '@/hooks/use-table-filter-change';
import {
  type IAuthData,
  type IExportParams,
  batchDeletePermission,
  batchUpdatePermission,
  deleteApiPermission,
  deleteResourcePermission,
  exportPermissionList,
  getPermissionList,
  getResourceListData,
  getResourcePermissionAppList,
} from '@/services/source/permission';
import { useFeatureFlag, useGateway, usePermission } from '@/stores';
import type { IDropList, ITableMethod } from '@/types/common';
import type { IPermission, IResource } from '@/types/permission';
import { sortByKey } from '@/utils';
import { GRANT_DIMENSION_TYPE_LIST } from '@/constants';
import ProactiveAuthorization from '@/views/permission/app/components/ProactiveAuthorization.vue';
import RenewalDialog from '@/views/permission/app/components/Renewal.vue';
import BatchRenewal from '@/views/permission/app/components/BatchRenewal.vue';
import BatchRemove from '@/views/permission/app/components/BatchRemove.vue';
import DeletePermission from '@/views/permission/app/components/DeletePermission.vue';
import AgTable from '@/components/ag-table/Index.vue';

const { t } = useI18n();
const { handleTableFilterChange } = useTableFilterChange();
const gatewayStore = useGateway();
const permissionStore = usePermission();
const featureFlagStore = useFeatureFlag();

const tableRef = useTemplateRef<InstanceType<typeof AgTable> & ITableMethod>('tableRef');
const tableColumns = shallowRef<any[]>([
  {
    title: t('蓝鲸应用ID'),
    colKey: 'bk_app_code',
    ellipsis: true,
    width: 200,
  },
  {
    title: t('授权维度'),
    colKey: 'grant_dimension',
    ellipsis: true,
    width: 120,
    cell: (h: any, { row }: { row: IPermission }) => {
      return (
        <span class="ag-auto-text">
          { getSearchDimensionText(row.grant_dimension) }
        </span>
      );
    },
    filter: {
      type: 'single',
      showConfirmAndReset: true,
      popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
      list: GRANT_DIMENSION_TYPE_LIST,
    },
  },
  {
    title: t('资源名称'),
    colKey: 'resource_name',
    ellipsis: true,
    cell: (h: any, { row }: { row: IPermission }) => {
      const data = row as IPermission;
      return (
        <span>{ data.resource_name || '--' }</span>
      );
    },
  },
  {
    title: t('请求路径'),
    colKey: 'resource_path',
    ellipsis: true,
    cell: (h: any, { row }: { row: IPermission }) => {
      const data = row as IPermission;
      return (
        <span>{ data.resource_path || '--' }</span>
      );
    },
  },
  {
    title: t('有效期'),
    colKey: 'expires',
    ellipsis: true,
    width: 100,
    cell: (h: any, { row }: { row: IPermission }) => {
      const data = row as IPermission;
      return (
        <span style={{ color: permissionStore.getDurationTextColor(data.expires) }}>
          { permissionStore.getDurationText(data.expires) }
        </span>
      );
    },
  },
  {
    title: t('授权类型'),
    colKey: 'grant_type',
    ellipsis: true,
    width: 120,
    cell: (h: any, { row }: { row: IPermission }) => {
      const data = row as IPermission;
      return (
        <span>
          { t(['initialize'].includes(data.grant_type) ? '主动授权' : '申请审批') }
        </span>
      );
    },
  },
  {
    title: t('操作人'),
    colKey: 'handled_by',
    ellipsis: true,
    width: 100,
    cell: (h: any, { row }: { row: IPermission }) => {
      const data = row as IPermission;
      return (
        !featureFlagStore.isEnableDisplayName
          ? <span>{data.handled_by || '--'}</span>
          : <span><bk-user-display-name user-id={data.handled_by} /></span>
      );
    },
  },
  {
    title: t('操作'),
    colKey: 'operate',
    fixed: 'right',
    width: 120,
    cell: (h: any, { row }: { row: IPermission }) => {
      return (
        <div>
          <Button
            class="mr-10px"
            theme="primary"
            text
            v-bk-tooltips={{
              content: t('权限有效期大于 360 天时，暂无法续期'),
              placement: 'left',
              disabled: row.renewable,
            }}
            disabled={!row.renewable}
            onClick={() => handleSingleApply(row)}
          >
            { t('续期') }
          </Button>
          <Button
            theme="primary"
            text
            onClick={() => handleRemove(row)}
          >
            { t('删除') }
          </Button>
        </div>
      );
    },
  },
]);
const filterData = ref<Record<string, string | string[]>>({});
const resourceList = ref<IResource[]>([]);
const curPermission = ref<IPermission>({
  id: -1,
  bk_app_code: '',
  resource_id: -1,
  resource_name: '',
  resource_path: '',
  resource_method: '',
  expires: '',
  grant_dimension: '',
  grant_type: '',
  renewable: false,
  detail: [],
});
const curSelections = ref<IPermission[]>([]);
// 导出下拉
const exportDropData = ref<IDropList[]>([
  {
    value: 'all',
    label: t('全部应用权限'),
  },
  {
    value: 'filtered',
    label: t('已筛选应用权限'),
    disabled: true,
  },
  {
    value: 'selected',
    label: t('已选应用权限'),
    disabled: true,
  },
]);
// 主动授权config
const authSliderConf = ref({
  isShow: false,
  isLoading: false,
  title: t('主动授权'),
});
// 当前授权数据
const curAuthData = ref<IAuthData>({
  bk_app_code: '',
  expire_type: 'permanent',
  expire_days: null,
  resource_ids: [],
  dimension: 'api',
});
const curAuthDataBack = ref<IAuthData>(cloneDeep(curAuthData.value));
const componentKey = ref(0);
const expireDays = ref(0);
const isBatchRenewal = ref(true);
// 批量续期dialog
const batchApplySliderConf = ref({
  isShow: false,
  saveLoading: false,
  title: t('批量续期'),
});
// 单个续期 dialog
const applyDialogConf = ref({
  isShow: false,
  saveLoading: false,
  title: t('续期'),
});
// 删除dialog
const removeDialogConf = ref({
  isShow: false,
  title: '',
});
// 批量删除 slider
const batchRemoveSliderConf = ref({
  isShow: false,
  saveLoading: false,
  title: t('批量删除'),
});
// 导出参数
const exportParams = ref<IExportParams>({ export_type: 'all' });
const filterValues = ref<ISearchValue[]>([]);
const filterConditions = ref<ISearchItem[]>([
  {
    name: t('授权维度'),
    id: 'grant_dimension',
    children: [
      {
        id: 'resource',
        name: t('按资源'),
      },
      {
        id: 'api',
        name: t('按网关'),
      },
    ],
    onlyRecommendChildren: true,
    noValidate: true,
  },
  {
    name: t('蓝鲸应用ID'),
    id: 'bk_app_code',
    children: [],
    onlyRecommendChildren: true,
    noValidate: true,
  },
  {
    name: t('资源名称'),
    id: 'resource_id',
  },
  {
    name: t('请求路径'),
    id: 'resource_path',
    noValidate: true,
  },
  {
    name: t('模糊搜索'),
    id: 'keyword',
    noValidate: true,
  },
]);
const tableData = ref([]);

const apigwId = computed(() => gatewayStore.apigwId);
// 可续期的数量
const renewableCount = computed(() => curSelections.value.filter((item: IPermission) => item.renewable).length);
// 资源维度权限列表
const selectedResourcePermList = computed(() =>
  curSelections.value.filter((perm: IPermission) => perm.grant_dimension === 'resource'),
);
// 网关维度权限列表
const selectedApiPermList = computed(() =>
  curSelections.value.filter((perm: IPermission) => perm.grant_dimension === 'api'),
);
// 资源维度可续期权限列表
const selectedRenewableResourcePermList = computed(() =>
  curSelections.value.filter((perm: IPermission) => perm.grant_dimension === 'resource' && perm.renewable),
);
// 网关维度可续期权限列表
const selectedRenewableApiPermList = computed(() =>
  curSelections.value.filter((perm: IPermission) => perm.grant_dimension === 'api' && perm.renewable),
);

// 监听搜索是否变化
watch(
  filterValues,
  () => {
    handleSearch();
  },
);
// 监听授权有效时间的类型
watch(
  () => curAuthData.value.expire_type,
  (expire: string) => {
    curAuthData.value.expire_days = ['custom'].includes(expire) ? 180 : null;
  },
);
// 处理表格复选框数据
watch(
  curSelections,
  (selection: IPermission[]) => {
    exportDropData.value.forEach((val: IDropList) => {
      // 已选资源
      if (['selected'].includes(val.value)) {
        val.disabled = !selection.length;
      }
    });
  },
  { deep: true },
);

const getTableData = async (params: Record<string, any> = {}) => {
  const results = await getPermissionList(apigwId.value, params);
  return results ?? [];
};

function getList() {
  tableRef.value?.fetchData(filterData.value, { resetPage: true });
}

function handleSearch() {
  filterData.value = {};
  if (filterValues.value) {
    // 把纯文本搜索项转换成查询参数
    const textItem = filterValues.value.find((val: ISearchValue) => val.type === 'text');
    if (textItem) {
      filterData.value.keyword = textItem.name || '';
    }
    filterValues.value.forEach((item: ISearchValue) => {
      if (item.values) {
        filterData.value[item.id] = item.values[0].id;
      }
    });
  }
  exportDropData.value.forEach((exp: IDropList) => {
    // 已选资源
    if (exp.value.includes('filtered')) {
      exp.disabled = filterValues.value.length === 0;
    }
  });
  getList();
}

const handleSelectionChange = ({ selections }: { selections: any[] }) => {
  isBatchRenewal.value = true;
  curSelections.value = selections as IPermission[];
};

// 处理表头筛选联动搜索框
const handleFilterChange = (filterItem: any) => {
  handleTableFilterChange({
    filterItem,
    filterData,
    searchOptions: filterConditions,
    searchParams: filterValues,
  });
  getList();
};

const handleClearSelection = () => {
  tableRef.value?.handleResetSelection();
  curSelections.value = [];
  isBatchRenewal.value = false;
};

const getBkAppCodes = async () => {
  const appCodeOption = filterConditions.value.find(
    (condition: ISearchItem) => condition.id === 'bk_app_code',
  );
  const response = ((await getResourcePermissionAppList(apigwId.value)) as string[]) || [];
  if (appCodeOption) {
    appCodeOption.children = response.map(appCode => ({
      id: appCode,
      name: appCode,
    }));
  }
  componentKey.value += 1;
};

// 获取资源列表数据
const getApigwResources = async () => {
  const pageParams: IGatewaysResourcesListQuery = {
    limit: 3000,
    order_by: 'path',
  };
  const resourceIdOption = filterConditions.value.find(
    (condition: ISearchItem) => condition.id === 'resource_id',
  );
  const response = await getResourceListData(apigwId.value, pageParams);
  const resources = response.results || [];
  const results = resources.map((resource: any) => ({
    id: resource.id,
    name: resource.name,
    path: resource.path,
    method: resource.method,
    resourceName: `${resource.method}：${resource.path}`,
    kind: resource.kind,
  }));
  resourceList.value = sortByKey(results, 'name');
  if (resourceIdOption) {
    resourceIdOption.children = resourceList.value.map((item: IResource) => ({
      id: String(item.id),
      name: item.name,
    }));
  }
  componentKey.value += 1;
};

// 导出
const handleExport = async () => {
  try {
    await exportPermissionList(apigwId.value, exportParams.value);
    Message({
      message: t('导出成功'),
      theme: 'success',
    });
  }
  finally {
    exportParams.value = { export_type: 'all' };
  }
};

// 确定续期
const handleBatchRenewalConfirm = async () => {
  batchApplySliderConf.value.saveLoading = true;
  const data = {
    resource_dimension_ids: [] as number[],
    gateway_dimension_ids: [] as number[],
    expire_days: expireDays.value,
  };
  if (selectedResourcePermList.value.length > 0) {
    data.resource_dimension_ids = selectedResourcePermList.value.map(
      (permission: IPermission) => permission.id,
    );
  }
  if (selectedApiPermList.value.length > 0) {
    data.gateway_dimension_ids = selectedApiPermList.value.map(
      (permission: IPermission) => permission.id,
    );
  }
  try {
    await batchUpdatePermission(apigwId.value, data);
    Message({
      theme: 'success',
      message: t('续期成功！'),
    });
    batchApplySliderConf.value.isShow = false;
    applyDialogConf.value.isShow = false;
    handleClearSelection();
    getList();
  }
  finally {
    batchApplySliderConf.value.saveLoading = false;
    applyDialogConf.value.saveLoading = false;
  }
};

// 批量续期
const handleBatchRenew = () => {
  batchApplySliderConf.value.isShow = true;
};

// 批量删除（暂未实现）
const handleBatchDelete = () => {
  batchRemoveSliderConf.value.isShow = true;
};

// 确定批量删除
const handleBatchRemovalConfirm = async () => {
  batchRemoveSliderConf.value.saveLoading = true;
  const params: {
    resource_dimension_ids?: number[]
    gateway_dimension_ids?: number[]
  } = {};
  if (selectedResourcePermList.value.length > 0) {
    params.resource_dimension_ids = selectedResourcePermList.value.map(
      (permission: IPermission) => permission.id,
    );
  }
  if (selectedApiPermList.value.length > 0) {
    params.gateway_dimension_ids = selectedApiPermList.value.map(
      (permission: IPermission) => permission.id,
    );
  }
  try {
    await batchDeletePermission(apigwId.value, params);
    Message({
      theme: 'success',
      message: t('删除成功'),
    });
    batchRemoveSliderConf.value.isShow = false;
    handleClearSelection();
    getList();
  }
  finally {
    batchRemoveSliderConf.value.saveLoading = false;
  }
};

// 单个续期
const handleSingleApply = (data: IPermission) => {
  isBatchRenewal.value = curSelections.value.length > 0;
  curSelections.value = [data];
  applyDialogConf.value.isShow = true;
};

const handleRemove = (data: IPermission) => {
  curPermission.value = data;
  removeDialogConf.value.isShow = true;
  removeDialogConf.value.title = t('确定要删除蓝鲸应用【{appCode}】的权限？', { appCode: curPermission.value.bk_app_code });
};

// 删除权限
const handleRemovePermission = async () => {
  const { id, grant_dimension } = curPermission.value;
  const ids = [id!];
  const fetchMethod = ['resource'].includes(grant_dimension ?? '') ? deleteResourcePermission : deleteApiPermission;
  await fetchMethod(apigwId.value, { ids });
  removeDialogConf.value.isShow = false;
  Message({
    theme: 'success',
    message: t('删除成功！'),
  });
  handleClearSelection();
  getList();
};

// 主动授权
const handleAuthShow = () => {
  authSliderConf.value.isShow = true;
};

// 主动授权保存
const handleSave = () => {
  Message({
    theme: 'success',
    message: t('授权成功！'),
  });
  curAuthData.value = cloneDeep(curAuthDataBack.value);
  handleClearSelection();
  getList();
};

const handleClearFilter = () => {
  filterData.value = {};
  filterValues.value = [];
};

const getSearchDimensionText = (row: string | null) => {
  if (row === 'resource') return t('按资源');
  if (row === 'api') return t('按网关');
  return '--';
};

const init = () => {
  getBkAppCodes();
  getApigwResources();
};
init();

// 校验查询的资源名称，使用户只能从给出的资源选项中选择查询的 resource_id
const validateSearchSelect = async (item: ISearchItem, values: {
  id: string
  name: string
}[]) => {
  if (item.id === 'resource_id') {
    const resourceIdOption = filterConditions.value.find(
      (condition: ISearchItem) => condition.id === 'resource_id',
    );

    if (resourceIdOption?.children) {
      if (resourceIdOption.children.find(option => option.name === values[0].name)) {
        return true;
      }
      else {
        return t('请从选项中选择资源');
      }
    }
    else {
      return true;
    }
  }
};
</script>

<style lang="scss" scoped>
.attention-dialog {

  :deep(.bk-dialog-header) {
    padding: 5px !important;
  }

  :deep(.bk-modal-footer) {
    background-color: #fff;
    border-top: none;
  }

  .title {
    font-size: 20px;
    color: #313238;
    text-align: center;
  }

  .sub-title {
    margin-top: 14px;
    margin-bottom: 20px;
    font-size: 14px;
    line-height: 1.5;
    color: #63656e;
    text-align: center;
  }

  .btn {
    text-align: center;
  }
}
</style>
