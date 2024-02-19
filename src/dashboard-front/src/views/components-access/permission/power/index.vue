<template>
  <div class="app-content">
    <div class="ag-top-header permissions-header">
      <div class="flex-nowrap">
        <span v-bk-tooltips="{ content: t('请选择待续期的权限'), disabled: permissionTableSelection.length }">
          <bk-button
            theme="primary"
            class="mr10 fl"
            @click="handleBatchApply"
            :disabled="!permissionTableSelection.length">
            {{ t('批量续期') }}
          </bk-button>
        </span>
        <bk-dropdown-menu
          trigger="click"
          style="vertical-align: middle; margin-right: 5px;"
          @show="isExportDropdownShow = true"
          @hide="isExportDropdownShow = false"
          font-size="medium">
          <bk-button>
            <span> {{ t('导出') }} </span>
            <i :class="['dropdown-icon bk-icon icon-angle-down', { 'open': isExportDropdownShow }]"></i>
          </bk-button>
          <template #content>
            <ul class="bk-dropdown-list">
              <li class="bk-dropdown-item">
                <a
                  href="javascript:;"
                  @click="handleExportAll()">
                  {{ t('全部应用权限') }}
                </a>
              </li>
              <li class="bk-dropdown-item">
                <a
                  href="javascript:;"
                  :class="{ disabled: !hasFiltered }"
                  v-bk-tooltips.right="{ disabled: hasFiltered, content: t('请先筛选资源') , boundary: 'window' }"
                  @click="handleExportFiltered($event, !hasFiltered)">
                  {{ t('已筛选应用权限') }}
                </a>
              </li>
              <li class="bk-dropdown-item">
                <a
                  href="javascript:;"
                  :class="{ disabled: !hasSelected }"
                  v-bk-tooltips.right="{ disabled: hasSelected, content: t('请先勾选资源') , boundary: 'window' }"
                  @click="handleExportSelected($event, !hasSelected)">
                  {{ t('已选应用权限') }}
                </a>
              </li>
            </ul>
          </template>
        </bk-dropdown-menu>
        <bk-button @click="handleApplyShow" class="ml5 mr10"> {{ t('主动授权') }} </bk-button>
      </div>

      <bk-form class="fr flex-nowrap form-box-cls">
        <bk-form-item :label="t('授权维度')" class="flex-nowrap">
          <bk-select
            style="width: 190px;"
            v-model="searchParams.dimension"
            :clearable="false"
            @change="handleDimensionChange">
            <bk-option
              v-for="option in dimensionList"
              :key="option.id"
              :id="option.id"
              :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <!-- <bk-form-item :label="t('授权类型')">
            <bk-select
                style="width: 190px;"
                v-model="searchParams.grant_type"
                clearable>
                <bk-option v-for="option in grantTypes"
                    :key="option.id"
                    :id="option.id"
                    :name="option.name">
                </bk-option>
            </bk-select>
        </bk-form-item> -->
        <bk-form-item label="" class="search-select-wrapper" style="flex: 1;">
          <bk-search-select
            :placeholder="t('搜索')"
            :show-popover-tag-change="true"
            :clearable="true"
            :data="searchParams.dimension === 'resource' ? searchResourceCondition : searchApiCondition"
            :show-condition="false"
            v-model="searchFilters"
            @change="formatFilterData">
          </bk-search-select>
        </bk-form-item>
      </bk-form>
    </div>
    <bk-table
      style="margin-top: 15px;"
      border="outer"
      :data="permissionList"
      :size="'small'"
      :pagination="pagination"
      @page-limit-change="handlePageLimitChange"
      @page-change="handlePageChange"
      @select="handlePageSelect"
      @select-all="handlePageSelectAll">
      <!-- <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getApigwPermissionList"
          @clear-filter="clearFilterKey"
        />
      </div> -->
      <bk-table-column type="selection" width="60" align="center"></bk-table-column>
      <bk-table-column :label="t('蓝鲸应用ID')" prop="bk_app_code"></bk-table-column>
      <bk-table-column
        :label="t('资源名称')"
        prop="resource_name"
        v-if="searchParams.dimension === 'resource'">
      </bk-table-column>
      <bk-table-column :label="t('请求路径')" prop="resource_path" v-if="searchParams.dimension === 'resource'">
        <template #default="props">
          <span class="ag-auto-text">
            {{props.row['resource_path'] || '--'}}
          </span>
        </template>
      </bk-table-column>
      <bk-table-column
        width="100"
        :label="t('请求方法')"
        prop="resource_method"
        v-if="searchParams.dimension === 'resource'">
        <template #default="props">
          {{props.row['resource_method'] || '--'}}
        </template>
      </bk-table-column>
      <bk-table-column :label="t('过期时间')" prop="expires">
        <template #default="props">
          {{props.row['expires'] || t('永久有效')}}
        </template>
      </bk-table-column>
      <bk-table-column width="150" :label="t('授权类型')" prop="expires">
        <template #default="props">
          {{props.row['grant_type'] === 'initialize' ? t('主动授权') : t('申请审批')}}
        </template>
      </bk-table-column>
      <bk-table-column width="150" :label="t('操作')">
        <template #default="props">
          <template v-if="props.row.renewable">
            <bk-button
              class="mr10"
              theme="primary"
              text
              @click="handleSingleApply(props.row)">
              {{ t('续期') }}
            </bk-button>
          </template>
          <template v-else>
            <span
              v-bk-tooltips.left="t('权限有效期大于 30 天时，暂无法续期')"
            >
              <bk-button class="mr10" theme="primary" text disabled> {{ t('续期') }} </bk-button>
            </span>
          </template>
          <bk-button theme="primary" text @click="handleRemove(props.row)"> {{ t('删除') }} </bk-button>
        </template>
      </bk-table-column>
    </bk-table>

    <bk-dialog
      v-model="batchApplyDialogConf.isShow"
      theme="primary"
      :width="searchParams.dimension === 'resource' ? 950 : 800"
      :title="t('批量续期')"
      :mask-close="true"
      @cancel="batchApplyDialogConf.isShow = false">
      <div>
        <div class="ag-alert primary mb10">
          <i class="apigateway-icon icon-ag-info"></i>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <p v-html="templateString"></p>
        </div>
        <bk-table
          :data="permissionSelectList"
          :size="'small'"
          :max-height="250"
          :key="applyKey">
          <!-- <div slot="empty">
            <table-empty empty />
          </div> -->
          <bk-table-column width="180" :label="t('蓝鲸应用ID')" prop="bk_app_code"></bk-table-column>
          <bk-table-column
            :label="t('资源名称')"
            prop="resource_name"
            v-if="searchParams.dimension === 'resource'">
          </bk-table-column>
          <!-- <bk-table-column :label="t('请求路径')" prop="resource_path" v-if="searchParams.dimension === 'resource'">
              <template slot-scope="props">
                  {{props.row['resource_path'] || '--'}}
              </template>
          </bk-table-column>
          <bk-table-column :label="t('请求方法')" prop="resource_method" v-if="searchParams.dimension === 'resource'">
              <template slot-scope="props">
                  {{props.row['resource_method'] || '--'}}
              </template>
          </bk-table-column> -->
          <bk-table-column :label="t('续期前的过期时间')" prop="expires">
            <template #default="props">
              {{props.row['expires'] || '--'}}
              <span
                class="ag-strong default fn"
                v-if="!props.row.renewable && props.row['expires']">
                {{ t('(有效期大于30天)') }}
              </span>
            </template>
          </bk-table-column>
          <bk-table-column width="180" :label="t('续期后的过期时间')" prop="expires">
            <template #default="props">
              <span class="ag-strong danger fn" v-if="!props.row.renewable"> {{ t('不可续期') }} </span>
              <span v-else class="ag-strong warning fn">{{applyNewTime}}</span>
            </template>
          </bk-table-column>
        </bk-table>
      </div>
      <template #footer>
        <template v-if="applyCount">
          <bk-button
            theme="primary"
            :disabled="applyCount === 0"
            @click="batchApplyPermission"
            :loading="isBatchApplyLoaading">
            {{ t('确定') }}
          </bk-button>
        </template>
        <template v-else>
          <bk-popover placement="top" :content="t('无可续期的权限')">
            <bk-button theme="primary" :disabled="true"> {{ t('确定') }} </bk-button>
          </bk-popover>
        </template>
        <bk-button theme="default" @click="batchApplyDialogConf.isShow = false"> {{ t('取消') }} </bk-button>
      </template>
    </bk-dialog>

    <bk-sideslider
      :title="applySliderConf.title"
      :width="800"
      v-model:is-show="applySliderConf.isShow"
      :quick-close="true"
      :before-close="handleBeforeClose"
      @hidden="handleHidden">
      <template #default>
        <div class="p30">
          <p class="ag-span-title"> {{ t('你将对指定的蓝鲸应用添加访问资源的权限') }} </p>
          <bk-form class="mb30 ml15" :label-width="120" :model="curApply">
            <bk-form-item
              :label="t('蓝鲸应用ID')"
              :required="true">
              <bk-input
                :placeholder="t('请输入应用ID')"
                v-model="curApply.bk_app_code"
                style="width: 256px;">
              </bk-input>
            </bk-form-item>
            <bk-form-item
              :label="t('有效时间')"
              :required="true">
              <bk-radio-group v-model="curApply.expire_type">
                <bk-radio :value="'custom'" style="margin-right: 65px;">
                  <bk-input
                    type="number"
                    :min="0"
                    v-model="curApply.expire_days"
                    class="mr5"
                    :show-controls="false"
                    style="width: 68px; display: inline-block;"
                    @focus="curApply.expire_type = 'custom'">
                  </bk-input>
                  {{ t('天') }}
                </bk-radio>
                <bk-radio :value="'None'"> {{ t('永久有效') }} </bk-radio>
              </bk-radio-group>
            </bk-form-item>
          </bk-form>
          <p class="ag-span-title"> {{ t('请选择要授权的资源') }} </p>
          <div class="ml20">
            <bk-radio-group class="ag-resource-radio" v-model="curApply.dimension">
              <bk-radio value="api">
                {{ t('按网关') }}
                <span v-bk-tooltips="t('包括网关下所有资源，包括未来新创建的资源')">
                  <i class="apigateway-icon icon-ag-help"></i>
                </span>
              </bk-radio>
              <bk-radio value="resource">
                {{ t('按资源') }}
                <span v-bk-tooltips="t('仅包含当前选择的资源')">
                  <i class="apigateway-icon icon-ag-help"></i>
                </span>
              </bk-radio>
            </bk-radio-group>

            <div class="ag-transfer-box" v-if="curApply.dimension === 'resource'">
              <bk-transfer
                ext-cls="resource-transfer-wrapper"
                :source-list="resourceList"
                :display-key="'name'"
                :setting-key="'id'"
                :title="[t('未选资源'), t('已选资源')]"
                :searchable="true"
                @change="handleResourceChange">
                <template #source-option="data">
                  <div
                    class="transfer-source-item"
                    :title="data.name"
                  >
                    {{ data.name }}
                  </div>
                </template>
                <template #target-option="data">
                  <div
                    class="transfer-source-item"
                    :title="data.name"
                  >
                    {{ data.name }}
                  </div>
                </template>
              </bk-transfer>
            </div>

            <div class="action mt20">
              <bk-button theme="primary" class="mr10" @click="submitApigwApply"> {{ t('保存') }} </bk-button>
              <bk-button @click="handleHideApplySlider"> {{ t('取消') }} </bk-button>
            </div>
          </div>
        </div>
      </template>
    </bk-sideslider>

    <bk-dialog
      v-model="removeDialogConf.isShow"
      theme="primary"
      :width="940"
      :title="removeDialogConfTitle"
      :mask-close="true"
      @cancel="removeDialogConf.isShow = false"
      @confirm="removePermission">
      <div>
        <bk-table
          style="margin-top: 15px;"
          :data="curPermission.details"
          :size="'small'"
          :key="tableIndex">
          <!-- <div slot="empty">
            <table-empty empty />
          </div> -->
          <bk-table-column :label="t('蓝鲸应用ID')" prop="bk_app_code"></bk-table-column>
          <bk-table-column :label="t('请求路径')" prop="resource_path"></bk-table-column>
          <bk-table-column :label="t('请求方法')" prop="resource_method"></bk-table-column>
        </bk-table>
      </div>
    </bk-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, watch, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { useCommon } from '@/store';
