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
  <Top />
  <BkResizeLayout
    class="content-resize"
    collapsible
    initial-divide="342px"
  >
    <template #aside>
      <div class="resize-aside">
        <div class="source-title">
          {{ t('资源列表') }}
        </div>
        <BkSelect
          v-model="stage"
          class="stage-select"
          filterable
          :clearable="false"
          :prefix="t('环境')"
          @change="handleStageChange"
        >
          <BkOption
            v-for="item in stageList"
            :id="item.id"
            :key="item.id"
            :name="getItemName(item)"
            :disabled="['unreleased', 'failure'].includes(item?.release?.status)"
          />
        </BkSelect>
        <div class="search-source">
          <BkInput
            v-model="keyword"
            clearable
            type="search"
          />
        </div>
        <BkCollapse
          v-if="resourceGroupLength"
          v-model="activeName"
          class="my-menu"
        >
          <template v-for="group of resourceGroup">
            <BkCollapsePanel
              v-if="group?.resources?.length"
              :key="group.labelId"
              :name="group.labelName"
            >
              <template #header>
                <div class="my-menu-header">
                  <AngleUpFill
                    class="menu-header-icon"
                    :class="[!activeName?.includes(group.labelName) ? 'fold' : '']"
                  />
                  <div class="my-menu-title">
                    {{ group.labelName }}
                  </div>
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
                      @click="() => handleShowDoc(component)"
                    >
                      <!-- eslint-disable-next-line vue/no-v-html -->
                      <p
                        v-dompurify-html="hightlight(component.name)"
                        v-bk-overflow-tips
                        class="name"
                      />
                      <!-- eslint-disable-next-line vue/no-v-html -->
                      <p
                        v-dompurify-html="hightlight(component.description) || t('暂无描述')"
                        v-bk-overflow-tips
                        class="label"
                      />
                    </li>
                  </ul>
                </div>
              </template>
            </BkCollapsePanel>
          </template>
        </BkCollapse>
        <template v-else-if="keyword">
          <TableEmpty
            :keyword="keyword"
            @clear-filter="keyword = ''"
          />
        </template>
      </div>
    </template>
    <template #main>
      <div
        v-show="resourceGroupLength"
        class="resize-main"
      >
        <div class="request-setting">
          <BkCollapse
            v-model="activeIndex"
            class="request-setting-collapse"
          >
            <BkCollapsePanel :name="1">
              <template #header>
                <div class="request-setting-title">
                  <div class="request-source-name">
                    <RightShape
                      class="request-source-icon"
                      :class="[activeIndex?.includes(1) ? 'switch' : '']"
                    />
                    <span class="source-title">{{ curResource?.name }}</span>
                    <span class="source-subtitle">（ {{ curResource?.description }} ）</span>
                  </div>
                  <div
                    v-show="showPath"
                    class="request-source-path seldom-path"
                  >
                    <div class="path-title">
                      {{ t('请求路径') }}：
                    </div>
                    <div class="source-path">
                      <div class="request-path-box">
                        <BkTag
                          theme="success"
                          class="method-tag"
                        >
                          {{ curResource?.method }}
                        </BkTag>
                        <span class="request-path">{{ curResource?.path }}</span>
                      </div>
                      <BkButton
                        class="fixed-w"
                        theme="primary"
                        :loading="isLoading"
                        :disabled="isLoading"
                        @click="handleSend"
                      >
                        {{ t('发送') }}
                      </BkButton>
                      <BkButton
                        class="ml8 fixed-w"
                        @click="viewDoc"
                      >
                        {{ t('查看文档') }}
                      </BkButton>
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
                      <span>
                        ({{ isDefaultAppAuth ? t('默认测试应用') : t('自定义应用') }})
                        bk_app_code：{{ isDefaultAppAuth ? testAppCode : formData.authorization.bk_app_code }}；
                        bk_app_secret：{{ isDefaultAppAuth ? '******' : formData.authorization.bk_app_secret }}
                      </span>
                      <BkPopConfirm
                        width="470"
                        trigger="click"
                        @confirm="saveAppAuthEdit"
                        @cancel="cancelAppAuthEdit"
                      >
                        <EditLine
                          class="edit-auth"
                          @click="handleEditAppAuth"
                        />

                        <template #content>
                          <div class="edit-user-auth">
                            <div class="title">
                              {{ t('应用认证') }}<span>*</span>
                            </div>
                            <BkRadioGroup
                              v-model="appAuthorization.appAuth"
                              class="auth-type"
                            >
                              <BkRadioButton label="use_test_app">
                                {{ t('默认测试应用') }}
                              </BkRadioButton>
                              <BkRadioButton label="use_custom_app">
                                {{ t('自定义应用') }}
                              </BkRadioButton>
                            </BkRadioGroup>
                            <template v-if="appAuthorization.appAuth === 'use_test_app'">
                              <BkInput
                                class="auth-value"
                                prefix="bk_app_code"
                                :value="testAppCode"
                                disabled
                              />
                              <BkInput
                                class="auth-value"
                                prefix="bk_app_secret"
                                :value="'******'"
                                disabled
                              />
                            </template>
                            <template v-else>
                              <BkInput
                                v-model="appAuthorization.bk_app_code"
                                class="auth-value"
                                prefix="bk_app_code"
                                :placeholder="t('请输入蓝鲸应用ID')"
                              />
                              <BkInput
                                v-model="appAuthorization.bk_app_secret"
                                class="auth-value"
                                prefix="bk_app_secret"
                                :placeholder="t('请输入蓝鲸应用密钥')"
                              />
                            </template>
                            <div class="edit-user-tips">
                              <InfoLine class="icon" />
                              <span class="tips">{{ t('默认测试应用，网关自动为其短期授权；自定义应用，需主动为应用授权资源访问权限') }}</span>
                            </div>
                            <!-- <div class="edit-user-btns">
                              <BkButton theme="primary" @click="saveAppAuthEdit">{{ t('保存') }}</BkButton>
                              <BkButton class="ml8" @click="cancelAppAuthEdit">{{ t('取消') }}</BkButton>
                              </div> -->
                          </div>
                        </template>
                      </BkPopConfirm>
                    </div>
                  </div>
                  <div
                    v-if="curResource?.verified_user_required"
                    class="request-setting-item top-flush"
                  >
                    <div class="request-setting-label">
                      {{ t('用户认证') }}：
                    </div>
                    <div class="request-setting-main">
                      <span>
                        ({{ formData.useUserFromCookies ? t('默认用户认证') : t('自定义用户认证') }})
                        bk_token：{{ formData.useUserFromCookies ? '******' : formData.authorization.bk_token }}
                      </span>
                      <BkPopConfirm
                        width="470"
                        trigger="click"
                        @confirm="saveUserAuthEdit"
                        @cancel="cancelUserAuthEdit"
                      >
                        <EditLine
                          class="edit-auth"
                          @click="handleEditUserAuth"
                        />

                        <template #content>
                          <div class="edit-user-auth">
                            <div class="title">
                              {{ t('用户认证') }}<span>*</span>
                            </div>
                            <BkRadioGroup
                              v-model="userCookies.useUserFromCookies"
                              class="auth-type"
                            >
                              <BkRadioButton label>
                                {{ t('默认用户认证') }}
                              </BkRadioButton>
                              <BkRadioButton :label="false">
                                {{ t('自定义用户认证') }}
                              </BkRadioButton>
                            </BkRadioGroup>
                            <template v-if="userCookies.useUserFromCookies">
                              <BkInput
                                class="auth-value"
                                prefix="bk_token"
                                :placeholder="t('请输入 Cookies 中，字段 bk_token 的值')"
                                :value="'******'"
                                disabled
                              />
                            </template>
                            <template v-else>
                              <BkInput
                                v-model="userCookies.bk_token"
                                class="auth-value"
                                prefix="bk_token"
                                :placeholder="t('请输入 Cookies 中，字段 bk_token 的值')"
                              />
                            </template>

                            <div class="edit-user-tips">
                              <InfoLine class="icon" />
                              <span class="tips">{{ t('默认用户认证，将默认从 Cookies 中获取用户认证信息；自定义用户认证，可自定义用户认证信息') }}</span>
                            </div>
                            <!-- <div class="edit-user-btns">
                              <BkButton theme="primary" @click="saveUserAuthEdit">{{ t('保存') }}</BkButton>
                              <BkButton class="ml8" @click="cancelUserAuthEdit">{{ t('取消') }}</BkButton>
                              </div> -->
                          </div>
                        </template>
                      </BkPopConfirm>
                    </div>
                  </div>
                  <div class="request-setting-item request-source-path">
                    <div class="request-setting-label path-title">
                      {{ t('请求路径') }}：
                    </div>
                    <div class="request-setting-main source-path">
                      <div class="request-path-box">
                        <BkTag
                          theme="success"
                          class="method-tag"
                        >
                          {{ curResource?.method }}
                        </BkTag>
                        <span class="request-path">{{ curResource?.path }}</span>
                      </div>
                      <BkButton
                        class="fixed-w"
                        theme="primary"
                        :loading="isLoading"
                        :disabled="isLoading"
                        @click="handleSend"
                      >
                        {{ t('发送') }}
                      </BkButton>
                      <BkButton
                        class="ml8 fixed-w"
                        @click="viewDoc"
                      >
                        {{ t('查看文档') }}
                      </BkButton>
                    </div>
                  </div>
                </div>
              </template>
            </BkCollapsePanel>
          </BkCollapse>
        </div>

        <BkResizeLayout
          style="height: 100%; overflow: hidden;"
          initial-divide="52px"
          :border="false"
          :min="52"
          placement="bottom"
          class="request-resize"
        >
          <template #aside>
            <div class="request-response">
              <ResponseContent
                ref="responseContentRef"
                :res="response"
                @response-fold="handleResponseFold"
                @response-unfold="handleResponseUnfold"
              />
            </div>
          </template>
          <template #main>
            <div class="request-payload">
              <RequestPayload
                ref="requestPayloadRef"
                :schema="payloadType"
                :tab="tab"
              />
            </div>
          </template>
        </BkResizeLayout>
      </div>

      <div
        v-show="!resourceGroupLength"
        class="exception-part"
      >
        <BkException
          class="exception-wrap-item"
          :description="t('暂无数据')"
          scene="part"
          type="empty"
        />
      </div>
    </template>
  </BkResizeLayout>

  <!-- 查看文档侧栏 -->
  <AgSideslider
    v-model="isShowDoc"
  >
    <template #header>
      <div class="custom-side-header">
        <div class="title">
          {{ t('查看文档详情') }}
        </div>
        <span />
        <div class="subtitle">
          {{ curResource?.name }}
        </div>

        <div class="opt-btns">
          <Share
            v-show="curResource?.is_public"
            class="opt-share"
            @click="() => openTab(curResource?.name)"
          />
          <CloseLine
            class="opt-close"
            @click="isShowDoc = false"
          />
        </div>
      </div>
    </template>
    <template #default>
      <div>
        <Doc
          :stage-name="getStageName"
          :resource-name="curResource?.name"
        />
      </div>
    </template>
  </AgSideslider>
