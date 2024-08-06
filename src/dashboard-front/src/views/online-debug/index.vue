<template>
  <online-test-top />
  <bk-resize-layout
    class="content-resize"
    collapsible
    initial-divide="342px"
  >
    <template #aside>
      <div class="resize-aside">
        <div class="source-title">{{ t('资源列表') }}</div>
        <bk-select
          class="stage-select"
          v-model="stage"
          filterable
          :clearable="false"
          :prefix="t('环境')"
          @change="handleStageChange"
        >
          <bk-option
            v-for="item in stageList"
            :id="item.id"
            :key="item.id"
            :name="item.name"
          />
        </bk-select>
        <div class="search-source">
          <bk-input
            v-model="keyword"
            :clearable="true"
            type="search"
          />
        </div>
        <bk-collapse class="my-menu" v-model="activeName" v-if="Object.keys(resourceGroup).length">
          <template v-for="group of resourceGroup">
            <bk-collapse-panel
              v-if="group?.resources?.length"
              :name="group.labelName"
              :key="group.labelId">
              <template #header>
                <div class="my-menu-header">
                  <angle-up-fill
                    :class="['menu-header-icon', !activeName?.includes(group.labelName) ? 'fold' : '']" />
                  <div class="my-menu-title">{{group.labelName}}</div>
                </div>
              </template>

              <template #content>
                <div>
                  <ul class="component-list list">
                    <li
                      v-for="component of group.resources"
                      :key="component.name"
                      :title="component.name"
                      :class="{ 'active': curComponentName === component.name }"
                      @click="handleShowDoc(component)">
                      <!-- eslint-disable-next-line vue/no-v-html -->
                      <p class="name" v-html="hightlight(component.name)" v-bk-overflow-tips></p>
                      <!-- eslint-disable-next-line vue/no-v-html -->
                      <p class="label" v-html="hightlight(component.description) || t('暂无描述')" v-bk-overflow-tips>
                      </p>
                    </li>
                  </ul>
                </div>
              </template>
            </bk-collapse-panel>
          </template>
        </bk-collapse>
        <template v-else-if="keyword">
          <TableEmpty
            :keyword="keyword"
            @clear-filter="keyword = ''"
          />
        </template>
      </div>
    </template>
    <template #main>
      <div class="resize-main">
        <div class="request-setting">
          <bk-collapse
            class="request-setting-collapse"
            v-model="activeIndex"
          >
            <bk-collapse-panel :name="1">
              <template #header>
                <div class="request-setting-title">
                  <div class="request-source-name">
                    <right-shape :class="['request-source-icon', activeIndex?.includes(1) ? 'switch' : '']" />
                    <span class="source-title">{{ curResource?.name }}</span>
                    <span class="source-subtitle">（{{ curResource?.description }}）</span>
                  </div>
                  <div
                    class="request-source-path seldom-path"
                    v-show="showPath"
                  >
                    <div class="path-title">
                      {{ t('请求路径') }}：
                    </div>
                    <div class="source-path">
                      <div class="request-path-box">
                        <bk-tag theme="success" class="method-tag">{{ curResource?.method }}</bk-tag>
                        <span class="request-path">{{ curResource?.path }}</span>
                      </div>
                      <bk-button class="fixed-w" theme="primary" @click="handleSend" :loading="isLoading">
                        {{ t('发送') }}
                      </bk-button>
                      <bk-button class="ml8 fixed-w" @click="viewDoc">{{ t('查看文档') }}</bk-button>
                    </div>
                  </div>
                </div>
              </template>
              <template #content>
                <div class="request-setting-content">
                  <div class="request-setting-item top-flush">
                    <div class="request-setting-label">
                      {{ t('应用认证') }}：
                    </div>
                    <div class="request-setting-main">
                      <bk-pop-confirm
                        width="470"
                        trigger="click"
                        @confirm="saveAppAuthEdit"
                        @cancel="cancelAppAuthEdit"
                      >
                        <div>
                          <span>
                            ({{ isDefaultAppAuth ? t('默认测试应用') : t('自定义应用') }})
                            bk_app_code：{{ isDefaultAppAuth ? testAppCode : formData.authorization.bk_app_code }}；
                            bk_app_secret：{{ isDefaultAppAuth ? '******' : formData.authorization.bk_app_secret }}
                          </span>
                          <edit-line class="edit-auth" @click="handleEditAppAuth" />
                        </div>

                        <template #content>
                          <div class="edit-user-auth">
                            <div class="title">{{ t('应用认证') }}<span>*</span></div>
                            <bk-radio-group v-model="appAuthorization.appAuth" class="auth-type">
                              <bk-radio-button label="use_test_app">{{ t('默认测试应用') }}</bk-radio-button>
                              <bk-radio-button label="use_custom_app">{{ t('自定义应用') }}</bk-radio-button>
                            </bk-radio-group>
                            <template v-if="appAuthorization.appAuth === 'use_test_app'">
                              <bk-input
                                class="auth-value"
                                prefix="bk_app_code"
                                :value="testAppCode"
                                :disabled="true"
                              />
                              <bk-input
                                class="auth-value"
                                prefix="bk_app_secret"
                                :value="'******'"
                                :disabled="true"
                              />
                            </template>
                            <template v-else>
                              <bk-input
                                class="auth-value"
                                prefix="bk_app_code"
                                v-model="appAuthorization.bk_app_code"
                                :placeholder="t('请输入蓝鲸应用ID')"
                              />
                              <bk-input
                                class="auth-value"
                                prefix="bk_app_secret"
                                v-model="appAuthorization.bk_app_secret"
                                :placeholder="t('请输入蓝鲸应用密钥')"
                              />
                            </template>
                            <div class="edit-user-tips">
                              <info-line /> <span class="tips">{{ t('默认测试应用，网关自动为其短期授权；自定义应用，需主动为应用授权资源访问权限') }}</span>
                            </div>
                            <!-- <div class="edit-user-btns">
                          <bk-button theme="primary" @click="saveAppAuthEdit">{{ t('保存') }}</bk-button>
                          <bk-button class="ml8" @click="cancelAppAuthEdit">{{ t('取消') }}</bk-button>
                        </div> -->
                          </div>
                        </template>
                      </bk-pop-confirm>
                    </div>
                  </div>
                  <div class="request-setting-item top-flush" v-if="curResource?.verified_user_required">
                    <div class="request-setting-label">
                      {{ t('用户认证') }}：
                    </div>
                    <div class="request-setting-main">
                      <bk-pop-confirm
                        width="470"
                        trigger="click"
                        @confirm="saveUserAuthEdit"
                        @cancel="cancelUserAuthEdit"
                      >
                        <div>
                          <span>
                            ({{ formData.useUserFromCookies ? t('默认用户认证') : t('自定义用户认证') }})
                            bk_token：{{ formData.useUserFromCookies ? '******' : formData.authorization.bk_token}}
                          </span>
                          <edit-line class="edit-auth" @click="handleEditUserAuth" />
                        </div>

                        <template #content>
                          <div class="edit-user-auth">
                            <div class="title">{{ t('用户认证') }}<span>*</span></div>
                            <bk-radio-group class="auth-type" v-model="userCookies.useUserFromCookies">
                              <bk-radio-button :label="true">{{ t('默认用户认证') }}</bk-radio-button>
                              <bk-radio-button :label="false">{{ t('自定义用户认证') }}</bk-radio-button>
                            </bk-radio-group>
                            <template v-if="userCookies.useUserFromCookies">
                              <bk-input
                                class="auth-value"
                                prefix="bk_token"
                                :placeholder="t('请输入 Cookies 中，字段 bk_token 的值')"
                                :value="'******'"
                                :disabled="true"
                              />
                            </template>
                            <template v-else>
                              <bk-input
                                class="auth-value"
                                prefix="bk_token"
                                :placeholder="t('请输入 Cookies 中，字段 bk_token 的值')"
                                v-model="userCookies.bk_token"
                              />
                            </template>

                            <div class="edit-user-tips">
                              <info-line /> <span class="tips">{{ t('默认测试应用，网关自动为其短期授权；自定义应用，需主动为应用授权资源访问权限') }}</span>
                            </div>
                            <!-- <div class="edit-user-btns">
                          <bk-button theme="primary" @click="saveUserAuthEdit">{{ t('保存') }}</bk-button>
                          <bk-button class="ml8" @click="cancelUserAuthEdit">{{ t('取消') }}</bk-button>
                        </div> -->
                          </div>
                        </template>
                      </bk-pop-confirm>
                    </div>
                  </div>
                  <div class="request-setting-item request-source-path">
                    <div class="request-setting-label path-title">
                      {{ t('请求路径') }}：
                    </div>
                    <div class="request-setting-main source-path">
                      <div class="request-path-box">
                        <bk-tag theme="success" class="method-tag">{{ curResource?.method }}</bk-tag>
                        <span class="request-path">{{ curResource?.path }}</span>
                      </div>
                      <bk-button class="fixed-w" theme="primary" @click="handleSend" :loading="isLoading">
                        {{ t('发送') }}
                      </bk-button>
                      <bk-button class="ml8 fixed-w" @click="viewDoc">{{ t('查看文档') }}</bk-button>
                    </div>
                  </div>
                </div>
              </template>
            </bk-collapse-panel>
          </bk-collapse>
        </div>

        <bk-resize-layout
          class="request-resize"
          placement="top"
        >
          <template #aside>
            <div class="request-payload">
              <request-payload ref="requestPayloadRef" :schema="payloadType" :tab="tab" />
            </div>
          </template>
          <template #main>
            <div class="request-response">
              <response-content :res="response" />
            </div>
          </template>
        </bk-resize-layout>
      </div>
    </template>
  </bk-resize-layout>

  <!-- 查看文档侧栏 -->
  <bk-sideslider v-model:isShow="isShowDoc" :width="960" quick-close>
    <template #header>
      <div class="custom-side-header">
        <div class="title">{{ t('查看文档详情') }}</div>
        <span></span>
        <div class="subtitle">{{ curResource?.name }}</div>

        <div class="opt-btns">
          <share class="opt-share" />
          <close-line class="opt-close" @click="isShowDoc = false" />
        </div>
      </div>
    </template>
    <template #default>
      <div class="">
        <doc :stage-name="getStageName" :resource-name="curResource?.name" />
      </div>
    </template>
  </bk-sideslider>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import onlineTestTop from '@/components/online-test-top.vue';
