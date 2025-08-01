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
  <div class="permission-app-container page-wrapper-padding">
    <div class="flex justify-between header">
      <div class="flex items-center header-btn">
        <BkButton
          v-bk-tooltips="{
            content: t('请选择待续期的权限'),
            disabled: selections.length,
          }"
          theme="primary"
          :disabled="!selections.length"
          @click="handleBatchApplyPermission"
        >
          {{ t("批量续期") }}
        </BkButton>
        <BkButton
          class="m-l-8px"
          :disabled="!tableData.length"
          @click="handleExport"
        >
          {{ t("导出全部") }}
        </BkButton>
        <BkButton
          class="m-l-8px"
          @click="handleAuthShow"
        >
          {{ t("主动授权") }}
        </BkButton>
      </div>
      <BkForm class="flex">
        <BkFormItem
          label=""
          class="m-b-0"
          label-width="10"
        >
          <BkSearchSelect
            :key="componentKey"
            v-model="filterValues"
            :data="filterConditions"
            :placeholder="t('搜索')"
            :value-split-code="'+'"
            clearable
            unique-select
            style="width: 450px; background: #fffff"
          />
        </BkFormItem>
      </BkForm>
    </div>
    <div class="app-content">
      <BkLoading :loading="isLoading">
        <BkTable
          ref="appTableRef"
          row-key="id"
          show-overflow-tooltip
          size="small"
          class="m-t-16px perm-app-table"
          :data="tableData"
          :pagination="pagination"
          :max-height="clientHeight"
          :columns="setTableColumns()"
          border="outer"
          remote-pagination
          @page-limit-change="handlePageSizeChange"
          @page-value-change="handlePageChange"
        >
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
      :api-list="selectedApiPermList"
      :resource-list="selectedResourcePermList"
      :apply-count="applyCount"
      @confirm="handleBatchConfirm"
    />

    <!-- 单个续期 -->
    <RenewalDialog
      v-model:expire-date="expireDays"
      v-model:dialog-params="ApplyDialogConf"
      :selections="curSelections"
      :apply-count="applyCount"
      @confirm="handleBatchConfirm"
    />

    <!-- 删除权限 -->
    <DeletePermission
      v-model:dialog-params="removeDialogConf"
      :permissions="curPermission"
      @confirm="handleRemovePermission"
    />
  </div>
</template>

<script lang="tsx" setup>
import { cloneDeep } from 'lodash-es';
import { Message } from 'bkui-vue';
import { type ISearchItem } from 'bkui-lib/search-select/utils';
import {
  type IAuthData,
  type IBatchUpdateParams,
  type IExportParams,
  type IFilterParams,
  batchUpdatePermission,
  deleteApiPermission,
  deleteResourcePermission,
  exportPermissionList,
  getPermissionList,
  getResourceListData,
  getResourcePermissionAppList,
} from '@/services/source/permission';
import { useGateway, usePermission } from '@/stores';
import { useMaxTableLimit, useQueryList } from '@/hooks';
import { IDropList } from '@/types/common';
import { IFilterValues, IPermission, IResource } from '@/types/permission';
import { sortByKey } from '@/utils';
import ProactiveAuthorization from '@/views/permission/app/components/ProactiveAuthorization.vue';
import RenewalDialog from '@/views/permission/app/components/Renewal.vue';
import BatchRenewal from '@/views/permission/app/components/BatchRenewal.vue';
import DeletePermission from '@/views/permission/app/components/DeletePermission.vue';
import TableEmpty from '@/components/table-empty/Index.vue';
import TableHeaderFilter from '@/components/table-header-filter';

const { t } = useI18n();
const { maxTableLimit, clientHeight } = useMaxTableLimit();
const gatewayStore = useGateway();
const permissionStore = usePermission();

