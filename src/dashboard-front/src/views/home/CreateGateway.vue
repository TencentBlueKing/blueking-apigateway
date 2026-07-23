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
          <div
            class="type-wrapper flex"
            :class="{ disabled: isEdit }"
          >
            <div
              class="item"
              :class="{ active: formData.kind === 0 }"
              @click="handleKindChange(0)"
            >
              <div class="type flex">
                <div class="icon">
                  <AgIcon
                    name="apiwangguan"
                    size="32"
                    color="#3A84FF"
                  />
                </div>
                <div class="title ml-8px">
                  {{ t('API 网关') }}
                </div>
              </div>
              <div class="desc">
                {{ t('标准 API 网关。将已有 HTTP 后端服务注册为资源，统一鉴权、限流、文档、监控与权限管理。') }}
              </div>
              <div class="scene">
                <div class="title">
                  {{ t('适用场景') }}
                </div>
                <div class="content">
                  {{ t('大多数后端业务 API 的统一接入与治理') }}
                </div>
              </div>
              <div class="check-icon-wrapper">
                <AgIcon
                  name="check-1"
                  size="16"
                />
              </div>
            </div>
            <div
              class="item m-l-16px m-r-16px"
              :class="{ active: formData.kind === 2 }"
              @click="handleKindChange(2)"
            >
              <div class="type flex">
                <div class="icon">
                  <AgIcon
                    name="AIwangguan"
                    size="32"
                    color="#3A84FF"
                  />
                </div>
                <div class="title ml-8px">
                  {{ t('AI 网关') }}
                </div>
              </div>
              <div class="desc">
                {{ t('在普通网关能力之上，新增「模型服务」与「模型代理 API」，把内部 OpenAI 兼容的大模型服务安全、可授权、可审计地暴露为统一调用入口。') }}
              </div>
              <div class="scene">
                <div class="title">
                  {{ t('适用场景') }}
                </div>
                <div class="content">
                  <p>{{ t('模型服务 + 模型代理 API') }}</p>
                  <p>{{ t('复用鉴权 / 发布 / 文档 / 监控') }}</p>
                  <p>{{ t('内部大模型 / chat-completions 服务的受控暴露与统一治理') }}</p>
                </div>
              </div>
              <div class="check-icon-wrapper">
                <AgIcon
                  name="check-1"
                  size="16"
                />
              </div>
            </div>
            <div
              class="item"
              :class="{ active: formData.kind === 1 }"
              @click="handleKindChange(1)"
            >
              <div class="type flex">
                <div class="icon">
                  <AgIcon
                    name="kebiancheng"
                    size="32"
                    color="#3A84FF"
                  />
                </div>
                <div class="title ml-8px">
                  {{ t('可编程网关') }}
                </div>
              </div>
              <div class="desc">
                {{ t('通过编写代码自定义网关逻辑，支持复杂的请求编排、协议转换、自定义鉴权等高级能力。') }}
              </div>
              <div class="scene">
                <div class="title">
                  {{ t('适用场景') }}
                </div>
                <div class="content">
                  {{ t('需要高度定制化网关行为的场景') }}
                </div>
              </div>
              <div class="check-icon-wrapper">
                <AgIcon
                  name="check-1"
                  size="16"
                />
              </div>
            </div>
          </div>
        </BkFormItem>
        <span class="common-form-tips form-item-name-tips">
          {{ t('网关类型在创建后') }}
          <span class="color-#EA3636 ml--2px">{{ t('不可更改') }}</span>,
          {{ t('请按业务形态谨慎选择') }}
        </span>
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
            @change="handleTenantUserChange"
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
          <bk-alert
            v-if="isShowRepoAuthAlert"
            theme="error"
            class="common-form-tips form-item-name-tips"
          >
            <template #title>
              <div class="flex items-center justify-between">
                <span>{{ t('代码仓库未授权') }}</span>
                <span
                  class="color-#3A84FF cursor-pointer"
                  @click="handleGoToAuth"
                >
                  {{ t('去授权') }}
                  <AgIcon
                    name="jump"
                    color="#3A84FF"
                  />
                </span>
              </div>
            </template>
          </bk-alert>
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
              :copyable="false"
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
              :copyable="false"
              collapse-tags
            />
            <span class="common-form-tips">{{ t('允许列表中的应用使用 sdk 或者开放 API 调用网关接口，同步环境/资源以及发布版本') }}</span>
          </BkFormItem>
        </template>
      </BkForm>
      <div>
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
          {{ t('确定') }}
        </BkButton>
        <BkButton
          class="m-l-8px min-w-88px"
          @click="handleCancel"
        >
          {{ t('取消') }}
        </BkButton>
      </div>
    </div>

    <div class="progress">
      <div class="title">
        {{ gatewayKindLabel }}
      </div>
      <BkTimeline :list="progressList" />
    </div>
  </div>