import { RightShape, EditLine, InfoLine, AngleUpFill, Share, CloseLine } from 'bkui-vue/lib/icon';
import requestPayload from '@/views/online-debug/components/request-payload.vue';
import responseContent from '@/views/online-debug/components/response-content.vue';
import doc from '@/views/online-debug/components/doc.vue';
import TableEmpty from '@/components/table-empty.vue';
import { useCommon } from '@/store';
import { Message } from 'bkui-vue';
import {
  getStages,
  getResourcesOnline,
  getApiDetail,
  resourceSchema,
  postAPITest,
} from '@/http';


const { t } = useI18n();
const common = useCommon();

const isLoading = ref<boolean>(false);
const keyword = ref<string>('');
const activeIndex = ref<number[]>([1]);
const stage = ref<number>();
const stageList = ref<any[]>([]);
const resourceList = ref<any>([]);
const activeName = ref<any>([]);
const testAppCode = ref('apigw-api-test');
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
const originResourceGroup = ref<any>({});
const curComponentName = ref<any>('');
const curResource = ref<any>({});
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
      bk_token: '',
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
const formData = ref<any>({ ...defaultValue.formData });
const isShowDoc = ref<boolean>(false);
const requestPayloadRef = ref();
const showPath = ref<boolean>(false);
const payloadType = reactive<any>({
  rawPayload: {},
  queryPayload: [],
  pathPayload: [],
  priorityPath: [],
  headersPayload: [],
  fromDataPayload: [],
});
const tab = ref<string>('Params');

