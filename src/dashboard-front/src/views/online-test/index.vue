<template>
  <div class="app-content online-test p20">
    <div class="panel-content">
      <div class="request-panel">
        <div class="panel-title"> {{ t('请求') }} </div>
        <bk-form ref="form" :label-width="120">
          <bk-form-item :label="t('环境')" :property="'name'">
            <bk-select
              :clearable="false"
              filterable
              :input-search="false"
              v-model="params.stage_id"
              @change="handleStageChange">
              <bk-option v-for="option in stageList" :key="option.id" :id="option.id" :name="option.name">
              </bk-option>
            </bk-select>
          </bk-form-item>
          <bk-form-item :required="true" :label="t('请求资源')" :error-display-type="'normal'">
            <bk-select
              :clearable="false"
              filterable
              :input-search="false"
              v-model="formData.path"
              @change="handleResourceChange">
              <bk-option v-for="option in resourceList" :key="option" :id="option" :name="option">
              </bk-option>
            </bk-select>
            <div class="resource-empty" v-show="!isPageLoading && resourceEmpty">
              {{ t('未找到可用的请求资源，因为当前选择环境未发布版本，请先发布版本到该环境') }}
            </div>
            <p class="ag-tip mt5">
              <i class="apigateway-icon icon-ag-info"></i>{{ t('资源必须发布到对应环境，才支持选择及调试') }}
            </p>
          </bk-form-item>
          <bk-form-item :required="true" :label="t('请求方法')" :error-display-type="'normal'">
            <bk-select :clearable="false" v-model="formData.method" @change="handleMethodChange">
              <bk-option v-for="option in methodList" :key="option.id" :id="option.id" :name="option.name">
              </bk-option>
            </bk-select>
          </bk-form-item>
          <bk-form-item :label="t('子路径')" v-if="isMatchAnyMethod || isShowSubpath">
            <bk-input v-model="formData.subpath"></bk-input>
            <p class="ag-tip mt5">
              <i class="apigateway-icon icon-ag-info"></i>
              {{ t('请求资源中，资源请求路径*部分的子路径') }}
            </p>
          </bk-form-item>
          <bk-form-item v-show="hasPathParmas" :required="true" :label="t('路径参数')">
            <apigw-key-valuer
              style="margin-right: 69px;" class="kv-wrapper" ref="pathKeyValuer" :key-readonly="true"
              :key-regex-rule="{}" :buttons="false" :value="formData.params.path">
            </apigw-key-valuer>
          </bk-form-item>
          <bk-form-item label="Headers">
            <apigw-key-valuer
              class="kv-wrapper" ref="headerKeyValuer" :value="formData.headers"
              @toggle-height="controlToggle">
            </apigw-key-valuer>
          </bk-form-item>
          <bk-form-item label="Query">
            <apigw-key-valuer
              class="kv-wrapper" ref="queryKeyValuer"
              :key-regex-rule="{ regex: /^[\w-]+$/, message: t('键由英文字母、数字、连接符（-）、下划线（_）组成') }"
              :value="formData.params.query" @toggle-height="controlToggle">
            </apigw-key-valuer>
          </bk-form-item>
          <bk-form-item label="Body">
            <bk-input class="ag-textarea" type="textarea" :placeholder="t('请输入')" v-model="params.body">
            </bk-input>
          </bk-form-item>
          <bk-form-item :label="t('应用认证')">
            <div class="bk-button-group">
              <bk-button
                class="ag-tab-button" :class="{ 'is-selected': isDefaultAppAuth }"
                @click="formData.appAuth = 'use_test_app'">
                {{ t('默认测试应用') }}
              </bk-button>
              <bk-button
                class="ag-tab-button" :class="{ 'is-selected': formData.appAuth === 'use_custom_app' }"
                @click="formData.appAuth = 'use_custom_app'">
                {{ t('自定义应用') }}
              </bk-button>
            </div>
            <template v-if="isDefaultAppAuth">
              <bk-input class="mt5" :value="testAppCode" :disabled="true" :placeholder="t('请输入蓝鲸应用ID')">
                <template #prefix>
                  <div class="group-text" style="width: 130px; text-align: right;">bk_app_code</div>
                </template>
              </bk-input>
              <bk-input class="mt5" :value="'******'" :disabled="true" :placeholder="t('请输入蓝鲸应用密钥')">
                <template #prefix>
                  <div class="group-text" style="width: 130px; text-align: right;">bk_app_secret</div>
                </template>
              </bk-input>
            </template>
            <template v-else>
              <bk-input class="mt5" v-model="formData.authorization.bk_app_code" :placeholder="t('请输入蓝鲸应用ID')">
                <template #prefix>
                  <div class="group-text" style="width: 130px; text-align: right;">bk_app_code</div>
                </template>
              </bk-input>
              <bk-input class="mt5" v-model="formData.authorization.bk_app_secret" :placeholder="t('请输入蓝鲸应用密钥')">
                <template #prefix>
                  <div class="group-text" style="width: 130px; text-align: right;">bk_app_secret</div>
                </template>
              </bk-input>
            </template>
            <p class="ag-tip mt5">
              <i class="apigateway-icon icon-ag-info"></i>
              {{ t('默认测试应用，网关自动为其短期授权；自定义应用，需主动为应用授权资源访问权限') }}
            </p>
          </bk-form-item>
          <bk-form-item :label="t('用户认证')" :key="tokenInputRender" v-if="curResource.verified_user_required">
            <div class="bk-button-group">
              <bk-button
                class="ag-tab-button" :class="{ 'is-selected': formData.useUserFromCookies }"
                @click="formData.useUserFromCookies = true">
                {{ t('默认用户认证') }}
              </bk-button>
              <bk-button
                class="ag-tab-button" :class="{ 'is-selected': !formData.useUserFromCookies }"
                @click="formData.useUserFromCookies = false">
                {{ t('自定义用户认证') }}
              </bk-button>
            </div>
            <template v-if="formData.useUserFromCookies">
              <bk-input
                v-for="(item, index) in cookieNames" class="mt5 token-input" v-model="userPlaceholder"
                :key="index" :disabled="true">
                <template #prefix>
                  <div class="group-text" style="width: 130px; text-align: right;">{{ item.cookie_name }}</div>
                </template>
              </bk-input>
            </template>
            <!-- 自定义 -->
            <template v-else>
              <bk-input
                v-for="(item, index) in cookieNames" class="mt5 token-input"
                v-model="formData.authorization[item.key]"
                :placeholder="t(`请输入 Cookies 中字段 ${item.cookie_name} 的值`)" :key="index">
                <template #prefix>
                  <div class="group-text" style="width: 130px; text-align: right;">{{ item.cookie_name }}</div>
                </template>
              </bk-input>
            </template>
            <p class="ag-tip mt5">
              <i class="apigateway-icon icon-ag-info"></i>
              {{ t('默认用户认证，将默认从 Cookies 中获取用户认证信息；自定义用户认证，可自定义用户认证信息') }}
            </p>
          </bk-form-item>
        </bk-form>
        <div class="footer-btn-wrapper">
          <bk-button
            v-if="!sendButtonDisabled" theme="primary" class="mr10" :loading="requestStatus === 0"
            @click.stop.prevent="handleSendRequest">
            {{ t('发送请求') }}
          </bk-button>
          <bk-popover :content="t('请完善请求信息')" v-else>
            <bk-button theme="primary" class="mr10" disabled>
              {{ t('发送请求') }}
            </bk-button>
          </bk-popover>
          <bk-button @click.stop.prevent="handleReset"> {{ t('重置') }} </bk-button>
        </div>
      </div>
      <div class="divider"></div>
      <div class="response-panel">
        <div class="panel-title"> {{ t('请求详情') }} </div>
        <div class="request-detail">
          <div v-if="requestStatus !== -1">{{ response.curl }}</div>
          <div v-else>
            <i class="apigateway-icon icon-ag-info"></i>
            {{ t('无') }}
          </div>
        </div>
        <div class="panel-title"> {{ t('响应') }} </div>
        <template v-if="requestStatus !== -1">
          <bk-form class="response-form" :label-width="90">
            <bk-form-item label="Time：">
              <span class="value">{{ response.proxy_time }}</span>
              <span class="unit"> {{ t('毫秒') }} </span>
            </bk-form-item>
            <bk-form-item label="Status：">
              <span class="value">{{ response.status_code }}</span>
            </bk-form-item>
            <bk-form-item label="Size：">
              <span class="value">{{ response.size }}</span>
              <span class="unit">KB</span>
            </bk-form-item>
            <bk-form-item :label-width="0" class="response-form-item code">
              <bk-tab v-model:active="responseActiveTab" ext-cls="response-content-tab" @tab-change="tabchange">
                <bk-tab-panel name="body" label="Body">
                  <div class="tab-content body">
                    <editor-monaco v-model="formattedResBody" :read-only="true" ref="bodyCodeViewer" />
                  </div>
                </bk-tab-panel>
                <bk-tab-panel name="headers" label="Headers">
                  <div class="tab-content headers">
                    <editor-monaco v-model="formattedResHeaders" :read-only="true" ref="headerCodeViewer" />
                  </div>
                </bk-tab-panel>
              </bk-tab>
            </bk-form-item>
          </bk-form>
        </template>
        <div v-else>
          <span class="unsent">
            <i class="apigateway-icon icon-ag-info"></i>
            {{ t('请先发送请求') }}
          </span>
        </div>
      </div>
    </div>
    <!-- 吸顶按钮组 -->
    <div class="fixed-footer-btn-wrapper" :style="{ paddingLeft: fixedLeft + 'px' }" v-show="isAdsorb">
      <bk-button
        v-if="!sendButtonDisabled" theme="primary" class="mr10" :loading="requestStatus === 0"
        @click.stop.prevent="handleSendRequest">
        {{ t('发送请求') }}
      </bk-button>
      <bk-popover :content="t('请完善请求信息')" v-else>
        <bk-button theme="primary" class="mr10" disabled>
          {{ t('发送请求') }}
        </bk-button>
      </bk-popover>
      <bk-button @click.stop.prevent="handleReset"> {{ t('重置') }} </bk-button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue';