</template>

<script lang="ts" setup>
import {
  AngleUpFill,
  CloseLine,
  EditLine,
  InfoLine,
  RightShape,
  Share,
} from 'bkui-vue/lib/icon';
import { Message } from 'bkui-vue';
import Top from '@/views/online-debugging/components/Top.vue';
import RequestPayload from '@/views/online-debugging/components/RequestPayload.vue';
import ResponseContent from '@/views/online-debugging/components/ResponseContent.vue';
import Doc from '@/views/online-debugging/components/Doc.vue';
import TableEmpty from '@/components/table-empty/Index.vue';
import AgSideslider from '@/components/ag-sideslider/Index.vue';
import { useEnv, useGateway } from '@/stores';
import {
  getApiDetail,
  getResourcesOnline,
  getStages,
  postAPITest,
  resourceSchema,
} from '@/services/source/online-debugging';

const { t } = useI18n();
const gatewayStore = useGateway();
const router = useRouter();
const route = useRoute();
const envStore = useEnv();

const isLoading = ref<boolean>(false);
const keyword = ref<string>('');
const activeIndex = ref<number[]>([1]);
const stage = ref<number>();
const stageList = ref<any[]>([]);
const resourceList = ref<any>([]);
const activeName = ref<any>([]);
const testAppCode = ref(envStore.env.BK_DEFAULT_TEST_APP_CODE);
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
const responseContentRef = ref();
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

