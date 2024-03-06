<template>
  <div class="app-content apigw-access-manager-wrapper">
    <div :class="['left-system-nav', { 'is-expand': !isExpand }]">
      <div class="left-wrapper">
        <render-system
          :list="systemList"
          ref="systemFilterRef"
          @on-select="handleSelect" />
      </div>
      <div class="handle-icon" @click="isExpand = !isExpand">
        <i class="apigateway-icon icon-ag-down-small"></i>
      </div>
    </div>
    <div :class="['right-wrapper', { 'is-expand': !isExpand }]">
      <bk-alert
        v-if="needNewVersion && syncEsbToApigwEnabled"
        class="mb15"
        theme="warning"
        :title="t('组件配置有更新，新增组件或更新组件请求方法、请求路径、权限级别、用户认证，需同步到网关才能生效')">
      </bk-alert>
      <div class="search-wrapper">
        <div class="action-wrapper">
          <bk-button
            theme="primary"
            @click="handleCreate">
            {{ t('新建组件') }}
          </bk-button>
          <bk-button
            :disabled="curSelectList.length < 1"
            @click="handleBatchDelete">
            {{ t('批量删除') }}
          </bk-button>
          <bk-button
            v-if="syncEsbToApigwEnabled"
            :disabled="isReleasing"
            :icon="isReleasing ? 'loading' : ''"
            @click="handlesync">
            <span
              v-bk-tooltips="{ content: t('组件正在同步及发布中，请不要重复操作'), disabled: !isReleasing }">
              {{ isReleasing ? t('正在同步中') : t('同步到网关') }}
            </span>
          </bk-button>
        </div>
        <div class="component-flex">
          <bk-input
            style="width: 300px; margin-right: 10px"
            :placeholder="t('请输入组件名称、请求路径，按Enter搜索')"
            v-model="searchValue"
            clearable
            right-icon="bk-icon icon-search"
            @enter="handleSearch">
          </bk-input>
          <i
            class="apigateway-icon icon-ag-cc-history history-icon"
            v-bk-tooltips="t('查看同步历史')"
            @click="handlerRouter"
            v-if="syncEsbToApigwEnabled">
          </i>
        </div>
      </div>
      <bk-loading
        :loading="isLoading"
        opacity="1"
      >
        <bk-table
          border="outer"
          style="margin-top: 16px;"
          :data="componentList"
          :size="setting.size"
          @setting-change="handleSettingChange"
          :is-row-select-enable="setDefaultSelect"
          :pagination="pagination"
          remote-pagination
          @select="handlerChange"
          @select-all="handlerAllChange"
          @page-value-change="handlePageChange"
          @row-mouse-enter="changeEnter"
          @row-mouse-leave="changeLeave"
          @page-limit-change="handlePageLimitChange">
          <bk-table-column type="selection" width="60" align="center"></bk-table-column>
          <bk-table-column :label="t('系统名称')" prop="system_name">
            <template #default="{ data }">
              {{ data?.system_name || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column
            v-if="flagComponentName.length"
            :label="t('组件名称')"
            prop="name"
            key="name"
          >
            <template #default="{ data }">
              <div class="ag-flex">
                <span class="ag-auto-text">
                  {{ data?.name || '--' }}
                </span>
                <div v-if="syncEsbToApigwEnabled">
                  <span class="ag-tag primary ml5" v-if="data?.is_created"> {{ t('新创建') }} </span>
                  <span class="ag-tag success ml5" v-else-if="data?.has_updated"> {{ t('有更新') }} </span>
                </div>
              </div>
            </template>
          </bk-table-column>
          <bk-table-column :label="t('请求方法')" :width="90">
            <template #default="{ row }">
              {{ row.method || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column
            v-if="flagUrl.length"
            :label="t('请求路径')"
            prop="path"
            :min-width="220"
            :show-overflow-tooltip="true"
          >
          </bk-table-column>
          <bk-table-column
            v-if="flagApiUrl.length"
            :label="t('API地址')"
            prop="api_url"
            :min-width="180"
            :max-width="260"
            :show-overflow-tooltip="true"
          >
            <template #default="{ row }">
              <div class="path-wrapper">
                <span class="path-text">{{row.api_url}}</span>
                <span class="path-icon">
                  <i
                    v-show="cursorId === row.id"
                    class="apigateway-icon icon-ag-clipboard copy-btn"
                    @click="handleClickCopyField(row.api_url)">
                  </i>
                </span>
              </div>
            </template>
          </bk-table-column>
          <bk-table-column
            v-if="flagDocumnetUrl.length"
            :label="t('文档地址')"
            prop="doc_link"
            :min-width="180"
            :max-width="260"
            :show-overflow-tooltip="true"
          >
            <template #default="{ row }">
              <div class="path-wrapper">
                <span class="path-text">{{row.doc_link}}</span>
                <span class="path-icon">
                  <i
                    v-show="cursorId === row.id"
                    class="apigateway-icon icon-ag-clipboard copy-btn"
                    @click="handleClickCopyField(row.doc_link)">
                  </i>
                </span>
              </div>
            </template>
          </bk-table-column>
          <bk-table-column
            v-if="flagUpdatedTime.length"
            :label="t('更新时间')"
            prop="updated_time"
            :min-width="90"
            :show-overflow-tooltip="true"
          ></bk-table-column>
          <bk-table-column :label="t('操作')" width="150">
            <template #default="{ row }">
              <bk-button theme="primary" class="mr10" text @click="handleEdit(row)"> {{ t('编辑') }} </bk-button>
              <bk-button
                text
                theme="primary"
                :disabled="row.is_official"
                @click="handleDelete(row)">
                <template v-if="row.is_official">
                  <span v-bk-tooltips="t('官方组件，不可删除')"> {{ t('删除') }} </span>
                </template>
                <template v-else>
                  {{ t('删除') }}
                </template>
              </bk-button>
            </template>
          </bk-table-column>
          <!-- <bk-table-column type="setting">
            <bk-table-setting-content
              :fields="setting.fields"
              :selected="setting.selectedFields"
              :size="setting.size"
              :max="setting.max"
              @setting-change="handleSettingChange">
            </bk-table-setting-content>
          </bk-table-column> -->
        </bk-table>
      </bk-loading>
    </div>

    <bk-sideslider
      v-model:is-show="isSliderShow"
      :width="960"
      :title="sliderTitle"
      :quick-close="true"
      :before-close="handleBeforeClose"
      ext-cls="apigw-access-manager-slider-cls"
      @animation-end="handleAnimationEnd">
      <template #default>
        <div style="padding: 20px; padding-bottom: 40px;">
          <bk-loading
            :loading="detailLoading"
          >
            <bk-form :label-width="180" :rules="rules" ref="form" :model="formData">
              <bk-form-item :label="t('系统')" :required="true" property="system_id" :error-display-type="'normal'">
                <bk-select
                  :disabled="isDisabled"
                  :clearable="false"
                  v-model="formData.system_id"
                  @selected="handleSysSelect">
                  <bk-option
                    v-for="option in systemList"
                    :key="option.id"
                    :id="option.id"
                    :name="option.name">
                  </bk-option>
                </bk-select>
              </bk-form-item>
              <bk-form-item :label="t('组件名称simple')" :required="true" property="name" :error-display-type="'normal'">
                <bk-input
                  :maxlength="128"
                  :disabled="isDisabled"
                  v-model="formData.name"
                  :placeholder="t('由字母、数字、下划线（_）组成，首字符必须是字母，长度小于128个字符')">
                </bk-input>
                <p
                  class="tips"
                >
                  <i class="apigateway-icon icon-ag-info"></i>
                  {{ t('组件名称在具体系统下应唯一，将用于展示组件时的标识') }}
                </p>
              </bk-form-item>
              <bk-form-item
                :label="t('组件描述simple')"
                :required="true"
                property="description"
                :error-display-type="'normal'">
                <bk-input
                  :maxlength="128"
                  :disabled="isDisabled"
                  v-model="formData.description"
                  :placeholder="t('不超过128个字符')">
                </bk-input>
              </bk-form-item>
              <bk-form-item :label="t('请求方法')" :required="true" property="method" :error-display-type="'normal'">
                <bk-select
                  :disabled="isDisabled"
                  :clearable="false"
                  v-model="formData.method">
                  <bk-option
                    v-for="option in methodList"
                    :key="option.id"
                    :id="option.id"
                    :name="option.name">
                  </bk-option>
                </bk-select>
              </bk-form-item>
              <bk-form-item :label="t('组件路径')" :required="true" property="path" :error-display-type="'normal'">
                <bk-input
                  :disabled="isDisabled"
                  :maxlength="255"
                  v-model="formData.path"
                  :placeholder="t('以斜杠开头，可包含斜杠、字母、数字、下划线(_)、连接符(-)，长度小于255个字符')">
                </bk-input>
                <p class="tips">
                  <i class="apigateway-icon icon-ag-info"></i>
                  {{ t(`可设置为'/{system_name}/{component_name}/'，例如'/host/get_host_list/'`) }}
                </p>
              </bk-form-item>
              <bk-form-item
                :label="t('组件类代号')"
                :required="true"
                property="component_codename"
                :error-display-type="'normal'">
                <bk-input
                  :disabled="isDisabled"
                  v-model="formData.component_codename"
                  :placeholder="t('包含小写字母、数字、下划线或点号，长度小于255个字符')">
                </bk-input>
                <p class="tips">
                  <i class="apigateway-icon icon-ag-info"></i>
                  {{ t('一般由三部分组成：“前缀(generic).小写的系统名.小写的组件类名”，例如 "generic.host.get_host_list"') }}
                </p>
              </bk-form-item>
              <bk-form-item
                :label="t('权限级别')"
                :required="true"
                property="permission_level"
                :error-display-type="'normal'">
                <bk-select :clearable="false" v-model="formData.permission_level">
                  <bk-option
                    v-for="option in levelList"
                    :key="option.id"
                    :id="option.id"
                    :name="option.name">
                  </bk-option>
                </bk-select>
                <p class="tips">
                  <i class="apigateway-icon icon-ag-info"></i>
                  {{ t('无限制，应用不需申请组件API权限；普通权限，应用需在开发者中心申请组件API权限，审批通过后访问') }}
                </p>
              </bk-form-item>
              <bk-form-item
                :label="t('用户认证')"
                :required="true"
                property="verified_user_required"
                :error-display-type="'normal'">
                <bk-checkbox
                  :true-value="true"
                  :false-value="false"
                  v-model="formData.verified_user_required">
                </bk-checkbox>
                <p class="ag-tip mt5">
                  <i class="apigateway-icon icon-ag-info"></i>
                  {{ t('用户认证，请求方需提供蓝鲸用户身份信息') }}
                </p>
              </bk-form-item>
              <bk-form-item :label="t('超时时长')">
                <bk-input type="number" :max="600" :min="1" :precision="0" v-model="formData.timeout">
                  <template #suffix>
                    <section class="timeout-append">
                      <div>{{t('秒')}}</div>
                    </section>
                  </template>
                </bk-input>
                <p class="tips">
                  <i class="apigateway-icon icon-ag-info"></i>
                  {{ t('未设置时使用系统的超时时长，最大600秒') }}
                </p>
              </bk-form-item>
              <bk-form-item :label="t('组件配置')" v-if="formData.config_fields.length > 0">
                <render-config :list="formData.config_fields" ref="configRef" />
              </bk-form-item>
              <bk-form-item :label="t('是否开启')">
                <bk-checkbox
                  :true-value="true"
                  :false-value="false"
                  v-model="formData.is_active">
                </bk-checkbox>
              </bk-form-item>
            </bk-form>
          </bk-loading>
        </div>
      </template>
      <template #footer>
        <div style="padding-left: 90px;">
          <bk-button
            theme="primary"
            :loading="submitLoading"
            @click="handleSubmit">
            {{ t('保存') }}
          </bk-button>
          <bk-button style="margin-left: 6px;" @click="handleCancel"> {{ t('取消') }} </bk-button>
        </div>
      </template>
    </bk-sideslider>

    <bk-dialog
      width="480"
      :mask-close="true"
      :is-show="deleteDialogConf.visiable"
      :title="t('确认删除？')"
      @after-leave="handleAfterLeave">
      <div> {{ t('该操作不可恢复，是否继续？') }} </div>
      <template #footer>
        <bk-button
          theme="primary"
          :loading="deleteDialogConf.loading"
          @click="handleDeleteComponent">
          {{ t('确定') }}
        </bk-button>
        <bk-button @click="deleteDialogConf.visiable = false"> {{ t('取消') }} </bk-button>
      </template>
    </bk-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, watch, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { Message } from 'bkui-vue';
import { useRouter } from 'vue-router';
import { useSidebar } from '@/hooks';
import { copy } from '@/common/util';
import { useCommon } from '@/store';
import {
  getEsbComponents,
  checkEsbNeedNewVersion,
  getSystems,
  addComponent,
  updateComponent,
  getComponentsDetail,
  deleteComponentByBatch,
  getReleaseStatus,
  getFeatures,
} from '@/http';
import RenderSystem from './components/render-system.vue';
import RenderConfig from './components/render-config.vue';

const router = useRouter();
const { t } = useI18n();
const common = useCommon();
const { initSidebarFormData, isSidebarClosed } = useSidebar();

const systemFilterRef = ref();
const form = ref();
const configRef = ref();

const getDefaultData = () => {
  return {
    system_id: '',
    name: '',
    description: '',
    method: '',
    path: '',
    component_codename: '',
    permission_level: '',
    timeout: 30,
    is_active: true,
    config_fields: [],
    verified_user_required: true,
  };
};

const fields = [{
  id: 'systemName',
  label: t('系统名称'),
  disabled: true,
}, {
  id: 'componentName',
  label: t('组件名称'),
}, {
  id: 'type',
  label: t('请求方法'),
  disabled: true,
}, {
  id: 'url',
  label: t('请求路径'),
}, {
  id: 'updated_time',
  label: t('更新时间'),
}, {
  id: 'api_url',
  label: t('API地址'),
}, {
  id: 'documnet_url',
  label: t('文档地址'),
}];

const searchValue = ref<string>('');
const componentList = ref<any>([]);
const pagination = reactive({
  current: 1,
  count: 0,
  limit: 10,
});
const formData = ref<any>(getDefaultData());
const componentData = ref<any>({});
const isSliderShow = ref<boolean>(false);
const systemList = ref<any>([]);
const requestQueue = reactive(['system', 'component']);
const allData = ref<any>([]);
const displayData = ref<any>([]);
const submitLoading = ref<boolean>(false);
const isLoading = ref<boolean>(false);
const curSelectList = ref<any>([]);
const deleteDialogConf = reactive<any>({
  visiable: false,
  loading: false,
  ids: [],
});
const detailLoading = ref<boolean>(false);
const isReleasing = ref<boolean>(false);
const needNewVersion = ref<boolean>(false);
const isCursor = ref<boolean>(false);
const cursorId = ref<string>('');
const setting = reactive({
  max: 9,
  fields,
  selectedFields: fields.slice(0, 5),
  size: 'small',
});
const syncEsbToApigwEnabled = ref<boolean>(false);
const tableEmptyConf = reactive<any>({
  keyword: '',
  isAbnormal: false,
});
const isExpand = ref<boolean>(true);
const isFilter = ref<boolean>(false);
const curSelectSystemId = ref<string>('*');
const methodList = ref<any>(common.methodList);
const levelList = ref<any>([
  {
    id: 'unlimited',
    name: t('无限制'),
  },
  {
    id: 'normal',
    name: t('普通'),
  },
]);
const rules = reactive({
  system_id: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  name: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      regex: /^[a-zA-Z][a-zA-Z0-9_]{0,128}$|^$/,
      message: t('由字母、数字、下划线（_）组成，首字符必须是字母，长度小于128个字符'),
      trigger: 'blur',
    },
  ],
  description: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  method: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  component_codename: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  path: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
    {
      regex: /^\/[\w{}/.-]*$/,
      message: t('以斜杠开头，可包含斜杠、字母、数字、下划线(_)、连接符(-)，长度小于255个字符'),
      trigger: 'blur',
    },
  ],
  permission_level: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
  verified_user_required: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
});

const isEdit = computed(() => Object.keys(componentData.value)?.length > 0);
const isDisabled = computed(() => isEdit.value && componentData.value?.is_official);
const sliderTitle = computed(() => (isEdit.value ? t('编辑组件') : t('新建组件')));
const flagComponentName = computed(() => setting.selectedFields?.filter(v => v.label === t('组件名称')));
const flagUrl = computed(() => setting.selectedFields?.filter(v => v.label === t('请求路径')));
const flagApiUrl = computed(() => setting.selectedFields?.filter(v => v.label === t('API地址')));
const flagDocumnetUrl = computed(() => setting.selectedFields?.filter(v => v.label === t('文档地址')));
const flagUpdatedTime = computed(() => setting.selectedFields?.filter(v => v.label === t('更新时间')));

const handleSelect = ({ id }: any) => {
  curSelectSystemId.value = id;
  if (curSelectSystemId.value === '*') {
    displayData.value = allData.value;
  } else {
    displayData.value = allData.value?.filter((item: any) => item.system_id === curSelectSystemId.value);
  }
  pagination.current = 1;
  pagination.limit = 10;
  pagination.count = displayData.value?.length;
  componentList.value = getDataByPage();
};

const getComponents = async (loading = false) => {
  isLoading.value = loading;
  try {
    const params = {
      limit: 10000,
      offset: 0,
    };

    const res = await getEsbComponents(params);
    allData.value = Object.freeze(res);
    displayData.value = res;
    pagination.count = displayData.value?.length;
    componentList.value = getDataByPage();
    if (curSelectSystemId.value !== '*') {
      handleSelect({ id: curSelectSystemId.value });
    }
    tableEmptyConf.isAbnormal = false;
  } catch (e) {
    tableEmptyConf.isAbnormal = true;
    console.log(e);
  } finally {
    if (requestQueue?.length > 0) {
      requestQueue.shift();
    }
    isLoading.value = false;
  }
};

const setDefaultSelect = ({ row }: any) => {
  return !row?.is_official;
};

const handlerChange = ({ row, checked }: any) => {
  if (checked) {
    curSelectList.value?.push(row);
  } else {
    curSelectList.value = curSelectList.value?.filter((item: any) => item.id !== row.id);
  }
};

const handlerAllChange = ({ checked, data }: any) => {
  if (checked) {
    curSelectList.value = [...data];
  } else {
    curSelectList.value = [];
  }
};

const handleSysSelect = (value: any, option: any) => {
  const tempList = formData.value?.component_codename?.split('.');
  let customStr = '';
  if (tempList.length === 3) {
    // customStr = tempList[2];
    [, , customStr] = tempList;
  }
  formData.value.component_codename = `generic.${option.lowerName}.${customStr}`;
  systemFilterRef.value?.setSelected(value);
};

const checkNeedNewVersion = async () => {
  try {
    const res = await checkEsbNeedNewVersion();
    needNewVersion.value = res?.need_new_release;
  } catch (e) {
    needNewVersion.value = false;
  }
};

const getSystemList = async () => {
  try {
    const res = await getSystems();
    systemList.value = Object.freeze(res);
    // 获取组件是否需要发版本更新
    checkNeedNewVersion();
    // 子组件状态更新
    nextTick(() => {
      systemFilterRef.value?.updateTableEmptyConfig();
    });
  } catch (e) {
    console.log(e);
  } finally {
    if (requestQueue.length > 0) {
      requestQueue.shift();
    }
  }
};

const handleCancel = () => {
  isSliderShow.value = false;
};

const handleSubmit = () => {
  form.value?.validate().then(async () => {
    submitLoading.value = true;
    const tempData = Object.assign({}, formData.value);
    if (!tempData.timeout) {
      tempData.timeout = null;
    }
    if (tempData.method === '*') {
      tempData.method = '';
    }
    if (tempData.config_fields?.length > 0) {
      tempData.config = configRef.value?.getData();
      delete tempData.config_fields;
    }
    if (!isEdit.value) {
      delete tempData.config_fields;
    }
    try {
      if (!isEdit.value) {
        await addComponent(tempData);
      } else {
        await updateComponent(componentData.value?.id, tempData);
      }

      isSliderShow.value = false;
      getComponents(true);
      getSystemList();
    } catch (e) {
      console.log(e);
    } finally {
      submitLoading.value = false;
    }
  }, (validator: any) => {
    console.error(validator);
  });
};

const handleAnimationEnd = () => {
  componentData.value = {};
  formData.value = Object.assign({}, getDefaultData());
};

const handleCreate = () => {
  componentData.value = {};
  const curSystem = systemList.value?.find((item: any) => item.id === curSelectSystemId.value);
  let curSystemName = '';
  if (curSystem) {
    curSystemName = curSystem?.name?.toLocaleLowerCase();
  }
  formData.value = Object.assign(getDefaultData(), {
    method: 'GET',
    permission_level: 'unlimited',
    system_id: curSelectSystemId.value === '*' ? '' : curSelectSystemId.value,
    component_codename: curSystemName === '' ? 'generic.{system_name}' : `generic.${curSystemName}.`,
  });
  isSliderShow.value = true;
  nextTick(() => {
    // 收集初始化状态
    initSidebarFormData(formData.value);
  });
};

const getDataByPage = (page?: any) => {
  if (!page) {
    page = 1;
    pagination.current = 1;
  }
  let startIndex = (page - 1) * pagination.limit;
  let endIndex = page * pagination.limit;
  if (startIndex < 0) {
    startIndex = 0;
  }
  if (endIndex > displayData.value?.length) {
    endIndex = displayData.value?.length;
  }
  updateTableEmptyConfig();
  return displayData.value?.slice(startIndex, endIndex);
};

const handleSearch = (payload: any) => {
  if (payload === '') {
    return;
  }
  pagination.current = 1;
  pagination.limit = 10;
  isFilter.value = true;
  displayData.value = allData.value?.filter((item: any) => {
    const reg = new RegExp(`(${payload})`, 'gi');
    return item?.path?.match(reg) || item?.name?.match(reg);
  });
  pagination.count = displayData.value?.length;
  componentList.value = getDataByPage();
};

const handlePageLimitChange = (limit: number) => {
  pagination.limit = limit;
  pagination.current = 1;
  handlePageChange(pagination.current);
};

const handlePageChange = (page: number) => {
  pagination.current = page;
  const data = getDataByPage(page);
  componentList.value?.splice(0, componentList.value?.length, ...data);
};

const handleEdit = async (payload: any) => {
  componentData.value = Object.assign({}, payload);
  isSliderShow.value = true;
  detailLoading.value = true;
  try {
    const res = await getComponentsDetail(componentData.value?.id);
    const {
      name,
      description,
      method,
      path,
      timeout,
    } = res;
    formData.value.description = description;
    formData.value.name = name;
    formData.value.method = method === '' ? '*' : method;
    formData.value.path = path;
    formData.value.timeout = timeout;
    formData.value.system_id = res?.system_id;
    formData.value.component_codename = res?.component_codename;
    formData.value.permission_level = res?.permission_level;
    formData.value.is_active = res?.is_active;
    formData.value.config_fields = res?.config_fields || [];
    formData.value.verified_user_required = res?.verified_user_required;
    nextTick(() => {
      initSidebarFormData(formData.value);
    });
  } catch (e) {
    console.warn(e);
    return false;
  } finally {
    detailLoading.value = false;
  }
};

const handleAfterLeave = () => {
  deleteDialogConf.ids = [];
};

const handleDeleteComponent = async () => {
  deleteDialogConf.loading = true;
  try {
    await deleteComponentByBatch({ ids: deleteDialogConf.ids });
    Message({
      message: t('删除成功'),
      theme: 'success',
    });
    deleteDialogConf.visiable = false;
    curSelectList.value = [];
    getComponents(true);
    getSystemList();
    return true;
  } catch (e) {
    console.warn(e);
    return false;
  } finally {
    deleteDialogConf.loading = false;
  }
};

const handleBatchDelete = () => {
  deleteDialogConf.ids = [...curSelectList.value?.map((item: any) => item.id)];
  deleteDialogConf.visiable = true;
};

const handleDelete = ({ id }: any) => {
  deleteDialogConf.ids?.push(id);
  deleteDialogConf.visiable = true;
};

const getStatus = async () => {
  try {
    const res = await getReleaseStatus();
    isReleasing.value = res?.is_releasing;
    if (isReleasing.value) {
      setTimeout(() => {
        getStatus();
      }, 5000);
    }
  } catch (e) {
    console.warn(e);
    return false;
  }
};

const handlesync = () => {
  router.push({
    name: 'syncApigwAccess',
  });
};

const handlerRouter = () => {
  router.push({
    name: 'syncHistory',
  });
};

const handleClickCopyField = (field: any) => {
  copy(field);
};

const changeEnter = (col: any, even: any, rowData: any) => {
  cursorId.value = rowData?.id;
  isCursor.value = true;
};

const changeLeave = () => {
  cursorId.value = '';
  isCursor.value = false;
};

const handleSettingChange = ({ fields, size }: any) => {
  setting.size = size;
  setting.selectedFields = fields;
};

const getFeature = async () => {
  try {
    const params = {
      limit: 10000,
      offset: 0,
    };
    const res = await getFeatures(params);
    syncEsbToApigwEnabled.value = res?.SYNC_ESB_TO_APIGW_ENABLED;
  } catch (e) {
    console.log(e);
  }
};

// const clearFilterKey = () => {
//   searchValue.value = '';
// };

const updateTableEmptyConfig = () => {
  tableEmptyConf.keyword = searchValue.value;
};

const handleBeforeClose = () => {
  return isSidebarClosed(JSON.stringify(formData.value));
};

const init = () => {
  getSystemList();
  getComponents(true);
  getStatus();
  getFeature();
};

init();

watch(
  () => searchValue.value,
  (newVal, oldVal) => {
    if (newVal === '' && oldVal !== '' && isFilter.value) {
      isFilter.value = false;
      pagination.current = 1;
      pagination.limit = 10;
      displayData.value = allData.value;
      pagination.count = displayData.value?.length;
      componentList.value = getDataByPage();
    }
  },
);

// watch(
//   () => requestQueue,
//   (value) => {
//     if (value?.length < 1) {
//       this.$store.commit('setMainContentLoading', false);
//     }
//   },
// );
</script>

<style lang="scss" scoped>
.app-content {
  min-height: calc(100vh - 104px);
  padding: 0;
}
.apigw-access-manager-wrapper {
  background: #fff;
  display: flex;
  justify-content: flex-start;
  .left-system-nav {
      position: relative;
      max-height: calc(100vh - 104px);
      background: #fff;
      width: 300px;
      &.is-expand {
          width: 0;
          .left-wrapper {
              width: 0;
          }
          .handle-icon i {
              transform: rotate(270deg);
          }
      }
  }
  .left-wrapper {
      padding: 10px 0;
      margin-right: 16px;
      width: 300px;
      overflow: hidden;
      height: 100%;
      background: #f6f7fb;
  }
  .handle-icon  {
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      right: -16px;
      width: 16px;
      height: 64px;
      background: #DCDEE5;
      border-radius: 0 4px 4px 0;
      cursor: pointer;
      display: flex;
      align-items: center;

      i {
          display: inline-block;
          margin-left: -5px;
          font-size: 24px;
          color: #fff;
          transform: rotate(90deg);
      }
  }
  .right-wrapper {
      padding: 0 10px;
      margin: 24px;
      width: calc(100% - 348px);
      &.is-expand {
          margin-left: 20px;
          width: calc(100% - 40px);
      }

  }
  .search-wrapper {
      display: flex;
      justify-content: space-between;
  }
  .component-flex{
      display: flex;
      justify-content: space-between;
      align-items: center;
      .history-icon{
          cursor: pointer;
          display: inline-block;
          height: 32px;
          line-height: 32px;
          width: 30px;
          border: 1px solid #c4c6cc;
          border-radius: 2px;
          background: #fff;
          color: #979ba5;
          &:hover {
              border-color: #979ba5;
              color: #63656e;
          }
      }
  }
  .bk-table {
      .api-name,
      .docu-link {
          max-width: 200px;
          display: inline-block;
          word-break: break-all;
          overflow: hidden;
          white-space: nowrap;
          text-overflow: ellipsis;
          vertical-align: bottom;
      }
      .copy-icon {
          font-size: 14px;
          cursor: pointer;
          &:hover {
              color: #3a84ff;
          }
      }
  }
}
.apigw-access-manager-slider-cls {
  .tips {
      line-height: 24px;
      font-size: 12px;
      color: #63656e;
      i {
        position: relative;
        top: -1px;
        margin-right: 3px;
      }
  }
  .timeout-append {
    width: 50px;
    line-height: 32px;
    font-size: 12px;
    text-align: center;
  }
}

.ag-flex {
  display: flex;
}
.ag-auto-text {
  vertical-align: middle;
}
.ag-tag.success {
  width: 44px;
}

.path-wrapper {
  position: relative;
  display: flex;
  width: 100%;
}

.path-text{
  display: inline-block;
  width: 200px;
  overflow: hidden;
  text-overflow:ellipsis; white-space: nowrap;
}
.path-icon {
  position: absolute;
  right: 0px;
  cursor: pointer;
  color: #3a84ff;
}

.copyCursor {
  cursor : pointer;
}
</style>

<style>
.tippy-content{
  max-width: 550px;
}
.bk-table-setting-content{
  width: 550px;
}
</style>
