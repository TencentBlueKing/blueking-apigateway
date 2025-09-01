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
  <AgSideslider
    v-model="isShow"
    :title="isEdit ? t('编辑网关') : t('新建网关')"
    :width="1020"
    class="gateway-operate-slider"
    :init-data="defaultFormData"
    @compare="handleCompare"
    @closed="handleCancel"
  >
    <template #default>
      <div class="create-gateway">
        <div class="create-form">
          <BkForm
            ref="formRef"
            form-type="vertical"
            class="create-gw-form"
            :model="formData"
            :rules="rules"
          >
            <BkFormItem
              :label="t('网关类型')"
              property="kind"
              required
            >
              <BkRadioGroup
                v-model="formData.kind"
                type="card"
                :disabled="isEdit"
                @change="handleKindChange"
              >
                <BkRadioButton :label="0">
                  {{ t('普通网关') }}
                </BkRadioButton>
                <BkRadioButton :label="1">
                  {{ t('可编程网关') }}
                </BkRadioButton>
              </BkRadioGroup>
            </BkFormItem>
            <BkAlert
              v-show="formData.kind === 1"
              theme="info"
              class="mt--10px mb-16px"
            >
              {{ t('通过编码的方式配置和管理网关的功能，支持接口组合、协议转换和接口编排等功能') }}
            </BkAlert>
            <BkFormItem
              :label="t('名称')"
              class="form-item-name"
              property="name"
              required
            >
              <BkInput
                v-model.trim="formData.name"
                :disabled="isEdit"
                :maxlength="formData.kind === 1 ? 16 : 30"
                :placeholder="nameInputPlaceholder"
                autofocus
                clearable
                show-word-limit
              />
            </BkFormItem>
            <span class="common-form-tips form-item-name-tips">
              {{ t('网关的唯一标识，创建后不可更改') }}
            </span>
            <BkFormItem
              v-if="formData.kind === 1"
              :label="t('开发语言')"
              property="extra_info.language"
              required
            >
              <BkSelect
                v-model="formData.extra_info!.language"
                :disabled="isEdit"
                class="bk-select"
              >
                <BkOption
                  v-for="item in languageList"
                  :id="item.value"
                  :key="item.value"
                  :name="item.label"
                />
              </BkSelect>
            </BkFormItem>
            <BkFormItem
              :label="t('维护人员')"
              property="maintainers"
              :required="false"
              class="member-selector-form"
              :class="[{ 'is-error': isShowMemberError}]"
            >
              <MemberSelector
                v-if="!featureFlagStore.isTenantMode"
                v-model="formData.maintainers"
                @change="handleMemberChange"
              />
              <BkUserSelector
                v-else
                v-model="formData.maintainers"
                :api-base-url="envStore.tenantUserDisplayAPI"
                multiple
                :tenant-id="userStore.info.tenant_id"
                @change="handleMemberChange"
              />
              <div
                v-if="isShowMemberError"
                class="color-#ea3636 text-12px p-t-4px leading-[1]"
              >
                {{ t('维护人员不能为空') }}
              </div>
            </BkFormItem>
            <BkFormItem
              :label="t('描述')"
              property="description"
            >
              <BkInput
                v-model.trim="formData.description"
                :maxlength="500"
                :placeholder="t('请输入网关描述')"
                type="textarea"
              />
            </BkFormItem>

            <template v-if="formData.kind === 1 && envStore.env.EDITION === 'te'">
              <BkFormItem
                :label="t('代码仓库')"
                class="form-item-name"
                property="extra_info.repository"
                required
              >
                <BkInput
                  v-model="formData.extra_info!.repository"
                  disabled
                />
              </BkFormItem>
              <span class="common-form-tips form-item-name-tips">
                {{ t('自动创建开源仓库，将模板代码初始化到仓库中，并将创建者设定为仓库管理员') }}
              </span>
            </template>

            <template v-if="formData.kind === 1 && envStore.env.EDITION === 'ee' && !isEdit">
              <BkFormItem
                :label="t('代码源')"
                required
              >
                <div class="flex items-center">
                  <div class="repository-item active">
                    <img
                      :src="bareGit"
                      :alt="t('Git 代码库')"
                    >
                    <p class="text">
                      {{ t('Git 代码库') }}
                    </p>
                    <div class="checked-icon">
                      <AgIcon name="check-circle-shape" />
                    </div>
                  </div>
                </div>
              </BkFormItem>
              <BkFormItem
                :label="t('代码仓库地址')"
                property="programmable_gateway_git_info.repository"
                required
              >
                <BkInput
                  v-model.trim="formData.programmable_gateway_git_info!.repository"
                  placeholder="http(s)://xxx.git"
                />
              </BkFormItem>
              <BkFormItem
                :label="t('账号')"
                property="programmable_gateway_git_info.account"
                required
              >
                <BkInput v-model.trim="formData.programmable_gateway_git_info!.account" />
              </BkFormItem>
              <BkFormItem
                :label="t('密码')"
                property="programmable_gateway_git_info.password"
                required
              >
                <BkInput
                  v-model.trim="formData.programmable_gateway_git_info!.password"
                  :placeholder="t('建议使用 access_token')"
                />
              </BkFormItem>
            </template>

            <BkFormItem
              :label="t('是否公开')"
              property="is_public"
              required
            >
              <span class="pr-4px">
                <BkSwitcher
                  v-model="formData.is_public"
                  theme="primary"
                />
              </span>
              <span class="common-form-tips">{{
                t('公开，则用户可查看资源文档、申请资源权限；不公开，则网关对用户隐藏')
              }}</span>
            </BkFormItem>

            <template v-if="featureFlagStore.isTenantMode && !isEdit">
              <template v-if="userStore.info.tenant_id === 'system'">
                <BkFormItem
                  :label="t('租户模式')"
                  property="tenant_mode"
                >
                  <BkSelect
                    v-model="formData.tenant_mode"
                    :clearable="false"
                    :filterable="false"
                    :input-search="false"
                    @change="handleTenantModeChange"
                  >
                    <BkOption
                      :label="t('全租户（Global）')"
                      value="global"
                    />
                    <BkOption
                      :label="t('单租户（Single）')"
                      value="single"
                    />
                  </BkSelect>
                </BkFormItem>
                <BkFormItem
                  v-if="formData.tenant_mode === 'single'"
                  :label="t('租户 ID')"
                  property="tenant_id"
                >
                  <BkInput
                    v-model="formData.tenant_id"
                    disabled
                  />
                </BkFormItem>
              </template>
            </template>

            <template v-if="isEdit">
              <BkFormItem
                v-if="featureFlagStore.flags.GATEWAY_APP_BINDING_ENABLED"
                :label="t('关联蓝鲸应用')"
                property="bk_app_codes"
              >
                <BkTagInput
                  v-model="formData.bk_app_codes"
                  :placeholder="t('请输入蓝鲸应用ID，并按enter确认')"
                  allow-create
                  has-delete-icon
                  collapse-tags
                  :list="[]"
                />
                <span class="common-form-tips">{{ t('仅影响 HomePage 中运维开发分数的计算') }}</span>
              </BkFormItem>
              <BkFormItem
                :label="t('管理网关的应用列表 ')"
                property="related_app_codes"
              >
                <BkTagInput
                  v-model="formData.related_app_codes"
                  :placeholder="t('请输入蓝鲸应用ID，并按enter确认')"
                  allow-create
                  has-delete-icon
                  collapse-tags
                />
                <span class="common-form-tips">{{ t('允许列表中的应用使用 sdk 或者开放 API 调用网关接口，同步环境/资源以及发布版本') }}</span>
              </BkFormItem>
            </template>
          </BkForm>
        </div>
        <div class="progress">
          <div class="title">
            {{ formData.kind === 0 ? t('普通网关发布流程') : t('编程网关发布流程') }}
          </div>
          <BkTimeline :list="progressList" />
        </div>
      </div>
    </template>
    <template #footer>
      <div class="p-l-24px">
        <BkPopConfirm
          v-if="!formData.maintainers?.includes(userStore.info.username) && isEdit"
          width="288"
          :content="t('您已将自己从维护人员列表中移除，移除后您将失去查看和编辑网关的权限。请确认！')"
          trigger="click"
          ext-cls="confirm-custom-btn"
          @confirm="handleConfirmCreate"
          @cancel="handleCancel"
        >
          <BkButton
            theme="primary"
            class="min-w-88px"
            :loading="submitLoading"
          >
            {{ t('保存') }}
          </BkButton>
        </BkPopConfirm>
        <BkButton
          v-else
          theme="primary"
          class="min-w-88px"
          :loading="submitLoading"
          @click="handleConfirmCreate"
        >
          {{ isEdit ? t('保存') : t('提交') }}
        </BkButton>
        <BkButton
          class="m-l-8px min-w-88px"
          @click="handleCancel"
        >
          {{ t('取消') }}
        </BkButton>
      </div>
    </template>
  </AgSideslider>

  <BkSideslider
    v-model:is-show="isShowMarkdown"
    :title="t('新建网关')"
    :width="1020"
  >
    <section class="guide-wrapper">
      <section class="header">
        <p class="success-icon">
          <AgIcon name="check-circle-shape" />
        </p>
        <div class="title">
          {{ t('网关（{name}）创建成功', { name: newGateway.name }) }}
        </div>
        <div class="tips">
          {{ t('接下来您可以按照开发指引，完成网关的开发，或进入环境概览查看环境信息') }}
        </div>
        <div class="btn-wrapper">
          <BkButton
            theme="primary"
            @click="handleGoToEnvOverview"
          >
            {{ t('环境概览') }}
          </BkButton>
          <BkButton
            class="ml-8px"
            @click="isShowMarkdown = false"
          >
            {{ t('关闭') }}
          </BkButton>
        </div>
      </section>
      <section class="markdown-box" />
    </section>
  </BkSideslider>