const apigwId = computed(() => gatewayStore.apigwId);

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
    }
    else {
      item?.resources?.forEach((resource: any) => {
        if ((resource.name || '').indexOf(keyword.value) > -1
          || (resource.description || '').indexOf(keyword.value) > -1) {
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

const resourceGroupLength = computed(() => {
  return Object.keys(resourceGroup.value)?.length;
});

watch(
  () => activeIndex.value,
  (index) => {
    setTimeout(() => {
      showPath.value = !index?.includes(1);
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
    }
    else if (curGroup.value) {
      activeName.value = [curGroup.value?.labelName];
    }
    else {
      activeName.value = [keys[0]];
    }
  },
);

watch(
  () => curResource.value,
  (resource) => {
    if (['POST', 'PUT'].includes(resource?.method)) {
      tab.value = 'Body';
    }
    else {
      tab.value = 'Params';
    }
  },
);

watch(() => route, () => {
  stage.value = 0;
  const stageId = route.query?.stage_id;
  stage.value = Number(stageId) || 0;
  if (stage.value) {
    handleStageChange(stage.value);
  }
}, { immediate: true });

watch(() => gatewayStore.currentGateway, () => {
  router.replace({ query: null });
}, { deep: true });

const getApigwReleaseResources = async () => {
  if (!stage.value) return;

  try {
    const query = {
      limit: 10000,
      offset: 0,
    };
    const res = await getResourcesOnline(apigwId.value, stage.value, query);
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
            }
            else {
              if (group[label.name]) {
                group[label.name]?.resources.push(resource);
              }
              else {
                const obj = {
                  labelId: label.id,
                  labelName: label.name,
                  resources: [resource],
                };
                group[label.name] = obj;
              }
            }
          }
          else {
            if (group[label]) {
              group[label]?.resources?.push(resource);
            }
            else {
              const obj = {
                labelId: label,
                labelName: label,
                resources: [resource],
              };
              group[label] = obj;
            }
          }
        });
      }
      else {
        defaultItem.resources.push(resource);
      }
    });
    if (defaultItem.resources.length) {
      group[t('默认')] = defaultItem;
    }
    originResourceGroup.value = group;
  }
  catch (e) {
    console.log(e);
  }
};