import { Message } from 'bkui-vue';
import { useI18n } from 'vue-i18n';
import { useCommon } from '@/store';
import { getReleaseResources, getStages, postAPITest, getApiDetail, getUserAuthType } from '@/http';
import ApigwKeyValuer from '@/components/key-valuer';
import editorMonaco from '@/components/ag-editor.vue';
import { cloneDeep } from 'lodash';

const { t } = useI18n();
const common = useCommon();

const BK_TEST_APP_CODE = 'apigw-api-test';

// 编辑器实例
const bodyCodeViewer: any = ref<InstanceType<typeof editorMonaco>>();
const headerCodeViewer: any = ref<InstanceType<typeof editorMonaco>>();
const form = ref();
// 键值对输入实例
const headerKeyValuer = ref();
const queryKeyValuer = ref();
const pathKeyValuer = ref();

const defaultValue = {
  params: {
    stage_id: '',
    resource_id: '',
    method: '',
    headers: {},
    path_params: {},
    query_params: {},
    body: '',
    use_test_app: true,
    subpath: '',
    use_user_from_cookies: false,
    authorization: {
      bk_app_code: '',
      bk_app_secret: '',
      uin: '',
      skey: '',
    },
  },
  formData: {
    path: '',
    method: '',
    subpath: '',
    appAuth: 'use_test_app',
    authorization: {
      bk_app_code: '',
      bk_app_secret: '',
      uin: '',
      skey: '',
      bk_ticket: '',
    },
    params: {
      path: {},
      query: {},
    },
    headers: {},
    // 用户认证
    useUserFromCookies: true,
  },
};

