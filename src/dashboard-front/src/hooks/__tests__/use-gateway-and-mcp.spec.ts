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

import { ref } from 'vue';
import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { popInfoBoxMock } = vi.hoisted(() => ({ popInfoBoxMock: vi.fn() }));

const reactiveRouteGatewayId = ref('10');

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: {
      get id() {
        return reactiveRouteGatewayId.value;
      },
    },
  }),
}));
vi.mock('vue-i18n', () => ({ useI18n: () => ({ t: (key: string) => key }) }));
vi.mock('@/locales', () => ({
  t: (key: string, params?: Record<string, any>) =>
    (params ? key.replace(/\{(\w+)\}/g, (_, k) => String(params[k] ?? '')) : key),
}));
vi.mock('@/hooks', () => ({ usePopInfoBox: popInfoBoxMock }));
vi.mock('@/services/source/gateway/member', () => ({ getMyGatewayRole: vi.fn() }));
vi.mock('@/services/source/platform/setting', () => ({ getFeatureFlags: vi.fn() }));

import { useGatewayRole } from '@/hooks/use-gateway-role';
import { useMcpAuthRisk } from '@/hooks/use-mcp-auth-risk';
import { useSidebar } from '@/hooks/use-sidebar';
import { useFeatureFlag } from '@/stores/useFeatureFlag';
import { useGatewayRoleStore } from '@/stores/useGatewayRole';

describe('hooks/use-gateway-role', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    reactiveRouteGatewayId.value = '10';
  });

  it('根据当前路由网关 ID 读取角色状态与权限，并在切换网关时响应式联动', () => {
    const roleStore = useGatewayRoleStore();

    const roleView = useGatewayRole();
    expect(roleView.roleStatus.value).toBe('idle');
    expect(roleView.currentRole.value).toBe('');
    expect(roleView.canEditBasicInfo.value).toBe(false);
    expect(roleView.canAccess('basic-view')).toBe(false);

    roleStore.roles[10] = {
      role: 'operator',
      status: 'ready',
      expiresAt: Date.now() + 60_000,
    };
    roleStore.roles[20] = {
      role: 'administrator',
      status: 'ready',
      expiresAt: Date.now() + 60_000,
    };
    expect(roleView.roleStatus.value).toBe('ready');
    expect(roleView.currentRole.value).toBe('operator');
    expect(roleView.canEditBasicInfo.value).toBe(false);
    expect(roleView.canAccess('basic-view')).toBe(true);
    expect(roleView.canAccess('stage')).toBe(false);

    // 切换路由网关 ID 后响应式切换到网关 20 的管理员角色
    reactiveRouteGatewayId.value = '20';
    expect(roleView.currentRole.value).toBe('administrator');
    expect(roleView.canEditBasicInfo.value).toBe(true);
    expect(roleView.canAccess('stage')).toBe(true);

    const loadErr = new Error('boom');
    roleStore.roles[20] = {
      role: '',
      status: 'error',
      error: loadErr,
    };
    expect(roleView.roleStatus.value).toBe('error');
    expect(roleView.roleError.value).toBe(loadErr);
    expect(roleView.canAccess('basic-view')).toBe(false);
  });
});

describe('hooks/use-mcp-auth-risk', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('结合功能开关与 Server 客户端模式组合，准确计算风险标识与提示文案', () => {
    const flagStore = useFeatureFlag();
    const { hasAppPermissionRisk, getAppPermissionRiskTips } = useMcpAuthRisk();

    const serverBoth = {
      oauth2_public_client_enabled: true,
      oauth2_personal_client_enabled: true,
      app_permission_risk: {
        has_risk: true,
        risk_tools: ['get_user', 'list_orders'],
      },
    };

    // 两个功能开关均关闭时，不提示风险
    expect(hasAppPermissionRisk(serverBoth)).toBe(false);
    expect(getAppPermissionRiskTips(serverBoth)).toEqual([]);

    // 仅开启 public 开关
    flagStore.flags.ENABLE_MCP_SERVER_OAUTH2_PUBLIC_CLIENT = true;
    expect(hasAppPermissionRisk(serverBoth)).toBe(true);
    const publicTips = getAppPermissionRiskTips(serverBoth);
    expect(publicTips).toHaveLength(2);
    expect(publicTips[0]).toContain('OAuth2公开客户端模式');
    expect(publicTips[0]).toContain('2个应用态鉴权工具(get_user、list_orders)');
    expect(publicTips[1]).toContain('public 应用身份');

    // 同时开启 personal 开关，触发 both 组合文案与两条身份说明
    flagStore.flags.ENABLE_MCP_SERVER_OAUTH2_PERSONAL_CLIENT = true;
    const bothTips = getAppPermissionRiskTips(serverBoth);
    expect(bothTips).toHaveLength(3);
    expect(bothTips[0]).toContain('OAuth2公开客户端与个人令牌模式');
    expect(bothTips[1]).toContain('public 应用身份');
    expect(bothTips[2]).toContain('个人令牌调用');

    // 仅 Server 开启 personal 模式
    const serverPersonalOnly = {
      oauth2_public_client_enabled: false,
      oauth2_personal_client_enabled: true,
      app_permission_risk: {
        has_risk: true,
        risk_tools: ['tool_a'],
      },
    };
    const personalTips = getAppPermissionRiskTips(serverPersonalOnly);
    expect(personalTips).toHaveLength(2);
    expect(personalTips[0]).toContain('个人令牌模式');

    // has_risk 为 false 时不展示
    expect(hasAppPermissionRisk({
      ...serverBoth,
      app_permission_risk: { has_risk: false },
    })).toBe(false);
  });
});

describe('hooks/use-sidebar', () => {
  beforeEach(() => {
    popInfoBoxMock.mockReset();
  });

  it('表单未改动时直接允许关闭；改动后通过确认弹窗决定是否关闭', async () => {
    const { initSidebarFormData, isSidebarClosed } = useSidebar();

    initSidebarFormData({ name: 'demo' });
    expect(await isSidebarClosed(JSON.stringify({ name: 'demo' }))).toBe(true);
    expect(popInfoBoxMock).not.toHaveBeenCalled();

    // 数组长度一致也视为未修改
    initSidebarFormData([1, 2]);
    expect(await isSidebarClosed([3, 4])).toBe(true);

    // 发生变更后触发弹窗，点击确认返回 true
    popInfoBoxMock.mockImplementationOnce((opts: any) => opts.onConfirm());
    expect(await isSidebarClosed([1])).toBe(true);
    expect(popInfoBoxMock).toHaveBeenCalledTimes(1);

    // 点击取消返回 false
    popInfoBoxMock.mockImplementationOnce((opts: any) => opts.onCancel());
    expect(await isSidebarClosed(JSON.stringify({ name: 'changed' }))).toBe(false);
  });
});