import { sortByKey } from '@/common/util';
import dayjs from 'dayjs';
import { Message, InfoBox } from 'bkui-vue';
// import sidebarMixin from '@/mixins/sidebar-mixin';
import {
  gatewayPermissionsRenew,
  resourcePermissionsRenew,
  gatewayPermissionsDelete,
  resourcePermissionsDelete,
  gatewayPermissions,
  resourcePermissions,
  getGatewayAppCodes,
  getResourceAppCodes,
  getGatewayPermissions,
  getResourcePermissions,
  getResourceListData,
  gatewayPermissionsExport,
  resourcePermissionsExport,
} from '@/http';

const { t } = useI18n();
const common = useCommon();

const searchResourceCondition = reactive<any>([
  {
    name: t('蓝鲸应用ID'),
    id: 'bk_app_code',
    children: [],
  },
  {
    name: t('资源名称'),
    id: 'resource_id',
    children: [],
  },
  {
    name: t('模糊搜索'),
    id: 'query',
  },
]);

const searchApiCondition = reactive<any>([
  {
    name: t('蓝鲸应用ID'),
    id: 'bk_app_code',
    children: [],
  },
  {
    name: t('模糊搜索'),
    id: 'query',
  },
]);
const applyNewTime = ref<string>('');
const searchFilters = ref<any>([]);
const keyword = ref<string>('');
const isPageLoading = ref<boolean>(true);
const isDataLoading = ref<boolean>(false);
const isBatchApplyLoaading = ref<boolean>(false);
const permissionList = ref<any>([]);
const pagination = reactive<any>({
  current: 1,
  count: 0,
  limit: 10,
});
const isExportDropdownShow = ref<boolean>(false);
const applySliderConf = reactive<any>({
  isLoading: false,
  isShow: false,
  title: t('主动授权'),
});
const resourceList = ref<any>([]);
const batchApplyDialogConf = reactive<any>({
  isShow: false,
});
const permissionSelectList = ref<any>([]);
const permissionTableSelection = ref<any>([]);
const applyKey = ref<number>(0);
const curApply = ref<any>({
  bk_app_code: '',
  expire_type: 'custom',
  expire_days: 180,
  resource_ids: [],
  dimension: 'api',
});
const curPermission = ref<any>({
  bk_app_code: '',
});
// const rules = reactive({
//   name: [
//     {
//       required: true,
//       message: t('必填项'),
//       trigger: 'blur',
//     },
//     {
//       max: 32,
//       message: t('不能多于32个字符'),
//       trigger: 'blur',
//     },
//   ],
// });
// const grantTypes = reactive([
//   {
//     id: 'initialize',
//     name: t('主动授权'),
//   },
//   {
//     id: 'apply',
//     name: t('申请审批'),
//   },
// ]);
const dimensionList = reactive([
  {
    id: 'api',
    name: t('按网关'),
  },
  {
    id: 'resource',
    name: t('按资源'),
  },
]);
const searchParams = reactive<any>({
  bk_app_code: '',
  query: '',
  resource_id: '',
  grant_type: '',
  dimension: 'resource',
});
const removeDialogConf = reactive({
  isShow: false,
});
const tableIndex = ref<number>(0);
const tableEmptyConf = reactive({
  keyword: '',
  isAbnormal: false,
});
const initDataStr = ref<string>('');


