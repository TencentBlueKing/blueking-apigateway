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
  <BkForm
    ref="formRef"
    :model="formData"
    :rules="rules"
    label-width="180"
    class="resource-basic-info"
    @validate="setInvalidPropId"
  >
    <BkFormItem
      v-if="isAIGateway"
      :label="t('资源类型')"
      required
    >
      <BkTag theme="info">
        {{ isModelProxy ? t('模型代理 API') : t('普通 API') }}
      </BkTag>
    </BkFormItem>
    <BkFormItem
      :label="t('名称')"
      property="name"
      required
    >
      <BkInput
        id="base-info-name"
        v-model="formData.name"
        :placeholder="namePlaceholder"
        class="name"
        clearable
      />
      <div
        v-if="!isModelProxy"
        class="text-12px color-#979ba5"
      >
        {{ t("资源名称在网关下唯一，将在SDK中用作操作名称，若修改，请联系 SDK 用户做相应调整") }}
      </div>
    </BkFormItem>
    <BkFormItem :label="t('描述')">
      <BkInput
        v-model="formData.description"
        :placeholder="t('请输入描述')"
        clearable
        class="desc"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('标签')"
      class="label-label"
    >
      <SelectCheckBox
        v-if="isLabelsEditable"
        v-model="formData.label_ids"
        :labels-data="labelsData"
        :width="700"
        is-add
        @updated="init"
        @added="handleLabelAddSuccess"
      />
      <div v-else>
        <div
          v-if="detail?.labels?.length"
          class="mt-8px flex gap-4px"
        >
          <BkTag
            v-for="(label, index) in detail.labels"
            :key="index"
          >
            {{ label }}
          </BkTag>
        </div>
        <span v-else>--</span>
      </div>
    </BkFormItem>
    <BkFormItem
      :label="t('认证方式')"
      required
    >
      <div class="auth-config">
        <BkAlert
          v-if="!formData.auth_config.app_verified_required && !formData.auth_config.auth_verified_required"
          theme="warning"
          class="mb-12px"
          :title="t('当前不校验应用身份和用户身份，调用无需认证即可通过，请确认这是预期配置。')"
        />
        <div class="auth-block">
          <div class="auth-field">
            <BkCheckbox
              v-model="formData.auth_config.app_verified_required"
              :disabled="!canEditAppAuth"
            >
              {{ t('应用认证') }}
            </BkCheckbox>
            <p class="auth-hint">
              {{ t('校验调用方是哪个蓝鲸应用。只开这一项、不开用户认证时，调用不必带上用户身份。') }}
            </p>
          </div>
          <div
            class="auth-child"
            :class="{ 'is-disabled': !formData.auth_config.app_verified_required }"
          >
            <div class="auth-child-row">
              <span class="auth-child-label">{{ t('检验应用权限') }}</span>
              <BkSwitcher
                v-model="formData.auth_config.resource_perm_required"
                :disabled="!canEditAppAuth || !formData.auth_config.app_verified_required"
                theme="primary"
                size="small"
              />
            </div>
            <p class="auth-hint">
              {{ formData.auth_config.app_verified_required
                ? t('开启后，蓝鲸应用必须已获得本资源访问权限才能调用。')
                : t('依赖「应用认证」。先勾选应用认证后才能开启。') }}
            </p>
          </div>
        </div>
        <div class="auth-block">
          <div class="auth-field">
            <BkCheckbox
              v-model="formData.auth_config.auth_verified_required"
              @change="handleAuthVerifiedRequiredChange"
            >
              {{ t('用户认证') }}
            </BkCheckbox>
            <p class="auth-hint">
              {{ t('校验调用代表哪个用户。开启后，调用必须携带用户身份（登录态或 AccessToken）。') }}
            </p>
          </div>
          <div
            class="auth-child"
            :class="{ 'is-disabled': !formData.auth_config.auth_verified_required }"
          >
            <div class="auth-child-row">
              <span class="auth-child-label">{{ t('个人令牌') }}</span>
              <BkSwitcher
                v-model="formData.auth_config.oauth2_personal_client_enabled"
                :disabled="!formData.auth_config.auth_verified_required"
                theme="primary"
                size="small"
              />
            </div>
            <p class="auth-hint">
              {{ formData.auth_config.auth_verified_required
                ? t('开启后，用户可以用个人令牌调用本接口，请求会带上该用户的身份。')
                : t('依赖「用户认证」。先勾选用户认证后才能开启。') }}
            </p>
          </div>
        </div>
        <BkAlert
          :theme="authSceneAlertTheme"
          :title="authSceneText"
        />
      </div>
    </BkFormItem>
    <BkFormItem
      :label="t('是否公开')"
      :description="t('公开，则用户可查看资源文档、申请资源权限；不公开，则资源对用户隐藏')"
      property="is_public"
      required
    >
      <div class="auth-config">
        <div class="auth-block">
          <div class="public-switch">
            <BkSwitcher
              v-model="formData.is_public"
              theme="primary"
              size="small"
            />
          </div>
          <div
            class="auth-child"
            :class="{ 'is-disabled': !canAllowApplyPermission }"
          >
            <div class="auth-child-row">
              <span class="auth-child-label">
                {{ t('允许申请权限') }}
              </span>
              <BkSwitcher
                v-model="formData.allow_apply_permission"
                :disabled="!canAllowApplyPermission"
                theme="primary"
                size="small"
              />
            </div>
            <p class="auth-hint">
              {{ allowApplyPermissionHint }}
            </p>
          </div>
        </div>
      </div>
    </BkFormItem>
  </BkForm>