// 编辑应用认证
const appAuthorization = reactive<any>({
  isEdit: false,
  appAuth: 'use_test_app',
  bk_app_code: '',
  bk_app_secret: '',
});
// 编辑用户认证
const userCookies = reactive<any>({
  isEdit: false,
  useUserFromCookies: true,
  bk_token: '',
});
const response = ref<any>({});

const isDefaultAppAuth = computed(() => formData.value.appAuth === 'use_test_app');

const getStageName = computed(() => {
  if (!stage.value) return '';
  const target = stageList.value?.find((item: any) => item.id === stage.value);
  return target?.name;
});

const curGroup = computed(() => {
  for (const key of Object.keys(originResourceGroup.value)) {
    const cur = originResourceGroup.value[key];
    const match = cur?.resources?.find((item: any) => {
      return item.name === curComponentName.value;
    });
    if (match) {
      return cur;
    }
  }
  return null;
});

const getApigwReleaseResources = async () => {
  if (!stage.value) return;

  try {
    const query = {
      limit: 10000,
      offset: 0,
    };
    const res = await getResourcesOnline(common.apigwId, stage.value, query);
    const group: any = {};
    const defaultItem: any = {
      labelId: 'default',
      labelName: t('默认'),
      resources: [],
    };
    resourceList.value = res;
    // 根据标签将资源分类
    resourceList.value?.forEach((resource: any) => {
      const { labels } = resource;
      if (labels?.length) {
        labels.forEach((label: any) => {
          if (typeof label === 'object') {
            if (group[label.id]) {
              group[label.id]?.resources.push(resource);
            } else {
              if (group[label.name]) {
                group[label.name]?.resources.push(resource);
              } else {
                const obj = {
                  labelId: label.id,
                  labelName: label.name,
                  resources: [resource],
                };
                group[label.name] = obj;
              }
            }
          } else {
            if (group[label]) {
              group[label]?.resources?.push(resource);
            } else {
              const obj = {
                labelId: label,
                labelName: label,
                resources: [resource],
              };
              group[label] = obj;
            }
          }
        });
      } else {
        defaultItem.resources.push(resource);
      }
    });
    if (defaultItem.resources.length) {
      group[t('默认')] = defaultItem;
    }
    originResourceGroup.value = group;
  } catch (e) {
    console.log(e);
  }
};