const getItemName = (item: any) => {
  if (!['unreleased', 'failure'].includes(item?.release?.status)) {
    return item.name;
  }
  if (item?.release?.status === 'unreleased') {
    return `${item.name} （未发布）`;
  }
  if (item?.release?.status === 'failure') {
    return `${item.name} （发布失败）`;
  }
};

const handleStageChange = (payload: number) => {
  const hasData = stageList.value.find((item: Record<string, number>) => item.id === payload);
  // 如果是未发布或者发布失败则不需要调资源列表
  if (!['unreleased', 'failure'].includes(hasData?.release?.status)) {
    router.replace({ query: { stage_id: payload } });
    getApigwReleaseResources();
  }
  else {
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
  if (!apigwId.value || !stage.value || !curResource.value?.id) return;
  const res = await resourceSchema(apigwId.value, stage.value, curResource.value?.id);

  clearSchema();
  if (res?.body_example) {
    payloadType.rawPayload = res?.body_example;
  }

  res?.parameter_schema?.forEach((item: any) => {
    if (item.in === 'query') {
      payloadType.queryPayload?.push(item);
    }
    else if (item.in === 'path') {
      payloadType.pathPayload?.push(item);
    }
    else if (item.in === 'header') {
      payloadType.headersPayload?.push(item);
    }
    else if (item.in === 'fromData') {
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
          schema: { type: 'string' },
        });
      }
    });
  }

  payloadType.priorityPath = pathArr;
};

