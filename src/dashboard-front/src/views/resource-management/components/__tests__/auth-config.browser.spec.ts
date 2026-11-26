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

import { defineComponent, h, nextTick, ref, shallowRef } from 'vue';
import { createMemoryHistory, createRouter } from 'vue-router';
import { Alert, Checkbox, InfoBox, Switcher } from 'bkui-vue';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { renderWithApp } from '@/components/__tests__/browser-render';
import { useEnv, useGateway } from '@/stores';
import type { IAuthConfig, IPublicConfig, IResourceAuthFormConfig } from '@/types/resource';
import { DEFAULT_AUTH_CONFIG } from '@/utils/auth-config';
import AuthConfig from '../AuthConfig.vue';
import LegacyResourceAuthSelector from '../LegacyResourceAuthSelector.vue';
import ResourceAuthSelector from '../ResourceAuthSelector.vue';

type ResourceDetailProp = (Partial<IPublicConfig> & {
  auth_config?: Partial<IAuthConfig> | string
}) | null;

interface IMountAuthConfigOptions {
  isV2?: boolean
  allowUpdateGatewayAuth?: boolean
  editingExisting?: boolean
  detail?: ResourceDetailProp
  gatewayId?: number
  docLinks?: {
    AUTH?: string
    AUTH_PERSONAL_TOKEN?: string
    GUIDE?: string
  }
}

const AUTH_EXTRA_COMPONENTS = {
  BkAlert: Alert,
  BkCheckbox: Checkbox,
  BkCheckboxGroup: Checkbox.Group,
  BkSwitcher: Switcher,
};

const AUTH_EXTRA_DIRECTIVES = {
  'bk-overflow-tips': {},
};

// 真实浏览器中 position: fixed 元素 offsetParent 为 null，统一用样式与几何尺寸判定可见性
const isElementVisible = (el: HTMLElement | null | undefined): boolean => {
  if (!el || !el.isConnected) return false;
  let current: HTMLElement | null = el;
  while (current && current !== document.body) {
    const style = getComputedStyle(current);
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
      return false;
    }
    current = current.parentElement;
  }
  const rect = el.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
};

// bkui-vue BkCheckbox 内部统一经 Promise.resolve(beforeChange).then(...) 异步提交变更
const flushAsyncUpdates = async () => {
  await Promise.resolve();
  await new Promise<void>((resolve) => {
    setTimeout(resolve, 0);
  });
  await nextTick();
};

const clickCheckbox = async (el: HTMLElement) => {
  el.click();
  await flushAsyncUpdates();
};

const createTestRouter = async (gatewayId = 42) => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: '/:id/resource/edit',
        name: 'ResourceEdit',
        component: { template: '<div />' },
      },
      {
        path: '/:id/permission/app',
        name: 'PermissionApp',
        component: { template: '<div />' },
      },
    ],
  });
  await router.push(`/${gatewayId}/resource/edit`);
  await router.isReady();
  return router;
};

const mountAuthConfig = async (options: IMountAuthConfigOptions = {}) => {
  const {
    isV2 = true,
    allowUpdateGatewayAuth = true,
    editingExisting = false,
    detail = {},
    gatewayId = 42,
    docLinks = {},
  } = options;

  const router = await createTestRouter(gatewayId);
  const authConfigRef = shallowRef<InstanceType<typeof AuthConfig>>();
  const detailState = ref<ResourceDetailProp>(detail);
  const editingExistingState = ref(editingExisting);

  const Host = defineComponent({
    setup() {
      // 在组件挂载前初始化网关与环境配置，贴近真实页面进入顺序
      const gatewayStore = useGateway();
      gatewayStore.setCurrentGateway({
        id: gatewayId,
        name: 'demo-gateway',
        oauth2_app_enabled: isV2,
        allow_update_gateway_auth: allowUpdateGatewayAuth,
      });

      const envStore = useEnv();
      envStore.env.DOC_LINKS.AUTH = docLinks.AUTH ?? '';
      envStore.env.DOC_LINKS.AUTH_PERSONAL_TOKEN = docLinks.AUTH_PERSONAL_TOKEN ?? '';
      envStore.env.DOC_LINKS.GUIDE = docLinks.GUIDE ?? '';

      return () => h(AuthConfig, {
        ref: authConfigRef,
        detail: detailState.value,
        editingExisting: editingExistingState.value,
      });
    },
  });

  const { screen } = await renderWithApp(Host, {
    global: {
      plugins: [router],
      components: AUTH_EXTRA_COMPONENTS,
      directives: AUTH_EXTRA_DIRECTIVES,
    },
  });

  return {
    authConfigRef,
    detailState,
    editingExistingState,
    gatewayStore: useGateway(),
    envStore: useEnv(),
    router,
    screen,
  };
};

// 查找组件内按文本匹配的卡片/复选框/开关/按钮
const findOptionCard = (container: Element, title: string) =>
  [...container.querySelectorAll<HTMLElement>('.auth-option')]
    .find(el => el.textContent?.includes(title));

