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
  <div
    class="auth-config"
    :class="{ 'is-compact': compact }"
  >
    <BkAlert
      v-if="!authConfig.app_verified_required && !authConfig.auth_verified_required"
      theme="warning"
      class="mb-12px"
      :title="t('当前不校验应用身份和用户身份，调用无需认证即可通过，请确认这是预期配置。')"
    />
    <div class="auth-block">
      <div class="auth-field">
        <BkCheckbox
          v-model="appRequired"
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
        :class="{ 'is-disabled': !authConfig.app_verified_required }"
      >
        <div class="auth-child-row">
          <span class="auth-child-label">{{ t('检验应用权限') }}</span>
          <BkSwitcher
            :model-value="authConfig.resource_perm_required"
            :disabled="!canEditAppAuth || !authConfig.app_verified_required"
            theme="primary"
            size="small"
            @change="(required: boolean) => updateAuthConfig({ resource_perm_required: required })"
          />
        </div>
        <p class="auth-hint">
          {{ authConfig.app_verified_required
            ? t('开启后，蓝鲸应用必须已获得本资源访问权限才能调用。')
            : t('依赖「应用认证」。先勾选应用认证后才能开启。') }}
        </p>
      </div>
    </div>
    <div class="auth-block">
      <div class="auth-field">
        <BkCheckbox v-model="userRequired">
          {{ t('用户认证') }}
        </BkCheckbox>
        <p class="auth-hint">
          {{ t('校验调用代表哪个用户。开启后，调用必须携带用户身份（登录态或 AccessToken）。') }}
        </p>
      </div>
      <div
        class="auth-child"
        :class="{ 'is-disabled': !authConfig.auth_verified_required }"
      >
        <div class="auth-child-row">
          <span class="auth-child-label">{{ t('个人令牌') }}</span>
          <BkSwitcher
            :model-value="authConfig.oauth2_personal_client_enabled"
            :disabled="!authConfig.auth_verified_required"
            theme="primary"
            size="small"
            @change="(enabled: boolean) => updateAuthConfig({ oauth2_personal_client_enabled: enabled })"
          />
        </div>
        <p class="auth-hint">
          {{ authConfig.auth_verified_required
            ? t('开启后，用户可以用个人令牌调用本接口，请求会带上该用户的身份。')
            : t('依赖「用户认证」。先勾选用户认证后才能开启。') }}
          <BkButton
            v-if="personalTokenLink"
            size="small"
            theme="primary"
            text
            class="text-12px! ml-8px"
            @click="openPersonalTokenDoc"
          >
            {{ t('查看文档') }}
          </BkButton>
        </p>
      </div>
    </div>
    <BkAlert
      :theme="!appRequired && !userRequired ? 'warning' : 'info'"
      :title="authSceneText"
    />
  </div>
</template>

<script lang="ts" setup>
import { useEnv } from '@/stores';
import type { IResourceAuthFormConfig } from '@/types/resource';

interface IProps {
  canEditAppAuth?: boolean
  compact?: boolean
}

const authConfig = defineModel<IResourceAuthFormConfig>('authConfig', { required: true });
const { canEditAppAuth = true, compact = false } = defineProps<IProps>();

const envStore = useEnv();
const { t } = useI18n();
let previousResourcePermission = false;

const appRequired = computed({
  get: () => authConfig.value.app_verified_required,
  set: (enabled: boolean) => {
    if (!enabled) previousResourcePermission = authConfig.value.resource_perm_required;
    updateAuthConfig({
      app_verified_required: enabled,
      resource_perm_required: enabled && previousResourcePermission,
    });
  },
});

const userRequired = computed({
  get: () => authConfig.value.auth_verified_required,
  set: (enabled: boolean) => {
    updateAuthConfig({
      auth_verified_required: enabled,
      oauth2_personal_client_enabled: enabled && authConfig.value.oauth2_personal_client_enabled,
      oauth2_public_client_enabled: enabled && authConfig.value.oauth2_public_client_enabled,
    });
  },
});

const personalTokenLink = computed(() => envStore.env.DOC_LINKS.AUTH_PERSONAL_TOKEN);
const authSceneText = computed(() => {
  const appAuth = authConfig.value.app_verified_required;
  const userAuth = authConfig.value.auth_verified_required;
  const permRequired = authConfig.value.resource_perm_required;
  const personalEnabled = authConfig.value.oauth2_personal_client_enabled;

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

const updateAuthConfig = (patch: Partial<IResourceAuthFormConfig>) => {
  authConfig.value = {
    ...authConfig.value,
    ...patch,
  };
};

const openPersonalTokenDoc = () => window.open(personalTokenLink.value, '_blank');
</script>

<style lang="scss" scoped>
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

.is-compact {

  .auth-hint,
  :deep(.bk-alert) {
    display: none;
  }

  .auth-block {
    padding: 8px 12px;
  }

  .auth-child {
    margin-top: 4px;
  }
}
</style>
