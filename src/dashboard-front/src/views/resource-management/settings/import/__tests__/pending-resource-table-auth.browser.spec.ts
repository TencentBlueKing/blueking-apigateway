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

import { defineComponent, h, nextTick, ref } from 'vue';
import { createMemoryHistory, createRouter } from 'vue-router';
import { Alert, Checkbox, PopConfirm, Switcher } from 'bkui-vue';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { renderWithApp } from '@/components/__tests__/browser-render';
import { AG_TABLE_CONTEXT_KEY } from '@/components/base/ag-table/context';
import { useGateway } from '@/stores';
import type { ActionType, ILocalImportedResource, IPublicConfig, IResourceAuthFormConfig } from '@/types/resource';
import { DEFAULT_AUTH_CONFIG } from '@/utils/auth-config';
import PendingResourceTable from '../components/PendingResourceTable.vue';

interface IMountPendingTableOptions {
  gateway?: {
    id: number
    name: string
    oauth2_app_enabled: boolean
    allow_update_gateway_auth: boolean
  } | null
}

const SAMPLE_ROWS: ILocalImportedResource[] = [
  {
    _localId: 0,
    _unchecked: false,
    id: null,
    name: 'get_users',
    method: 'GET',
    path: '/api/v1/users/',
    is_public: true,
    allow_apply_permission: true,
    auth_config: { ...DEFAULT_AUTH_CONFIG },
    backend: {
      name: 'default',
      config: {
        method: 'GET',
        path: '/users/',
        match_subpath: false,
        timeout: 30,
      },
    },
  },
];

const mountPendingTable = async (options: IMountPendingTableOptions = {}) => {
  const {
    gateway = {
      id: 1,
      name: 'demo-gw',
      oauth2_app_enabled: true,
      allow_update_gateway_auth: true,
    },
  } = options;

  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: '/:id/resource/import',
        name: 'ResourceImport',
        component: { template: '<div />' },
      },
      {
        path: '/:id/permission/app',
        name: 'PermissionApp',
        component: { template: '<div />' },
      },
    ],
  });
  await router.push('/1/resource/import');
  await router.isReady();

  const tempPublicConfig = ref<IPublicConfig>({
    is_public: true,
    allow_apply_permission: true,
  });
  const confirmCalls: Array<[ActionType, IResourceAuthFormConfig]> = [];

  const Host = defineComponent({
    setup() {
      const gatewayStore = useGateway();
      if (gateway) {
        gatewayStore.setCurrentGateway(gateway);
      }

      return () => h(PendingResourceTable, {
        'action': 'add',
        'tableData': SAMPLE_ROWS,
        'tempPublicConfig': tempPublicConfig.value,
        'onUpdate:tempPublicConfig': (val: IPublicConfig) => {
          tempPublicConfig.value = val;
        },
        'onConfirmAuthConfig': (action: ActionType, config: IResourceAuthFormConfig) => {
          confirmCalls.push([action, { ...config }]);
        },
      });
    },
  });

  const { screen } = await renderWithApp(Host, {
    global: {
      plugins: [router],
      provide: {
        [AG_TABLE_CONTEXT_KEY as symbol]: { getNoticeHeight: () => 0 },
      },
      components: {
        BkAlert: Alert,
        BkCheckbox: Checkbox,
        BkCheckboxGroup: Checkbox.Group,
        BkPopConfirm: PopConfirm,
        BkSwitcher: Switcher,
      },
      directives: {
        'bk-overflow-tips': {},
      },
    },
  });

  return {
    confirmCalls,
    gatewayStore: useGateway(),
    screen,
    tempPublicConfig,
  };
};

// 真实浏览器中 position: fixed 元素的 offsetParent 为 null，统一用样式与几何尺寸判定可见性
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