const resourceGroup = computed(() => {
  const group: any = {};
  let keys = Object.keys(originResourceGroup.value).sort();

  if (keys.includes(t('默认'))) {
    const list = keys.filter(item => item !== t('默认'));
    keys = [t('默认'), ...list];
  }
  for (const key of keys) {
    let resources: any = [];
    const obj: any = {};
    const item = originResourceGroup.value[key];
    if (!keyword.value) {
      resources = item?.resources || [];
    } else {
      item?.resources?.forEach((resource: any) => {
        if ((resource.name || '').indexOf(keyword.value) > -1
        ||       (resource.description || '').indexOf(keyword.value) > -1) {
          resources.push(resource);
        }
      });
    }

    if (resources.length) {
      obj.labelId = item.labelId;
      obj.labelName = item.labelName;
      obj.resources = resources;
      group[key] = obj;
    }
  }

  // 默认选中第一个标签的第一个资源
  if (!curComponentName.value) {
    activeName.value = [Object.keys(group)[0]];
    curResource.value = group[Object.keys(group)[0]]?.resources[0];
    curComponentName.value = curResource.value?.name;
    getResourceParams();
  }

  return group;
});

const handleStageChange = (payload: number) => {
  const hasData = stageList.value.find((item: Record<string, number>) => item.id === payload);
  // 如果是未发布或者发布失败则不需要调资源列表
  if (!['unreleased', 'failure'].includes(hasData?.release?.status)) {
    getApigwReleaseResources();
  } else {
    // formData.value = Object.assign(formData.value, { path: '', method: '' });
    // methodList.value = [];
    // resources.value = {};
  }
};

const clearSchema = () => {
  payloadType.rawPayload = {};
  payloadType.queryPayload = [];
  payloadType.pathPayload = [];
  payloadType.priorityPath = [];
  payloadType.headersPayload = [];
  payloadType.fromDataPayload = [];
};

const getResourceParams = async () => {
  if (!common.apigwId || !stage.value || !curResource.value?.id) return;
  const res = await resourceSchema(common.apigwId, stage.value, curResource.value?.id);

  clearSchema();
  if (res?.body_example) {
    payloadType.rawPayload = res?.body_example;
  }

  res?.parameter_schema?.forEach((item: any) => {
    if (item.in === 'query') {
      payloadType.queryPayload?.push(item);
    } else if (item.in === 'path') {
      payloadType.pathPayload?.push(item);
    } else if (item.in === 'header') {
      payloadType.headersPayload?.push(item);
    } else if (item.in === 'fromData') {
      payloadType.fromDataPayload?.push(item);
    }
  });
  matchPath(curResource.value);
};