const expandWidth = 384;
// const awayWidth = 204;

const isPageLoading = ref<boolean>(true);
const requestStatus = ref<number>(-1);
const stageList = ref<any>([]);
const resources = ref<any>({});
const methodList = ref<any[]>([]);
const responseActiveTab = ref<string>('body');
const params = ref({ ...defaultValue.params });
const formData = ref<any>({ ...defaultValue.formData });
const response = ref<any>({});
const isResponseBodyJson = ref<boolean>(false);
const isMatchAnyMethod = ref<boolean>(false);
const tokenInputRender = ref<number>(0);
const curApigw = ref({
  name: '',
  description: '',
  status: 0,
  statusBoolean: false,
  statusForFe: false,
  is_public: true,
  user_auth_type: '',
  maintainers: [],
  maintainersForFe: [],
});
const testAppCode = ref(BK_TEST_APP_CODE);
const cookieNames = ref([]);
const isAdsorb = ref<boolean>(false);
const fixedLeft = ref(expandWidth);
const userPlaceholder = '******';
const allMethodList = ref([common.methodList]);
const headerViewRef = ref(null);


const isDefaultAppAuth = computed(() => formData.value.appAuth === 'use_test_app');
const curResource = computed(() => {
  if (resources.value[formData.value.path]) {
    return resources.value[formData.value.path][0] || {};
  }
  return {};
});
const tokenName = computed(() => {
  return cookieNames.value[0]?.cookie_name;
});
const isShowSubpath = computed(() => {
  if (formData.value.method && formData.value.path) {
    let paths = [];
    const resourceId = formData.value.method.split('_')[0];
    for (const key of Object.keys(resources.value)) {
      if (key === formData.value.path) {
        paths = resources.value[key];
      }
    }
    const resource = paths.find((item: any) => String(item.id) === String(resourceId));
    return resource?.match_subpath;
  }
  return false;
});
const formattedResHeaders = computed(() => {
  const headers = JSON.stringify(response.value?.headers, null, 4);
  headerCodeViewer.value?.setValue(headers);
  return headers;
});
const formattedResBody = computed(() => {
  let { body } = response.value;
  try {
    const bodyJSON = JSON.parse(response.value?.body);
    body = JSON.stringify(bodyJSON, null, 4);
  } catch (e) {
    // nothing
  }
  bodyCodeViewer.value?.setValue(body);
  return body;
});

