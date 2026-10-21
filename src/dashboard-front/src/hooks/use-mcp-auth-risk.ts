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

/**
 * MCP Server 应用态鉴权风险展示组合式函数
 *
 * 风险标识只在「OAuth2 客户端模式已开启」时才有意义：
 * 公开客户端与个人令牌各自受独立的功能开关控制，二者任一开启都需要展示风险，
 * 文案则需要按实际开启的模式区分，避免把未开启 public 的 Server 描述成 public 模式。
 */

import { t } from '@/locales';
import { useFeatureFlag } from '@/stores';

/** 已开启的 OAuth2 客户端模式 */
export type OAuthClientMode = 'public' | 'personal';

interface IRiskServer {
  oauth2_public_client_enabled?: boolean
  oauth2_personal_client_enabled?: boolean
  app_permission_risk?: {
    has_risk?: boolean
    risk_tools?: string[]
  }
}

/** 计算 Server 已开启且对应功能开关允许的 OAuth2 客户端模式 */
function getEnabledOAuthClientModes(
  server: IRiskServer | undefined,
  flags: {
    publicClient?: boolean
    personalClient?: boolean
  },
): OAuthClientMode[] {
  const modes: OAuthClientMode[] = [];
  if (flags?.publicClient && server?.oauth2_public_client_enabled) modes.push('public');
  if (flags?.personalClient && server?.oauth2_personal_client_enabled) modes.push('personal');
  return modes;
}

/** 已开启的 OAuth2 客户端模式组合，both 表示两种模式同时开启 */
type RiskModeKey = OAuthClientMode | 'both';

/** 模式组合 -> 风险概述文案 */
const RISK_SUMMARY_I18N_MAP: Record<RiskModeKey, string> = {
  both: '此 MCP Server 已开启 OAuth2公开客户端与个人令牌模式，且包含{count}个应用态鉴权工具({content})',
  public: '此 MCP Server 已开启 OAuth2公开客户端模式，且包含{count}个应用态鉴权工具({content})',
  personal: '此 MCP Server 已开启个人令牌模式，且包含{count}个应用态鉴权工具({content})',
};

/** 模式 -> 调用身份说明文案 */
const RISK_IDENTITY_I18N_MAP: Record<OAuthClientMode, string> = {
  public: '该工具通过 public 应用身份调用，所有 OAuth2 授权用户均可访问。',
  personal: '该工具通过个人令牌调用，用户授权后即可访问。',
};

export function useMcpAuthRisk() {
  const featureFlagStore = useFeatureFlag();

  // 两个 OAuth2 客户端开关相互独立，任一开启都可能存在应用态鉴权风险
  const oauthClientFlags = computed(() => ({
    publicClient: Boolean(featureFlagStore?.flags?.ENABLE_MCP_SERVER_OAUTH2_PUBLIC_CLIENT),
    personalClient: Boolean(featureFlagStore?.flags?.ENABLE_MCP_SERVER_OAUTH2_PERSONAL_CLIENT),
  }));

  /** 是否展示应用态鉴权风险标识：已开启任一 OAuth2 客户端模式且接口返回存在风险 */
  const hasAppPermissionRisk = (server: IRiskServer | undefined): boolean =>
    getEnabledOAuthClientModes(server, oauthClientFlags.value).length > 0
    && Boolean(server?.app_permission_risk?.has_risk);

  /** 应用态鉴权风险的提示文案，按已开启的模式逐条返回，未开启任何模式时返回空数组 */
  const getAppPermissionRiskTips = (server: IRiskServer | undefined): string[] => {
    const modes = getEnabledOAuthClientModes(server, oauthClientFlags.value);
    if (!modes.length || !server?.app_permission_risk?.has_risk) return [];

    const riskTools = server?.app_permission_risk?.risk_tools ?? [];
    const options = {
      count: riskTools.length,
      content: riskTools.join('、'),
    };

    const modeKey: RiskModeKey = modes.length > 1 ? 'both' : modes[0];

    return [
      t(RISK_SUMMARY_I18N_MAP[modeKey], options),
      ...modes.map(mode => t(RISK_IDENTITY_I18N_MAP[mode])),
    ];
  };

  return {
    hasAppPermissionRisk,
    getAppPermissionRiskTips,
  };
}
