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
    class="resource-auth-selector"
    :class="{ 'is-compact': compact }"
  >
    <DefinePermissionRow>
      <div class="auth-followup-row">
        <span>{{ t('校验应用权限') }}</span>
        <BkSwitcher
          :model-value="resourcePermRequired"
          theme="primary"
          size="small"
          @change="setResourcePermRequired"
        />
        <p class="auth-hint">
          {{ resourcePermHint }}
          <BkButton
            v-if="resourcePermRequired"
            size="small"
            theme="primary"
            text
            class="auth-doc-link text-12px! ml-8px"
            @click.stop="handleViewPermGuide"
          >
            {{ t('权限申请指引') }}
            <AgIcon
              name="jump"
              size="12"
              class="ml-4px"
            />
          </BkButton>
        </p>
      </div>
    </DefinePermissionRow>

    <BkRadioGroup
      v-model="selectedAuthOption"
      class="auth-options"
    >
      <div class="auth-option-row">
        <div
          class="auth-option"
          :class="{ 'is-active': selectedAuthKind === 'user' }"
          @click="handleSelectKind('user')"
        >
          <div class="auth-option-title">
            <BkRadio label="user">
              {{ t('用户认证') }}
            </BkRadio>
            <BkButton
              v-if="personalTokenLink"
              size="small"
              theme="primary"
              text
              class="auth-doc-link text-12px!"
              @click.stop="handleViewDoc"
            >
              {{ t('查看文档') }}
              <AgIcon
                name="jump"
                size="12"
                class="ml-4px"
              />
            </BkButton>
          </div>
          <p class="auth-hint auth-option-hint">
            <span
              v-bk-overflow-tips
              class="auth-option-hint-text"
            >
              {{ t('适用于需识别调用用户的接口') }}
            </span>
          </p>
        </div>
        <div
          class="auth-option"
          :class="{ 'is-active': selectedAuthKind === 'app' }"
          @click="handleSelectKind('app')"
        >
          <BkRadio label="app">
            {{ t('应用认证') }}
          </BkRadio>
          <p class="auth-hint auth-option-hint">
            <span
              v-bk-overflow-tips
              class="auth-option-hint-text"
            >
              {{ t('适用于需校验应用身份的接口') }}
            </span>
          </p>
        </div>
        <div
          v-bk-tooltips="{
            content: t('当前网关不允许设置为不认证'),
            disabled: allowNoAuth,
          }"
          class="auth-option"
          :class="{
            'is-active': selectedAuthOption === 'none',
            'is-disabled': !allowNoAuth,
          }"
          @click="handleSelectKind('')"
        >
          <BkRadio
            label="none"
            :disabled="!allowNoAuth"
          >
            {{ t('不认证') }}
          </BkRadio>
          <p class="auth-hint auth-option-hint">
            <span
              v-bk-overflow-tips
              class="auth-option-hint-text"
            >
              {{ t('适用于完全公开的接口') }}
            </span>
          </p>
        </div>
      </div>
      <div
        v-if="selectedAuthKind === 'user'"
        class="auth-extra"
        @click.stop
      >
        <BkCheckboxGroup
          v-model="selectedUserAuthMethods"
          class="auth-method-group"
        >
          <div
            v-for="option in userAuthOptions"
            :key="option.value"
            class="auth-method-item"
          >
            <div class="auth-method-main">
              <BkCheckbox
                :label="option.value"
                :before-change="option.value === 'oauth' ? beforeOAuthChange : undefined"
              >
                {{ option.label }}
              </BkCheckbox>
              <p
                v-bk-overflow-tips
                class="auth-hint"
              >
                {{ option.hint }}
              </p>
            </div>
            <div
              v-if="option.value === 'oauth' && oauthEnabled"
              class="auth-followup"
            >
              <ReusePermissionRow />
            </div>
          </div>
        </BkCheckboxGroup>
      </div>

      <div
        v-if="selectedAuthKind === 'app'"
        class="auth-extra"
        @click.stop
      >
        <ReusePermissionRow />
      </div>
    </BkRadioGroup>

    <BkAlert
      v-if="isAuthEmpty"
      theme="warning"
      :title="t('网关不校验调用方身份，请确认接口可以完全公开。')"
    />
  </div>