// path 参数
const matchPath = (resource: any) => {
  if (!resource) return;

  const { path } = resource;
  const pathArr: any[] = [];

  if (path?.indexOf('{') !== -1) {
    path.split('/').forEach((str: string) => {
      if (str.indexOf('{') !== -1) {
        const tempStr = str.split('{')[1];
        pathArr.push({
          name: tempStr.split('}')[0],
          description: '',
          in: 'path',
          required: true,
          schema: {
            type: 'string',
          },
        });
      }
    });
  }

  payloadType.priorityPath = pathArr;
};

// 点击资源列表项
const handleShowDoc = (resource: any) => {
  curResource.value = resource;
  curComponentName.value = resource.name;
  getResourceParams();
  response.value = {};
};

const hightlight = (value: string) => {
  if (keyword.value) {
    return value.replace(new RegExp(`(${keyword.value})`), '<em class="ag-keyword">$1</em>');
  }
  return value;
};

const getApigwStages = async () => {
  const pageParams = {
    no_page: true,
    order_by: 'name',
  };

  try {
    const res = await getStages(common.apigwId, pageParams);
    stageList.value = res || [];
    if (stageList.value.length) {
      const { id, release } = stageList.value[0];
      // params.value.stage_id = id;
      stage.value = id;
      // 如果是未发布或者发布失败则不需要调资源列表
      if (!['unreleased', 'failure'].includes(release?.status)) {
        getApigwReleaseResources();
      }
    }
  } catch (e) {
    console.log(e);
  }
};

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
  // formData.value.authorization[tokenName.value] = '';
  // tokenInputRender.value += 1;
};

const handleEditAppAuth = () => {
  appAuthorization.bk_app_code = formData.value.authorization.bk_app_code;
  appAuthorization.bk_app_secret = formData.value.authorization.bk_app_secret;
  appAuthorization.appAuth = formData.value.appAuth;
  appAuthorization.isEdit = true;
};

const saveAppAuthEdit = () => {
  if (appAuthorization.appAuth === 'use_test_app') {
    formData.value.authorization.bk_app_code = '';
    formData.value.authorization.bk_app_secret = '';
  } else {
    formData.value.authorization.bk_app_code = appAuthorization.bk_app_code;
    formData.value.authorization.bk_app_secret = appAuthorization.bk_app_secret;
  }

  formData.value.appAuth = appAuthorization.appAuth;
  appAuthorization.isEdit = false;
};

const cancelAppAuthEdit = () => {
  appAuthorization.isEdit = false;
};

const handleEditUserAuth = () => {
  userCookies.useUserFromCookies = formData.value.useUserFromCookies;
  userCookies.bk_token = formData.value.authorization.bk_token;
  userCookies.isEdit = true;
};

const saveUserAuthEdit = () => {
  if (userCookies.useUserFromCookies) {
    formData.value.authorization.bk_token = '';
  } else {
    formData.value.authorization.bk_token = userCookies.bk_token;
  }

  formData.value.useUserFromCookies = userCookies.useUserFromCookies;
  userCookies.isEdit = false;
};

const cancelUserAuthEdit = () => {
  userCookies.isEdit = false;
};

const getKeyValue = (list: any[]) => {
  if (!list?.length) return {};

  const obj: any = {};
  list.forEach((item: any) => {
    if (item.name) {
      obj[item.name] = item.value;
    }
  });

  return obj;
};