</template>

<script lang="ts" setup>
// @ts-nocheck
import { getEnv } from '@/services/source/basic.ts';
import {
  checkNameAvailable,
  checkRepoAuthorization,
  createGateway,
  patchGateway,
} from '@/services/source/gateway.ts';
import { usePopInfoBox } from '@/hooks';
import { Form, Message, Tag } from 'bkui-vue';
import { cloneDeep } from 'lodash-es';
import type { IFormMethod } from '@/types/common';
import type { IGatewayCreateInputSLZ } from '@/services/types/body/post/gateways';
import MemberSelector from '@/components/member-selector';
import BkUserSelector from '@blueking/bk-user-selector';
import bareGit from '@/images/bare_git.png';
import {
  useEnv,
  useFeatureFlag,
  useGateway,
  useUserInfo,
} from '@/stores';
import AgIcon from '@/components/ag-icon/Index.vue';

type ParamType = IGatewayCreateInputSLZ & {
  id?: number
  tenant_mode?: string
  tenant_id?: string
};

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const userStore = useUserInfo();
const featureFlagStore = useFeatureFlag();
const envStore = useEnv();
const gatewayStore = useGateway();

const formRef = ref<InstanceType<typeof Form> & IFormMethod>();
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
const gatewayKindLabelMap: Record<number, string> = {
  0: '普通网关发布流程',
  1: '可编程网关发布流程',
  2: 'AI 网关发布流程',
};
const gatewayKindLabel = computed(() => t(gatewayKindLabelMap[formData.value.kind] ?? '普通网关发布流程'));
const submitLoading = ref(false);
const isShowMemberError = ref(false);
const repositoryUrl = ref('');
// 代码仓库授权状态：null=未检测，true=已授权，false=未授权
const isRepoAuthorized = ref<boolean | null>(null);
const authUrl = ref('');
// 授权状态轮询定时器
let authPollingTimer: ReturnType<typeof setInterval> | null = null;

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

const isNameAvailable = ref(true);
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
        const reg = formData.value.kind !== 1 ? /^[a-z][a-z0-9-]*$/ : /^[a-z0-9-]{3,16}$/;
        return reg.test(value);
      },
      message: () => formData.value.kind !== 1
        ? t('由小写字母、数字、连接符（-）组成，首字符必须是小写字母，长度大于3小于30个字符')
        : t('只能包含小写字母(a-z)、数字(0-9)和半角连接符(-)，长度在 3-16 之间'),
      trigger: 'blur',
    },
    {
      validator: async (value: string) => {
        try {
          if (isEdit.value) return true;
          if (!value) return true;

          const response = await checkNameAvailable({ name: value });
          isNameAvailable.value = response?.is_available;
          return isNameAvailable.value;
        }
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        catch (_) {
          return false;
        }
      },
      message: t('网关名已被占用'),
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

const isShowRepoAuthAlert = computed(() => isRepoAuthorized.value === false);

const isEdit = computed(() => {
  return !!formData.value?.id;
});

const nameInputPlaceholder = computed(() =>
  formData.value.kind !== 1
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
  else if (formData.value.kind === 1) {
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
  }
  return [
    {
      tag: t('创建网关'),
      content: `<span class="progress-subtitle">
        ${t('初始化环境： prod ，并可新增环境')}
      </span>`,
      color: 'blue',
    },
    {
      tag: h(
        'div',
        {
          class: 'timeline-title-with-tag',
        },
        [
          t('配置模型服务'),
          h(
            Tag,
            {
              theme: 'info',
            },
            'AI',
          ),
        ],
      ),
      content: h(
        'p',
        {
          class: 'progress-subtitle',
        },
        t('按环境配置 OpenAI 兼容的 endpoint、auth、model 等，并做连通测试'),
      ),
      nodeType: 'vnode',
    },
    {
      tag: t('资源配置'),
      content: `<p class="progress-subtitle">${t('新建「模型代理 API」引用模型服务，或新建普通资源')}</p>`,
    },
    {
      tag: t('生成版本'),
      content: `<p class="progress-subtitle">${t('资源列表快照可以用于对比差异')}</p> `,
    },
    {
      tag: t('发布到环境'),
      content: `<p class="progress-subtitle">${t('发布后下发 APISIX，即可通过网关受控调用模型')}</p>`,
    },
  ];
});

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

