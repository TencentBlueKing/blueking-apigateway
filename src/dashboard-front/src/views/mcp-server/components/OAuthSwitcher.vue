/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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
    v-show="featureFlagStore?.flags?.ENABLE_MCP_SERVER_OAUTH2_PUBLIC_CLIENT"
    class="flex items-center justify-between oauth-switch-wrapper"
  >
    <div class="flex items-center">
      <AgIcon
        name="oauth2"
        size="42"
        color="#3a84ff"
      />
      <div class="ml-20px">
        <div class="text-14px color-#313238 lh-22px font-700">
          {{ t('OAuth2 公开客户端模式') }}
        </div>
        <div class="text-12px color-#4d4f56 lh-20px">
          {{ t('开启后，用户通过浏览器 OAuth2 授权即可使用，无需手动配置 API 凭证。票据将以 public 公开应用身份签发。') }}
        </div>
      </div>
    </div>
    <BkSwitcher
      v-model="formData.oauth2_public_client_enabled"
      theme="primary"
      @change="handleOAuthChange"
    />
  </div>
</template>

<script lang="ts" setup>
import { t } from '@/locales';
import { useFeatureFlag } from '@/stores';
import type { IMCPFormData } from '@/services/source/mcp-server';

const formData = defineModel<IMCPFormData>('formData', {
  type: Object,
  required: true,
});

const emit = defineEmits<{ oauthChange: [value: boolean] }>();

const featureFlagStore = useFeatureFlag();

const handleOAuthChange = (value: boolean) => {
  emit('oauthChange', value);
};
</script>

<style lang="scss" scoped>
.oauth-switch-wrapper {
  border: 1px solid #dcdee5;
  padding: 18px 24px;
  margin-bottom: 24px;
}
</style>
