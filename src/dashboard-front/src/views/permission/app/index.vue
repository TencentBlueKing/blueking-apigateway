<template>
  <div class="permission-app-container page-wrapper-padding">
    <div class="header mb5">
      <div class="header-btn flex-1 flex-row align-items-center">
        <span class="mr10" v-bk-tooltips="{ content: t('请选择待续期的权限'), disabled: selections.length }">
          <bk-button theme="primary" class="mr5" @click="handleBatchApplyPermission" :disabled="!selections.length">
            {{ t('批量续期') }}
          </bk-button>
        </span>
        <bk-dropdown-menu
          trigger="click"
          class="mr5"
          @show="() => isExportDropdownShow = true"
          @hide="() => isExportDropdownShow = false"
          font-size="medium"
        >
          <ag-dropdown :text="t('导出')" :dropdown-list="exportDropData" @on-change="handleExport"></ag-dropdown>
        </bk-dropdown-menu>
        <bk-button class=" mr10" @click="handleAuthShow"> {{ t('主动授权') }} </bk-button>
      </div>
      <bk-form class="flex-row ">
        <bk-form-item label="" class="mb0" label-width="10">
          <bk-search-select
            v-model="filterValues"
            :data="filterConditions"
            :placeholder="t('搜索')"
            :clearable="true"
            :key="componentKey"
            :value-split-code="'+'"
            unique-select
            style="width: 450px; background:#fff"
          />
        </bk-form-item>
      </bk-form>
    </div>
    <div class="app-content">
      <bk-loading :loading="isLoading">
        <bk-table
          show-overflow-tooltip
          class="perm-app-table mt15"
          :data="tableData"
          size="small"
          :pagination="pagination"
          border="outer"
          remote-pagination
          @page-limit-change="handlePageSizeChange"
          @page-value-change="handlePageChange"
          @selection-change="handleSelectionChange"
          @select-all="handleSelecAllChange"
        >
          <bk-table-column type="selection" width="60" align="center"></bk-table-column>
          <bk-table-column :label="t('蓝鲸应用ID')" prop="bk_app_code"></bk-table-column>
          <bk-table-column :label="t('搜索维度')">
            <template #default="{ row }: { row: IPermission }">
              <span class="ag-auto-text">
                {{ getSearchDimensionText(row.grant_dimension) }}
              </span>
            </template>
          </bk-table-column>
          <bk-table-column :label="t('资源名称')">
            <template #default="{ row }: { row: IPermission }">
              {{ row.resource_name || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('请求路径')">
            <template #default="{ row }: { row: IPermission }">
              <span class="ag-auto-text">
                {{ row.resource_path || '--' }}
              </span>
            </template>
          </bk-table-column>
          <bk-table-column :label="t('过期时间')">
            <template #default="{ row }: { row: IPermission }">
              {{ row.expires || t('永久有效') }}
            </template>
          </bk-table-column>
          <bk-table-column width="150" :label="t('授权类型')">
            <template #default="{ row }: { row: IPermission }">
              {{ row.grant_type === 'initialize' ? t('主动授权') : t('申请审批') }}
            </template>
          </bk-table-column>
          <bk-table-column width="150" :label="t('操作')">
            <template #default="{ row }: { row: IPermission }">
              <template v-if="row.renewable">
                <bk-button class="mr10" theme="primary" text @click="handleSingleApply(row)"> {{ t('续期') }}</bk-button>
              </template>
              <template v-else>
                <span v-bk-tooltips="renewableConfig">
                  <bk-button class="mr10" theme="primary" text disabled> {{ t('续期') }} </bk-button>
                </span>
              </template>
              <bk-button theme="primary" text @click="handleRemove(row)"> {{ t('删除') }} </bk-button>
            </template>
          </bk-table-column>
          <template #empty>
            <TableEmpty
              :keyword="tableEmptyConf.keyword"
              :abnormal="tableEmptyConf.isAbnormal"
              @reacquire="getList"
              @clear-filter="handleClearFilterKey"
            />
          </template>
        </bk-table>
      </bk-loading>
    </div>

    <!-- 主动授权sideslider -->
    <bk-sideslider
      v-model:isShow="authSliderConf.isShow"
      :title="authSliderConf.title"
      :width="800"
      quick-close
      :before-close="handleBeforeClose"
      class="auth-sideslider"
      @hidden="handleHidden"
    >
      <template #default>
        <p class="ag-span-title"> {{ t('你将对指定的蓝鲸应用添加访问资源的权限') }} </p>
        <bk-form class="mb30 ml15" :label-width="120" :model="curAuthData">
          <bk-form-item :label="t('蓝鲸应用ID')" :required="true">
            <bk-input class="code-input" :placeholder="t('请输入应用ID')" v-model="curAuthData.bk_app_code">
            </bk-input>
          </bk-form-item>
          <bk-form-item :label="t('有效时间')" :required="true">
            <bk-radio-group v-model="curAuthData.expire_type">
              <bk-radio label="custom" class="mr15">
                <bk-input
                  type="number" :min="0" v-model="curAuthData.expire_days" class="mr5 w85"
                  @focus="curAuthData.expire_type = 'custom'">
                </bk-input>
                {{ t('天') }}
              </bk-radio>
              <bk-radio label="None"> {{ t('永久有效') }} </bk-radio>
            </bk-radio-group>
          </bk-form-item>
        </bk-form>
        <p class="ag-span-title"> {{ t('请选择要授权的资源') }} </p>
        <div class="ml20">
          <bk-radio-group class="ag-resource-radio" v-model="curAuthData.dimension">
            <bk-radio label="api">
              {{ t('按网关') }}
              <span v-bk-tooltips="t('包括网关下所有资源，包括未来新创建的资源')">
                <i class="apigateway-icon icon-ag-help"></i>
              </span>
            </bk-radio>
            <bk-radio label="resource" class="ml0">
              {{ t('按资源') }}
              <span v-bk-tooltips="t('仅包含当前选择的资源')">
                <i class="apigateway-icon icon-ag-help"></i>
              </span>
            </bk-radio>
          </bk-radio-group>
          <div class="ag-transfer-box" v-if="curAuthData.dimension === 'resource'">
            <bk-transfer
              ext-cls="resource-transfer-wrapper" :source-list="resourceList" :display-key="'name'"
              :setting-key="'id'" :title="[t('未选资源'), t('已选资源')]" :searchable="true" @change="handleResourceChange">
              <template #source-option="data">
                <div class="transfer-source-item">
                  {{ data.name }}
                </div>
              </template>
              <template #target-option="data">
                <div class="transfer-source-item">
                  {{ data.name }}
                </div>
              </template>
            </bk-transfer>
          </div>
          <div class="action mt20">
            <bk-button theme="primary" class="mr10" @click="handleSave"> {{ t('保存') }} </bk-button>
            <bk-button @click="handleSidesliderCancel"> {{ t('取消') }} </bk-button>
          </div>
        </div>
      </template>
    </bk-sideslider>

    <!-- 删除dialog -->
    <bk-dialog
      :is-show="removeDialogConf.isShow" theme="primary" :width="940" :title="removeDialogConfTitle"
      :quick-close="true" @closed="removeDialogConf.isShow = false" @confirm="handleRemovePermission">
      <div>
        <bk-table :data="[curPermission]" size="small" class="mb15">
          <bk-table-column :label="t('蓝鲸应用ID')">
            <template #default="{ row }: { row: IPermission }">
              {{ row.bk_app_code || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('搜索维度')">
            <template #default="{ row }: { row: IPermission }">
              <span class="ag-auto-text">
                {{ getSearchDimensionText(row.grant_dimension) }}
              </span>
            </template>
          </bk-table-column>
          <bk-table-column :label="t('资源名称')">
            <template #default="{ row }: { row: IPermission }">
              {{ row.resource_name || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('请求路径')">
            <template #default="{ row }: { row: IPermission }">
              {{ row.resource_path || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('过期时间')">
            <template #default="{ row }: { row: IPermission }">
              {{ row.expires ? row.expires : t('永久有效') }}
            </template>
          </bk-table-column>
        </bk-table>
      </div>
    </bk-dialog>

    <!--  批量续期 slider  -->
    <bk-sideslider
      v-model:isShow="batchApplySliderConf.isShow"
      width="960"
      :title="t('批量续期')"
      quick-close
      @hidden="batchApplySliderConf.isShow = false"
    >
      <template #default>
        <div class="renew-slider-content-wrap">
          <ExpDaySelector v-model="expireDays" form-type="vertical" />
          <div class="collapse-wrap">
            <bk-collapse
              v-model="activeIndex"
              class="collapse-cls"
              use-card-theme
            >
              <bk-collapse-panel name="resource">
                <template #header>
                  <div class="panel-header">
                    <angle-up-fill
                      :class="[activeIndex?.includes('resource') ? 'panel-header-show' : 'panel-header-hide']"
                    />
                    <div class="title">{{ t('按资源') }}</div>
                  </div>
                </template>
                <template #content>
                  <bk-table
                    :data="selectedResourcePermList"
                    size="small"
                    :max-height="250"
                    :border="['row', 'outer']"
                  >
                    <bk-table-column width="180" :label="t('蓝鲸应用ID')" prop="bk_app_code"></bk-table-column>
                    <bk-table-column :label="t('资源名称')">
                      <template #default="{ row }">
                        {{ row.resource_name || '--' }}
                      </template>
                    </bk-table-column>
                    <bk-table-column
                      :label="t('续期前的过期时间')"
                      :width="392"
                    >
                      <template #default="{ row }">
                        {{ row.expires || '--' }}
                        <span class="ag-strong default" v-if="!row.renewable && row.expires">
                          {{ t('(有效期大于30天)') }}
                        </span>
                      </template>
                    </bk-table-column>
                    <bk-table-column width="180" :label="t('续期后的过期时间')">
                      <template #default="{ row }">
                        <span class="ag-strong danger" v-if="!row.renewable"> {{ t('不可续期') }} </span>
                        <span v-else class="ag-strong warning">{{ getExpTimeAfterRenew(row) }}</span>
                      </template>
                    </bk-table-column>
                  </bk-table>
                </template>
              </bk-collapse-panel>
              <bk-collapse-panel name="gateway">
                <template #header>
                  <div class="panel-header">
                    <angle-up-fill
                      :class="[activeIndex?.includes('gateway') ? 'panel-header-show' : 'panel-header-hide']"
                    />
                    <div class="title">{{ t('按网关') }}</div>
                  </div>
                </template>
                <template #content>
                  <bk-table
                    :data="selectedApiPermList"
                    size="small"
                    :max-height="250"
                    :border="['row', 'outer']"
                  >
                    <bk-table-column width="180" :label="t('蓝鲸应用ID')" prop="bk_app_code"></bk-table-column>
                    <bk-table-column :label="t('资源名称')">
                      <template #default="{ row }">
                        {{ row.resource_name || '--' }}
                      </template>
                    </bk-table-column>
                    <bk-table-column
                      :label="t('续期前的过期时间')"
                      :width="392"
                    >
                      <template #default="{ row }">
                        {{ row.expires || '--' }}
                        <span class="ag-strong default" v-if="!row.renewable && row.expires">
                          {{ t('(有效期大于30天)') }}
                        </span>
                      </template>
                    </bk-table-column>
                    <bk-table-column width="180" :label="t('续期后的过期时间')">
                      <template #default="{ row }">
                        <span class="ag-strong danger" v-if="!row.renewable"> {{ t('不可续期') }} </span>
                        <span v-else class="ag-strong warning">{{ getExpTimeAfterRenew(row) }}</span>
                      </template>
                    </bk-table-column>
                  </bk-table>
                </template>
              </bk-collapse-panel>
            </bk-collapse>
          </div>
        </div>
      </template>
      <template #footer>
        <div>
          <bk-button
            theme="primary"
            :disabled="applyCount === 0"
            :loading="isBatchApplyLoading"
            @click="handleBatchConfirm"
          > {{ t('确定') }} </bk-button>
          <bk-button class="ml8" @click="batchApplySliderConf.isShow = false"> {{ t('取消') }} </bk-button>
        </div>
      </template>
    </bk-sideslider>

    <!--  单个续期 dialog  -->
    <bk-dialog
      v-model:is-show="isApplyDialogShow"
      theme="primary"
      :width="860"
      :title="t('续期')"
      quick-close
    >
      <div>
        <ExpDaySelector v-model="expireDays" />
        <bk-table :data="curSelections" size="small" :max-height="250" class="mb30">
          <bk-table-column width="100" :label="t('蓝鲸应用ID')" prop="bk_app_code"></bk-table-column>
          <bk-table-column :label="t('资源名称')">
            <template #default="{ row }">
              {{ row.resource_name || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('续期前的过期时间')">
            <template #default="{ row }">
              {{ row.expires || '--' }}
              <span class="ag-strong default" v-if="!row.renewable && row.expires">
                {{ t('(有效期大于30天)') }}
              </span>
            </template>
          </bk-table-column>
          <bk-table-column :label="t('续期后的过期时间')">
            <template #default="{ row }">
              <span class="ag-strong danger" v-if="!row.renewable"> {{ t('不可续期') }} </span>
              <span v-else class="ag-strong warning ">{{ getExpTimeAfterRenew(row) }}</span>
            </template>
          </bk-table-column>
        </bk-table>
      </div>
      <template #footer>
        <template v-if="applyCount">
          <bk-button
            theme="primary" :disabled="applyCount === 0" @click="handleBatchConfirm"
            :loading="isBatchApplyLoading"> {{ t('确定') }} </bk-button>
        </template>
        <template v-else>
          <bk-popover placement="top" :content="t('无可续期的权限')">
            <bk-button theme="primary" :disabled="true"> {{ t('确定') }} </bk-button>
          </bk-popover>
        </template>
        <bk-button @click="isApplyDialogShow = false"> {{ t('取消') }} </bk-button>
      </template>
    </bk-dialog>
  </div>
</template>

<script setup lang="ts">
import { isEqual } from 'lodash';
import {
  InfoBox,
  Message,
} from 'bkui-vue';
import {
  computed,
  reactive,
  ref,
  watch,
} from 'vue';
import { useI18n } from 'vue-i18n';
import {
  sortByKey,
  timeFormatter,
} from '@/common/util';
import {
  authApiPermission,
  authResourcePermission,
  batchUpdatePermission,
  deleteApiPermission,
  deleteResourcePermission,
  exportPermissionList,
  fetchPermissionList,
  getResourceListData,
  getResourcePermissionAppList,
} from '@/http';
import { useCommon } from '@/store';
import {
  useQueryList,
  useSelection,
} from '@/hooks';
import { IDropList } from '@/types';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import ExpDaySelector from '@/views/permission/app/comps/exp-day-selector.vue';
import agDropdown from '@/components/ag-dropdown.vue';
import TableEmpty from '@/components/table-empty.vue';
import {
  IFilterValues,
  IPermission,
  IResource,
} from './types';
import {
  IAuthData,
  IBatchUpdateParams,
  IExportParams,
  IFilterParams,
} from '@/http/permission';
import dayjs from 'dayjs';

const { t } = useI18n();
const common = useCommon();
const { apigwId } = common; // 网关id

const filterData = ref<IFilterParams>({});

// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList<IPermission>(fetchPermissionList, filterData);

// checkbox hooks
const {
  selections,
  handleSelectionChange,
  handleSelecAllChange,
  resetSelections,
} = useSelection();

const isExportDropdownShow = ref(false);
const resourceList = ref<IResource[]>([]);
const isBatchApplyLoading = ref(false);
const curPermission = ref<Partial<IPermission>>({ bk_app_code: '', detail: [], id: -1 });
const curSelections = ref([]);
const renewableConfig = reactive({
  content: t('权限有效期大于 30 天时，暂无法续期'), placement: 'left',
});

// 导出下拉
const exportDropData = ref<IDropList[]>([
  { value: 'all', label: t('全部应用权限') },
  { value: 'filtered', label: t('已筛选应用权限'), disabled: true },
  { value: 'selected', label: t('已选应用权限'), disabled: true },
]);

// 主动授权config
const authSliderConf = reactive({
  isLoading: false,
  isShow: false,
  title: t('主动授权'),
});
// 当前授权数据
const curAuthData = ref<IAuthData>({
  bk_app_code: '',
  expire_type: 'custom',
  expire_days: 180,
  resource_ids: [],
  dimension: 'api',
});

const expireDays = ref<0 | 180 | 360>(0);
const activeIndex = ref(['resource', 'gateway']);

const tableEmptyConf = ref<{keyword: string, isAbnormal: boolean}>({
  keyword: '',
  isAbnormal: false,
});
// 批量续期dialog
const batchApplySliderConf = reactive({
  isShow: false,
});
// 单个续期 dialog
const isApplyDialogShow = ref(false);
// 删除dialog
const removeDialogConf = reactive({
  isShow: false,
});
// 导出参数
const exportParams = ref<IExportParams>({
  export_type: '',
});

const filterValues = ref<IFilterValues[]>([]);
const componentKey = ref(0);
const filterConditions = ref([
  {
    name: t('维度'),
    id: 'grant_dimension',
    children: [
      {
        id: 'resource',
        name: t('资源'),
      },
      {
        id: 'api',
        name: t('网关'),
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

// 可续期的数量
const applyCount = computed(() => {
  return curSelections.value.filter((item: { renewable: boolean; }) => item.renewable).length;
});
// 删除dialog title
const removeDialogConfTitle = computed(() => {
  // return t(`确定要删除蓝鲸应用【${curPermission.value.bk_app_code}】的权限？`);
  return t('确定要删除蓝鲸应用【{appCode}】的权限？', { appCode: curPermission.value.bk_app_code });
});

// 资源维度权限列表
const selectedResourcePermList = computed(() => curSelections.value.filter(perm => perm.grant_dimension === 'resource'));

// 网关维度权限列表
const selectedApiPermList = computed(() => curSelections.value.filter(perm => perm.grant_dimension === 'api'));

// 监听搜索是否变化
watch(
  () => filterValues.value,
  (v) => {
    resetSelections();
    filterData.value = {};
    let isEmpty = false;
    if (v) {
      v.forEach((item) => {
        filterData.value[item.id] = item.values[0].id;
      });
      isEmpty = v.length === 0;
    }
    exportDropData.value.forEach((e: IDropList) => {
      // 已选资源
      if (e.value === 'filtered') {
        e.disabled = isEmpty;
      }
    });
  },
  { immediate: true, deep: true },
);
// 监听授权有效时间的类型
watch(
  () => curAuthData.value.expire_type,
  (v: string) => {
    if (v === 'custom') {
      curAuthData.value.expire_days = 180;
    } else {
      curAuthData.value.expire_days = null;
    }
  },
);
watch(
  () => selections.value,
  (v: number[]) => {
    exportDropData.value.forEach((e: IDropList) => {
      // 已选资源
      if (e.value === 'selected') {
        e.disabled = !v.length;
      }
    });
  },
  {  deep: true },
);
watch(
  () => filterData.value, () => {
    // filterData 变化重新请求列表数据，数据还未返回时执行 updateTableEmptyConfig 偶现问题，因此加入延迟
    setTimeout(() => {
      updateTableEmptyConfig();
    }, 100);
  },
  {
    deep: true,
  },
);

const getBkAppCodes = async () => {
  const appCodeOption = filterConditions.value.find(condition => condition.id === 'bk_app_code');
  const response = await getResourcePermissionAppList(apigwId) as string[] || [];
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
  const resourceIdOption = filterConditions.value.find(condition => condition.id === 'resource_id');
  const response = await getResourceListData(apigwId, pageParams);
  const resources: IResource[] = response.results || [];
  const results = resources.map(resource => ({
    id: resource.id,
    name: resource.name,
    path: resource.path,
    method: resource.method,
    resourceName: `${resource.method}：${resource.path}`,
  }));
  resourceList.value = sortByKey(results, 'name');
  resourceIdOption.children = resourceList.value.map(item => ({
    id: item.id,
    name: item.name,
  }));
  componentKey.value += 1;
};

// 导出
const handleExport = async ({ value }: { value: 'all' | 'selected' | 'filtered' }) => {
  exportParams.value.export_type = value;
  switch (value) {
    case 'selected':
      if (selections.value.some(p => p.grant_dimension === 'resource')) {
        exportParams.value.resource_permission_ids = selections.value.filter(p => p.grant_dimension === 'resource').map(e => e.id);
      }
      if (selections.value.some(p => p.grant_dimension === 'api')) {
        exportParams.value.gateway_permission_ids = selections.value.filter(p => p.grant_dimension === 'api').map(e => e.id);
      }
      break;
    case 'filtered':
      filterValues.value?.forEach((item) => {
        const value = item.values[0];
        if (value) {
          exportParams.value[item.id] = String(value.id);
        }
      });
      break;
    case 'all':
      if (tableData.value.length < 1) {
        Message({
          message: t('没有数据'),
          theme: 'warning',
        });
        return;
      }
      break;
  }
  try {
    const response = await exportPermissionList(apigwId, exportParams.value);
    if (response.success) {
      Message({
        message: t('导出成功！'),
        theme: 'success',
      });
    }
  } catch (error: unknown) {
    const e = error as { message: string };
    Message({
      message: e.message || t('导出失败'),
      theme: 'error',
    });
  } finally {
    exportParams.value = {
      export_type: '',
    };
  }
};

// 确定续期
const handleBatchConfirm = async () => {
  if (isBatchApplyLoading.value) return;
  isBatchApplyLoading.value = true;
  const data: IBatchUpdateParams = {
    resource_dimension_ids: [] as number[],
    gateway_dimension_ids: [] as number[],
    expire_days: expireDays.value,
  };

  if (selectedResourcePermList.value.length > 0) {
    data.resource_dimension_ids = selectedResourcePermList.value.map(permission => permission.id);
  }

  if (selectedApiPermList.value.length > 0) {
    data.gateway_dimension_ids = selectedApiPermList.value.map(permission => permission.id);
  }

  try {
    await batchUpdatePermission(apigwId, data);
    batchApplySliderConf.isShow = false;
    await getList(fetchPermissionList);
    resetSelections();
    Message({
      theme: 'success',
      message: t('续期成功！'),
    });
    isApplyDialogShow.value = false;
  } catch (error: unknown) {
    const e = error as { message: string };
    Message({
      message: e.message || t('续期失败'),
      theme: 'error',
    });
  } finally {
    isBatchApplyLoading.value = false;
  }
};
// 批量续期
const handleBatchApplyPermission = () => {
  curSelections.value = selections.value;
  batchApplySliderConf.isShow = true;
};
// 单个续期
const handleSingleApply = (data: IPermission) => {
  curSelections.value = [data];
  isApplyDialogShow.value = true;
};

// 删除text
const handleRemove = (data: IPermission) => {
  curPermission.value = data;
  removeDialogConf.isShow = true;
};
// 删除 dialog btn
const handleRemovePermission = async () => {
  try {
    const dimension = curPermission.value.grant_dimension;
    const ids = [curPermission.value.id];
    const fetchMethod = dimension === 'resource' ? deleteResourcePermission : deleteApiPermission;
    await fetchMethod(apigwId, { ids });
    removeDialogConf.isShow = false;
    await getList(fetchPermissionList);
    Message({
      theme: 'success',
      message: t('删除成功！'),
    });
  } catch (error: unknown) {
    const e = error as { message: string };
    Message({
      message: e.message || t('删除失败'),
      theme: 'error',
    });
  }
};

// 初始化授权data
const initAuthData = () => {
  curAuthData.value = {
    bk_app_code: '',
    expire_type: 'custom',
    expire_days: 180,
    resource_ids: [],
    dimension: 'api',
  };
};
// 主动授权
const handleAuthShow = () => {
  authSliderConf.isShow = true;
};
// 主动授权关闭前
const handleBeforeClose = () => {
  const initData = {
    bk_app_code: '',
    expire_type: 'custom',
    expire_days: 180,
    resource_ids: [] as number[],
    dimension: 'api',
  };
  const isSame = isEqual(initData, curAuthData.value);
  if (!isSame) {
    InfoBox({
      title: t('确认离开当前页？'),
      subTitle: t('离开将会导致未保存信息丢失'),
      confirmText: t('离开'),
      cancelText: t('取消'),
      onConfirm() {
        authSliderConf.isShow = false;
      },
      onClosed() {
        return false;
      },
    });
  } else {
    authSliderConf.isShow = false;
  }
};

// 选择授权的资源数量发生改变触发
const handleResourceChange = (sourceList: IResource[], targetList: IResource[], targetValueList: number[]) => {
  curAuthData.value.resource_ids = targetValueList;
};
// 主动授权关闭btn
const handleHidden = () => {
  initAuthData();
};
// 主动授权 不同选项，数据的更改
const formatData = () => {
  const params: IAuthData = JSON.parse(JSON.stringify(curAuthData.value));
  if (params.expire_type === 'None') {
    params.expire_days = null;
  }
  if (params.dimension === 'api') {
    params.resource_ids = null;
  }
  return params;
};
// 核查授权数据
const checkDate = (params: IAuthData) => {
  const codeReg = /^[a-z][a-z0-9-_]+$/;
  if (!params.bk_app_code) {
    Message({
      theme: 'error',
      message: t('请输入蓝鲸应用ID'),
    });
    return false;
  }

  if (!codeReg.test(params.bk_app_code)) {
    Message({
      theme: 'error',
      delay: 5000,
      message: t('蓝鲸应用ID格式不正确，只能包含：小写字母、数字、连字符(-)、下划线(_)，首字母必须是字母'),
    });
    return false;
  }

  if (params.expire_type === 'custom' && !params.expire_days) {
    Message({
      theme: 'error',
      message: t('请输入有效时间'),
    });
    return false;
  }

  if (params.dimension === 'resource' && !params.resource_ids.length) {
    Message({
      theme: 'error',
      message: t('请选择要授权的资源'),
    });
    return false;
  }
  return true;
};
// 授权接口
const authAppDimension = async (params: IAuthData) => {
  const fetchMethod = params.dimension === 'resource' ? authResourcePermission : authApiPermission;
  try {
    await fetchMethod(apigwId, params);
    authSliderConf.isShow = false;
    await getList(fetchPermissionList);
    Message({
      theme: 'success',
      message: t('授权成功！'),
    });
  } catch (error: unknown) {
    const e = error as { message: string };
    Message({
      message: e.message || t('授权失败'),
      theme: 'error',
    });
  }
};
// 主动授权保存btn
const handleSave = () => {
  const params = formatData();
  const isLegal = checkDate(params);
  if (isLegal) {
    authAppDimension(params);
  }
};
// 主动授权取消btn
const handleSidesliderCancel = () => {
  authSliderConf.isShow = false;
};

const handleClearFilterKey = () => {
  filterData.value = {};
  filterValues.value = [];
  getList();
  updateTableEmptyConfig();
};

const updateTableEmptyConfig = () => {
  const searchParams = {
    ...filterData.value,
  };
  filterValues.value?.forEach((item) => {
    searchParams[item.id] = item.values[0]?.id;
  });
  const list = Object.values(searchParams).filter(item => item !== '');
  tableEmptyConf.value.isAbnormal = pagination.value.abnormal;
  if (list.length && !tableData.value.length) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (list.length) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const getSearchDimensionText = (raw: string | null) => {
  if (raw === 'resource') return t('按资源');
  if (raw === 'api') return t('按网关');
  return '--';
};

// 计算续期后的过期时间
const getExpTimeAfterRenew = (permission: IPermission, days?: number) => {
  const _days = days || expireDays.value;
  if (!permission.expires || _days === 0) return t('永久');

  try {
    return timeFormatter(`${dayjs().add(_days * 24 * 60 * 60 * 1000, 'millisecond')}`);
  } catch {
    Message({
      theme: 'error',
      message: t('日期格式错误'),
    });
    return '--';
  }
};

const init = () => {
  getBkAppCodes();
  getApigwResources();
};

init();

</script>

<style lang="scss" scoped>
.w85 {
  width: 85px;
}

.w88 {
  width: 88px;
}

.w150 {
  width: 150px;
}

.w400 {
  width: 400px;
}
.ag-strong {
    font-weight: bold;
    color: #63656E;
    font-style: normal;

    &.default {
        color: #979BA5;
    }

    &.primary {
        color: #3a84ff;
    }

    &.success {
        color: #34d97b;
    }

    &.danger {
        color: #ff5656;
    }

    &.warning {
        color: #ffb400;
    }
}
.ag-span-title {
  font-size: 14px;
  font-weight: bold;
  color: #63656E;
  margin-bottom: 20px;
  line-height: 1;
}

.ag-resource-radio {
  display: block;

  label {
    display: block;
    margin-bottom: 10px;
  }
}

.perm-app-table {
  :deep(.bk-table-head) {
    scrollbar-color: transparent transparent;
  }
  :deep(.bk-table-body) {
    scrollbar-color: transparent transparent;
  }
}

.ag-transfer-box {
  padding: 20px;
  background: #FAFBFD;
  border: 1px solid #F0F1F5;
  border-radius: 2px;

  .bk-transfer {
    color: #63656e;

    :deep(.header) {
      font-weight: normal;
    }

    .transfer-source-item {
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
    }
  }
}

.search-input {
  background-color: #fff;
}

.header {
  display: flex;
  justify-content: space-between;
}

.app-content {
  height: calc(100% - 90px);
  min-height: 600px;
}

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
    text-align: center;
    color: #313238;
  }

  .sub-title {
    font-size: 14px;
    color: #63656e;
    line-height: 1.5;
    text-align: center;
    margin-bottom: 21px;
    margin-top: 14px;
  }

  .btn {
    text-align: center;
  }
}
:deep(.app-content){
  .bk-exception{
    height: 280px;
    max-height: 280px;
    justify-content: center;
  }
}

.renew-slider-content-wrap {
  padding: 20px 24px;
}

.collapse-wrap {
  //padding: 24px 24px 0 24px;

  :deep(.collapse-cls) {
    margin-bottom: 24px;

    .bk-collapse-item {
      //background: #fff;
      box-shadow: none;
      margin-bottom: 16px;
      background-color: #F0F1F5;
    }
  }

  .panel-header {
    display: flex;
    align-items: center;
    padding: 10px 12px;
    color: #63656E;
    cursor: pointer;

    .title {
      font-weight: 700;
      font-size: 14px;
      margin-left: 8px;
    }

    .panel-header-show {
      transition: .2s;
      transform: rotate(0deg);
    }

    .panel-header-hide {
      transition: .2s;
      transform: rotate(-90deg);
    }
  }

  :deep(.bk-collapse-content) {
    padding: 0 !important;
  }
}
</style>
<style lang="scss">
.auth-sideslider {
  .bk-modal-content {
    padding: 30px;
  }

  .bk-radio-label {
    font-size: 14px !important;
  }

  .code-input {
    width: 256px;
  }
}
</style>
