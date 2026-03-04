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
  <div class="oauth-alert-wrapper">
    <div
      :style="renderAlertStyles"
      class="pt-12px pb-16px"
    >
      <div
        v-if="!appAuthStatusList.length"
        class="color-#299e56 text-12px "
      >
        <div class="font-700 px-30px">
          <AgIcon
            name="check-circle-shape"
            size="12"
          />
          <span class="ml-8px">{{ t('无安全风险') }}</span>
        </div>
        <div class="mt-12px pl-50px">
          {{ t('当前已选择的工具均为「用户态」鉴权，开启 OAuth2 公开客户端模式不会产生额外安全风险。每个用户仍需通过 OAuth2 授权验证身份后才能调用。') }}
        </div>
      </div>
      <div
        v-else
        class="color-#e71818 text-12px"
      >
        <div class="font-700 px-26px">
          <AgIcon
            name="zhiming"
            size="16"
          />
          <span class="ml-8px">{{ t('存在安全风险 — 请谨慎评估') }}</span>
        </div>
        <div class="mt-12px pl-50px pr-24px">
          <div class="lh-20px mb-6px">
            {{ t('当前已选择的工具均为「用户态」鉴权，开启 OAuth2 公开客户端模式不会产生额外安全风险。每个用户仍需通过 OAuth2 授权验证身份后才能调用。') }}
          </div>
          <div class="lh-20px mb-6px">
            <span class="oauth-alter-circle" />
            <span>{{ t('开启 OAuth2 公开客户端模式后，这些工具将通过 public 应用身份调用，所有通过 OAuth2 授权的用户均可调用，原有的应用级权限隔离将不再生效。') }}</span>
          </div>
          <div class="lh-20px mb-6px">
            <span class="oauth-alter-circle" />
            <span>{{ t('仅包含应用态鉴权（无用户态）的工具风险最高，任何人授权后即可调用。') }}</span>
          </div>
          <div class="flex items-baseline lh-20px">
            <div :class="`font-700 min-w-${locale.indexOf('zh-cn') > -1 ? 88 : 100}px`">
              {{ t('受影响的工具：') }}
            </div>
            <div class="break-all">
              {{ renderToolData }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { locale, t } from '@/locales';
import { type IMCPServerTool } from '@/services/source/mcp-server';

interface IProps { appAuthStatusList?: IMCPServerTool[] }

const { appAuthStatusList = [] } = defineProps<IProps>();

const renderAlertStyles = computed(() => {
  // 应用态数据样式
  if (appAuthStatusList.length) {
    return {
      border: '1px solid #f8b4b4',
      backgroundColor: '#fff0f0',
    };
  }

  return {
    border: '1px solid #a1e3ba',
    backgroundColor: '#ebfaf0',
  };
});
const renderToolData = computed(() => {
  const results = appAuthStatusList.map((item) => {
    if (item.contexts?.resource_auth?.config?.length) {
      const authConfig = JSON.parse(item.contexts?.resource_auth?.config);
      if (authConfig?.auth_verified_required && !authConfig?.app_verified_required) {
        return { name: `${item.name} (${t('仅用户态')})` };
      }
      if (!authConfig?.auth_verified_required && authConfig?.app_verified_required) {
        return { name: `${item.name} (${t('仅应用态')})` };
      }
      if (authConfig?.auth_verified_required && authConfig?.app_verified_required) {
        return { name: `${item.name} (${t('应用态 + 用户态')})` };
      }
    }
    return item;
  });
  return results.map(item => item.name).join('、');
});
</script>

<style lang="scss" scoped>
.oauth-alter-circle {
  display: inline-block;
  width: 4px;
  height: 4px;
  vertical-align: middle;
  background-color: #ea3636;
  border-radius: 50%;
  margin-right: 4px;
}
</style>