const findCheckboxByLabel = (container: Element, label: string) =>
  [...container.querySelectorAll<HTMLElement>('label.bk-checkbox')]
    .find(el => el.textContent?.trim() === label);

const findButtonByText = (container: Element, text: string) =>
  [...container.querySelectorAll<HTMLButtonElement>('button')]
    .find(btn => btn.textContent?.includes(text));

const findSwitcherInRow = (container: Element, rowSelector: string, label: string) => {
  const row = [...container.querySelectorAll<HTMLElement>(rowSelector)]
    .find(el => el.textContent?.includes(label));
  return row?.querySelector<HTMLElement>('.bk-switcher') ?? null;
};

const findVisibleInfoBox = () =>
  [...document.querySelectorAll<HTMLElement>('.bk-infobox')]
    .find((el) => {
      const body = el.querySelector<HTMLElement>('.bk-modal-body');
      return isElementVisible(body ?? el);
    });

const cleanupVisibleInfoBoxes = async () => {
  const visible = findVisibleInfoBox();
  if (visible) {
    const cancelBtn = [...visible.querySelectorAll<HTMLButtonElement>('button')]
      .find(btn => btn.textContent?.trim() === '取消');
    cancelBtn?.click();
  }
  // bkui-vue InfoBox 为全局单例，不能移除其挂载节点，仅通过 hide() 安全隐藏并等待淡出动画结束
  InfoBox({ isShow: false }).hide();
  await vi.waitFor(() => {
    expect(findVisibleInfoBox()).toBeUndefined();
  });
};