</template>

<script lang="ts" setup>
import { getEnv } from '@/services/source/basic.ts';
import {
  createGateway,
  getGuideDocs,
  patchGateway,
} from '@/services/source/gateway.ts';
import { Message } from 'bkui-vue';
import { cloneDeep } from 'lodash-es';
import MemberSelector from '@/components/member-selector';
import BkUserSelector from '@blueking/bk-user-selector';
import bareGit from '@/images/bare_git.png';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import {
  useEnv,
  useFeatureFlag,
  useUserInfo,
} from '@/stores';
import AgIcon from '@/components/ag-icon/Index.vue';
import AgSideslider from '@/components/ag-sideslider/Index.vue';

type ParamType = Parameters<typeof patchGateway>[1];

type FormMethod = {
  validate: () => void
  clearValidate: () => void
};

interface IProps { initData?: ParamType }

const isShow = defineModel<boolean>({ default: false });

const {
  initData = {
    kind: 0,
    extra_info: {
      language: 'python',
      repository: '',
    },
  },
} = defineProps<IProps>();

const emit = defineEmits<{ done: [void] }>();

const { t } = useI18n();
const router = useRouter();
const userStore = useUserInfo();
const featureFlagStore = useFeatureFlag();
const envStore = useEnv();

const formRef = ref<InstanceType<typeof BkForm> & FormMethod>();
const formData = ref<ParamType>({
  name: '',
  description: '',
  is_public: true,
  kind: 0,
  maintainers: [userStore.info.username],
  extra_info: {
    language: 'python',
    repository: '',
  },
  programmable_gateway_git_info: {
    repository: '',
    account: '',
    password: '',
  },
});
const submitLoading = ref(false);
const isShowMarkdown = ref(false);
const isShowMemberError = ref(false);
const markdownHtml = ref('');
const newGateway = ref({
  name: '',
  id: 0,
});
const repositoryUrl = ref('');