// 编辑模式：从 BasicInfo 页面跳转时，从 useGateway store 获取 initData
onMounted(() => {
  if (route.query.from === 'basic-info') {
    const currentGateway = gatewayStore.currentGateway;
    if (currentGateway?.id) {
      formData.value = cloneDeep({
        id: currentGateway.id,
        name: currentGateway.name || '',
        description: currentGateway.description,
        maintainers: currentGateway.maintainers || [],
        developers: currentGateway.developers || [],
        is_public: currentGateway.is_public,
        kind: currentGateway.kind,
        extra_info: currentGateway.extra_info || {},
        bk_app_codes: currentGateway.bk_app_codes || [],
        tenant_mode: currentGateway.tenant_mode || '',
        tenant_id: currentGateway.tenant_id || '',
        programmable_gateway_git_info: (currentGateway as any).programmable_gateway_git_info || {},
      });
      defaultFormData.value = cloneDeep(formData.value);
    }
  }
});

// 检查代码仓库授权状态
const checkAuthorization = async () => {
  if (envStore.env.EDITION !== 'te' || formData.value.kind !== 1) return;
  try {
    const res = await checkRepoAuthorization();
    isRepoAuthorized.value = res?.authorized ?? false;
    authUrl.value = res?.address ?? '';
  }
  catch {
    isRepoAuthorized.value = false;
  }
};

const setRepositoryAddress = () => {
  if (envStore.env.EDITION === 'te' && formData.value.kind === 1) {
    formData.value.extra_info!.repository = `${repositoryUrl.value.replace('{{gateway_name}}', formData.value.name || '')}`;
    // 代码仓库地址变更后清除旧轮询并重新检测授权状态
    clearAuthPolling();
    if (formData.value.name) {
      checkAuthorization();
    }
  }
};

const handleKindChange = (type: number) => {
  if (isEdit.value) return;

  formData.value.kind = type;
  setRepositoryAddress();
};

const handleMemberChange = (member: string[]) => {
  formData.value.maintainers = member;
  isShowMemberError.value = !member.length;
};

const handleTenantUserChange = (members: { id: string }[]) => {
  formData.value.maintainers = members.map(member => member.id);
  isShowMemberError.value = !members.length;
};

const getUrlPrefix = async () => {
  const res = await getEnv();
  repositoryUrl.value = res.BK_PAAS_APP_REPO_URL_TMPL;
};

if (envStore.env.EDITION === 'te') {
  getUrlPrefix();
}

// 清除授权状态轮询
const clearAuthPolling = () => {
  if (authPollingTimer !== null) {
    clearInterval(authPollingTimer);
    authPollingTimer = null;
  }
};

// 启动授权状态轮询
const startAuthPolling = () => {
  clearAuthPolling();
  authPollingTimer = setInterval(async () => {
    await checkAuthorization();
    // 已授权则停止轮询
    if (isRepoAuthorized.value) {
      clearAuthPolling();
    }
  }, 3000);
};