</template>

<script lang="ts" setup>
import { createReusableTemplate } from '@vueuse/core';
import { usePopInfoBox } from '@/hooks';
import { useEnv } from '@/stores';
import type { IResourceAuthFormConfig } from '@/types/resource';
import {
  type AuthKind,
  type UserAuthMethod,
  applyAuthKind,
  applyUserAuthMethods,
  getAuthKind,
  getUserAuthMethods,
  isAuthConfigEmpty,
} from '@/utils/auth-config';

interface IProps {
  compact?: boolean
  allowNoAuth?: boolean
  hasSavedAuthorization?: boolean
}

const authConfig = defineModel<IResourceAuthFormConfig>('authConfig', {
  type: Object,
  required: true,
});

const {
  compact = false,
  allowNoAuth = true,
  hasSavedAuthorization = false,
} = defineProps<IProps>();

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const envStore = useEnv();
const [DefinePermissionRow, ReusePermissionRow] = createReusableTemplate();

const userAuthOptions = computed(() => [
  {
    value: 'personal' as const,
    label: t('个人令牌'),
    hint: t('适用于脚本、CI 和本地工具，以指定用户身份调用接口。'),
  },
  {
    value: 'public' as const,
    label: t('公开客户端'),
    hint: t('适用于 Cursor 等 MCP 客户端，任意客户端都可以调用，仅建议用于可公开接口。'),
  },
  {
    value: 'oauth' as const,
    label: t('OAuth 授权'),
    hint: t('适用于蓝鲸应用代用户访问。用户完成登录授权后，应用即可使用该用户身份调用。'),
  },
]);

const userAuthMethods = computed<UserAuthMethod[]>(() => getUserAuthMethods(authConfig.value));
const pendingOAuthRemoval = shallowRef<(confirmed: boolean) => void>();
const lastUserAuthMethods = ref<UserAuthMethod[]>(['oauth']);
const selectedUserAuthMethods = computed<UserAuthMethod[]>({
  get: () => userAuthMethods.value,
  set: (methods: UserAuthMethod[]) => {
    authConfig.value = applyUserAuthMethods(authConfig.value, methods);
  },
});
const selectedAuthKind = computed<AuthKind>({
  get: () => getAuthKind(authConfig.value),
  set: (kind: AuthKind) => {
    if (kind === '' && !allowNoAuth) {
      return;
    }
    authConfig.value = applyAuthKind(authConfig.value, kind, lastUserAuthMethods.value);
  },
});
const selectedAuthOption = computed<AuthKind | 'none'>({
  get: () => selectedAuthKind.value || 'none',
  set: (option) => {
    selectedAuthKind.value = option === 'none' ? '' : option;
  },
});
const personalTokenLink = computed(() => envStore.env.DOC_LINKS.AUTH_PERSONAL_TOKEN);
const oauthEnabled = computed(() => userAuthMethods.value.includes('oauth'));
const resourcePermRequired = computed(() => !!authConfig.value.resource_perm_required);
const isAuthEmpty = computed(() => isAuthConfigEmpty(authConfig.value));
const resourcePermHint = computed(() => {
  if (resourcePermRequired.value) {
    return t('开启后，应用需先申请资源权限，通过后才能调用。');
  }
  return selectedAuthKind.value === 'user'
    ? t('关闭后，任意蓝鲸应用经用户授权后都可以调用。')
    : t('关闭后，任意蓝鲸应用都可以调用。');
});

watch(userAuthMethods, (methods) => {
  if (selectedAuthKind.value === 'user') {
    lastUserAuthMethods.value = methods;
  }
}, { immediate: true });

const finishOAuthRemoval = (confirmed: boolean) => {
  const resolve = pendingOAuthRemoval.value;
  pendingOAuthRemoval.value = undefined;
  resolve?.(confirmed);
};

