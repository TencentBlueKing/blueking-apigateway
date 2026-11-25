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

import { describe, expect, it } from 'vitest';
import {
  DEFAULT_AUTH_CONFIG,
  applyAuthKind,
  applyUserAuthMethods,
  canAllowApplyPermission,
  canConfigureResourcePerm,
  getAuthKind,
  getAuthTypeLabel,
  getResourceAuthFilterOptions,
  getUserAuthMethodLabels,
  getUserAuthMethods,
  getUserAuthMethodsLabel,
  isAuthConfigEmpty,
  normalizeAuthConfig,
  parseAuthTypeQuery,
  parseResourceAuthConfig,
} from '@/utils/auth-config';

const t = (key: string) => key;

describe('utils/auth-config', () => {
  describe('parseResourceAuthConfig', () => {
    it('支持解析合法对象与 JSON 字符串，拒绝数组、原始值与非法 JSON', () => {
      expect(parseResourceAuthConfig({ auth_verified_required: true })).toEqual({ auth_verified_required: true });
      expect(parseResourceAuthConfig('{"app_verified_required":false}')).toEqual({ app_verified_required: false });
      expect(parseResourceAuthConfig('[1,2]')).toBeNull();
      expect(parseResourceAuthConfig('"plain"')).toBeNull();
      expect(parseResourceAuthConfig('{invalid')).toBeNull();
      expect(parseResourceAuthConfig(null)).toBeNull();
      expect(parseResourceAuthConfig(undefined)).toBeNull();
    });
  });

  describe('getUserAuthMethods & getUserAuthMethodLabels', () => {
    it('未开启用户认证时返回空列表', () => {
      expect(getUserAuthMethods({
        auth_verified_required: false,
        app_verified_required: true,
        oauth2_personal_client_enabled: true,
        oauth2_public_client_enabled: true,
      })).toEqual([]);
    });

    it('按固定顺序返回已开启的用户认证方式及对应文案', () => {
      const config = {
        auth_verified_required: true,
        oauth2_personal_client_enabled: true,
        oauth2_public_client_enabled: true,
        app_verified_required: true,
      };
      expect(getUserAuthMethods(config)).toEqual(['personal', 'public', 'oauth']);
      expect(getUserAuthMethodLabels(config, t)).toEqual(['个人令牌', '公开客户端', 'OAuth 授权']);
    });
  });

  describe('getAuthKind & applyUserAuthMethods & applyAuthKind', () => {
    it('准确推导认证大类', () => {
      expect(getAuthKind({ auth_verified_required: true })).toBe('user');
      expect(getAuthKind({
        auth_verified_required: false,
        app_verified_required: true,
      })).toBe('app');
      expect(getAuthKind({
        auth_verified_required: false,
        app_verified_required: false,
      })).toBe('');
      expect(getAuthKind(null)).toBe('');
    });

    it('切换用户认证方式时联动 app_verified_required 与 resource_perm_required', () => {
      // 从无应用认证切换到包含 oauth 时，默认自动开启资源权限校验
      const base = {
        ...DEFAULT_AUTH_CONFIG,
        app_verified_required: false,
        resource_perm_required: false,
      };
      expect(applyUserAuthMethods(base, ['personal', 'oauth'])).toEqual({
        auth_verified_required: true,
        app_verified_required: true,
        resource_perm_required: true,
        oauth2_personal_client_enabled: true,
        oauth2_public_client_enabled: false,
      });

      // 已开启应用认证且用户显式关闭了资源权限校验时，保留 false
      const keepPermFalse = {
        ...DEFAULT_AUTH_CONFIG,
        app_verified_required: true,
        resource_perm_required: false,
      };
      expect(applyUserAuthMethods(keepPermFalse, ['oauth']).resource_perm_required).toBe(false);

      // 不包含 oauth 时关闭应用认证与资源权限校验
      expect(applyUserAuthMethods(DEFAULT_AUTH_CONFIG, ['public'])).toEqual({
        auth_verified_required: true,
        app_verified_required: false,
        resource_perm_required: false,
        oauth2_personal_client_enabled: false,
        oauth2_public_client_enabled: true,
      });
    });

    it('applyAuthKind 在大类未变化时返回原引用，变化时正确重置关联字段', () => {
      expect(applyAuthKind(DEFAULT_AUTH_CONFIG, 'user')).toBe(DEFAULT_AUTH_CONFIG);

      const appConfig = applyAuthKind(DEFAULT_AUTH_CONFIG, 'app');
      expect(appConfig).toEqual({
        auth_verified_required: false,
        app_verified_required: true,
        resource_perm_required: true,
        oauth2_personal_client_enabled: false,
        oauth2_public_client_enabled: false,
      });

      const noneConfig = applyAuthKind(appConfig, '');
      expect(noneConfig).toEqual({
        auth_verified_required: false,
        app_verified_required: false,
        resource_perm_required: false,
        oauth2_personal_client_enabled: false,
        oauth2_public_client_enabled: false,
      });

      expect(applyAuthKind(noneConfig, 'user', ['personal'])).toEqual({
        auth_verified_required: true,
        app_verified_required: false,
        resource_perm_required: false,
        oauth2_personal_client_enabled: true,
        oauth2_public_client_enabled: false,
      });
    });
  });

  describe('normalizeAuthConfig & 权限/展示辅助函数', () => {
    it('归一化时清理不合法的联动开关组合', () => {
      expect(normalizeAuthConfig()).toEqual(DEFAULT_AUTH_CONFIG);
      expect(normalizeAuthConfig({
        auth_verified_required: false,
        app_verified_required: false,
        resource_perm_required: true,
        oauth2_personal_client_enabled: true,
        oauth2_public_client_enabled: true,
      })).toEqual({
        auth_verified_required: false,
        app_verified_required: false,
        resource_perm_required: false,
        oauth2_personal_client_enabled: false,
        oauth2_public_client_enabled: false,
      });
    });

    it('正确区分 v1 与 v2 的认证类型文案与方式文案', () => {
      const both = {
        auth_verified_required: true,
        app_verified_required: true,
        oauth2_personal_client_enabled: true,
      };
      expect(getAuthTypeLabel(both, t, false)).toBe('用户认证、应用认证');
      expect(getAuthTypeLabel(both, t, true)).toBe('用户认证');
      expect(getAuthTypeLabel({
        auth_verified_required: false,
        app_verified_required: true,
      }, t, true)).toBe('应用认证');
      expect(getAuthTypeLabel({
        auth_verified_required: false,
        app_verified_required: false,
      }, t, true)).toBe('不认证');
      expect(getAuthTypeLabel({}, t, true)).toBe('--');
      expect(getAuthTypeLabel(null, t, true)).toBe('--');

      expect(getUserAuthMethodsLabel(both, t, true)).toBe('个人令牌、OAuth 授权');
      expect(getUserAuthMethodsLabel({ auth_verified_required: false }, t, true)).toBe('--');
      expect(getUserAuthMethodsLabel(both, t, false)).toBe('开启');
      expect(getUserAuthMethodsLabel({ oauth2_personal_client_enabled: false }, t, false)).toBe('关闭');
      expect(getUserAuthMethodsLabel(null, t, false)).toBe('--');
    });

    it('正确判定空认证、可配置资源权限及可申请应用权限', () => {
      expect(isAuthConfigEmpty({
        auth_verified_required: false,
        app_verified_required: false,
      })).toBe(true);
      expect(isAuthConfigEmpty({ auth_verified_required: false })).toBe(false);

      expect(canConfigureResourcePerm({ app_verified_required: true })).toBe(true);
      expect(canConfigureResourcePerm({ app_verified_required: false })).toBe(false);

      expect(canAllowApplyPermission(true, {
        app_verified_required: true,
        resource_perm_required: true,
      })).toBe(true);
      expect(canAllowApplyPermission(false, {
        app_verified_required: true,
        resource_perm_required: true,
      })).toBe(false);
      expect(canAllowApplyPermission(true, {
        app_verified_required: true,
        resource_perm_required: false,
      })).toBe(false);
    });
  });

  describe('getResourceAuthFilterOptions & parseAuthTypeQuery', () => {
    it('按约定顺序返回 5 项认证方式筛选选项及区分认证大类的文案', () => {
      expect(getResourceAuthFilterOptions(t)).toEqual([
        {
          id: 'app',
          name: '应用认证',
        },
        {
          id: 'personal',
          name: '用户认证-个人令牌',
        },
        {
          id: 'public',
          name: '用户认证-公开客户端',
        },
        {
          id: 'oauth',
          name: '用户认证-OAuth 授权',
        },
        {
          id: 'none',
          name: '不认证',
        },
      ]);
    });

    it('解析字符串与数组形式的 auth_type 参数，自动去重、去空白并过滤非法值', () => {
      expect(parseAuthTypeQuery('personal,public')).toEqual(['personal', 'public']);
      expect(parseAuthTypeQuery(' oauth , app , invalid , oauth , , none ')).toEqual(['oauth', 'app', 'none']);
      expect(parseAuthTypeQuery(['personal,public', 'public', 'unknown', 'app'])).toEqual([
        'personal',
        'public',
        'app',
      ]);
      expect(parseAuthTypeQuery('')).toEqual([]);
      expect(parseAuthTypeQuery('invalid,foo')).toEqual([]);
      expect(parseAuthTypeQuery(null)).toEqual([]);
      expect(parseAuthTypeQuery(undefined)).toEqual([]);
      expect(parseAuthTypeQuery(123)).toEqual([]);
    });
  });
});