const hasPathParmas = computed(() => Object.keys(formData.value.params.path).length > 0);
const resourceList = computed(() => Object.keys(resources.value));
const resourceEmpty = computed(() => !resourceList.value.length);
const sendButtonDisabled = computed(() => resourceEmpty.value || !params.value?.resource_id);

const getUserAuthTypeData = async () => {
  const res = await getUserAuthType();
  cookieNames.value = res.login_ticket;
};
getUserAuthTypeData();

watch(
  () => response.value?.body,
  (body) => {
    try {
      const bodyJson = JSON.parse(body);
      isResponseBodyJson.value = bodyJson && typeof bodyJson === 'object';
    } catch (e) {
      isResponseBodyJson.value = false;
    }
  },
);

watch(
  () => isShowSubpath,
  () => {
    formData.value.subpath = '';
  },
);

const getApigwReleaseResources = async () => {
  const stageId = params.value?.stage_id;
  if (!stageId) return;

  try {
    const res = await getReleaseResources(common.apigwId, stageId);
    resources.value = res || {};

    // 环境变更会触发资源列表更新，资源更新后需要清空已有的选择
    formData.value.path = '';
    formData.value.method = '';
  } catch (e) {
    console.log(e);
  } finally {
    isPageLoading.value = false;
  }
};

const getApigwStages = async () => {
  const pageParams = {
    no_page: true,
    order_by: 'name',
  };

  try {
    const res = await getStages(common.apigwId, pageParams);
    stageList.value = res;

    params.value.stage_id = (stageList.value[0] || {})?.id;
    getApigwReleaseResources();
  } catch (e) {
    console.log(e);
  }
};

const postApigwAPITest = async (data: any) => {
  requestStatus.value = 0;
  try {
    const res = await postAPITest(common.apigwId, data);
    response.value = res;
  } catch (e) {
    console.log(e);
  } finally {
    responseActiveTab.value = 'body';
    requestStatus.value = 1;
  }
};

const tabchange = (name: string) => {
  nextTick(() => {
    if (name === 'headers') {
      headerCodeViewer.value?.setValue(formattedResHeaders.value);
    } else {
      bodyCodeViewer.value?.setValue(formattedResBody.value);
    }
  });
};

const checkFormData = (data: any) => {
  const pathParams = Object.values(data.path_params);
  const reg = /^[\w{}/.-]*$/;
  const codeReg = /^[a-z][a-z0-9-_]+$/;
  if ((isMatchAnyMethod.value || isShowSubpath) && !reg.test(data.subpath)) {
    Message({
      theme: 'error',
      message: t('请输入合法的子路径'),
    });
    form.value.validate();
    return false;
  }
  if (hasPathParmas.value && pathParams.some((val: any) => !val?.length)) {
    Message({
      theme: 'error',
      message: t('请输入完整的路径参数'),
    });
    form.value.validate();
    return false;
  }
  if (data.authorization.bk_app_code && !codeReg.test(data.authorization.bk_app_code)) {
    Message({
      theme: 'error',
      delay: 5000,
      message: t('应用ID格式不正确，只能包含：小写字母、数字、连字符(-)、下划线(_)，首字母必须是字母'),
    });
    return false;
  }

  return true;
};