</template>

<script setup lang="ts">
import { useRouteParams, useRouteQuery } from '@vueuse/router';
import { useGateway } from '@/stores';
import { getGatewayLabels } from '@/services/source/gateway.ts';
import SelectCheckBox from '@/views/resource-management/settings/components/SelectCheckBox.vue';

interface IProps {
  detail?: any
  isClone?: boolean
  // 是否允许编辑标签，用于控制是否只展示静态标签
  isLabelsEditable?: boolean
}

const {
  detail = {},
  isClone = false,
  isLabelsEditable = true,
} = defineProps<IProps>();

const { t } = useI18n();
const gatewayStore = useGateway();
const gatewayId = useRouteParams('id', 0, { transform: Number });
const queryKind = useRouteQuery('kind');

const formRef = ref(null);
const formData = ref({
  kind: queryKind.value,
  name: '',
  description: '',
  label_ids: [] as number[],
  auth_config: {
    auth_verified_required: true,
    app_verified_required: true,
    resource_perm_required: true,
    // oauth2_public_client_enabled: false,
    oauth2_personal_client_enabled: false,
  },
  is_public: true,
  allow_apply_permission: true,
});

const labelsData = ref<{
  id: number
  name: string
}[]>([]);

const resourcePermRequiredBackup = ref(false);

// 错误表单项的 #id
const invalidFormElementIds = ref<string[]>([]);

const isAIGateway = computed(() => gatewayStore.isAIGateway);
// 是否是模型代理 API
const isModelProxy = computed(() => isAIGateway && queryKind.value === 'ai');

const canEditAppAuth = computed(() => !!gatewayStore.currentGateway?.allow_update_gateway_auth);

const canAllowApplyPermission = computed(() => (
  formData.value.is_public && formData.value.auth_config.resource_perm_required
));

const allowApplyPermissionHint = computed(() => {
  if (!formData.value.is_public) {
    return t('依赖「是否公开」。资源不公开时，用户无法查看接口文档和申请权限。');
  }
  if (!formData.value.auth_config.resource_perm_required) {
    return t('需要开启「检验应用权限」，才可以配置「允许申请权限」。');
  }
  return t('开启后，其他蓝鲸应用可在开发者中心申请本资源访问权限；关闭则只能由网关管理员主动授权。');
});

const authSceneText = computed(() => {
  const appAuth = formData.value.auth_config.app_verified_required;
  const userAuth = formData.value.auth_config.auth_verified_required;
  const permRequired = formData.value.auth_config.resource_perm_required;
  const personalEnabled = formData.value.auth_config.oauth2_personal_client_enabled;

  if (!appAuth && !userAuth) {
    return t('当前效果：不校验应用身份、也不校验用户身份。');
  }
  if (appAuth && !userAuth) {
    return permRequired
      ? t('当前效果：仅应用认证，且调用应用必须已获授权。不接受用户 Token / 个人令牌。')
      : t('当前效果：仅应用认证，只接受应用密钥调用，不接受用户 Token / 个人令牌。');
  }
  if (!appAuth && userAuth) {
    return personalEnabled
      ? t('当前效果：只校验用户身份，并允许使用个人令牌。不校验调用方是哪个应用。')
      : t('当前效果：只校验用户身份。不校验调用方是哪个应用。');
  }
  if (permRequired) {
    return personalEnabled
      ? t('当前效果：须同时具备应用身份和用户身份，应用须已获授权；允许使用个人令牌。')
      : t('当前效果：须同时具备应用身份和用户身份，且应用须已获授权。');
  }
  return personalEnabled
    ? t('当前效果：须同时具备应用身份和用户身份；允许使用个人令牌。')
    : t('当前效果：须同时具备应用身份和用户身份。');
});

