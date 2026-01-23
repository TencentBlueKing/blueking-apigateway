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

interface IState {
  flags: FlagType
  showNoticeAlert: boolean
  showComManagement: boolean
}

export const useFeatureFlag = defineStore('useFeatureFlag', {
  state: (): IState => ({
    flags: {
      ALLOW_CREATE_APPCHAT: false,
      ALLOW_UPLOAD_SDK_TO_REPOSITORY: false,
      ENABLE_AI_COMPLETION: false,
      ENABLE_BK_NOTICE: false,
      ENABLE_DISPLAY_NAME_RENDER: false,
      ENABLE_GATEWAY_OPERATION_STATUS: false,
      ENABLE_HEALTH_CHECK: false,
      ENABLE_MCP_SERVER_PROMPT: false,
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
    showNoticeAlert: false,
    showComManagement: false,
  }),
  getters: {
    apiBaseUrl: () => import.meta.env.VITE_BK_USER_WEB_API_URL || '',
    // 是否开启了多租户模式
    isTenantMode: state => !!state.flags?.ENABLE_MULTI_TENANT_MODE,
    // 是否需要展示display_name
    isEnableDisplayName: state => !!state.flags?.ENABLE_DISPLAY_NAME_RENDER,
    // 是否启用了 AI 问答和翻译功能
    isAIEnabled: state => state.flags?.ENABLE_AI_COMPLETION,
    // 是否开启了通知组件展示
    isEnabledNotice: state => state.showNoticeAlert,
    // 是否显示组件管理
    isEnableComManagement: state => state.showComManagement,
  },
  actions: {
    async fetchFlags() {
      this.flags = await getFeatureFlags({
        limit: 10000,
        offset: 0,
      });
    },
    setNoticeAlert(isShow: boolean) {
      this.showNoticeAlert = isShow;
    },
    setDisplayComManagement(isShow: boolean) {
      this.showComManagement = isShow;
    },
  },
});