const apigwId = computed(() => common.apigwId);
const hasSelected = computed(() => permissionTableSelection.value.length > 0);
const hasFiltered = computed(() => {
  return !!(searchParams.resource_id || searchParams.query || searchParams.bk_app_code);
});
const applyCount = computed(() => {
  return permissionSelectList.value.filter((item: any) => item.renewable).length;
});
const unApplyCount = computed(() => {
  return permissionSelectList.value.filter((item: any) => !item.renewable).length;
});
const templateString = computed(() => {
  return t('将给以下  <i class="ag-strong success m5">{applyCount}</i> 个权限续期<i class="ag-strong">180</i>天<span v-if="unApplyCount">；<i class="ag-strong danger m5">{unApplyCount}</i> 个权限不可续期，权限大于30天不支持续期</span>', { applyCount, unApplyCount });
});
const removeDialogConfTitle = computed(() => {
  return t('确定要删除蓝鲸应用【{appCode}】的权限？', { appCode: curPermission.value.bk_app_code });
});


const initSidebarFormData = (data: any) => {
  initDataStr.value = JSON.stringify(data);
};

const isSidebarClosed = (targetDataStr: any) => {
  let isEqual = initDataStr.value === targetDataStr;
  if (typeof targetDataStr !== 'string') {
    // 数组长度对比
    const initData = JSON.parse(initDataStr.value);
    isEqual = initData.length === targetDataStr.length;
  }
  return new Promise((resolve) => {
    // 未编辑
    if (isEqual) {
      resolve(true);
    } else {
      // 已编辑
      InfoBox({
        title: t('确认离开当前页？'),
        subTitle: t('离开将会导致未保存信息丢失'),
        confirmText: t('离开'),
        onConfirm() {
          resolve(true);
        },
        onClosed() {
          resolve(false);
        },
      });
    }
  });
};