// 只有直接取消已保存的 OAuth 授权才需要确认。
const beforeOAuthChange = (checked: boolean | string | number) => {
  if (checked || !hasSavedAuthorization) return true;
  return new Promise<boolean>((resolve) => {
    finishOAuthRemoval(false);
    pendingOAuthRemoval.value = resolve;
    usePopInfoBox({
      isShow: true,
      type: 'warning',
      title: t('确定取消 OAuth 授权？'),
      subTitle: () => h('div', [
        h('div', t('取消 OAuth 授权后，网关不再校验应用 ID、应用密钥。')),
        h('div', { class: 'mt-8px' }, t('已按应用配置的频率限制、权限校验都会失效。')),
      ]),
      confirmText: t('确定取消'),
      cancelText: t('取消'),
      confirmButtonTheme: 'danger',
      onConfirm: () => finishOAuthRemoval(true),
      onCancel: () => finishOAuthRemoval(false),
    });
  });
};

const handleSelectKind = (kind: AuthKind) => {
  selectedAuthKind.value = kind;
};

const setResourcePermRequired = (required: boolean) => {
  authConfig.value = {
    ...authConfig.value,
    resource_perm_required: required,
  };
};

const handleViewDoc = () => {
  window.open(personalTokenLink.value, '_blank');
};

const handleViewPermGuide = () => {
  const doc = envStore.env.DOC_LINKS.AUTH || envStore.env.DOC_LINKS.GUIDE;
  if (doc) {
    window.open(doc, '_blank');
    return;
  }
  const { href } = router.resolve({
    name: 'PermissionApp',
    params: { id: route.params.id },
  });
  window.open(href, '_blank');
};

onBeforeUnmount(() => finishOAuthRemoval(false));
</script>

<style lang="scss" scoped>
.resource-auth-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 700px;

  &.is-compact {
    max-width: none;
  }
}

.auth-doc-link {
  display: inline-flex;
  align-items: center;
}

.auth-option-hint {
  display: flex;
  align-items: center;
  min-width: 0;
}

.auth-option-hint-text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.auth-option-hint .auth-doc-link {
  flex-shrink: 0;
}

:deep(.bk-radio-label),
:deep(.bk-checkbox-label) {
  font-size: 14px;
  line-height: 22px;
  color: #313238;
}

:deep(.bk-checkbox),
:deep(.bk-radio) {
  display: flex;
  align-items: center;
  height: auto;
  min-height: 0;
  margin-bottom: 0;
  line-height: 22px;
}

.auth-option-title {
  display: flex;
  gap: 8px;
  align-items: center;
}

.auth-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.auth-option-row {
  display: flex;
  gap: 12px;
  align-items: stretch;
  width: 100%;
}

.auth-option {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  padding: 14px 16px;
  cursor: pointer;
  background: #fff;
  border: 1px solid #dcdee5;
  border-radius: 2px;
  transition: border-color .2s, background-color .2s;

  &:hover {
    border-color: #a3c5fd;
  }

  &.is-active {
    background: #f5f9ff;
    border-color: #3a84ff;
  }

  &.is-disabled {
    cursor: not-allowed;
    background: #fafbfd;
    border-color: #dcdee5;

    :deep(.bk-radio-label),
    :deep(.bk-checkbox-label) {
      color: #c4c6cc;
    }
  }

  .auth-hint {
    padding-left: 22px;
  }
}

.auth-method-item .auth-method-main {
  display: flex;
  gap: 12px;
  align-items: center;
  min-width: 0;

  :deep(.bk-checkbox) {
    flex-shrink: 0;
  }

  .auth-hint {
    min-width: 0;
    padding-left: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.auth-hint {
  margin: 0;
  font-size: 12px;
  line-height: 18px;
  color: #979ba5;
}

.auth-method-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.auth-method-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: #fff;
  border: 1px solid transparent;
  border-radius: 2px;
  transition: border-color .2s, background-color .2s;

  &:hover {
    border-color: #dcdee5;
  }

  .auth-hint {
    padding-left: 24px;
  }
}

.auth-followup {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  margin-top: 8px;
  margin-left: 24px;
  background: #f5f7fa;
  border-radius: 2px;
}

.auth-extra {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 2px;

  > .auth-hint {
    padding-left: 0;
  }
}

.auth-followup-row {
  display: flex;
  gap: 12px;
  align-items: center;
  min-width: 0;

  > span {
    flex-shrink: 0;
    font-size: 13px;
    line-height: 20px;
    color: #313238;
  }
}

.auth-followup .auth-hint {
  padding-left: 0;
}

</style>