const defaultFilterData = ref<DefaultSearchParamsInterface>({ grant_dimension: 'ALL' });
const singleSelectData = ref<{ [key: string]: string }>(cloneDeep(defaultFilterData));
const checkedGrantDimensionFilterOptions = ref<string[]>([]);
// 授权维度表头过滤
const grantDimensionFilterOptions = ref({
  list: [
    {
      name: t('按网关'),
      id: 'api',
    },
    {
      name: t('按资源'),
      id: 'resource',
    },
  ],
  checked: checkedGrantDimensionFilterOptions.value,
  filterFn: (checked: string[], row: IPermission) => {
    if (!checked.length) {
      return true;
    }
    return grantDimensionList.value.includes(row.grant_dimension);
  },
});
const isAllChecked = ref(false);
const checkedGrantTypeFilterOptions = ref<string[]>([]);
const filterData = ref<IFilterParams>({});
const resourceList = ref<IResource[]>([]);
const curPermission = ref<Partial<IPermission>>({
  bk_app_code: '',
  detail: [],
  id: -1,
});
const selections = ref<IPermission[]>([]);
const curSelections = ref([]);
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
const authSliderConf = reactive({
  isShow: false,
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
const appTableRef = ref<InstanceType<typeof BkTable> & { clearSelection: () => void }>();
const componentKey = ref(0);
const expireDays = ref(0);
const tableEmptyConf = ref<{
  emptyType: string
  isAbnormal: boolean
}>({
  emptyType: '',
  isAbnormal: false,
});
// 批量续期dialog
const batchApplySliderConf = reactive({
  isShow: false,
  saveLoading: false,
  title: t('批量续期'),
});
// 单个续期 dialog
const ApplyDialogConf = reactive({
  isShow: false,
  saveLoading: false,
  title: t('续期'),
});
// 删除dialog
const removeDialogConf = reactive({
  isShow: false,
  title: t('确定要删除蓝鲸应用【{appCode}】的权限？', { appCode: curPermission.value.bk_app_code }),
});
// 导出参数
const exportParams = ref<IExportParams>({ export_type: 'all' });
const filterValues = ref<IFilterValues[]>([]);
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
  },
  {
    name: t('蓝鲸应用ID'),
    id: 'bk_app_code',
    children: [],
    onlyRecommendChildren: true,
  },
  {
    name: t('资源名称'),
    id: 'resource_id',
    children: [],
    onlyRecommendChildren: true,
  },
  {
    name: t('模糊搜索'),
    id: 'keyword',
  },
]);

// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList<IPermission>({
  apiMethod: getPermissionList,
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
// 授权维度筛选值转换
const grantDimensionList = computed(() => {
  const results = checkedGrantDimensionFilterOptions.value.map((dimension) => {
    if ([t('按网关'), 'By Gateway'].includes(dimension)) {
      return 'api';
    }
    if ([t('按资源'), 'By Resource'].includes(dimension)) {
      return 'resource';
    }
    return dimension;
  });
  return results;
});
// 可续期的数量
const applyCount = computed(() => {
  return curSelections.value.filter((item: { renewable: boolean }) => item.renewable)
    .length;
});
// 资源维度权限列表
const selectedResourcePermList = computed(() =>
  curSelections.value.filter(perm => ['resource'].includes(perm.grant_dimension)),
);
// 网关维度权限列表
const selectedApiPermList = computed(() =>
  curSelections.value.filter(perm => ['api'].includes(perm.grant_dimension)),
);

