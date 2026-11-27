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
    :model="formData"
    label-width="180"
    class="resource-auth-config"
  >
    <BkFormItem
      :label="gatewayStore.isResourceAuthV2 ? t('认证类型') : t('认证方式')"
      required
    >
      <ResourceAuthSelector
        v-if="gatewayStore.isResourceAuthV2"
        :key="`v2-${detailRevision}`"
        v-model:auth-config="formData.auth_config"
        :allow-no-auth="canUpdateGatewayAuth"
        :has-saved-authorization="hasSavedOAuth"
      />
      <LegacyResourceAuthSelector
        v-else
        :key="`v1-${detailRevision}`"
        v-model:auth-config="formData.auth_config"
        :can-edit-app-auth="canUpdateGatewayAuth"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('是否公开')"
      :description="t('公开，则用户可查看资源文档、申请资源权限；不公开，则资源对用户隐藏')"
      property="is_public"
      required
    >
      <div class="public-config">
        <div class="public-switch">
          <BkSwitcher
            v-model="formData.is_public"
            theme="primary"
            size="small"
          />
          <span class="public-state">
            {{ formData.is_public ? t('公开') : t('不公开') }}
          </span>
        </div>
        <div
          v-if="canAllowApply || !gatewayStore.isResourceAuthV2"
          class="public-child"
        >
          <div class="public-child-row">
            <span>{{ t('允许申请权限') }}</span>
            <BkSwitcher
              v-model="formData.allow_apply_permission"
              :disabled="!canAllowApply"
              theme="primary"
              size="small"
            />
            <p
              v-bk-overflow-tips
              class="public-hint"
            >
              {{ allowApplyHint }}
            </p>
          </div>
        </div>
      </div>
    </BkFormItem>
  </BkForm>
</template>

<script lang="ts" setup>
import { useGateway } from '@/stores';
import type { IAuthConfig, IPublicConfig } from '@/types/resource';
import { DEFAULT_AUTH_CONFIG, canAllowApplyPermission, getUserAuthMethods, normalizeAuthConfig } from '@/utils/auth-config';
import ResourceAuthSelector from './ResourceAuthSelector.vue';
import LegacyResourceAuthSelector from './LegacyResourceAuthSelector.vue';

interface IProps {
  editingExisting?: boolean
  detail?: (Partial<IPublicConfig> & { auth_config?: Partial<IAuthConfig> | string }) | null
}

const { detail = {}, editingExisting = false } = defineProps<IProps>();

const { t } = useI18n();
const gatewayStore = useGateway();

const formData = ref({
  auth_config: { ...DEFAULT_AUTH_CONFIG },
  is_public: true,
  allow_apply_permission: true,
});
// 每次回显新资源详情时递增，重置子选择器中的临时交互记忆与未决弹窗
const detailRevision = shallowRef(0);

const hasSavedOAuth = computed(() => editingExisting && getUserAuthMethods(detail?.auth_config).includes('oauth'));
const canUpdateGatewayAuth = computed(() => !!gatewayStore.currentGateway?.allow_update_gateway_auth);
const canAllowApply = computed(() => canAllowApplyPermission(formData.value.is_public, formData.value.auth_config));

const allowApplyHint = computed(() => {
  if (gatewayStore.isResourceAuthV2) return t('开启后，蓝鲸应用可在开发者中心申请本资源权限；关闭则仅网关管理员可主动授权。');
  if (!formData.value.is_public) return t('依赖「是否公开」。资源不公开时，用户无法查看接口文档和申请权限。');
  if (!canAllowApply.value) return t('需要开启「检验应用权限」，才可以配置「允许申请权限」。');
  return t('开启后，其他蓝鲸应用可在开发者中心申请本资源访问权限；关闭则只能由网关管理员主动授权。');
});

watch(canAllowApply, (allowed) => {
  if (!allowed) {
    formData.value.allow_apply_permission = false;
  }
});

watch(
  () => detail,
  (resource) => {
    if (resource && Object.keys(resource).length) {
      const isPublic = resource.is_public ?? true;
      const authConfig = normalizeAuthConfig(resource.auth_config);
      formData.value = {
        auth_config: authConfig,
        is_public: isPublic,
        allow_apply_permission: canAllowApplyPermission(isPublic, authConfig)
          && !!resource.allow_apply_permission,
      };
      detailRevision.value += 1;
    }
  },
  { immediate: true },
);

defineExpose({ formData });
</script>

<style lang="scss" scoped>
.resource-auth-config {

  .public-config {
    display: flex;
    flex-direction: column;
    max-width: 700px;
    padding: 16px;
    background: #f5f7fa;
    border-radius: 2px;
  }

  .public-switch {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .public-state {
    font-size: 14px;
    line-height: 22px;
    color: #313238;
  }

  .public-child {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 10px 12px;
    margin-top: 12px;
    margin-left: 4px;
    background: #fff;
    border-radius: 2px;
  }

  .public-child-row {
    display: flex;
    gap: 12px;
    align-items: center;

    > span {
      flex-shrink: 0;
      font-size: 13px;
      line-height: 20px;
      color: #313238;
    }
  }

  .public-hint {
    min-width: 0;
    margin: 0;
    overflow: hidden;
    font-size: 12px;
    line-height: 18px;
    color: #979ba5;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>
