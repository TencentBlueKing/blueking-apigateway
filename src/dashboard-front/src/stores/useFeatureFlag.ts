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
import { defineStore } from 'pinia';

import { getFeatureFlags } from '@/services/source/basic';

type FlagType = Awaited<ReturnType<typeof getFeatureFlags>>;

export const useFeatureFlag = defineStore('useFeatureFlag', {
  state: (): Record<string, FlagType> => ({
    flags: {
      ALLOW_CREATE_APPCHAT: false,
      ALLOW_UPLOAD_SDK_TO_REPOSITORY: false,
      ENABLE_AI_COMPLETION: false,
      ENABLE_BK_NOTICE: false,
      ENABLE_MONITOR: false,
      ENABLE_MULTI_TENANT_MODE: false,
      ENABLE_RUN_DATA: false,
      ENABLE_RUN_DATA_METRICS: false,
      ENABLE_SDK: false,
      GATEWAY_APP_BINDING_ENABLED: false,
      MENU_ITEM_ESB_API: false,
      MENU_ITEM_ESB_API_DOC: false,
      SYNC_ESB_TO_APIGW_ENABLED: false,
    },
  }),
  getters: {
    apiBaseUrl: () => import.meta.env.VITE_BK_USER_WEB_API_URL || '',
    // 是否开启了多租户模式
    isTenantMode: state => !!state.flags?.ENABLE_MULTI_TENANT_MODE,
    // 是否启用了 ai 问答功能
    isAIEnabled: state => state.flags?.ENABLE_AI_COMPLETION,
  },
  actions: {
    async fetchFlags() {
      this.flags = await getFeatureFlags({
        limit: 10000,
        offset: 0,
      });
    },
  },
});