// 跳转到代码仓库授权页面
const handleGoToAuth = () => {
  if (authUrl.value) {
    startAuthPolling();
    window.open(authUrl.value);
  }
};

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

    if (!isNameAvailable.value) {
      return;
    }

    if (!formData.value.maintainers.length) {
      return;
    }

    // 可编程网关在 te 版中需要检测代码仓库授权状态
    if (formData.value.kind === 1 && envStore.env.EDITION === 'te' && !isEdit.value && isRepoAuthorized.value === false) {
      usePopInfoBox({
        isShow: true,
        type: 'warning',
        title: t('代码仓库未授权'),
        subTitle: t('请先完成代码仓库授权后再提交'),
        confirmText: t('去授权'),
        cancelText: t('取消'),
        onConfirm: () => {
          handleGoToAuth();
        },
        onCancel: () => {
          clearAuthPolling();
        },
      });
      return;
    }

    submitLoading.value = true;
    const payload = cloneDeep(formData.value);
    if (payload.kind !== 1) {
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
      gatewayStore.setCurrentGateway(payload);
      router.push(`/${gatewayStore.currentGateway.id}/basic-info`);
    }
    else {
      const response = await createGateway(payload);

      reset();
      if (payload.kind === 1) {
        router.push({
          name: 'GatewayGuide',
          params: { id: response.id,
            name: payload.name },
        });
      }
      else {
        Message({
          message: t('创建成功'),
          theme: 'success',
        });
        router.push({ name: 'Home' });
      }
    }
  }
  finally {
    submitLoading.value = false;
  }
};

const reset = () => {
  clearAuthPolling();
  formRef?.value?.clearValidate();
  formData.value = cloneDeep(defaultFormData.value);
  isShowMemberError.value = false;
};

const handleCancel = () => {
  reset();
  router.back();
};

</script>

<style lang="scss" scoped>
.create-gateway {
  width: 1280px;
  margin: 0 auto;
  padding: 16px 0 24px 0;
  box-sizing: border-box;
  display: flex;

  .create-form {
    padding: 24px;
    background: #FFF;
    flex: 1;

    .form-item-name {
      :deep(.bk-form-error) {
        position: relative;
      }
    }

    .form-item-name-tips {
      position: relative;
      top: -20px;
    }

    .common-form-tips {
      font-size: 12px;
      color: #979ba5;
    }

    .repository-item {
      display: flex;
      width: 124px;
      height: 88px;
      box-sizing: border-box;
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

    .type-wrapper {

      .item {
        display: flex;
        flex-direction: column;
        padding: 16px;
        border-radius: 4px;
        border: 1px solid #DCDEE5;
        background: #ffffff;
        box-shadow: 0 2px 4px 0 #1919290d;
        position: relative;

        .check-icon-wrapper {
          position: absolute;
          top: 0;
          right: 0;
          display: none;
          width: 28px;
          height: 28px;
          align-items: flex-start;
          justify-content: flex-end;
          color: #FFF;

          &::before {
            content: '';
            position: absolute;
            top: 0;
            right: -1px;
            width: 100%;
            height: 100%;
            background: #3A84FF;
            clip-path: polygon(0 0, 100% 0, 100% 100%);
          }

          .apigateway-icon {
            position: relative;
            z-index: 1;
          }
        }

        &.active {
          border: 1px solid #3A84FF;
          background: #F0F5FF;

          .scene {
            background: #FAFBFD;
          }

          .check-icon-wrapper {
            display: flex;
          }
        }

        &:not(.active) {
          cursor: pointer;
        }
      }

      &.disabled {
        .item {
          cursor: not-allowed;
          opacity: 0.5;
        }
      }

      .type {
        margin-bottom: 12px;
        .icon {
          width: 32px;
          height: 32px;
          border-radius: 4px;
        }
        .title {
          color: #313238;
          font-size: 14px;
          font-weight: Bold;
        }
      }

      .desc {
        color: #4d4f56;
        font-size: 12px;
        line-height: 20px;
        margin-bottom: 12px;
      }

      .scene {
        width: 240px;
        height: 118px;
        padding: 6px 8px;
        box-sizing: border-box;
        border-radius: 4px;
        background: #F5F7FA;
        margin-top: auto;

        .title {
          color: #4d4f56;
          font-size: 12px;
          font-weight: Bold;
          line-height: 24px;
        }
        .content {
          color: #979ba5;
          font-size: 12px;
          line-height: 20px;
        }
      }
    }
  }

  .progress {
    width: 360px;
    padding: 24px;
    box-sizing: border-box;
    background: #FFF;
    margin-left: 24px;

    .title {
      padding-bottom: 16px;
      font-size: 14px;
      font-weight: bold;
      color: #4D4F56;
    }
  }
}

:deep(.timeline-title-with-tag) {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

:deep(.progress-subtitle) {
  font-size: 12px;
  line-height: 20px;
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