const checkFormData = (data: any) => {
  const pathValues = Object.values(data.path_params);
  const pathKeys = Object.keys(data.path_params);
  // const reg = /^[\w{}/.-]*$/;
  const codeReg = /^[a-z][a-z0-9-_]+$/;
  // if ((isShowSubpath.value) && !reg.test(data.subpath)) {
  //   Message({
  //     theme: 'error',
  //     message: t('请输入合法的子路径'),
  //   });
  //   form.value.validate();
  //   return false;
  // }
  if (pathKeys?.length && pathValues.some((val: any) => !val?.length)) {
    Message({
      theme: 'error',
      message: t('请输入完整的路径参数'),
    });
    // form.value.validate();
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

const formatPayload = () => {
  const payload = requestPayloadRef.value?.getData();
  const { headers } = payload;
  const { path, query } = payload.params;
  const { raw } = payload.body;
  // formData: formDataList, urlencoded,

  const data: any = {};
  data.stage_id = stage.value;
  data.resource_id = curResource.value?.id;
  data.method = curResource.value?.method;
  data.query_params = getKeyValue(query);
  data.path_params = getKeyValue(path);
  data.headers = getKeyValue(headers);
  data.body = raw;

  // 用户认证
  data.use_user_from_cookies = curResource.value?.verified_user_required ? formData.value?.useUserFromCookies : false;
  data.authorization = formData.value?.authorization || {};
  data.use_test_app = isDefaultAppAuth.value;

  // 默认应用认证数据过滤
  if (isDefaultAppAuth.value) {
    data.authorization.bk_app_secret = '';
    data.authorization.bk_app_code = '';
  }

  // 默认用户认证数据过滤
  if (formData.value?.useUserFromCookies) {
    data.authorization.bk_token = '';
  }

  if (checkFormData(data)) {
    return data;
  }
  return false;
};

const handleSend = async (e: Event) => {
  e?.stopPropagation();
  const isValidate = await requestPayloadRef.value?.validate();
  if (!isValidate) return;
  const data = formatPayload();
  if (!data) return;

  try {
    isLoading.value = true;
    const res = await postAPITest(common.apigwId, data);
    response.value = res;
  } catch (e) {
    console.log(e);
  } finally {
    isLoading.value = false;
  }
};

const viewDoc = (e: Event) => {
  e?.stopPropagation();
  isShowDoc.value = true;
};

const init = async () => {
  await getApigwDetail();
  getApigwStages();
  setUserToken();
};

init();

watch(
  () => activeIndex.value,
  (index) => {
    setTimeout(() => {
      if (index?.includes(1)) {
        showPath.value = false;
      } else {
        showPath.value = true;
      }
    }, 180);
  },
);

// watch(
//   () => curGroup.value,
//   () => {
//     if (curGroup.value) {
//       activeName.value = [curGroup.value?.labelName];
//     }
//   },
// );

watch(
  () => keyword.value,
  (val) => {
    const keys = Object.keys(resourceGroup.value);
    if (val) {
      activeName.value = keys;
    } else if (curGroup.value) {
      activeName.value = [curGroup.value?.labelName];
    } else {
      activeName.value = [keys[0]];
    }
  },
);

watch(
  () => curResource.value,
  (resource) => {
    if (['POST', 'PUT'].includes(resource?.method)) {
      tab.value = 'Body';
    } else {
      tab.value = 'Params';
    }
  },
);
</script>

<style lang="scss" scoped>
.bk-resize-layout-border {
  border: none;
}
.content-resize {
  height: 100%;
  :deep(.bk-resize-trigger:hover) {
    border-right: 2px solid #3a84ff;
  }
  .resize-aside {
    background: #FFFFFF;
    height: 100%;
    box-sizing: border-box;
    padding: 24px 0px;
    .source-title {
      font-weight: 700;
      font-size: 14px;
      color: #313238;
      margin-bottom: 10px;
      padding: 0 24px;
    }
    .stage-select {
      margin: 0px 24px 12px;
    }
    .search-source {
      margin: 0px 24px 18px;
    }
  }
  .request-setting {
    background: #FFFFFF;
    box-shadow: 0 2px 4px 0 #1919290d;
    .request-setting-title {
      padding: 24px 24px 4px;
      .request-source-name {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
        cursor: pointer;
        .request-source-icon {
          transition: all .2s;
          &.switch {
            transform: rotate(90deg);
          }
        }
        .source-title {
          font-weight: 700;
          font-size: 16px;
          color: #313238;
          margin: 0 8px;
        }
        .source-subtitle {
          font-size: 12px;
          color: #979BA5;
        }
      }
    }
  }
  .request-setting-content {
    .request-setting-item {
      display: flex;
      align-items: center;
      margin-bottom: 4px;
      &.top-flush {
        align-items: self-start;
      }
      .request-setting-label {
        font-size: 12px;
        color: #63656E;
        text-align: right;
        margin-right: 4px;
      }
      .request-setting-main {
        font-size: 12px;
      }
    }
  }
  .request-setting-collapse {
    :deep(.bk-collapse-content) {
      padding: 0px 45px 20px 45px;
    }
  }
}
.ml8 {
  margin-left: 8px;
}
.edit-auth {
  margin-left: 6px;
  color: #3A84FF;
  font-size: 14px;
  cursor: pointer;
}
.request-source-path {
  display: flex;
  align-items: center;
  .path-title {
    color: #63656E;
    font-size: 12px;
    margin-right: 4px;
  }
  .source-path {
    display: flex;
    align-items: center;
    .request-path-box {
      padding: 6px;
      padding-right: 15px;
      background: #F5F7FA;
      border-radius: 2px;
      margin-right: 8px;
    }
    .request-path {
      color: #313238;
      font-size: 12px;
    }
  }
}
.edit-user-auth {
  .title {
    font-size: 12px;
    color: #63656E;
    margin-bottom: 8px;
    span {
      color: #EA3636;
      margin-left: 6px;
      vertical-align: middle;
    }
  }
  .auth-type {
    margin-bottom: 16px;
  }
  .auth-value {
    margin-bottom: 16px;
  }
  .edit-user-tips {
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    font-size: 14px;
    .tips {
      margin-left: 6px;
      font-size: 12px;
      color: #63656E;
    }
  }
}
.seldom-path {
  padding: 2px 20px 20px;
}
.request-payload {
  background: #FFFFFF;
  margin: 16px 24px 8px;
  box-shadow: 0 2px 4px 0 #1919290d;
  border-radius: 2px;
  padding-left: 24px;
  padding-bottom: 14px;
}
.request-response {
  background: #FFFFFF;
}
.my-menu {
  max-height: 100%;
  overflow: auto;
  :deep(.icon-angle-right) {
    display: none;
  }
  &::-webkit-scrollbar {
    width: 4px;
    background-color: lighten(#C4C6CC, 80%);
  }
  &::-webkit-scrollbar-thumb {
    height: 5px;
    border-radius: 2px;
    background-color: #C4C6CC;
  }
  .custom-icon {
    margin: -3px 6px 0 0;
    font-size: 13px;
    vertical-align: middle;
    display: inline-block;
  }
  .my-menu-header {
    padding: 6px 24px;
    display: flex;
    align-items: center;
    cursor: pointer;
    .my-menu-title {
      font-size: 12px;
      color: #63656E;
      margin-left: 8px;
    }
    .menu-header-icon {
      transition: all .2s;
      color: #979BA5;
      font-size: 14px;
      &.fold {
        transform: rotate(-90deg);
      }
    }
  }
  :deep(.bk-collapse-content) {
    padding: 8px 0;
  }
  .component-list {
    list-style: none;
    margin: 0;
    padding: 0;
    >li {
      font-size: 12px;
      position: relative;
      padding: 6px 36px 6px 56px;
      cursor: pointer;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      &:hover,
      &.active {
        background: #F0F5FF;

        .name,
        .label {
          color: #3A84FF;
        }
      }
    }
    .name {
      color: #63656E;
      font-weight: 700;
    }
    .label {
      color: #979BA5;
    }
    .name,
    .label {
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
    }
  }
}
.custom-side-header {
  width: 100%;
  position: relative;
  .opt-btns {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    right: 24px;
    display: flex;
    align-items: center;
    .opt-share,
    .opt-close {
      font-size: 14px;
      cursor: pointer;
      margin: 0;
      background: transparent;
      width: 50%;
      height: 14px;
      color: #979BA5;
      &:hover {
        color: #3A84FF;
      }
    }
    .opt-share {
      margin-right: 26px;
    }
    .opt-close {
      font-size: 16px;
    }
  }
}
.request-resize {
  :deep(.bk-resize-trigger:hover) {
    border-top: 2px solid #3a84ff;
  }
  :deep(.bk-resize-layout-aside:after) {
    bottom: -5px;
  }
}
.fixed-w {
  width: 88px;
}
.method-tag {
  height: 16px;
  line-height: 16px;
}
.fixed-w {
  width: 88px;
}
</style>