const defaultFormData = ref({
  name: '',
  description: '',
  is_public: true,
  kind: 0,
  maintainers: [userStore.info.username],
  extra_info: {
    language: 'python',
    repository: '',
  },
  programmable_gateway_git_info: {
    repository: '',
    account: '',
    password: '',
  },
});

const rules = {
  'name': [
    {
      required: true,
      message: t('请填写名称'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => value.length >= 3,
      message: t('不能小于3个字符'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => value.length <= 30,
      message: t('不能多于30个字符'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => {
        const reg = formData.value.kind === 0 ? /^[a-z][a-z0-9-]*$/ : /^[a-z0-9-]{3,16}$/;
        return reg.test(value);
      },
      message: () => formData.value.kind === 0
        ? t('由小写字母、数字、连接符（-）组成，首字符必须是小写字母，长度大于3小于30个字符')
        : t('只能包含小写字母(a-z)、数字(0-9)和半角连接符(-)，长度在 3-16 之间'),
      trigger: 'blur',
    },
  ],
  'programmable_gateway_git_info.repository': [
    {
      required: true,
      message: t('请填写代码仓库地址'),
      trigger: 'change',
    },
    {
      validator: (value: string) => {
        const reg = /^https?:\/\/[^\s]+\.git$/;
        return reg.test(value);
      },
      message: t('请输入正确的代码仓库地址，http(s)://xxx.git'),
      trigger: 'change',
    },
  ],
};

const languageList = [
  {
    value: 'python',
    label: 'Python',
  },
  {
    value: 'go',
    label: 'Go',
  },
];

const isEdit = computed(() => {
  return !!formData.value?.id;
});

const nameInputPlaceholder = computed(() =>
  formData.value.kind === 0
    ? t('请输入小写字母、数字、连字符(-)，以小写字母开头')
    : t('只能包含小写字母(a-z)、数字(0-9)和半角连接符(-)，长度在 3-16 之间'),
);

const progressList = computed(() => {
  if (formData.value.kind === 0) {
    return [
      {
        tag: t('创建网关'),
        content: `<span class="progress-subtitle">${t('初始化环境： prod ，并可新增环境')}</span>`,
        color: 'blue',
      },
      {
        tag: t('配置后端服务'),
        content: `<span class="progress-subtitle">${t('每个环境都可以单独配置后端 API 的域名')}</span>`,
      },
      {
        tag: t('资源配置'),
        content: `<span class="progress-subtitle">${t('页面添加或通过 Swagger/OpenAPI 文件导入')}</span>`,
      },
      {
        tag: t('生成版本'),
        content: `<span class="progress-subtitle">${t('资源列表快照可以用于对比差异，并生成 SDK')}</span>`,
      },
      {
        tag: t('发布到环境'),
        content: `<span class="progress-subtitle">${t('发布成后，即可通过网关访问 API')}</span>`,
      },
    ];
  }
  return [
    {
      tag: t('创建网关'),
      content: `<span class="progress-subtitle">
        ${t('自动创建代码仓库并包含代码示例初始化')} <b>2</b> ${t('套环境：stag 和 prod')}
      </span>`,
      color: 'blue',
    },
    {
      tag: t('开发 API'),
      content: `<p class="progress-subtitle progress-p">${t('在代码仓库定义资源配置')}</p>
      <p class="progress-subtitle">${t('同时可对 API 进行')} <b>${t('网络协议转、接口组合编排')}</b> ${t('等')}</p>`,
    },
    {
      tag: t('发布到环境'),
      content: `<p class="progress-subtitle progress-p">${t('自动生成版本')}</p>
      <p class="progress-subtitle">${t('自动部署 web 服务，并将域名到注册后端服务地址')}</p> `,
    },
  ];
});

const md = new MarkdownIt({
  linkify: false,
  html: true,
  breaks: true,
  highlight(str: string, lang: string) {
    try {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(str, {
          language: lang,
          ignoreIllegals: true,
        }).value;
      }
    }
    catch {
      return str;
    }
    return str;
  },
});

const handleCompare = (callback) => {
  callback(cloneDeep(formData.value));
};

watch(
  () => featureFlagStore.flags.ENABLE_MULTI_TENANT_MODE,
  () => {
    if (featureFlagStore.flags.ENABLE_MULTI_TENANT_MODE) {
      formData.value = Object.assign(formData.value, {
        tenant_id: userStore.info.tenant_id || 'system',
        tenant_mode: ['system'].includes(userStore.info.tenant_id) ? 'global' : 'single',
      });
      defaultFormData.value = Object.assign(defaultFormData.value, {
        tenant_id: userStore.info.tenant_id || 'system',
        tenant_mode: ['system'].includes(userStore.info.tenant_id) ? 'global' : 'single',
      });
    }
    else {
      formData.value = Object.assign(formData.value, {
        tenant_id: 'default',
        tenant_mode: 'single',
      });
      defaultFormData.value = Object.assign(defaultFormData.value, {
        tenant_id: 'default',
        tenant_mode: 'single',
      });
    }
  },
  { immediate: true },
);

watch(
  () => userStore.info.username,
  () => {
    if (userStore.info.username && !formData.value.maintainers?.length) {
      formData.value.maintainers = [userStore.info.username];
    }
  },
  { immediate: true },
);

watch(
  () => formData.value?.name,
  () => {
    setRepositoryAddress();
  },
);

watch(
  () => initData,
  () => {
    if (initData) {
      formData.value = cloneDeep(initData);
      defaultFormData.value = cloneDeep(initData);
    }
  },
);

const setRepositoryAddress = () => {
  if (envStore.env.EDITION === 'te' && formData.value.kind === 1) {
    formData.value.extra_info!.repository
        = `${repositoryUrl.value.replace('{{gateway_name}}', formData.value.name || '')}`;
  }
};

const handleKindChange = () => {
  setRepositoryAddress();
};

const handleMemberChange = (member: string[]) => {
  formData.value.maintainers = member;
  isShowMemberError.value = !member.length;
};

const showGuide = async () => {
  const data = await getGuideDocs(newGateway.value?.id);
  markdownHtml.value = md.render(data.content);
  isShowMarkdown.value = true;
};

const handleGoToEnvOverview = () => {
  router.push({
    name: 'StageOverview',
    params: { id: newGateway.value?.id },
  });
};

const getUrlPrefix = async () => {
  const res = await getEnv();
  repositoryUrl.value = res.BK_PAAS_APP_REPO_URL_TMPL;
};

if (envStore.env.EDITION === 'te') {
  getUrlPrefix();
}

const handleTenantModeChange = (tenant_mode: string) => {
  if (tenant_mode === 'global') {
    formData.value.tenant_id = '';
  }
  else if (tenant_mode === 'single') {
    formData.value.tenant_id = userStore.info.tenant_id || 'system';
  }
};

const handleConfirmCreate = async () => {
  try {
    await formRef.value?.validate();

    if (!formData.value.maintainers.length) {
      return;
    }
    submitLoading.value = true;
    const payload = cloneDeep(formData.value);
    if (payload.kind === 0) {
      payload.extra_info = undefined;
    }
    if (payload.kind === 1 && envStore.env.EDITION === 'ee' && !isEdit.value) {
      payload.extra_info!.repository = payload.programmable_gateway_git_info!.repository;
    }

    if (isEdit.value) {
      if (!featureFlagStore.flags.GATEWAY_APP_BINDING_ENABLED) {
        payload.bk_app_codes = undefined;
      }
      await patchGateway(payload.id!, payload);
      Message({
        message: t('编辑成功'),
        theme: 'success',
        width: 'auto',
      });
    }
    else {
      const response = await createGateway(payload);

      if (payload.kind === 1) {
        newGateway.value = {
          name: payload.name!,
          id: response.id,
        };
        showGuide();
      }
      else {
        Message({
          message: t('创建成功'),
          theme: 'success',
        });
      }
    }
    handleCancel();
    emit('done');
  }
  finally {
    submitLoading.value = false;
  }
};

const handleCancel = () => {
  formRef?.value?.clearValidate();
  formData.value = cloneDeep(defaultFormData.value);
  isShowMemberError.value = false;
  isShow.value = false;
};

</script>

<style lang="scss" scoped>
.gateway-operate-slider {

  :deep(.bk-modal-content) {
    overflow-y: hidden;
  }

  .create-gateway {
    display: flex;

    .create-form {
      max-height: calc(100vh - 130px);
      padding: 0 24px;
      overflow-y: auto;
      background: #FFF;
      flex: 1;
    }

    .form-item-name {

      :deep(.bk-form-error) {
        position: relative;
      }
    }

    .form-item-name-tips {
      position: relative;
      top: -20px;
    }

    .progress {
      width: 400px;
      max-height: calc(100vh - 92px);
      padding: 24px;
      margin-top: -16px;
      margin-right: -14px;
      overflow-y: auto;
      background: #F5F7FA;
      box-sizing: border-box;

      .title {
        padding-bottom: 16px;
        font-size: 14px;
        font-weight: bold;
        color: #4D4F56;
      }
    }
  }

  .common-form-tips {
    font-size: 12px;
    color: #979ba5;
  }
}

.repository-item {
  display: flex;
  width: 124px;
  height: 88px;
  cursor: pointer;
  border: 1px solid #c4c6cc;
  border-radius: 2px;
  flex-direction: column;
  justify-content: center;
  align-items: center;

  img {
    width: 40px;
    height: 40px;
  }

  .text {
    font-size: 14px;
    color: #63656E;
  }

  &.active {
    position: relative;
    border: 1px solid #3A84FF;

    .checked-icon {
      position: absolute;
      top: -9px;
      right: -9px;
      display: flex;
      width: 18px;
      height: 18px;
      background-color: #FFF;
      align-items: center;
      justify-content: center;

      .apigateway-icon {
        width: 14px;
        height: 14px;
        color: #3A84FF;
      }
    }
  }
}

.guide-wrapper {
  padding: 16px 24px;

  .header {
    margin-bottom: 32px;
    text-align: center;

    .success-icon {
      margin-bottom: 18px;

      i {
        font-size: 42px;
        color: #65C389;
        background: #EBFAF0;
      }
    }

    .title {
      font-size: 20px;
      color: #313238;
    }

    .tips {
      margin: 12px 0 24px;
      font-size: 14px;
      color: #4D4F56;
    }
  }
}

:deep(.progress-subtitle) {
  font-size: 12px;
  color: #979BA5;
}

:deep(.progress-p) {
  margin-bottom: 4px;
}

:deep(.bk-timeline-content) {
  word-break: normal !important;
}

:deep(.ag-markdown-view pre) {
  background: #F5F7FA;
}

:deep(.ag-markdown-view code) {
  color: #4D4F56;
}

:deep(.ag-markdown-view .ag-copy-btn) {
  color: #3A84FF;
  background: #F5F7FA;
}

.member-selector-form {
  :deep(.bk-form-label) {
    &::after {
      position: absolute;
      top: 0;
      width: 14px;
      color: #ea3636;
      text-align: center;
      content: "*";
    }
  }

  &.is-error {
    :deep(.bk-tag-input-trigger),
    :deep(.tags-container) {
      border-color: #ea3636;
    }
  }
}
</style>
