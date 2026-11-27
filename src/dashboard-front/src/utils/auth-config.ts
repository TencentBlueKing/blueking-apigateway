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

import type { IAuthConfig, IResourceAuthFormConfig } from '@/types/resource';

type ResourceAuthInput = Partial<IAuthConfig> | string | null | undefined;
type Translate = (key: string) => string;
export type UserAuthMethod = 'personal' | 'public' | 'oauth';
export type AuthKind = 'user' | 'app' | '';
export type ResourceAuthFilterType = UserAuthMethod | 'app' | 'none';

export interface IResourceAuthFilterOption {
  id: ResourceAuthFilterType
  name: string
}

export const RESOURCE_AUTH_FILTER_TYPES: readonly ResourceAuthFilterType[] = [
  'app',
  'personal',
  'public',
  'oauth',
  'none',
];

const RESOURCE_AUTH_FILTER_TYPE_SET = new Set<string>(RESOURCE_AUTH_FILTER_TYPES);

const RESOURCE_AUTH_FILTER_LABELS: Record<ResourceAuthFilterType, string> = {
  app: '应用认证',
  personal: '用户认证-个人令牌',
  public: '用户认证-公开客户端',
  oauth: '用户认证-OAuth2 授权',
  none: '不认证',
};

export const DEFAULT_AUTH_CONFIG: IResourceAuthFormConfig = {
  auth_verified_required: true,
  app_verified_required: true,
  resource_perm_required: true,
  oauth2_personal_client_enabled: false,
  oauth2_public_client_enabled: false,
};

export const parseResourceAuthConfig = (input: ResourceAuthInput): Partial<IAuthConfig> | null => {
  try {
    const config = typeof input === 'string' ? JSON.parse(input) : input;
    return config && typeof config === 'object' && !Array.isArray(config) ? config : null;
  }
  catch {
    return null;
  }
};

export const getUserAuthMethods = (input: ResourceAuthInput): UserAuthMethod[] => {
  const config = parseResourceAuthConfig(input);
  if (!config?.auth_verified_required) return [];

  const methods: UserAuthMethod[] = [];
  if (config.oauth2_personal_client_enabled) methods.push('personal');
  if (config.oauth2_public_client_enabled) methods.push('public');
  if (config.app_verified_required) methods.push('oauth');
  return methods;
};

export const canConfigureResourcePerm = (input: ResourceAuthInput): boolean =>
  !!parseResourceAuthConfig(input)?.app_verified_required;

/**
 * 判断资源的「校验应用权限」是否实际生效（需同时开启应用认证与校验应用权限）。
 * 缺失 `app_verified_required` 时与 `canConfigureResourcePerm` 保持一致，按未生效处理。
 */
export const isResourcePermEffective = (input: ResourceAuthInput): boolean => {
  const config = parseResourceAuthConfig(input);
  return Boolean(config?.app_verified_required && config.resource_perm_required);
};

export const getAuthKind = (config: Partial<IAuthConfig> | null | undefined): AuthKind => {
  if (config?.auth_verified_required) return 'user';
  if (config?.app_verified_required) return 'app';
  return '';
};

export const applyUserAuthMethods = (
  config: IResourceAuthFormConfig,
  methods: UserAuthMethod[],
): IResourceAuthFormConfig => {
  const useOAuth = methods.includes('oauth');
  return {
    ...config,
    auth_verified_required: true,
    app_verified_required: useOAuth,
    resource_perm_required: useOAuth && (!config.app_verified_required || config.resource_perm_required),
    oauth2_personal_client_enabled: methods.includes('personal'),
    oauth2_public_client_enabled: methods.includes('public'),
  };
};

export const applyAuthKind = (
  config: IResourceAuthFormConfig,
  kind: AuthKind,
  userMethods: UserAuthMethod[] = ['oauth'],
): IResourceAuthFormConfig => {
  if (kind === getAuthKind(config)) return config;
  if (kind === 'user') return applyUserAuthMethods(config, userMethods);
  const requireApp = kind === 'app';
  return {
    ...config,
    auth_verified_required: false,
    app_verified_required: requireApp,
    resource_perm_required: requireApp && (!config.app_verified_required || config.resource_perm_required),
    oauth2_personal_client_enabled: false,
    oauth2_public_client_enabled: false,
  };
};