const handleBeforeClose = async () => {
  return isSidebarClosed(JSON.stringify(curApply));
};

const handleHidden = () => {
  initCurApplyData();
};

const initCurApplyData = () => {
  curApply.value = {
    bk_app_code: '',
    expire_type: 'custom',
    expire_days: 180,
    resource_ids: [],
    dimension: 'api',
  };
};

const updateTableEmptyConfig = () => {
  if (searchFilters.value.length) {
    tableEmptyConf.keyword = 'placeholder';
    return;
  } if (searchParams.dimension) {
    tableEmptyConf.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.keyword = '';
};

// const clearFilterKey = () => {
//   searchFilters.value = [];
// };

// const checkPermissionSelect = (row, index) => {
//   return row.renewable;
// };

const batchApplyPermission = async () => {
  if (isBatchApplyLoaading.value) {
    return false;
  }
  isBatchApplyLoaading.value = true;

  const ids = permissionSelectList.value.map((permission: any) => permission.id);
  const data = {
    dimension: searchParams.dimension,
    ids,
  };

  try {
    const renewFn = data.dimension === 'api' ? gatewayPermissionsRenew : resourcePermissionsRenew;
    await renewFn(apigwId.value, data);

    getApigwPermissionList();
    batchApplyDialogConf.isShow = false;
    Message({
      theme: 'success',
      message: t('续期成功！'),
    });
  } catch (e) {
    console.error(e);
  } finally {
    isBatchApplyLoaading.value = false;
  }
};

const handleDimensionChange = () => {
  searchFilters.value = [];
};

const handlePageSelectAll = (selection: any) => {
  permissionTableSelection.value = selection;
};

const handlePageSelect = (selection: any) => {
  permissionTableSelection.value = selection;
};

const handleBatchApply = () => {
  if (!permissionTableSelection.value.length) {
    Message({
      theme: 'error',
      message: t('请选择要续期的权限'),
    });
    return false;
  }

  applyNewTime.value = dayjs(Date.now() + 180 * 24 * 60 * 60 * 1000).format('YYYY-MM-DD HH:mm:ss');
  applyKey.value += 1;
  permissionSelectList.value = permissionTableSelection.value.sort((a: any, b: any) => {
    if ((a.renewable && b.renewable) || (!a.renewable && !b.renewable)) {
      return 0;
    } if (a.renewable && !b.renewable) {
      return -1;
    } if (!a.renewable && b.renewable) {
      return 1;
    }
  });
  batchApplyDialogConf.isShow = true;
};

const handleSingleApply = (data: any) => {
  permissionSelectList.value = [data];
  applyNewTime.value = dayjs(Date.now() + 180 * 24 * 60 * 60 * 1000).format('YYYY-MM-DD HH:mm:ss');
  applyKey.value += 1;
  batchApplyDialogConf.isShow = true;
};

const handleHideApplySlider = () => {
  initCurApplyData();
  applySliderConf.isShow = false;
};

const handleResourceChange = (sourceList: any, targetList: any, targetValueList: any) => {
  curApply.value.resource_ids = targetValueList;
};

const formatData = () => {
  const params = JSON.parse(JSON.stringify(curApply));
  if (params.expire_type === 'None') {
    params.expire_days = null;
  }

  if (params.dimension === 'api') {
    params.resource_ids = null;
  }

  return params;
};

const checkData = (params: any) => {
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

const submitApigwApply = () => {
  const params = formatData();

  if (checkData(params)) {
    addPermissionApply(params);
  }
};

const handleRemove = (data: any) => {
// const self = this
  curPermission.value = data;
  curPermission.value.details = [data];
  // $bkInfo({
  //     title: `确定删除【${data.bk_app_code}】权限？`,
  //     subTitle: '删除后将无法恢复，请确认是否删除？',
  //     confirmFn () {
  //         self.removePermission()
  //     }
  // })
  tableIndex.value += 1;
  removeDialogConf.isShow = true;
};

const handleSearch = () => {
  searchParams.bk_app_code = keyword.value;
};

const formatFilterData = () => {
  const map: any = {};
  searchFilters.value.forEach((filter: any) => {
    map[filter.id] = filter;
  });
  const keys = Object.keys(map);
  searchFilters.value = [];
  keys.forEach((key) => {
    searchFilters.value.push(map[key]);
  });
  // handleSearch()
};

const removePermission = async () => {
  try {
    const ids = [curPermission.value.id];

    const data = {
      dimension: searchParams.dimension,
      ids,
    };

    const deleteFn = data.dimension === 'api' ? gatewayPermissionsDelete : resourcePermissionsDelete;
    await deleteFn(apigwId.value, data);

    // 当前页只有一条数据
    if (permissionList.value.length === 1 && pagination.current > 1) {
      pagination.current -= 1;
    }
    getApigwPermissionList();

    Message({
      theme: 'success',
      message: t('删除成功！'),
    });
  } catch (e) {
    console.error(e);
  }
};

// const updatePermission = async () => {
//   try {
//     const data = { name: curPermission.value.name };
//     const permissionId = curPermission.value.id;
//     await store.dispatch('permission/updateApigwPermission', { apigwId: apigwId.value, permissionId, data });
//     permissionDialogConf.visiable = false;
//     getApigwPermissionList();

//     Message({
//       theme: 'success',
//       message: t('更新成功！'),
//     });
//   } catch (e) {
//     console.error(e);
//   }
// };

const addPermissionApply = async (data: any) => {
  try {
    const accreditFn = data.dimension === 'api' ? gatewayPermissions : resourcePermissions;
    await accreditFn(apigwId.value, data);

    searchParams.dimension = data.dimension;
    getApigwPermissionList();
    Message({
      theme: 'success',
      message: t('授权成功！'),
    });
    handleHideApplySlider();
  } catch (e) {
    console.error(e);
  }
};

const exportDownload = async (data: any) => {
  isDataLoading.value = true;

  try {
    const exportFn = data.dimension === 'api' ? gatewayPermissionsExport : resourcePermissionsExport;
    const res = await exportFn(apigwId.value, data);

    if (res.success) {
      Message({
        theme: 'success',
        message: t('导出成功！'),
      });
    } else {
      Message({
        theme: 'error',
        message: t('导出失败！'),
      });
    }
  } catch (e) {
    console.error(e);
  } finally {
    isDataLoading.value = false;
  }
};

// const handleCancel = () => {};

const handlePageChange = (newPage: number) => {
  pagination.current = newPage;
  getApigwPermissionList(newPage);
};

const handlePageLimitChange = (limit: number) => {
  pagination.limit = limit;
  pagination.current = 1;
  getApigwPermissionList(pagination.current);
};

const handleApplyShow = () => {
  applySliderConf.isShow = true;
  // 收集初始化状态
  initSidebarFormData(curApply);
};

const handleExportFiltered = (event: any, disabled: any) => {
  if (disabled) {
    event.stopPropagation();
    return false;
  }

  const data = {
    export_type: 'filtered',
    ...searchParams,
  };

  exportDownload(data);
};

const handleExportSelected = (event: any, disabled: any) => {
  if (disabled) {
    event.stopPropagation();
    return false;
  }

  const data = {
    export_type: 'selected',
    dimension: searchParams.dimension,
    permission_ids: permissionTableSelection.value.map((item: any) => item.id),
  };

  exportDownload(data);
};

const handleExportAll = () => {
  const data = {
    export_type: 'all',
    dimension: searchParams.dimension,
  };

  exportDownload(data);
};

const getBkAppCodes = async () => {
  const pageParams = {
    dimension: searchParams.dimension,
  };

  try {
    const getAppCodes = pageParams.dimension === 'api' ? getGatewayAppCodes : getResourceAppCodes;
    const res = await getAppCodes(apigwId.value, pageParams);

    const resources = res.data.map((item: any) => {
      return {
        id: item,
        name: item,
      };
    });
    searchResourceCondition[0].children = resources;
    searchApiCondition[0].children = resources;
  } catch (e) {
    console.error(e);
  }
};

const getApigwResources = async () => {
  const pageParams = {
    no_page: true,
    order_by: 'path',
  };

  try {
    const res = await getResourceListData(apigwId.value, pageParams);
    const results = res.data.results.map((item: any) => {
      return {
        id: item.id,
        name: item.name,
        path: item.path,
        method: item.method,
        resourceName: `${item.method}：${item.path}`,
      };
    });

    resourceList.value = sortByKey(results, 'name');
    searchResourceCondition[1].children = resourceList.value.map((item: any) => {
      return {
        id: item.id,
        name: item.name,
      };
    });
  } catch (e) {
    console.error(e);
  }
};

const getApigwPermissionList = async (page?: any) => {
  const curPage = page || pagination.current;
  const pageParams = {
    limit: pagination.limit,
    offset: pagination.limit * (curPage - 1),
    dimension: searchParams.dimension,
    bk_app_code: searchParams.bk_app_code,
    grant_type: searchParams.grant_type,
    resource_id: searchParams.resource_id,
    query: searchParams.query,
  };

  isDataLoading.value = true;
  permissionTableSelection.value = [];
  try {
    const getPermissionList = pageParams.dimension === 'api' ? getGatewayPermissions : getResourcePermissions;
    const res = await getPermissionList(apigwId.value, pageParams);

    res.data.results.forEach((item: any) => {
      item.updated_time = item.updated_time || '--';
    });
    permissionList.value = res.data.results;
    pagination.count = res.data.count;
    updateTableEmptyConfig();
    tableEmptyConf.isAbnormal = false;
  } catch (e) {
    tableEmptyConf.isAbnormal = true;
    console.error(e);
  } finally {
    isPageLoading.value = false;
    isDataLoading.value = false;
  }
};

const init = () => {
  getApigwPermissionList();
  getApigwResources();
  getBkAppCodes();
};

init();

watch(
  () => keyword.value,
  (newVal, oldVal) => {
    if (oldVal && !newVal) {
      handleSearch();
    }
  },
);

watch(
  () => searchParams,
  () => {
    pagination.current = 1;
    pagination.count = 0;
    getApigwPermissionList();
  },
  {
    deep: true,
  },
);

watch(
  () => searchFilters.value,
  () => {
    nextTick(() => {
      searchParams.query = '';
      searchParams.bk_app_code = '';
      searchParams.resource_id = '';
      searchFilters.value.forEach((item: any) => {
        searchParams[item.id] = item.values[0].id;
      });
    });
  },
);

watch(
  () => curApply.value.expire_type,
  (value) => {
    if (value === 'custom') {
      curApply.value.expire_days = 180;
    } else {
      curApply.value.expire_days = '';
    }
  },
);
</script>

<style lang="scss" scoped>
.app-content {
  padding: 24px;
  .ag-top-header {
    min-height: 32px;
    margin-bottom: 20px;
    position: relative;
  }
}
.ag-resource-radio {
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
}

.ag-dl {
  padding: 15px 40px 5px 30px;
}

.ag-user-type {
  width: 560px;
  height: 80px;
  background: #FAFBFD;
  border-radius: 2px;
  border: 1px solid #DCDEE5;
  padding: 17px 20px 0 20px;
  position: relative;
  overflow: hidden;

  .apigateway-icon {
    font-size: 80px;
    position: absolute;
    color: #ECF2FC;
    top: 15px;
    right: 20px;
    z-index: 0;
  }

  strong {
    font-size: 14px;
    margin-bottom: 10px;
    line-height: 1;
    display: block;
  }

  p {
    font-size: 12px;
    color: #63656E;
  }
}

.dropdown-icon {
  margin: 0 -4px;
  &.open {
    transform: rotate(180deg);
  }
}

.bk-dropdown-item {
  .disabled {
    color: #C4C6CC;
    cursor: not-allowed;

    &:hover {
      color: #C4C6CC;
    }
  }
}

.permissions-header {
  display: flex;
  justify-content: space-between;

  .flex-nowrap {
    display: flex;
    flex-wrap: nowrap;
    :deep(.bk-label) {
      white-space: nowrap;
    }
  }
  .form-box-cls {
    flex: 1;
    max-width: 770px;
  }
  .search-select-wrapper :deep(.bk-form-content) {
    width: 100%;
  }
}
</style>
