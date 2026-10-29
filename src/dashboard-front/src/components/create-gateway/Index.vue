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
  <BkDialog
    v-model:is-show="isShow"
    :title="t('编辑基本信息')"
    width="640"
    @compare="handleCompare"
    @closed="handleCancel"
  >
    <BkForm
      ref="formRef"
      form-type="vertical"
      :model="formData"
      :rules="rules"
    >
      <BkFormItem
        :label="t('网关 ID')"
        class="form-item-with-tips"
        property="name"
        required
      >
        <BkInput
          v-model.trim="formData.name"
          disabled
          clearable
          show-word-limit
        />
        <p class="common-form-tips">
          {{ t('网关的唯一标识，创建后不可更改') }}
        </p>
      </BkFormItem>
      <BkFormItem
        :label="t('网关展示名')"
        class="form-item-with-tips"
        property="display_name"
        required
      >
        <BkInput
          v-model.trim="formData.display_name"
          :maxlength="64"
          :placeholder="t('请输入网关展示名')"
          clearable
          show-word-limit
        />
        <p class="common-form-tips">
          {{ t('用于页面展示，可随时修改') }}
        </p>
      </BkFormItem>
      <BkFormItem
        v-if="formData.kind === 1"
        :label="t('开发语言')"
        property="extra_info.language"
        required
      >
        <BkSelect
          v-model="formData.extra_info!.language"
          disabled
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

      <BkFormItem
        v-if="featureFlagStore.flags.GATEWAY_APP_BINDING_ENABLED"
        :label="t('关联蓝鲸应用')"
        property="bk_app_codes"
      >
        <BkTagInput
          v-model="formData.bk_app_codes"
          :placeholder="t('请输入蓝鲸应用 ID，并按 enter 确认')"
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
          :placeholder="t('请输入应用 ID，以回车键确认')"
          allow-create
          has-delete-icon
          :copyable="false"
          collapse-tags
        />
        <span class="common-form-tips">{{ t('配置后，列表中的应用可管理该网关') }}</span>
      </BkFormItem>
    </BkForm>
    <template #footer>
      <div class="p-l-24px">
        <BkButton
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
    </template>
  </BkDialog>
</template>

<script lang="ts" setup>
// @ts-nocheck
import { Form, Message } from 'bkui-vue';
import { cloneDeep } from 'lodash-es';
import { getEnv } from '@/services/source/basic.ts';
import AgIcon from '@/components/ag-icon/Index.vue';
import type { IFormMethod } from '@/types/common';
import type { IGatewayCreateInputSLZ } from '@/services/types/body/post/gateways';
import {
  useEnv,
  useFeatureFlag,
  useUserInfo,
} from '@/stores';
import {
  checkRepoAuthorization,
  patchGateway,
} from '@/services/source/gateway.ts';
import { useGatewayDisplayNameCheck } from '@/hooks';

export type ParamType = IGatewayCreateInputSLZ & {
  id?: number
  tenant_mode?: string
  tenant_id?: string
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
const userStore = useUserInfo();
const featureFlagStore = useFeatureFlag();
const envStore = useEnv();

const formRef = ref<InstanceType<typeof Form> & IFormMethod>();
const formData = ref<ParamType>({
  name: '',
  display_name: '',
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
const repositoryUrl = ref('');
// 代码仓库授权状态：null=未检测，true=已授权，false=未授权
const isRepoAuthorized = ref<boolean | null>(null);
const authUrl = ref('');
// 授权状态轮询定时器
let authPollingTimer: ReturnType<typeof setInterval> | null = null;

const defaultFormData = ref({
  name: '',
  display_name: '',
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

const { checkDisplayName } = useGatewayDisplayNameCheck({
  gatewayId: () => formData.value.id,
  gatewayName: () => formData.value.name,
  displayName: () => formData.value.display_name,
});

const rules = {
  'display_name': [
    {
      required: true,
      message: t('请输入网关展示名'),
      trigger: 'blur',
    },
    {
      validator: () => checkDisplayName(),
      message: t('展示名已被使用'),
      trigger: 'blur',
    },
  ],
  'name': [
    {
      required: true,
      message: t('请填写网关 ID'),
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

const handleCompare = (callback: (data: any) => void) => {
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
  () => initData,
  () => {
    if (initData) {
      formData.value = cloneDeep(initData);
      defaultFormData.value = cloneDeep(initData);
    }
  },
);

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

const handleConfirmCreate = async () => {
  try {
    await formRef.value?.validate();

    if (!isNameAvailable.value) {
      return;
    }

    submitLoading.value = true;
    const payload = cloneDeep(formData.value);
    // 展示名有独立编辑入口；未实际修改时不提交该字段，避免用按当前语言返回的展示名覆盖后端默认（中文）展示名
    if (payload.display_name === defaultFormData.value.display_name) {
      delete (payload as Record<string, any>).display_name;
    }
    if (payload.kind !== 1) {
      payload.extra_info = undefined;
    }

    if (!featureFlagStore.flags.GATEWAY_APP_BINDING_ENABLED) {
      payload.bk_app_codes = undefined;
    }

    await patchGateway(payload.id!, payload);

    Message({
      message: t('编辑成功'),
      theme: 'success',
      width: 'auto',
    });
    handleCancel();
    emit('done');
  }
  finally {
    submitLoading.value = false;
  }
};

const handleCancel = () => {
  clearAuthPolling();
  formRef?.value?.clearValidate();
  formData.value = cloneDeep(defaultFormData.value);
  isShow.value = false;
};

</script>

<style lang="scss" scoped>

.form-item-name-tips {
  position: relative;
  top: -20px;
}

.form-item-with-tips {

  .common-form-tips {
    margin: 4px 0 0;
    line-height: 18px;
  }
}

.common-form-tips {
  font-size: 12px;
  color: #979ba5;
}
</style>