describe('ResourceManagement / AuthConfig 浏览器组件测试', () => {
  afterEach(async () => {
    await cleanupVisibleInfoBoxes();
  });

  describe('V2 模式（AuthConfig + ResourceAuthSelector）', () => {
    it('新建资源默认开启用户认证 + OAuth 授权 + 校验应用权限 + 公开 + 允许申请权限', async () => {
      const { authConfigRef, screen } = await mountAuthConfig({ isV2: true });

      expect(screen.container.textContent).toContain('认证类型');
      expect(authConfigRef.value!.formData).toEqual({
        auth_config: { ...DEFAULT_AUTH_CONFIG },
        is_public: true,
        allow_apply_permission: true,
      });

      // 用户认证卡片处于激活态，仅勾选 OAuth 授权，不显示不认证告警
      expect(findOptionCard(screen.container, '用户认证')?.classList.contains('is-active')).toBe(true);
      expect(findCheckboxByLabel(screen.container, 'OAuth 授权')?.classList.contains('is-checked')).toBe(true);
      expect(findCheckboxByLabel(screen.container, '个人令牌')?.classList.contains('is-checked')).toBe(false);
      expect(findCheckboxByLabel(screen.container, '公开客户端')?.classList.contains('is-checked')).toBe(false);
      expect(screen.container.querySelector('.bk-alert')).toBeNull();

      // 校验应用权限与允许申请权限默认均开启，且权限申请指引按钮可见
      const permSwitcher = findSwitcherInRow(screen.container, '.auth-followup-row', '校验应用权限');
      const allowApplySwitcher = findSwitcherInRow(screen.container, '.public-child-row', '允许申请权限');
      expect(permSwitcher?.classList.contains('is-checked')).toBe(true);
      expect(allowApplySwitcher?.classList.contains('is-checked')).toBe(true);
      expect(findButtonByText(screen.container, '权限申请指引')).not.toBeUndefined();
      expect(screen.container.querySelector('.public-state')?.textContent?.trim()).toBe('公开');
    });

    it('支持三类认证切换、子方式多选与校验应用权限/是否公开对允许申请权限的联动（不记忆原值）', async () => {
      const { authConfigRef, screen } = await mountAuthConfig({
        isV2: true,
        allowUpdateGatewayAuth: true,
      });

      // 1. 从用户认证（OAuth）切换到应用认证：保留校验应用权限与允许申请权限
      findOptionCard(screen.container, '应用认证')!.click();
      await nextTick();
      expect(authConfigRef.value!.formData).toEqual({
        auth_config: {
          auth_verified_required: false,
          app_verified_required: true,
          resource_perm_required: true,
          oauth2_personal_client_enabled: false,
          oauth2_public_client_enabled: false,
        },
        is_public: true,
        allow_apply_permission: true,
      });

      // 2. 在应用认证下关闭校验应用权限：allow_apply_permission 自动置 false 且 V2 下隐藏该行
      const appPermSwitcher = findSwitcherInRow(screen.container, '.auth-followup-row', '校验应用权限')!;
      appPermSwitcher.click();
      await nextTick();
      expect(authConfigRef.value!.formData.auth_config.resource_perm_required).toBe(false);
      expect(authConfigRef.value!.formData.allow_apply_permission).toBe(false);
      expect(screen.container.querySelector('.public-child')).toBeNull();
      expect(screen.container.textContent).toContain('关闭后，任意蓝鲸应用都可以调用。');
      expect(findButtonByText(screen.container, '权限申请指引')).toBeUndefined();

      // 重新开启校验应用权限：允许申请权限行恢复显示，但不记忆之前的 true
      appPermSwitcher.click();
      await nextTick();
      expect(authConfigRef.value!.formData.auth_config.resource_perm_required).toBe(true);
      expect(authConfigRef.value!.formData.allow_apply_permission).toBe(false);
      const allowApplySwitcher = findSwitcherInRow(screen.container, '.public-child-row', '允许申请权限')!;
      expect(allowApplySwitcher.classList.contains('is-checked')).toBe(false);

      // 手动再次开启允许申请权限，然后关闭「是否公开」：置 false 且隐藏
      allowApplySwitcher.click();
      await nextTick();
      expect(authConfigRef.value!.formData.allow_apply_permission).toBe(true);

      const publicSwitcher = screen.container.querySelector<HTMLElement>('.public-switch .bk-switcher')!;
      publicSwitcher.click();
      await nextTick();
      expect(authConfigRef.value!.formData.is_public).toBe(false);
      expect(authConfigRef.value!.formData.allow_apply_permission).toBe(false);
      expect(screen.container.querySelector('.public-state')?.textContent?.trim()).toBe('不公开');
      expect(screen.container.querySelector('.public-child')).toBeNull();

      // 重新打开「是否公开」：不记忆原值，allow_apply_permission 保持 false
      publicSwitcher.click();
      await nextTick();
      expect(authConfigRef.value!.formData.is_public).toBe(true);
      expect(authConfigRef.value!.formData.allow_apply_permission).toBe(false);

      // 3. 切换到「不认证」：5 项开关全 false，展示警告条
      findOptionCard(screen.container, '不认证')!.click();
      await nextTick();
      expect(authConfigRef.value!.formData.auth_config).toEqual({
        auth_verified_required: false,
        app_verified_required: false,
        resource_perm_required: false,
        oauth2_personal_client_enabled: false,
        oauth2_public_client_enabled: false,
      });
      expect(screen.container.querySelector('.bk-alert')?.textContent)
        .toContain('网关不校验调用方身份，请确认接口可以完全公开。');

      // 4. 切回「用户认证」，默认恢复上次子方式（OAuth），勾选个人令牌与公开客户端，并直接取消 OAuth（新建态不弹窗）
      findOptionCard(screen.container, '用户认证')!.click();
      await nextTick();
      expect(authConfigRef.value!.formData.auth_config).toEqual({
        auth_verified_required: true,
        app_verified_required: true,
        resource_perm_required: true,
        oauth2_personal_client_enabled: false,
        oauth2_public_client_enabled: false,
      });

      await clickCheckbox(findCheckboxByLabel(screen.container, '个人令牌')!);
      await clickCheckbox(findCheckboxByLabel(screen.container, '公开客户端')!);
      expect(authConfigRef.value!.formData.auth_config.oauth2_personal_client_enabled).toBe(true);
      expect(authConfigRef.value!.formData.auth_config.oauth2_public_client_enabled).toBe(true);

      // 新建态取消 OAuth 授权不弹出确认框，直接关闭 app_verified_required 与 resource_perm_required
      await clickCheckbox(findCheckboxByLabel(screen.container, 'OAuth 授权')!);
      expect(authConfigRef.value!.formData.auth_config.app_verified_required).toBe(false);
      expect(findVisibleInfoBox()).toBeUndefined();
      expect(authConfigRef.value!.formData.auth_config).toEqual({
        auth_verified_required: true,
        app_verified_required: false,
        resource_perm_required: false,
        oauth2_personal_client_enabled: true,
        oauth2_public_client_enabled: true,
      });

      // 同一资源内切换到应用认证再切回用户认证，应恢复个人令牌 + 公开客户端
      findOptionCard(screen.container, '应用认证')!.click();
      await nextTick();
      findOptionCard(screen.container, '用户认证')!.click();
      await nextTick();
      expect(authConfigRef.value!.formData.auth_config).toEqual({
        auth_verified_required: true,
        app_verified_required: false,
        resource_perm_required: false,
        oauth2_personal_client_enabled: true,
        oauth2_public_client_enabled: true,
      });
    });

    it('网关 allow_update_gateway_auth=false 时禁用不认证卡片且点击卡片外层也不可切换', async () => {
      const { authConfigRef, screen } = await mountAuthConfig({
        isV2: true,
        allowUpdateGatewayAuth: false,
      });

      const noneCard = findOptionCard(screen.container, '不认证')!;
      expect(noneCard.classList.contains('is-disabled')).toBe(true);
      expect(noneCard.querySelector<HTMLInputElement>('input[type="radio"]')?.disabled).toBe(true);

      noneCard.click();
      await nextTick();
      expect(authConfigRef.value!.formData.auth_config).toEqual(DEFAULT_AUTH_CONFIG);
      expect(noneCard.classList.contains('is-active')).toBe(false);
      expect(screen.container.querySelector('.bk-alert')).toBeNull();
    });

    it('编辑已保存 OAuth 资源取消 OAuth 授权时弹出确认框，支持取消、右上角关闭、ESC 与确定取消', async () => {
      const { authConfigRef, screen } = await mountAuthConfig({
        isV2: true,
        editingExisting: true,
        detail: {
          is_public: true,
          allow_apply_permission: true,
          auth_config: {
            auth_verified_required: true,
            app_verified_required: true,
            resource_perm_required: true,
            oauth2_personal_client_enabled: true,
            oauth2_public_client_enabled: false,
          },
        },
      });

      const getOAuthCheckbox = () => findCheckboxByLabel(screen.container, 'OAuth 授权')!;

      // 场景 1：点击取消勾选 → 弹窗出现 → 点击「取消」→ 保持勾选且可再次触发
      getOAuthCheckbox().click();
      await vi.waitFor(() => {
        expect(findVisibleInfoBox()?.textContent).toContain('确定取消 OAuth 授权？');
      });
      const cancelBtn = [...findVisibleInfoBox()!.querySelectorAll<HTMLButtonElement>('button')]
        .find(btn => btn.textContent?.trim() === '取消')!;
      cancelBtn.click();

      await vi.waitFor(() => {
        expect(findVisibleInfoBox()).toBeUndefined();
      });
      expect(authConfigRef.value!.formData.auth_config.app_verified_required).toBe(true);
      expect(authConfigRef.value!.formData.allow_apply_permission).toBe(true);
      expect(getOAuthCheckbox().classList.contains('is-checked')).toBe(true);

      // 场景 2：再次点击取消勾选 → 点击右上角关闭图标（bkui InfoBox 将 onClick 绑在子图标元素上）→ 回滚勾选且不卡死
      getOAuthCheckbox().click();
      await vi.waitFor(() => {
        expect(findVisibleInfoBox()?.textContent).toContain('确定取消 OAuth 授权？');
      });
      const closeTarget = findVisibleInfoBox()!.querySelector<Element>('.bk-modal-close > *')
        ?? findVisibleInfoBox()!.querySelector<Element>('.bk-modal-close')!;
      closeTarget.dispatchEvent(new MouseEvent('click', { bubbles: true }));

      await vi.waitFor(() => {
        expect(findVisibleInfoBox()).toBeUndefined();
      });
      expect(authConfigRef.value!.formData.auth_config.app_verified_required).toBe(true);
      expect(getOAuthCheckbox().classList.contains('is-checked')).toBe(true);

      // 场景 3：再次点击取消勾选 → 按下 Escape 键后不应导致弹窗关闭但复选框永久卡死
      getOAuthCheckbox().click();
      await vi.waitFor(() => {
        expect(findVisibleInfoBox()?.textContent).toContain('确定取消 OAuth 授权？');
      });
      document.dispatchEvent(new KeyboardEvent('keydown', {
        key: 'Escape',
        code: 'Escape',
        keyCode: 27,
        bubbles: true,
      }));
      await nextTick();
      // 如果 InfoBox 未响应 ESC，手动关掉以继续验证场景 4；如果已响应 ESC 关闭，则验证复选框未卡死
      if (findVisibleInfoBox()) {
        const fallbackCancel = [...findVisibleInfoBox()!.querySelectorAll<HTMLButtonElement>('button')]
          .find(btn => btn.textContent?.trim() === '取消')!;
        fallbackCancel.click();
        await vi.waitFor(() => {
          expect(findVisibleInfoBox()).toBeUndefined();
        });
      }

      // 场景 4：点击取消勾选 → 点击「确定取消」→ 取消 OAuth 并联动清零应用权限与允许申请权限
      getOAuthCheckbox().click();
      await vi.waitFor(() => {
        expect(findVisibleInfoBox()?.textContent).toContain('确定取消 OAuth 授权？');
      });
      const confirmBtn = [...findVisibleInfoBox()!.querySelectorAll<HTMLButtonElement>('button')]
        .find(btn => btn.textContent?.trim() === '确定取消')!;
      confirmBtn.click();

      await vi.waitFor(() => {
        expect(authConfigRef.value!.formData.auth_config.app_verified_required).toBe(false);
      });
      expect(authConfigRef.value!.formData.auth_config).toEqual({
        auth_verified_required: true,
        app_verified_required: false,
        resource_perm_required: false,
        oauth2_personal_client_enabled: true,
        oauth2_public_client_enabled: false,
      });
      expect(authConfigRef.value!.formData.allow_apply_permission).toBe(false);
    });

    it('新建态取消全部用户认证子方式时，仍保持用户认证大类并清空应用权限与允许申请权限', async () => {
      const fresh = await mountAuthConfig({ isV2: true });
      await clickCheckbox(findCheckboxByLabel(fresh.screen.container, 'OAuth 授权')!);
      expect(fresh.authConfigRef.value!.formData).toEqual({
        auth_config: {
          auth_verified_required: true,
          app_verified_required: false,
          resource_perm_required: false,
          oauth2_personal_client_enabled: false,
          oauth2_public_client_enabled: false,
        },
        is_public: true,
        allow_apply_permission: false,
      });
      expect(findOptionCard(fresh.screen.container, '用户认证')?.classList.contains('is-active')).toBe(true);
    });

    it('OAuth 取消确认弹窗打开期间卸载组件（如路由回退）时，确认弹窗同步关闭不残留遮挡页面', async () => {
      const { screen } = await mountAuthConfig({
        isV2: true,
        editingExisting: true,
        detail: {
          is_public: true,
          allow_apply_permission: true,
          auth_config: { ...DEFAULT_AUTH_CONFIG },
        },
      });

      findCheckboxByLabel(screen.container, 'OAuth 授权')!.click();
      await vi.waitFor(() => {
        expect(findVisibleInfoBox()?.textContent).toContain('确定取消 OAuth 授权？');
      });

      // 卸载组件（模拟路由跳转/后退/关闭侧栏）：弹窗应随之关闭，不应残留挂在 body 上遮挡新页面
      screen.unmount();
      await vi.waitFor(() => {
        expect(findVisibleInfoBox()).toBeUndefined();
      });
    });

    it('克隆场景或已保存资源原本未开启 OAuth 时，取消勾选 OAuth 不弹出二次确认框', async () => {
      // 克隆场景：editingExisting=false，即便 detail 带有 OAuth 也不弹窗
      const cloneCtx = await mountAuthConfig({
        isV2: true,
        editingExisting: false,
        detail: {
          is_public: true,
          allow_apply_permission: true,
          auth_config: { ...DEFAULT_AUTH_CONFIG },
        },
      });
      await clickCheckbox(findCheckboxByLabel(cloneCtx.screen.container, 'OAuth 授权')!);
      expect(cloneCtx.authConfigRef.value!.formData.auth_config.app_verified_required).toBe(false);
      expect(findVisibleInfoBox()).toBeUndefined();
      cloneCtx.screen.unmount();

      // 已保存资源原本仅开启个人令牌：临时勾选 OAuth 再取消也不弹窗
      const nonOAuthCtx = await mountAuthConfig({
        isV2: true,
        editingExisting: true,
        detail: {
          is_public: true,
          allow_apply_permission: false,
          auth_config: {
            auth_verified_required: true,
            app_verified_required: false,
            resource_perm_required: false,
            oauth2_personal_client_enabled: true,
            oauth2_public_client_enabled: false,
          },
        },
      });
      await clickCheckbox(findCheckboxByLabel(nonOAuthCtx.screen.container, 'OAuth 授权')!);
      expect(nonOAuthCtx.authConfigRef.value!.formData.auth_config.app_verified_required).toBe(true);

      await clickCheckbox(findCheckboxByLabel(nonOAuthCtx.screen.container, 'OAuth 授权')!);
      expect(nonOAuthCtx.authConfigRef.value!.formData.auth_config.app_verified_required).toBe(false);
      expect(findVisibleInfoBox()).toBeUndefined();
    });

    it('支持 JSON 字符串回显与脏数据归一化，并支持查看文档与权限申请指引外链/路由回退跳转', async () => {
      const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);

      const { authConfigRef, envStore, screen } = await mountAuthConfig({
        isV2: true,
        gatewayId: 99,
        detail: {
          is_public: true,
          allow_apply_permission: true,
          auth_config: JSON.stringify({
            auth_verified_required: true,
            app_verified_required: true,
            resource_perm_required: true,
            oauth2_personal_client_enabled: false,
            oauth2_public_client_enabled: false,
          }),
        },
        docLinks: {
          AUTH_PERSONAL_TOKEN: 'https://docs.example.com/personal-token',
          AUTH: 'https://docs.example.com/auth-guide',
          GUIDE: 'https://docs.example.com/general-guide',
        },
      });

      expect(authConfigRef.value!.formData.allow_apply_permission).toBe(true);

      // 点击个人令牌查看文档
      findButtonByText(screen.container, '查看文档')!.click();
      expect(openSpy).toHaveBeenLastCalledWith('https://docs.example.com/personal-token', '_blank');

      // 权限申请指引：优先 AUTH → 次选 GUIDE → 兜底 PermissionApp 路由
      findButtonByText(screen.container, '权限申请指引')!.click();
      expect(openSpy).toHaveBeenLastCalledWith('https://docs.example.com/auth-guide', '_blank');

      envStore.env.DOC_LINKS.AUTH = '';
      await nextTick();
      findButtonByText(screen.container, '权限申请指引')!.click();
      expect(openSpy).toHaveBeenLastCalledWith('https://docs.example.com/general-guide', '_blank');

      envStore.env.DOC_LINKS.GUIDE = '';
      await nextTick();
      findButtonByText(screen.container, '权限申请指引')!.click();
      expect(openSpy).toHaveBeenLastCalledWith('/99/permission/app', '_blank');
    });

    it('detail 省略 auth_config 或仅含部分字段时，allow_apply_permission 按归一化结果保留为 true', async () => {
      // detail 中 auth_config 仅传部分字段（app_verified_required / resource_perm_required 走默认值 true）
      const { authConfigRef } = await mountAuthConfig({
        isV2: true,
        detail: {
          is_public: true,
          allow_apply_permission: true,
          auth_config: { auth_verified_required: true },
        },
      });

      // normalizeAuthConfig 已补全 app_verified_required=true、resource_perm_required=true
      expect(authConfigRef.value!.formData.auth_config.app_verified_required).toBe(true);
      expect(authConfigRef.value!.formData.auth_config.resource_perm_required).toBe(true);
      // 正确预期：既然最终表单处于可申请权限状态且 detail.allow_apply_permission=true，应保留 true
      expect(authConfigRef.value!.formData.allow_apply_permission).toBe(true);
    });

    it('同一组件实例切换编辑不同资源（detail 变更）时，前一条资源的 lastUserAuthMethods 不污染下一条资源', async () => {
      // 模拟 ResourceEditSlider 复用同一个 AuthConfig 实例先后编辑两条资源
      const { authConfigRef, detailState, screen } = await mountAuthConfig({
        isV2: true,
        detail: {
          is_public: true,
          allow_apply_permission: true,
          auth_config: {
            auth_verified_required: true,
            app_verified_required: true,
            resource_perm_required: true,
            oauth2_personal_client_enabled: false,
            oauth2_public_client_enabled: false,
          },
        },
      });

      // 资源 A：勾选个人令牌、取消 OAuth，然后切换到应用认证
      await clickCheckbox(findCheckboxByLabel(screen.container, '个人令牌')!);
      await clickCheckbox(findCheckboxByLabel(screen.container, 'OAuth 授权')!);
      expect(authConfigRef.value!.formData.auth_config.app_verified_required).toBe(false);
      findOptionCard(screen.container, '应用认证')!.click();
      await nextTick();

      // 切换编辑资源 B（原本是纯应用认证，从未配置过用户认证）
      detailState.value = {
        is_public: true,
        allow_apply_permission: true,
        auth_config: {
          auth_verified_required: false,
          app_verified_required: true,
          resource_perm_required: true,
          oauth2_personal_client_enabled: false,
          oauth2_public_client_enabled: false,
        },
      };
      await nextTick();

      // 在资源 B 上点击「用户认证」：应默认选中 OAuth 授权，而不是泄漏资源 A 的「仅个人令牌」
      findOptionCard(screen.container, '用户认证')!.click();
      await nextTick();
      expect(authConfigRef.value!.formData.auth_config).toEqual({
        auth_verified_required: true,
        app_verified_required: true,
        resource_perm_required: true,
        oauth2_personal_client_enabled: false,
        oauth2_public_client_enabled: false,
      });
    });

    it('仅 app_verified_required 变为 false 时，allow_apply_permission 联动清零', async () => {
      const { authConfigRef } = await mountAuthConfig({ isV2: true });
      expect(authConfigRef.value!.formData.allow_apply_permission).toBe(true);

      // 模拟异常/外部路径仅将 app_verified_required 改为 false 而未同步改 resource_perm_required
      authConfigRef.value!.formData.auth_config = {
        ...authConfigRef.value!.formData.auth_config,
        app_verified_required: false,
      };
      await nextTick();

      // canAllowApply 此时已是 false，表单值 allow_apply_permission 也必须同步归零
      expect(authConfigRef.value!.formData.allow_apply_permission).toBe(false);
    });
  });

  describe('V1 模式（AuthConfig + LegacyResourceAuthSelector）', () => {
    it('默认态、8 种认证组合场景文案与级联开关（含清理隐藏公开客户端字段）全部准确', async () => {
      const { authConfigRef, screen } = await mountAuthConfig({
        isV2: false,
        allowUpdateGatewayAuth: true,
        detail: {
          is_public: true,
          allow_apply_permission: true,
          auth_config: {
            auth_verified_required: true,
            app_verified_required: true,
            resource_perm_required: true,
            oauth2_personal_client_enabled: false,
            oauth2_public_client_enabled: true,
          },
        },
      });

      expect(screen.container.textContent).toContain('认证方式');

      const getSceneAlert = () => {
        const alerts = [...screen.container.querySelectorAll<HTMLElement>('.bk-alert')];
        return alerts[alerts.length - 1];
      };
      const appCheckbox = () => findCheckboxByLabel(screen.container, '应用认证')!;
      const userCheckbox = () => findCheckboxByLabel(screen.container, '用户认证')!;
      const permSwitcher = () => findSwitcherInRow(screen.container, '.auth-child-row', '检验应用权限')!;
      const personalSwitcher = () => findSwitcherInRow(screen.container, '.auth-child-row', '个人令牌')!;
      const allowApplySwitcher = () => findSwitcherInRow(screen.container, '.public-child-row', '允许申请权限')!;

      // 组合 1：app=T, user=T, perm=T, personal=F
      expect(getSceneAlert().textContent).toContain('当前效果：须同时具备应用身份和用户身份，且应用须已获授权。');

      // 组合 2：开启个人令牌 → app=T, user=T, perm=T, personal=T
      personalSwitcher().click();
      await nextTick();
      expect(authConfigRef.value!.formData.auth_config.oauth2_personal_client_enabled).toBe(true);
      expect(getSceneAlert().textContent)
        .toContain('当前效果：须同时具备应用身份和用户身份，应用须已获授权；允许使用个人令牌。');

      // 组合 3：关闭检验应用权限 → app=T, user=T, perm=F, personal=T，同时禁用并清空允许申请权限
      permSwitcher().click();
      await nextTick();
      expect(authConfigRef.value!.formData.auth_config.resource_perm_required).toBe(false);
      expect(authConfigRef.value!.formData.allow_apply_permission).toBe(false);
      expect(allowApplySwitcher().classList.contains('is-disabled')).toBe(true);
      expect(screen.container.textContent).toContain('需要开启「检验应用权限」，才可以配置「允许申请权限」。');
      expect(getSceneAlert().textContent)
        .toContain('当前效果：须同时具备应用身份和用户身份；允许使用个人令牌。');

      // 组合 4：关闭个人令牌 → app=T, user=T, perm=F, personal=F
      personalSwitcher().click();
      await nextTick();
      expect(getSceneAlert().textContent).toContain('当前效果：须同时具备应用身份和用户身份。');

      // 组合 5：关闭应用认证 → app=F, user=T, perm=F, personal=F
      await clickCheckbox(appCheckbox());
      expect(authConfigRef.value!.formData.auth_config.app_verified_required).toBe(false);
      expect(permSwitcher().classList.contains('is-disabled')).toBe(true);
      expect(getSceneAlert().textContent).toContain('当前效果：只校验用户身份。不校验调用方是哪个应用。');

      // 组合 6：开启个人令牌 → app=F, user=T, perm=F, personal=T
      personalSwitcher().click();
      await nextTick();
      expect(getSceneAlert().textContent)
        .toContain('当前效果：只校验用户身份，并允许使用个人令牌。不校验调用方是哪个应用。');

      // 组合 7：关闭用户认证 → app=F, user=F，同时自动清零个人令牌与隐藏的公开客户端字段，出现顶部警告
      await clickCheckbox(userCheckbox());
      expect(authConfigRef.value!.formData.auth_config).toEqual({
        auth_verified_required: false,
        app_verified_required: false,
        resource_perm_required: false,
        oauth2_personal_client_enabled: false,
        oauth2_public_client_enabled: false,
      });
      expect(personalSwitcher().classList.contains('is-disabled')).toBe(true);
      expect(screen.container.querySelectorAll('.bk-alert')).toHaveLength(2);
      expect(screen.container.textContent)
        .toContain('当前不校验应用身份和用户身份，调用无需认证即可通过，请确认这是预期配置。');
      expect(getSceneAlert().textContent).toContain('当前效果：不校验应用身份、也不校验用户身份。');

      // 组合 8 & 9：重新勾选应用认证（仅应用认证，无权限 / 有权限）
      await clickCheckbox(appCheckbox());
      expect(authConfigRef.value!.formData.auth_config.app_verified_required).toBe(true);
      expect(authConfigRef.value!.formData.auth_config.resource_perm_required).toBe(false);
      expect(getSceneAlert().textContent)
        .toContain('当前效果：仅应用认证，只接受应用密钥调用，不接受用户 Token / 个人令牌。');

      permSwitcher().click();
      await nextTick();
      expect(getSceneAlert().textContent)
        .toContain('当前效果：仅应用认证，且调用应用必须已获授权。不接受用户 Token / 个人令牌。');

      // V1 下关闭是否公开：允许申请权限行仍保留展示但禁用，文案切换为依赖是否公开
      const publicSwitcher = screen.container.querySelector<HTMLElement>('.public-switch .bk-switcher')!;
      publicSwitcher.click();
      await nextTick();
      expect(allowApplySwitcher().classList.contains('is-disabled')).toBe(true);
      expect(screen.container.textContent)
        .toContain('依赖「是否公开」。资源不公开时，用户无法查看接口文档和申请权限。');
    });

    it('allow_update_gateway_auth=false 时禁用应用认证与检验应用权限，用户认证与个人令牌仍可编辑', async () => {
      const { authConfigRef, screen } = await mountAuthConfig({
        isV2: false,
        allowUpdateGatewayAuth: false,
      });

      const appCheckbox = findCheckboxByLabel(screen.container, '应用认证')!;
      const permSwitcher = findSwitcherInRow(screen.container, '.auth-child-row', '检验应用权限')!;
      const userCheckbox = findCheckboxByLabel(screen.container, '用户认证')!;
      const personalSwitcher = findSwitcherInRow(screen.container, '.auth-child-row', '个人令牌')!;

      expect(appCheckbox.classList.contains('is-disabled')).toBe(true);
      expect(permSwitcher.classList.contains('is-disabled')).toBe(true);
      expect(userCheckbox.classList.contains('is-disabled')).toBe(false);
      expect(personalSwitcher.classList.contains('is-disabled')).toBe(false);

      // 尝试点击禁用的应用认证和检验应用权限不应改变状态
      await clickCheckbox(appCheckbox);
      permSwitcher.click();
      await nextTick();
      expect(authConfigRef.value!.formData.auth_config.app_verified_required).toBe(true);
      expect(authConfigRef.value!.formData.auth_config.resource_perm_required).toBe(true);

      // 用户认证与个人令牌可正常切换
      personalSwitcher.click();
      await nextTick();
      expect(authConfigRef.value!.formData.auth_config.oauth2_personal_client_enabled).toBe(true);
    });

    it('V1 模式下个人令牌「查看文档」按钮按 DOC_LINKS.AUTH_PERSONAL_TOKEN 显隐并打开新标签页', async () => {
      const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
      const { envStore, screen } = await mountAuthConfig({
        isV2: false,
        docLinks: { AUTH_PERSONAL_TOKEN: '' },
      });

      expect(findButtonByText(screen.container, '查看文档')).toBeUndefined();

      envStore.env.DOC_LINKS.AUTH_PERSONAL_TOKEN = 'https://docs.example.com/v1-personal-token';
      await nextTick();
      const docBtn = findButtonByText(screen.container, '查看文档');
      expect(docBtn).not.toBeUndefined();
      docBtn!.click();
      expect(openSpy).toHaveBeenCalledWith('https://docs.example.com/v1-personal-token', '_blank');
    });

    it('同一组件实例切换编辑不同资源（detail 变更）时，前一条资源的 previousResourcePermission 不污染下一条资源', async () => {
      const { authConfigRef, detailState, screen } = await mountAuthConfig({
        isV2: false,
        allowUpdateGatewayAuth: true,
        detail: {
          is_public: true,
          allow_apply_permission: true,
          auth_config: {
            auth_verified_required: false,
            app_verified_required: true,
            resource_perm_required: true,
            oauth2_personal_client_enabled: false,
            oauth2_public_client_enabled: false,
          },
        },
      });

      // 资源 A：关闭应用认证（内部将 previousResourcePermission 记为 true）
      await clickCheckbox(findCheckboxByLabel(screen.container, '应用认证')!);
      expect(authConfigRef.value!.formData.auth_config.app_verified_required).toBe(false);

      // 切换编辑资源 B（原本应用认证与检验应用权限均为 false）
      detailState.value = {
        is_public: true,
        allow_apply_permission: false,
        auth_config: {
          auth_verified_required: true,
          app_verified_required: false,
          resource_perm_required: false,
          oauth2_personal_client_enabled: false,
          oauth2_public_client_enabled: false,
        },
      };
      await nextTick();

      // 在资源 B 上首次开启应用认证：不应继承资源 A 的 previousResourcePermission=true
      await clickCheckbox(findCheckboxByLabel(screen.container, '应用认证')!);
      expect(authConfigRef.value!.formData.auth_config.app_verified_required).toBe(true);
      expect(authConfigRef.value!.formData.auth_config.resource_perm_required).toBe(false);
    });

    it('网关 oauth2_app_enabled 动态切换时，AuthConfig 在 V1 与 V2 选择器间无缝切换', async () => {
      const { gatewayStore, screen } = await mountAuthConfig({ isV2: false });
      expect(screen.container.querySelector('.auth-config')).not.toBeNull();
      expect(screen.container.querySelector('.resource-auth-selector')).toBeNull();

      gatewayStore.setCurrentGateway({
        id: 42,
        name: 'demo-gateway',
        oauth2_app_enabled: true,
        allow_update_gateway_auth: true,
      });
      await nextTick();
      expect(screen.container.querySelector('.resource-auth-selector')).not.toBeNull();
      expect(screen.container.querySelector('.auth-config')).toBeNull();
    });
  });

  describe('独立选择器 compact 模式', () => {
    it('ResourceAuthSelector 与 LegacyResourceAuthSelector 在 compact=true 时均正确附加 is-compact 类', async () => {
      const router = await createTestRouter();
      const v2Model = ref<IResourceAuthFormConfig>({ ...DEFAULT_AUTH_CONFIG });
      const v1Model = ref<IResourceAuthFormConfig>({ ...DEFAULT_AUTH_CONFIG });

      const CompactHost = () => h('div', [
        h(ResourceAuthSelector, {
          'authConfig': v2Model.value,
          'onUpdate:authConfig': (val: IResourceAuthFormConfig) => {
            v2Model.value = val;
          },
          'compact': true,
        }),
        h(LegacyResourceAuthSelector, {
          'authConfig': v1Model.value,
          'onUpdate:authConfig': (val: IResourceAuthFormConfig) => {
            v1Model.value = val;
          },
          'compact': true,
        }),
      ]);

      const { screen } = await renderWithApp(CompactHost, {
        global: {
          plugins: [router],
          components: AUTH_EXTRA_COMPONENTS,
          directives: AUTH_EXTRA_DIRECTIVES,
        },
      });

      expect(screen.container.querySelector('.resource-auth-selector')?.classList.contains('is-compact')).toBe(true);
      expect(screen.container.querySelector('.auth-config')?.classList.contains('is-compact')).toBe(true);
    });
  });
});
