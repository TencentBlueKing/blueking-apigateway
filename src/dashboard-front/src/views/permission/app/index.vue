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
          trigger="click" class="mr5" @show="isExportDropdownShow = true"
          @hide="isExportDropdownShow = false" font-size="medium">
          <ag-dropdown :text="t('导出')" :dropdown-list="exportDropData" @on-change="handleExport"></ag-dropdown>
        </bk-dropdown-menu>
        <bk-button class=" mr10" @click="handleAuthShow"> {{ t('主动授权') }} </bk-button>
      </div>
      <bk-form class="flex-row ">
        <bk-form-item :label="$t('授权维度')" class="mb0">
          <bk-select v-model="dimension" class="w150" :clearable="false">
            <bk-option v-for="option of dimensionList" :key="option.id" :value="option.id" :label="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item label="" class="mb0" label-width="10">
          <bk-input class="search-input w400" :placeholder="t('请输入应用ID')" v-model="searchQuery"></bk-input>
        </bk-form-item>
      </bk-form>
    </div>
    <div class="app-content">
      <bk-loading :loading="isLoading">
        <bk-table
          show-overflow-tooltip
          class="mt15" :data="tableData" :size="'small'" :pagination="pagination"
          remote-pagination
          @page-limit-change="handlePageSizeChange"
          @page-value-change="handlePageChange"
          @selection-change="handleSelectionChange"
          @select-all="handleSelecAllChange">
          <bk-table-column type="selection" width="60" align="center"></bk-table-column>
          <bk-table-column :label="t('蓝鲸应用ID')" prop="bk_app_code"></bk-table-column>
          <bk-table-column :label="t('资源名称')" prop="resource_name" v-if="dimension === 'resource'"></bk-table-column>
          <bk-table-column :label="t('请求路径')" prop="resource_path" v-if="dimension === 'resource'">
            <template #default="{ data }">
              <span class="ag-auto-text">
                {{ data?.resource_path || '--' }}
              </span>
            </template>
          </bk-table-column>
          <bk-table-column width="100" :label="t('请求方法')" prop="resource_method" v-if="dimension === 'resource'">
            <template #default="{ data }">
              {{ data?.resource_method || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('过期时间')" prop="expires">
            <template #default="{ data }">
              {{ data?.expires || t('永久有效') }}
            </template>
          </bk-table-column>
          <bk-table-column width="150" :label="t('授权类型')" prop="expires">
            <template #default="{ data }">
              {{ data?.grant_type === 'initialize' ? t('主动授权') : t('申请审批') }}
            </template>
          </bk-table-column>
          <bk-table-column width="150" :label="t('操作')">
            <template #default="{ data }">
              <template v-if="data?.renewable">
                <bk-button class="mr10" theme="primary" text @click="handleSingleApply(data)"> {{ t('续期') }}</bk-button>
              </template>
              <template v-else>
                <span v-bk-tooltips="renewableConfi">
                  <bk-button class="mr10" theme="primary" text disabled> {{ t('续期') }} </bk-button>
                </span>
              </template>
              <bk-button theme="primary" text @click="handleRemove(data)"> {{ t('删除') }} </bk-button>
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
      ext-cls="auth-sideslider" :title="authSliderConf.title" :width="800"
      v-model:isShow="authSliderConf.isShow" quick-close :before-close="handleBeforeClose" @hidden="handleHidden">
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

    <!-- 提示dialog -->
    <bk-dialog ext-cls="attention-dialog" :is-show="isVisible" :title="''" :theme="'primary'">
      <p class="title">{{ t('确认离开当前页？') }}</p>
      <p class="sub-title">{{ t('离开将会导致未保存信息丢失') }}</p>
      <div class="btn">
        <bk-button theme="primary" class="mr5 w88" @click="handleDialogLeave">{{ t('离开') }}</bk-button>
        <bk-button class="w88" @click="handleDialogCancel">{{ t('取消') }}</bk-button>
      </div>
      <template #footer></template>
    </bk-dialog>

    <!-- 删除dialog -->
    <bk-dialog
      :is-show="removeDialogConf.isShow" theme="primary" :width="940" :title="removeDialogConfTitle"
      :quick-close="true" @closed="removeDialogConf.isShow = false" @confirm="handleRemovePermission">
      <div>
        <bk-table :data="curPermission.detail" :size="'small'" :key="tableIndex" class="mb15">
          <bk-table-column :label="t('蓝鲸应用ID')" prop="bk_app_code">
            <template #default="{ data }">
              {{ data?.bk_app_code || '--' }}
            </template>
          </bk-table-column>
          <template v-if="dimension === 'resource'">
            <bk-table-column :label="t('请求路径')" prop="resource_path">
              <template #default="{ data }">
                {{ data?.resource_path || '--' }}
              </template>
            </bk-table-column>
            <bk-table-column :label="t('请求方法')" prop="resource_method">
              <template #default="{ data }">
                {{ data?.resource_method || '--' }}
              </template>
            </bk-table-column>
          </template>
          <template v-else>
            <bk-table-column :label="t('授权维度')">
              {{ dimensionType[dimension as keyof typeof dimensionType] }}
            </bk-table-column>
            <bk-table-column :label="t('过期时间')" prop="expires">
              <template #default="{ data }">
                {{ data?.expires === null ? t('永久有效') : data?.expires }}
              </template>
            </bk-table-column>
          </template>
        </bk-table>
      </div>
    </bk-dialog>

    <!-- 续期dialog -->
    <bk-dialog
      :is-show="batchApplyDialogConf.isShow" theme="primary"
      :width="dimension === 'resource' ? 950 : 800" :title="t('批量续期')" :quick-close="true"
      @closed="batchApplyDialogConf.isShow = false">
      <div>
        <bk-alert theme="info" class="mb15">
          <template #title>
            {{t('将给以下') }} <i class="ag-strong success">{{applyCount}}</i>{{t('个权限续期') }}
            <i class="ag-strong">180</i>天
            <span>；
              <i class="ag-strong danger m5">{{unApplyCount}}</i>
              {{t('个权限不可续期，权限大于30天不支持续期') }}
            </span>
          </template>
        </bk-alert>
        <bk-table :data="curSelections" :size="'small'" :max-height="250" class="mb30">
          <bk-table-column width="180" :label="t('蓝鲸应用ID')" prop="bk_app_code"></bk-table-column>
          <bk-table-column :label="t('资源名称')" prop="resource_name" v-if="dimension === 'resource'">
          </bk-table-column>
          <bk-table-column :label="t('续期前的过期时间')" prop="expires" :width="dimension === 'resource' ? 330 : 392">
            <template #default="{ data }">
              {{ data?.expires || '--' }}
              <span class="ag-strong default " v-if="!data?.renewable && data?.expires">
                {{ t('(有效期大于30天)') }}
              </span>
            </template>
          </bk-table-column>
          <bk-table-column width="180" :label="t('续期后的过期时间')" prop="expires">
            <template #default="{ data }">
              <span class="ag-strong danger " v-if="!data?.renewable"> {{ t('不可续期') }} </span>
              <span v-else class="ag-strong warning ">{{ applyNewTime }}</span>
            </template>
          </bk-table-column>
        </bk-table>
      </div>
      <template #footer>
        <template v-if="applyCount">
          <bk-button
            theme="primary" :disabled="applyCount === 0" @click="handleComfirmBatch"
            :loading="isBatchApplyLoaading"> {{ t('确定') }} </bk-button>
        </template>
        <template v-else>
          <bk-popover placement="top" :content="t('无可续期的权限')">
            <bk-button theme="primary" :disabled="true"> {{ t('确定') }} </bk-button>
          </bk-popover>
        </template>
        <bk-button @click="batchApplyDialogConf.isShow = false"> {{ t('取消') }} </bk-button>
      </template>
    </bk-dialog>
  </div>
</template>

<script setup lang="ts">
import { isEqual } from 'lodash';
import { Message } from 'bkui-vue';
import { reactive, ref, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { sortByKey, timeFormatter } from '@/common/util';
import agDropdown from '@/components/ag-dropdown.vue';
import TableEmpty from '@/components/table-empty.vue';
import {
  getResourceListData,
  getApiPermissionList,
  getResourcePermissionList,
  authApiPermission,
  authResourcePermission,
  deleteApiPermission,
  deleteResourcePermission,
  batchUpdateApiPermission,
  batchUpdateResourcePermission,
  exportApiPermission,
  exportResourcePermission,
} from '@/http';
import { useCommon } from '@/store';
import { useQueryList, useSelection } from '@/hooks';
import { IDropList } from '@/types';

const { t } = useI18n();
const common = useCommon();
const { apigwId } = common; // 网关id

const filterData = ref({ bk_app_code: '', keyword: '', grant_type: '', grant_dimension: '', resource_id: '' });
const isExportDropdownShow = ref<boolean>(false);
const resourceList = ref([]);
const isVisible = ref<boolean>(false);
const isBatchApplyLoaading = ref<boolean>(false);
const tableIndex = ref<number>(0);
const curPermission = ref({ bk_app_code: '', detail: [], id: -1 });
const dimension = ref<string>('resource');
const searchQuery = ref<string>('');
const applyNewTime = ref<string>('');
const curSelections = ref([]);
const renewableConfi = reactive({
  content: t('权限有效期大于 30 天时，暂无法续期'), placement: 'left',
});
const dimensionType = reactive({
  api: t('网关'),
  resource: t('资源'),
});
// 导出下拉
const exportDropData = ref<IDropList[]>([
  { value: 'all', label: t('全部应用权限') },
  { value: 'filtered', label: t('已筛选应用权限'), disabled: true },
  { value: 'selected', label: t('已选应用权限'), disabled: true },
]);
// 授权维度
const dimensionList = reactive([
  { id: 'api', name: t('按网关') },
  { id: 'resource', name: t('按资源') },
]);
// 主动授权config
const authSliderConf = reactive({
  isLoading: false,
  isShow: false,
  title: t('主动授权'),
});
// 当前授权数据
const curAuthData = ref({
  bk_app_code: '',
  expire_type: 'custom',
  expire_days: 180,
  resource_ids: [],
  dimension: 'api',
});
const tableEmptyConf = ref<{keyword: string, isAbnormal: boolean}>({
  keyword: '',
  isAbnormal: false,
});
// 批量续期dialog
const batchApplyDialogConf = reactive({
  isShow: false,
});
// 删除dialog
const removeDialogConf = reactive({
  isShow: false,
});
// 导出参数
const exportParams: IexportParams = reactive({
  export_type: '',
});
// 导出参数interface
interface IexportParams {
  export_type: string
  bk_app_code?: string
  keyword?: string
  resource_ids?: number
  permission_ids?: Array<number>
  grant_type?: string
}

// 可续期的数量
const applyCount = computed(() => {
  const number = curSelections.value.filter((item: { renewable: boolean; }) => item.renewable).length;
  return number;
});
// 不可续期的数量
const unApplyCount = computed(() => {
  const number = curSelections.value.filter((item: { renewable: boolean; }) => !item.renewable).length;
  return number;
});
// 删除dialog title
const removeDialogConfTitle = computed(() => {
  // return t(`确定要删除蓝鲸应用【${curPermission.value.bk_app_code}】的权限？`);
  return t('确定要删除蓝鲸应用【{appCode}】的权限？', { appCode: curPermission.value.bk_app_code });
});


// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
  getMethod,
} = useQueryList(getResourcePermissionList, filterData);

// checkbox hooks
const {
  selections,
  handleSelectionChange,
  handleSelecAllChange,
  resetSelections,
} = useSelection();

// 监听授权维度是否变化
watch(
  () => dimension.value,
  async (value: string) => {
    // filterData.value.grant_dimension = value;
    // resetSelections();
    // const method = dimension.value === 'resource' ? getResourcePermissionList : getApiPermissionList;
    // await getList(method);
    resetSelections();
    getMethod.value = dimension.value === 'resource' ? getResourcePermissionList : getApiPermissionList;
    filterData.value.grant_dimension = value;
  },
  { deep: true },
);
// 监听搜索是否变化
watch(
  () => searchQuery.value,
  (v: string) => {
    resetSelections();
    filterData.value.keyword = v;
    const isEmpty = v.trim() === '';
    exportDropData.value.forEach((e: IDropList) => {
      // 已选资源
      if (e.value === 'filtered') {
        e.disabled = isEmpty;
      }
    });
    // updateTableEmptyConfig();
  },
  { deep: true },
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

// 获取资源列表数据
const getApigwResources = async () => {
  const pageParams = {
    limit: 3000,
    order_by: 'path',
  };
  try {
    const res = await getResourceListData(apigwId, pageParams);
    const results = res.results.map((item: any) => {
      return {
        id: item.id,
        name: item.name,
        path: item.path,
        method: item.method,
        resourceName: `${item.method}：${item.path}`,
      };
    });
    resourceList.value = sortByKey(results, 'name');
  } catch (error) {
    console.log('error', error);
  }
};

// 导出
const handleExport = async ({ value }: {value: string}) => {
  console.log(exportDropData.value);
  console.log(value);
  exportParams.export_type = value;
  switch (value) {
    case 'selected':
      exportParams.permission_ids = selections.value.map(e => e.id);
      break;
    case 'filtered':
      exportParams.keyword = searchQuery.value;
      break;
    default:
      break;
  }
  const fetchMethod = dimension.value === 'resource' ? exportResourcePermission : exportApiPermission;
  try {
    const res = await fetchMethod(apigwId, exportParams);
    if (res.success) {
      Message({
        message: t('导出成功'),
        theme: 'success',
      });
    }
  } catch ({ error }: any) {
    Message({
      message: error.message || t('导出失败'),
      theme: 'error',
    });
  } finally {
    exportParams.export_type = '';
    exportParams.permission_ids = [];
    exportParams.keyword = '';
  }
};

// 确定续期
const handleComfirmBatch = async () => {
  if (isBatchApplyLoaading.value) {
    return false;
  }
  isBatchApplyLoaading.value = true;
  const ids = curSelections.value.map(permission => permission.id);
  const data = {
    ids,
  };
  const fetchMethod = dimension.value === 'resource' ? batchUpdateResourcePermission : batchUpdateApiPermission;
  try {
    await fetchMethod(apigwId, data);
    batchApplyDialogConf.isShow = false;
    const method = dimension.value === 'resource' ? getResourcePermissionList : getApiPermissionList;
    getList(method);
    resetSelections();
    Message({
      theme: 'success',
      message: t('续期成功！'),
    });
  } catch ({ error }: any) {
    Message({
      message: error.message || t('续期失败'),
      theme: 'error',
    });
  } finally {
    isBatchApplyLoaading.value = false;
  }
};
// 批量续期
const handleBatchApplyPermission = () => {
  curSelections.value = selections.value;
  const dataStr: any = Date.now() + 180 * 24 * 60 * 60 * 1000;
  applyNewTime.value = timeFormatter(dataStr);
  batchApplyDialogConf.isShow = true;
};
// 单个续期
const handleSingleApply = (data: any) => {
  curSelections.value = [data];
  const dataStr: any = Date.now() + 180 * 24 * 60 * 60 * 1000;
  applyNewTime.value = timeFormatter(dataStr);
  batchApplyDialogConf.isShow = true;
};

// 删除text
const handleRemove = (data: any) => {
  curPermission.value = data;
  const curData: any = curPermission.value;
  curData.detail = [data];
  // eslint-disable-next-line no-plusplus
  tableIndex.value++;
  removeDialogConf.isShow = true;
};
// 删除 dialog btn
const handleRemovePermission = async () => {
  const ids: any = [curPermission.value?.id];
  const data = { ids };
  const fetchMethod = dimension.value === 'resource' ? deleteResourcePermission : deleteApiPermission;
  try {
    await fetchMethod(apigwId, data);
    removeDialogConf.isShow = false;
    const method = dimension.value === 'resource' ? getResourcePermissionList : getApiPermissionList;
    getList(method);
    Message({
      theme: 'success',
      message: t('删除成功！'),
    });
  } catch ({ error }: any) {
    Message({
      message: error.message || t('删除失败'),
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
  const initData: any = {
    bk_app_code: '',
    expire_type: 'custom',
    expire_days: 180,
    resource_ids: [],
    dimension: 'api',
  };
  const isSame = isEqual(initData, curAuthData.value);
  if (!isSame) {
    isVisible.value = true;
    return;
  }
  authSliderConf.isShow = false;
};
// 提示dialog离开btn
const handleDialogLeave = () => {
  isVisible.value = false;
  authSliderConf.isShow = false;
};
// 提示dialog取消btn
const handleDialogCancel = () => {
  isVisible.value = false;
  authSliderConf.isShow = true;
};
// 选择授权的资源数量发生改变触发
const handleResourceChange = (sourceList: any, targetList: any, targetValueList: any) => {
  curAuthData.value.resource_ids = targetValueList;
};
// 主动授权关闭btn
const handleHidden = () => {
  initAuthData();
};
// 主动授权 不同选项，数据的更改
const formatData = () => {
  const params = JSON.parse(JSON.stringify(curAuthData.value));
  if (params.expire_type === 'None') {
    params.expire_days = null;
  }
  if (params.dimension === 'api') {
    params.resource_ids = null;
  }
  return params;
};
// 核查授权数据
const checkDate = (params: any) => {
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
const authAppDimension = async (params: any) => {
  const fetchMethod = params.dimension === 'resource' ? authResourcePermission : authApiPermission;
  console.log(fetchMethod);
  const isSame = params.dimension === dimension.value;
  try {
    await fetchMethod(apigwId, params);
    dimension.value = params.dimension;
    authSliderConf.isShow = false;
    if (isSame) {
      const method = dimension.value === 'resource' ? getResourcePermissionList : getApiPermissionList;
      getList(method);
    }
    Message({
      theme: 'success',
      message: t('授权成功！'),
    });
  } catch ({ error }: any) {
    Message({
      message: error.message || t('授权失败'),
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
    console.log(params);
  }
};
// 主动授权取消btn
const handleSidesliderCancel = () => {
  authSliderConf.isShow = false;
};

const handleClearFilterKey = () => {
  filterData.value = { bk_app_code: '', keyword: '', grant_type: '', grant_dimension: '', resource_id: '' };
  dimension.value = '';
  searchQuery.value = '';
  getList();
  updateTableEmptyConfig();
};

const updateTableEmptyConfig = () => {
  const searchParams = {
    ...filterData.value,
    searchQuery: searchQuery.value,
    dimension: dimension.value,
  };
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

const init = () => {
  getApigwResources();
  console.log(selections.value);
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

.auth-sideslider {
  :deep(.bk-modal-content) {
    padding: 30px;
  }

  :deep(.bk-radio-label) {
    font-size: 14px !important;
  }

  .code-input {
    width: 256px;
  }
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
</style>