// 打开认证方式表头的批量修改弹层并返回可见的弹层内容节点
const openAuthBulkPopover = async (container: Element) => {
  const trigger = container.querySelector<HTMLElement>('.auth-config-col-label .edit-action')!;
  expect(trigger).not.toBeNull();
  trigger.click();

  let popoverContent: HTMLElement | undefined;
  await vi.waitFor(() => {
    popoverContent = [...document.querySelectorAll<HTMLElement>('.bk-pop-confirm')]
      .find(el => el.textContent?.includes('批量修改认证方式') && isElementVisible(el));
    expect(popoverContent).not.toBeUndefined();
  });
  return popoverContent!;
};

describe('ResourceImport / PendingResourceTable 批量修改认证方式浏览器测试', () => {
  afterEach(() => {
    document.querySelectorAll('.bk-popover').forEach(node => node.remove());
  });
  it('V2 模式下 allow_update_gateway_auth=false 时，批量弹层应禁用「不认证」并可提交合法配置', async () => {
    const { confirmCalls, screen } = await mountPendingTable({
      gateway: {
        id: 1,
        name: 'demo-gw',
        oauth2_app_enabled: true,
        allow_update_gateway_auth: false,
      },
    });

    const popover = await openAuthBulkPopover(screen.container);
    const noneOption = [...popover.querySelectorAll<HTMLElement>('.auth-option')]
      .find(el => el.textContent?.includes('不认证'))!;
    expect(noneOption.classList.contains('is-disabled')).toBe(true);

    // 尝试点击不认证无效，改为切换到应用认证后确认提交
    noneOption.click();
    await nextTick();
    const appOption = [...popover.querySelectorAll<HTMLElement>('.auth-option')]
      .find(el => el.textContent?.includes('应用认证'))!;
    appOption.click();
    await nextTick();

    const confirmBtn = [...popover.querySelectorAll<HTMLButtonElement>('button')]
      .find(btn => btn.textContent?.trim() === '确定')!;
    confirmBtn.click();
    await nextTick();

    expect(confirmCalls).toEqual([
      [
        'add',
        {
          auth_verified_required: false,
          app_verified_required: true,
          resource_perm_required: true,
          oauth2_personal_client_enabled: false,
          oauth2_public_client_enabled: false,
        },
      ],
    ]);
  });

  it('V1 模式下 allow_update_gateway_auth=false 时，批量弹层禁用应用认证编辑且默认保持应用认证开启', async () => {
    const { confirmCalls, screen } = await mountPendingTable({
      gateway: {
        id: 2,
        name: 'v1-gw',
        oauth2_app_enabled: false,
        allow_update_gateway_auth: false,
      },
    });

    const popover = await openAuthBulkPopover(screen.container);
    const appCheckbox = [...popover.querySelectorAll<HTMLElement>('label.bk-checkbox')]
      .find(el => el.textContent?.trim() === '应用认证')!;
    const userCheckbox = [...popover.querySelectorAll<HTMLElement>('label.bk-checkbox')]
      .find(el => el.textContent?.trim() === '用户认证')!;

    // 网关不允许更新应用认证时，应用认证复选框禁用且默认开启；用户认证仍可正常勾选并提交
    expect(appCheckbox.classList.contains('is-disabled')).toBe(true);
    expect(appCheckbox.classList.contains('is-checked')).toBe(true);
    expect(userCheckbox.classList.contains('is-disabled')).toBe(false);

    userCheckbox.click();
    await Promise.resolve();
    await new Promise<void>((resolve) => {
      setTimeout(resolve, 0);
    });
    await nextTick();

    const confirmBtn = [...popover.querySelectorAll<HTMLButtonElement>('button')]
      .find(btn => btn.textContent?.trim() === '确定')!;
    confirmBtn.click();
    await nextTick();

    expect(confirmCalls).toEqual([
      [
        'add',
        {
          auth_verified_required: true,
          app_verified_required: true,
          resource_perm_required: true,
          oauth2_personal_client_enabled: false,
          oauth2_public_client_enabled: false,
        },
      ],
    ]);
  });

  it('批量修改公开设置关闭「是否公开」时立即清空「允许申请权限」且重开不记忆；V1 取消批量认证后重置内部记忆', async () => {
    const { screen, tempPublicConfig } = await mountPendingTable({
      gateway: {
        id: 3,
        name: 'v1-editable-gw',
        oauth2_app_enabled: false,
        allow_update_gateway_auth: true,
      },
    });

    // 1. 公开设置：关闭「是否公开」时应将 allow_apply_permission 置为 false，再次开启后不恢复旧勾选态
    const publicTrigger = screen.container.querySelector<HTMLElement>('.public-config-col-label .edit-action')!;
    publicTrigger.click();

    let publicPopover: HTMLElement | undefined;
    await vi.waitFor(() => {
      publicPopover = [...document.querySelectorAll<HTMLElement>('.bk-pop-confirm')]
        .find(el => el.textContent?.includes('批量修改公开设置') && isElementVisible(el));
      expect(publicPopover).not.toBeUndefined();
    });

    expect(tempPublicConfig.value).toEqual({
      is_public: true,
      allow_apply_permission: true,
    });
    const publicSwitcher = publicPopover!.querySelector<HTMLElement>('.bk-switcher')!;
    publicSwitcher.click();
    await nextTick();
    expect(tempPublicConfig.value).toEqual({
      is_public: false,
      allow_apply_permission: false,
    });

    // 重新打开「是否公开」后，「允许申请权限」仍为 false
    publicSwitcher.click();
    await nextTick();
    expect(tempPublicConfig.value).toEqual({
      is_public: true,
      allow_apply_permission: false,
    });

    const closePublicBtn = [...publicPopover!.querySelectorAll<HTMLButtonElement>('button')]
      .find(btn => btn.textContent?.trim() === '取消')!;
    closePublicBtn.click();
    await nextTick();

    // 2. V1 认证批量弹层：勾选应用认证与检验应用权限后取消应用认证并点击「取消」，下次再打开勾选应用认证不应残留检验应用权限
    const clickCheckboxAndFlush = async (el: HTMLElement) => {
      el.click();
      await Promise.resolve();
      await new Promise<void>((resolve) => {
        setTimeout(resolve, 0);
      });
      await nextTick();
    };

    const firstPopover = await openAuthBulkPopover(screen.container);
    const firstAppCb = [...firstPopover.querySelectorAll<HTMLElement>('label.bk-checkbox')]
      .find(el => el.textContent?.trim() === '应用认证')!;
    await clickCheckboxAndFlush(firstAppCb);
    const firstPermSwitcher = [...firstPopover.querySelectorAll<HTMLElement>('.auth-child-row')]
      .find(el => el.textContent?.includes('检验应用权限'))!
      .querySelector<HTMLElement>('.bk-switcher')!;
    firstPermSwitcher.click();
    await nextTick();
    expect(firstPermSwitcher.classList.contains('is-checked')).toBe(true);

    // 取消勾选应用认证（记录 previousResourcePermission=true），随后点击「取消」按钮重置
    await clickCheckboxAndFlush(firstAppCb);
    const cancelAuthBtn = [...firstPopover.querySelectorAll<HTMLButtonElement>('button')]
      .find(btn => btn.textContent?.trim() === '取消')!;
    cancelAuthBtn.click();
    await nextTick();

    // 再次打开批量修改认证方式并勾选应用认证：检验应用权限应保持关闭，不继承上次取消前的记忆
    const secondPopover = await openAuthBulkPopover(screen.container);
    const secondAppCb = [...secondPopover.querySelectorAll<HTMLElement>('label.bk-checkbox')]
      .find(el => el.textContent?.trim() === '应用认证')!;
    await clickCheckboxAndFlush(secondAppCb);
    const secondPermSwitcher = [...secondPopover.querySelectorAll<HTMLElement>('.auth-child-row')]
      .find(el => el.textContent?.includes('检验应用权限'))!
      .querySelector<HTMLElement>('.bk-switcher')!;
    expect(secondPermSwitcher.classList.contains('is-checked')).toBe(false);
  });
});