// 监听搜索是否变化
watch(
  filterValues,
  () => {
    let isEmpty = false;
    filterData.value = {};
    // 当前有资源名称过滤，且过滤值不在资源列表中，则删除该过滤条件
    const resourceIdFilterIndex = filterValues.value.findIndex(
      filter => filter.id === 'resource_id',
    );
    // 找到授权维度联动表头筛选
    const rantDimensionIndex = filterValues.value.findIndex(filter => ['grant_dimension'].includes(filter.id));
    singleSelectData.value.grant_dimension = rantDimensionIndex > -1 ? filterValues.value[rantDimensionIndex].values?.[0]?.id : 'ALL';
    if (resourceIdFilterIndex > -1) {
      const resourceId = filterValues.value[resourceIdFilterIndex].values[0].id as string;
      const validResourceIds = filterConditions.value.find(condition => condition.id === 'resource_id')?.children.map(option => option.id);
      if (!validResourceIds.includes(resourceId)) {
        filterValues.value.splice(resourceIdFilterIndex, 1);
        Message({
          theme: 'warning',
          message: t('请选择有效的资源名称'),
        });
      }
    }
    if (filterValues.value) {
      // 把纯文本搜索项转换成查询参数
      const textItem = filterValues.value.find(val => val.type === 'text');
      if (textItem) {
        filterData.value.keyword = textItem.name || '';
      }
      filterValues.value.forEach((item) => {
        if (item.values) {
          filterData.value[item.id] = item.values[0].id;
        }
      });
      isEmpty = filterValues.value.length === 0;
    }
    exportDropData.value.forEach((e: IDropList) => {
      // 已选资源
      if (e.value === 'filtered') {
        e.disabled = isEmpty;
      }
    });
    clearSelection();
  },
  {
    immediate: true,
    deep: true,
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
  selections,
  (selection) => {
    exportDropData.value.forEach((drop: IDropList) => {
      // 已选资源
      if (['selected'].includes(drop.value)) {
        drop.disabled = !selection.length;
      }
    });
  },
  { deep: true },
);
// 侦听返回的数据和表头 filter 变化，更新空数据展示状态
watch(
  [tableData, checkedGrantDimensionFilterOptions, checkedGrantTypeFilterOptions],
  () => {
    clearSelection();
    updateTableEmptyConfig();
  },
  { deep: true },
);

function clearSelection() {
  isAllChecked.value = false;
  selections.value = [];
  appTableRef.value?.clearSelection();
};

const handleCheckAllClick = (checked: boolean) => {
  isAllChecked.value = checked;
  if (checked) {
    selections.value = tableData.value.filter(row => row.renewable);
  }
  else {
    clearSelection();
  }
};

const getFilterData = (payload: Record<string, string>, curData: Record<string, string>) => {
  const { id, name } = payload;
  filterData.value[curData.id] = payload.id;
  const hasData = filterValues.value.find((item: Record<string, any>) => [curData.id].includes(item.id));
  if (hasData) {
    hasData.values = [{
      id,
      name,
    }];
  }
  else {
    filterValues.value.push({
      id: curData.id,
      name: curData.name,
      values: [{
        id,
        name,
      }],
    });
  }
  if (['ALL'].includes(payload.id)) {
    delete filterData.value[curData.id];
    filterValues.value = filterValues.value.filter((item: Record<string, any>) => ![curData.id].includes(item.id));
  }
};

const renderGrantDimensionLabel = () => {
  return h('div', { class: 'application-permission-custom-label' }, [
    h(
      TableHeaderFilter,
      {
        hasAll: true,
        columnLabel: t('授权维度'),
        selectValue: singleSelectData.value.grant_dimension,
        list: grantDimensionFilterOptions.value.list,
        onSelected: (select: Record<string, string>) => {
          const curData = {
            name: t('授权维度'),
            id: 'grant_dimension',
          };
          getFilterData(select, curData);
        },
      },
    ),
  ]);
};

const setTableColumns = () => {
  return [
    {
      label: () => {
        return (
          <BkCheckbox
            v-model={isAllChecked.value}
            onChange={(checked: boolean) => handleCheckAllClick(checked)}
          />
        );
      },
      minWidth: 60,
      align: 'center',
      render: ({ row }: { row: IPermission }) => {
        return (
          <BkCheckbox
            v-bk-tooltips={{
              content: t('权限有效期大于 360 天时，暂无法续期'),
              disabled: row.renewable,
            }}
            disabled={!row.renewable}
            modelValue={!!selections.value.find(item => item.id === row.id)}
            onChange={(checked: boolean) => handleCheckboxChange(checked, row)}
          />
        );
      },
    },
    {
      label: t('蓝鲸应用ID'),
      field: 'bk_app_code',
    },
    {
      label: renderGrantDimensionLabel,
      field: 'grant_dimension',
      render: ({ row }: { row: IPermission }) => {
        return (
          <span class="ag-auto-text">
            { getSearchDimensionText(row.grant_dimension) }
          </span>
        );
      },
    },
    {
      label: t('资源名称'),
      field: 'resource_name',
      render: ({ row }: { row: IPermission }) => {
        return (
          <span>{ row.resource_name || '--' }</span>
        );
      },
    },
    {
      label: t('请求路径'),
      field: 'resource_path',
      render: ({ row }: { row: IPermission }) => {
        return (
          <span>{ row.resource_path || '--' }</span>
        );
      },
    },
    {
      label: t('有效期'),
      field: 'expires',
      render: ({ row }: { row: IPermission }) => {
        return (
          <span style={{ color: permissionStore.getDurationTextColor(row.expires) }}>
            { permissionStore.getDurationText(row.expires) }
          </span>
        );
      },
    },
    {
      label: t('授权类型'),
      field: 'grant_type',
      render: ({ row }: { row: IPermission }) => {
        return (
          <span>
            { t(['initialize'].includes(row.grant_type) ? '主动授权' : '申请审批') }
          </span>
        );
      },
    },
    {
      label: t('操作'),
      field: 'operate',
      fixed: 'right',
      width: 150,
      render: ({ row }: { row: IPermission }) => {
        return (
          <div>
            <BkButton
              class="m-r-10px"
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
            </BkButton>
            <BkButton
              theme="primary"
              text
              onClick={() => handleRemove(row)}
            >
              { t('删除') }
            </BkButton>
          </div>
        );
      },
    },
  ];
};

const handleCheckboxChange = (checked: boolean, row: IPermission) => {
  if (checked) {
    selections.value.push(row);
  }
  else {
    selections.value = selections.value.filter(item => item.id !== row.id);
  }
};

const getBkAppCodes = async () => {
  const appCodeOption = filterConditions.value.find(
    condition => condition.id === 'bk_app_code',
  );
  const response = ((await getResourcePermissionAppList(apigwId.value)) as string[]) || [];
  appCodeOption.children = response.map(appCode => ({
    id: appCode,
    name: appCode,
  }));
  componentKey.value += 1;
};

// 获取资源列表数据
const getApigwResources = async () => {
  const pageParams = {
    limit: 3000,
    order_by: 'path',
  };
  const resourceIdOption = filterConditions.value.find(
    condition => condition.id === 'resource_id',
  );
  const response = await getResourceListData(apigwId.value, pageParams);
  const resources: IResource[] = response.results || [];
  const results = resources.map(resource => ({
    id: resource.id,
    name: resource.name,
    path: resource.path,
    method: resource.method,
    resourceName: `${resource.method}：${resource.path}`,
  }));
  resourceList.value = sortByKey(results, 'name');
  if (resourceIdOption) {
    resourceIdOption.children = resourceList.value.map(item => ({
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
      message: t('导出成功！'),
      theme: 'success',
    });
  }
  catch (error: unknown) {
    const e = error as { message: string };
    Message({
      message: e?.message || t('导出失败'),
      theme: 'error',
    });
  }
  finally {
    exportParams.value = { export_type: 'all' };
  }
};

// 确定续期
const handleBatchConfirm = async () => {
  batchApplySliderConf.saveLoading = true;
  const data: IBatchUpdateParams = {
    resource_dimension_ids: [] as number[],
    gateway_dimension_ids: [] as number[],
    expire_days: expireDays.value,
  };
  if (selectedResourcePermList.value.length > 0) {
    data.resource_dimension_ids = selectedResourcePermList.value.map(
      permission => permission.id,
    );
  }
  if (selectedApiPermList.value.length > 0) {
    data.gateway_dimension_ids = selectedApiPermList.value.map(
      permission => permission.id,
    );
  }
  try {
    await batchUpdatePermission(apigwId.value, data);
    Message({
      theme: 'success',
      message: t('续期成功！'),
    });
    batchApplySliderConf.isShow = false;
    ApplyDialogConf.isShow = false;
    getList();
  }
  finally {
    batchApplySliderConf.saveLoading = false;
    ApplyDialogConf.saveLoading = false;
  }
};

// 批量续期
const handleBatchApplyPermission = () => {
  curSelections.value = [...selections.value];
  batchApplySliderConf.isShow = true;
};

// 单个续期
const handleSingleApply = (data: IPermission) => {
  curSelections.value = [data];
  ApplyDialogConf.isShow = true;
};

const handleRemove = (data: IPermission) => {
  curPermission.value = data;
  removeDialogConf.isShow = true;
};

// 删除权限
const handleRemovePermission = async () => {
  const { id, grant_dimension } = curPermission.value;
  const ids = [id];
  const fetchMethod = ['resource'].includes(grant_dimension) ? deleteResourcePermission : deleteApiPermission;
  await fetchMethod(apigwId.value, { ids });
  removeDialogConf.isShow = false;
  Message({
    theme: 'success',
    message: t('删除成功！'),
  });
  clearSelection();
  getList();
};

// 主动授权
const handleAuthShow = () => {
  authSliderConf.isShow = true;
};

// 主动授权保存
const handleSave = () => {
  Message({
    theme: 'success',
    message: t('授权成功！'),
  });
  curAuthData.value = cloneDeep(curAuthDataBack.value);
  clearSelection();
  getList();
};

const handleClearFilterKey = () => {
  filterData.value = {};
  filterValues.value = [];
  checkedGrantDimensionFilterOptions.value = [];
  checkedGrantTypeFilterOptions.value = [];
};

const updateTableEmptyConfig = () => {
  const searchParams = { ...filterData.value };
  filterValues.value?.forEach((item) => {
    searchParams[item.id] = Array.isArray(item.values) ? item.values?.[0]?.id : '';
  });
  const list = Object.values(searchParams).filter(item => item !== '');
  tableEmptyConf.value.isAbnormal = pagination.value.abnormal;
  if (
    list.length
    || checkedGrantDimensionFilterOptions.value.length
    || checkedGrantTypeFilterOptions.value.length
  ) {
    tableEmptyConf.value.emptyType = 'searchEmpty';
    return;
  }
  tableEmptyConf.value.emptyType = '';
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
</script>

<style lang="scss" scoped>
.attention-dialog {
  :deep(.bk-dialog-header) {
    padding: 5px !important;
  }

  :deep(.bk-modal-footer) {
    background-color: #ffffff;
    border-top: none;
  }

  .title {
    font-size: 20px;
    text-align: center;
    color: #313238;
  }

  .sub-title {
    font-size: 14px;
    color: #63656e;
    line-height: 1.5;
    text-align: center;
    margin-bottom: 20px;
    margin-top: 14px;
  }

  .btn {
    text-align: center;
  }
}
</style>