export const normalizeAuthConfig = (input?: ResourceAuthInput): IResourceAuthFormConfig => {
  const parsed = parseResourceAuthConfig(input);
  const authVerified = parsed?.auth_verified_required ?? DEFAULT_AUTH_CONFIG.auth_verified_required;
  const appVerified = parsed?.app_verified_required ?? DEFAULT_AUTH_CONFIG.app_verified_required;
  const resourcePerm = parsed?.resource_perm_required ?? DEFAULT_AUTH_CONFIG.resource_perm_required;
  return {
    auth_verified_required: Boolean(authVerified),
    app_verified_required: Boolean(appVerified),
    resource_perm_required: Boolean(appVerified && resourcePerm),
    oauth2_personal_client_enabled: Boolean(authVerified && parsed?.oauth2_personal_client_enabled),
    oauth2_public_client_enabled: Boolean(authVerified && parsed?.oauth2_public_client_enabled),
  };
};

export const isAuthConfigEmpty = (input: ResourceAuthInput): boolean => {
  const config = parseResourceAuthConfig(input);
  return config?.auth_verified_required === false && config.app_verified_required === false;
};

export const getAuthTypeLabel = (input: ResourceAuthInput, t: Translate, isV2: boolean): string => {
  const config = parseResourceAuthConfig(input);
  if (!config) return '--';
  if (!isV2 && config.auth_verified_required && config.app_verified_required) {
    return [t('用户认证'), t('应用认证')].join('、');
  }
  if (config.auth_verified_required) return t('用户认证');
  if (config.app_verified_required) return t('应用认证');
  return isAuthConfigEmpty(config) ? t('不认证') : '--';
};

const USER_AUTH_METHOD_LABELS = {
  personal: '个人令牌',
  public: '公开客户端',
  oauth: 'OAuth2 授权',
} as const;

export const getUserAuthMethodLabels = (input: ResourceAuthInput, t: Translate): string[] =>
  getUserAuthMethods(input).map(method => t(USER_AUTH_METHOD_LABELS[method]));

export const getUserAuthMethodsLabel = (input: ResourceAuthInput, t: Translate, isV2: boolean): string => {
  if (isV2) return getUserAuthMethodLabels(input, t).join('、') || '--';
  const config = parseResourceAuthConfig(input);
  if (!config) return '--';
  return config.oauth2_personal_client_enabled ? t('开启') : t('关闭');
};

export const canAllowApplyPermission = (isPublic: boolean, input: ResourceAuthInput): boolean => {
  const config = parseResourceAuthConfig(input);
  return Boolean(isPublic && config?.app_verified_required && config.resource_perm_required);
};

// 资源列表「认证方式」筛选选项（区分应用认证、用户认证子方式与不认证）
export const getResourceAuthFilterOptions = (t: Translate): IResourceAuthFilterOption[] =>
  RESOURCE_AUTH_FILTER_TYPES.map(id => ({
    id,
    name: t(RESOURCE_AUTH_FILTER_LABELS[id]),
  }));

// 解析 URL 或筛选器中的 auth_type 参数，过滤非法取值并保持原顺序去重
export const parseAuthTypeQuery = (input: unknown): ResourceAuthFilterType[] => {
  const rawValues = Array.isArray(input)
    ? input.flatMap(item => (typeof item === 'string' ? item.split(',') : []))
    : typeof input === 'string'
      ? input.split(',')
      : [];

  const result: ResourceAuthFilterType[] = [];
  const seen = new Set<ResourceAuthFilterType>();
  rawValues.forEach((item) => {
    const normalized = item.trim();
    if (!RESOURCE_AUTH_FILTER_TYPE_SET.has(normalized)) return;
    const authType = normalized as ResourceAuthFilterType;
    if (!seen.has(authType)) {
      seen.add(authType);
      result.push(authType);
    }
  });
  return result;
};