const handleSendRequest = async () => {
  params.value.headers = headerKeyValuer.value?.getValue();
  params.value.query_params = queryKeyValuer.value?.getValue();
  params.value.path_params = pathKeyValuer.value?.getValue();
  params.value.subpath = isMatchAnyMethod.value || isShowSubpath ? formData.value.subpath : '';
  // 用户认证
  params.value.use_user_from_cookies = curResource.value?.verified_user_required
    ? formData.value?.useUserFromCookies
    : false;
  params.value.authorization = formData.value.authorization;
  params.value.use_test_app = isDefaultAppAuth.value;
  const data: any = cloneDeep(params.value);

  // 默认应用认证数据过滤
  if (isDefaultAppAuth.value) {
    data.authorization.bk_app_secret = '';
    data.authorization.bk_app_code = '';
  }
  // 默认用户认证数据过滤
  if (formData.value.useUserFromCookies) {
    cookieNames.value.forEach((item) => {
      data.authorization[item.key] = '';
    });
  }

  try {
    await form.value?.validate();

    if (checkFormData(data)) {
      postApigwAPITest(data);
    }
  } catch (e) {
    console.error(e);
  }
};

const handleResourceChange = (value: any) => {
  // 环境/资源/方法类似三级联动，上级改变了下级值需要清空
  formData.value.method = '';

  // 重置选择后value可能为空
  const resourceList = resources.value[value] || [];
  // 取得指定资源路径下的请求方法列表
  methodList.value = resourceList.map((resource: any) => ({
    id: `${resource.id}_${resource.method}`,
    name: resource.method,
  }));

  // 只有一个时，any需要转换为全部，否则默认选中
  if (methodList.value.length === 1) {
    if (methodList.value[0].name === 'ANY') {
      methodList.value = allMethodList.value?.slice(0, -1);
      isMatchAnyMethod.value = true;
    } else {
      formData.value.method = methodList.value[0].id;
      isMatchAnyMethod.value = false;
      handleMethodChange(formData.value.method);
    }
  }

  formData.value.params.path = {};
  if (value) {
    const matches = value.matchAll(/{([\w-]+?)}/g);
    for (const match of matches) {
      formData.value.params.path[match[1]] = '';
    }
  }
};

const handleMethodChange = (value: string) => {
  const methodValue = value.split('_');
  const { path } = formData.value;
  const resourceList = resources.value[path] || [];

  // 路径与方法确定一个资源
  const resource = resourceList.find((resource: any) => resource.path === path && resource.method === methodValue[1]);

  if (resource) {
    params.value.resource_id = resource.id;
    params.value.method = resource.method;
  } else if (resourceList.length && value) {
    // 存在资源但匹配不到则认为是any，any取第一个元素的id
    params.value.resource_id = resourceList[0].id;
    // any没有id值，[0]元素即为method名称
    // params.value.method = methodValue[0];
    [params.value.method] = methodValue;
  } else {
    params.value.resource_id = '';
    params.value.method = '';
  }
};

const handleStageChange = () => {
  getApigwReleaseResources();
};

const handleReset = () => {
  const defaultParams = { ...defaultValue.params };
  defaultParams.stage_id = params.value?.stage_id;
  params.value = defaultParams;
  formData.value = { ...defaultValue.formData };
  formData.value.params.query = {};
  formData.value.headers = {};
  formData.value.authorization = {
    bk_app_code: '',
    bk_app_secret: '',
    uin: '',
    skey: '',
    bk_ticket: '',
  };
  nextTick(() => {
    controlToggle();
  });
};

// const handleAuthChange = () => {
//   formData.value.authorization.bk_app_code = '';
//   formData.value.authorization.bk_app_secret = '';
// };

const getApigwDetail = async () => {
  try {
    const res = await getApiDetail(common.apigwId);
    curApigw.value = res;
    curApigw.value.statusBoolean = Boolean(curApigw.value?.status);
  } catch (e) {
    console.log(e);
  }
};

const setUserToken = () => {
  formData.value.authorization[tokenName.value] = '';
  tokenInputRender.value += 1;
};

// 元素滚动判断元素是否吸顶
const controlToggle = () => {
  const el = document.querySelector('.footer-btn-wrapper');
  const bottomDistance = getDistanceToBottom(el);
  const maxDistance = 1000;
  // 是否吸附
  if (bottomDistance < 25 || bottomDistance > maxDistance) {
    isAdsorb.value = true;
    el.classList.add('is-pinned');
  } else {
    isAdsorb.value = false;
    el.classList.remove('is-pinned');
  }
};

const observerBtnScroll = () => {
  const container = document.querySelector('.default-header-view');
  container?.addEventListener('scroll', controlToggle);
};

const destroyEvent = () => {
  const container = document.querySelector('.default-header-view');
  container?.removeEventListener('scroll', controlToggle);
  headerViewRef.value?.removeEventListener('scroll', controlToggle);
};