// 点击资源列表项
const handleShowDoc = (resource: any) => {
  if (resource.id === curResource.value?.id) {
    return;
  }

  curResource.value = resource;
  curComponentName.value = resource.name;
  getResourceParams();
  responseContentRef.value?.setInit();
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
    const res = await getStages(apigwId.value, pageParams);
    stageList.value = res || [];
    if (stageList.value.length) {
      const effectiveStage = stageList.value.find((item: any) => item.release?.status === 'success') || stageList.value[0];
      const { id, release } = effectiveStage;

      if (!stage.value) {
        stage.value = id;
      }
      // 如果是未发布或者发布失败则不需要调资源列表
      if (!['unreleased', 'failure'].includes(release?.status)) {
        getApigwReleaseResources();
      }
    }
  }
  catch (e) {
    console.log(e);
  }
};

const getApigwDetail = async () => {
  try {
    const res = await getApiDetail(apigwId.value);
    curApigw.value = res;
    curApigw.value.statusBoolean = Boolean(curApigw.value?.status);
  }
  catch (e) {
    console.log(e);
  }
};

const setAsideHeight = (height: number) => {
  const aside: any = document.querySelector('.request-resize .bk-resize-layout-aside');

  if (aside) {
    aside.style.height = `${height}px`;
  }
};

const handleResponseFold = () => {
  setAsideHeight(52);
};

const handleResponseUnfold = () => {
  setAsideHeight(400);
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
  }
  else {
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
  }
  else {
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
    const res = await postAPITest(apigwId.value, data);
    response.value = res;

    setAsideHeight(400);
  }
  catch (e) {
    console.log(e);
  }
  finally {
    isLoading.value = false;
  }
};

const viewDoc = (e: Event) => {
  e?.stopPropagation();
  isShowDoc.value = true;
};

const openTab = (name?: string) => {
  if (!name) {
    return;
  }
  const routeData = router.resolve({
    name: 'ApiDocDetail',
    params: {
      curTab: 'gateway',
      targetName: gatewayStore.currentGateway?.name,
      componentName: name,
    },
  });
  window.open(routeData.href, '_blank');
};

const init = async () => {
  await getApigwDetail();
  getApigwStages();
  setUserToken();
};

init();

</script>

<style lang="scss" scoped>
@use "sass:color";

.bk-resize-layout-border {
  border: none;
}
.content-resize {
  height: 100%;
  :deep(.bk-resize-trigger:hover) {
    border-right: 2px solid #3a84ff;
  }
  &.bk-resize-layout-collapsed {
    :deep(.bk-resize-layout-aside) {
      border-right: none;
    }
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
          margin-top: 2px;
        }
      }
    }
  }
  .request-setting-content {
    .request-setting-item {
      display: flex;
      align-items: center;
      margin-bottom: 4px;
      line-height: 28px;
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
      padding: 2px 15px 2px 6px;
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
    align-items: flex-start;
    font-size: 14px;
    .icon {
      margin-top: 2px;
    }
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
  max-height: calc(100% - 16px);
  height: calc(100% - 24px);
  box-sizing: border-box;
  overflow-y: auto;
}
.request-response {
  background: #FFFFFF;
  height: 100%;
}
.my-menu {
  max-height: 100%;
  overflow: auto;
  :deep(.icon-angle-right) {
    display: none;
  }
  &::-webkit-scrollbar {
    width: 4px;
    background-color: color.scale(#C4C6CC, $lightness: 80%);
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
    padding: 7px 24px;
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
    padding: 2px 0;
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
      line-height: 20px;
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
      width: 14px;
      color: #979BA5;
      &:hover {
        color: #3A84FF;
      }
    }
    .opt-share {
      margin-right: 26px;
    }
    .opt-close {
      width: 16px;
    }
  }
}
.request-resize {
  flex: 1;
  :deep(.bk-resize-trigger:hover) {
    border-top: 2px solid #3a84ff;
  }
}
.fixed-w {
  width: 88px;
}
.method-tag {
  height: 16px;
  line-height: 16px;
}
.resize-main {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.exception-part {
  background-color: #fff;
  height: 100%;
  margin: 24px;
  box-sizing: border-box;
  .exception-wrap-item {
    height: 100%;
    justify-content: center;
  }
}
</style>