const authSceneAlertTheme = computed(() => (
  !formData.value.auth_config.app_verified_required && !formData.value.auth_config.auth_verified_required
    ? 'warning'
    : 'info'
));

const namePlaceholder = t('由字母、数字、下划线（_）组成，首字符必须是字母，长度小于256个字符');

const rules = {
  name: [
    {
      required: true,
      message: t('请填写名称'),
      trigger: 'blur',
    },
    {
      trigger: 'blur',
      message: namePlaceholder,
      validator: (value: string) => {
        const reg = /^[a-zA-Z][a-zA-Z0-9_]{0,255}$|^$/;
        return reg.test(value);
      },
    },
  ],
};

watch(
  () => detail,
  (val: any) => {
    if (Object.keys(val).length) {
      const { name, description, auth_config, is_public, allow_apply_permission, labels } = val;
      let label_ids: number[] = [];
      if (labels?.length) {
        // labels 由 id 和 name 组成的情况
        if (labels[0].id && labels[0].name) {
          label_ids = labels.map((label: {
            id: number
            name: string
          }) => label.id);
        }
        // labels 由纯数组组成的情况
        else {
          label_ids = labelsData.value.filter((label: {
            id: number
            name: string
          }) => labels.includes(label.name)).map((label: {
            id: number
            name: string
          }) => label.id);
        }
      }
      formData.value = {
        kind: queryKind.value,
        name: isClone ? `${name}_clone` : name,
        description,
        auth_config: { ...auth_config },
        is_public,
        allow_apply_permission,
        label_ids,
      };
      resourcePermRequiredBackup.value = !!auth_config?.resource_perm_required;
    }
  },
  { immediate: true },
);

watch(
  () => [formData.value.is_public, formData.value.auth_config.resource_perm_required],
  ([v1, v2]) => {
    if (!v1 || !v2) {
      formData.value.allow_apply_permission = false;
    }
  },
);

watch(
  () => formData.value.auth_config.app_verified_required,
  (val: boolean) => {
    formData.value.auth_config.resource_perm_required = val ? resourcePermRequiredBackup.value : false;
  },
);

watch(
  () => formData.value.auth_config.resource_perm_required,
  () => {
    if (formData.value.auth_config.app_verified_required) {
      resourcePermRequiredBackup.value = formData.value.auth_config.resource_perm_required;
    }
  },
);

const init = async () => {
  labelsData.value = await getGatewayLabels(gatewayId.value);
};

const handleLabelAddSuccess = async (labelId: number) => {
  await init();
  if (!formData.value.label_ids.includes(labelId)) {
    formData.value.label_ids.push(labelId);
  }
};

// 重置 OAuth2 开关（默认false）
const resetOauth2Switch = () => {
  // formData.value.auth_config.oauth2_public_client_enabled = false;
  formData.value.auth_config.oauth2_personal_client_enabled = false;
};

const handleAuthVerifiedRequiredChange = (value: boolean) => {
  if (!value) {
    resetOauth2Switch();
  }
};

// 监听表单校验时间，收集 #id
const setInvalidPropId = (property: string, result: boolean) => {
  if (!result) {
    invalidFormElementIds.value.push(`base-info-${property}`);
  }
};

const validate = async () => {
  invalidFormElementIds.value = [];
  await (formRef.value as any)?.validate();
};

init();

defineExpose({
  formData,
  invalidFormElementIds,
  validate,
});
</script>

<style lang="scss" scoped>
.resource-basic-info {

  .desc,
  .name {
    max-width: 700px;
  }

  .public-switch {
    display: flex;
    align-items: center;
  }

  .auth-config {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-width: 700px;
  }

  .auth-block {
    display: flex;
    flex-direction: column;
    padding: 16px;
    background: #f5f7fa;
    border-radius: 2px;

    :deep(.bk-checkbox) {
      display: flex;
      align-items: center;
      height: auto;
      min-height: 0;
      line-height: 22px;
    }

    :deep(.bk-checkbox-label) {
      line-height: 22px;
    }
  }

  .auth-field {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .auth-hint {
      padding-left: 22px;
    }
  }

  .auth-hint {
    margin: 0;
    font-size: 12px;
    line-height: 18px;
    color: #979ba5;
  }

  .auth-child {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 0 0 0 8px;
    margin-top: 16px;
    margin-left: 22px;
    border-left: 4px solid #dcdee5;

    &.is-disabled .auth-child-row {
      opacity: 50%;
    }
  }

  .auth-child-row {
    display: flex;
    gap: 16px;
    align-items: center;
  }

  .auth-child-label {
    font-size: 14px;
    line-height: 22px;
    color: #63656e;
  }

  .label-label {

    :deep(.bk-form-label) {
      margin-top: 4px;
    }
  }
}
</style>