// 获取按钮底部距离
const getDistanceToBottom = (element: any) => {
  const rect = element?.getBoundingClientRect();
  return Math.max(0, window.innerHeight - rect.bottom);
};

const clearAuthData = () => {
  formData.value.authorization.bk_app_secret = '';
  formData.value.authorization.bk_app_code = '';
  cookieNames.value.forEach((item) => {
    formData.value.authorization[item.key] = '';
  });
};

const init = async () => {
  getApigwStages();
  await getApigwDetail();
  setUserToken();
};

init();

onMounted(() => {
  nextTick(() => {
    headerViewRef.value = document.querySelector('.default-header-view');
    // 初始化判断按钮组是否吸附
    controlToggle();
    observerBtnScroll();
  });
});

onBeforeUnmount(() => {
  destroyEvent();
  clearAuthData();
});
</script>

<style lang="scss" scoped>
.panel-content {
  display: flex;
  min-height: calc(100vh - 260px);

  .request-panel {
    flex: 1;
    min-width: 590px;
    padding-bottom: 60px;

    .bk-form-item {
      margin-bottom: 20px;
    }

    .resource-empty {
      font-size: 12px;
      color: #7b7d8a;
    }

    .auth-checkbox {
      line-height: 32px;
    }
  }

  .response-panel {
    flex: 1;
    max-width: 100%;

    .unsent {
      color: #7b7d8a;
      font-size: 14px;
      margin-left: 12px;
    }
  }

  .panel-title {
    font-size: 14px;
    font-weight: 700;
    color: #313238;
    margin-bottom: 16px;
  }

  .divider {
    flex: none;
    margin: 0 40px;
    width: 1px;
    background: #DCDEE5;
  }

  .response-form {
    .bk-form-item {
      margin-bottom: 0px;
    }
    .response-form-item.code {
      padding-left: 90px;
    }
  }

  .response-content-tab {
    width: 100%;
    background: #fff;
    margin-top: 10px;

    .tab-content {
      padding: 0 16px;
      color: #7b7d8a;
      font-size: 14px;
      min-height: 70px;
      line-height: 22px;
      width: 100%;
      height: 460px;
      box-sizing: border-box;
    }
  }

  .request-detail {
    background: #fff;
    padding: 8px 12px;
    margin-bottom: 48px;
    font-size: 14px;
    line-height: 22px;
    color: #63656E;
    font-family: 'Courier New', Courier, monospace;
  }

  .form-wrap {
    display: flex;
    margin-top: 10px;

    .label {
      width: 120px;
      font-size: 14px;
      text-align: right;
    }

    .input-wrap {
      flex: 1;
    }
  }

  .wrapper {
    display: flex;
    border: 1px solid #dcdee5;
    margin-top: 10px;
    background: #FFF;
    border-radius: 2px;

    .left {
      width: 70px;
      text-align: center;
      line-height: 95px;
      background: #f1f4f8;
      border-right: 1px solid #dcdee5;
    }

    .right {
      padding: 10px;
      flex: 1;
    }
  }
}

.ag-inner-btn {
  background: #3a84ff;
  color: #FFF !important;
  width: 60px;
  height: 30px;
  line-height: 30px;
  border-radius: 0 2px 2px 0;
  font-size: 13px;
  text-align: center;
  -webkit-box-shadow: 0px 0 0px 1px #3a84ff;
  box-shadow: 0px 0 0px 1px #3a84ff;
  cursor: pointer;
}

.footer-btn-wrapper {
  position: sticky;
  bottom: 0;
  margin-top: 8px;
  height: 52px;
  background: #f6f7fb;
  padding-left: 120px;
  width: 101%;
  display: flex;
  align-items: center;
  z-index: 9;
}

.fixed-footer-btn-wrapper {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 10px 0;
  background: #fff;
  box-shadow: 0 -2px 4px 0 #0000000f;
  z-index: 9;
  transition: .3s;
}

.is-pinned {
  opacity: 0;
}

.user-tips {
  font-size: 12px;
  color: #63656E;
  line-height: 16px;
}

.group-text {
  display: inline-block;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #63656e;
  padding: 0 15px;
  font-size: 12px;
  font-size: var(--font-size);
  vertical-align: middle;
  line-height: 28px;
  border-right: 1px solid #c4c6cc;
  background-color: #f5f7fa;
}
</style>

<style lang="scss">
.bk-input.is-disabled,
.bk-input.is-readonly {
  .group-text {
    border-color: #dcdee5;
  }
}
</style>
