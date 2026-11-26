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

import { defineComponent, h, nextTick } from 'vue';
import { createPinia, setActivePinia } from 'pinia';
import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useGateway } from '@/stores';
import type { ActionType, IAuthConfig } from '@/types/resource';
import type { IImportPreviewGroups } from '../types';

const {
  checkResourceImportMock,
  pushMock,
} = vi.hoisted(() => ({
  checkResourceImportMock: vi.fn(),
  pushMock: vi.fn(),
}));

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>();
  return {
    ...actual,
    onBeforeRouteLeave: vi.fn(),
    useRouter: () => ({
      push: pushMock,
    }),
  };
});

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>();
  return {
    ...actual,
    useI18n: () => ({ t: (key: string) => key }),
  };
});

vi.mock('bkui-vue', () => ({
  InfoBox: vi.fn(),
  Message: vi.fn(),
}));

vi.mock('@/services/source/gateway/resource', () => ({
  checkResourceImport: checkResourceImportMock,
  importResource: vi.fn(),
}));

vi.mock('../components/ResourceImportEditor.vue', () => ({
  default: {
    name: 'ResourceImportEditorStub',
    emits: ['validate'],
    template: '<div class="import-editor-stub" />',
    methods: {
      getSourceSnapshot: () => ({
        content: 'swagger: "2.0"',
        isCurrent: () => true,
      }),
    },
  },
}));

vi.mock('../components/ResourceImportPreview.vue', () => ({
  default: defineComponent({
    name: 'ResourceImportPreviewStub',

    props: {
      groups: {
        type: Object,
        required: true,
      },
    },

    emits: ['update-auth-config'],

    setup(props, { emit, expose }) {
      expose({
        getGroups: () => props.groups as IImportPreviewGroups,
        triggerUpdateAuthConfig: (action: ActionType, config: IAuthConfig) => {
          emit('update-auth-config', action, config);
        },
      });
      return () => h('div', { class: 'import-preview-stub' });
    },
  }),
}));

vi.mock('../components/ResourceImportResult.vue', () => ({
  default: {
    name: 'ResourceImportResultStub',
    template: '<div class="import-result-stub" />',
  },
}));

import ResourceImportPage from '../Index.vue';

interface IStubImportedResource {
  id: number | null
  name: string
  method: string
  path: string
  is_public: boolean
  allow_apply_permission: boolean
  change_type: 'add' | 'update'
  auth_config?: Partial<IAuthConfig>
  backend: {
    name: string
    config: {
      method: string
      path: string
      match_subpath: boolean
      timeout: number
    }
  }
}

const createImportedRow = (
  overrides: Partial<IStubImportedResource> & Pick<IStubImportedResource, 'name'>,
): IStubImportedResource => ({
  id: null,
  method: 'GET',
  path: `/api/v1/${overrides.name}/`,
  is_public: true,
  allow_apply_permission: true,
  change_type: 'add',
  backend: {
    name: 'default',
    config: {
      method: 'GET',
      path: `/${overrides.name}/`,
      match_subpath: false,
      timeout: 30,
    },
  },
  ...overrides,
});

const mountImportPreview = async (options: {
  oauth2AppEnabled: boolean
  allowUpdateGatewayAuth: boolean
  resources: IStubImportedResource[]
}) => {
  checkResourceImportMock.mockResolvedValue(options.resources);

  const pinia = createPinia();
  setActivePinia(pinia);
  useGateway().setCurrentGateway({
    id: 42,
    name: 'demo-gw',
    kind: 0,
    oauth2_app_enabled: options.oauth2AppEnabled,
    allow_update_gateway_auth: options.allowUpdateGatewayAuth,
  });

  const wrapper = mount(ResourceImportPage, {
    props: {
      gatewayId: 42,
    },
    global: {
      plugins: [pinia],
      directives: {
        'bk-tooltips': {},
      },
      stubs: {
        BkSteps: { template: '<div />' },
        BkDialog: { template: '<div><slot /></div>' },
        BkButton: {
          emits: ['click'],
          template: '<button type="button" @click="$emit(\'click\')"><slot /></button>',
        },
      },
    },
  });

  // 先完成语法检测使「下一步」可用，再点击「下一步」进入资源信息确认预览页
  wrapper.findComponent({ name: 'ResourceImportEditorStub' }).vm.$emit('validate');
  await flushPromises();
  await nextTick();

  const nextStepBtn = wrapper.findAll('button').find(btn => btn.text().trim() === '下一步')!;
  await nextStepBtn.trigger('click');
  await flushPromises();
  await nextTick();

  const previewVm = wrapper.findComponent({ name: 'ResourceImportPreviewStub' }).vm as unknown as {
    getGroups: () => IImportPreviewGroups
    triggerUpdateAuthConfig: (action: ActionType, config: IAuthConfig) => void
  };

  return {
    previewVm,
    wrapper,
  };
};

describe('views/resource-management/settings/import 批量修改认证方式', () => {
  beforeEach(() => {
    checkResourceImportMock.mockReset();
    pushMock.mockReset();
  });

  it('V1 且网关禁止修改应用认证时，批量操作保留各行原有的应用认证、权限校验与公开客户端设置，并联动允许申请权限', async () => {
    const { previewVm, wrapper } = await mountImportPreview({
      oauth2AppEnabled: false,
      allowUpdateGatewayAuth: false,
      resources: [
        // 行 0：原行开启应用认证但关闭权限校验
        createImportedRow({
          name: 'app_no_perm',
          is_public: true,
          allow_apply_permission: false,
          auth_config: {
            auth_verified_required: false,
            app_verified_required: true,
            resource_perm_required: false,
            oauth2_personal_client_enabled: false,
            oauth2_public_client_enabled: false,
          },
        }),
        // 行 1：原行关闭应用认证，同时带有不合法的历史 allow_apply_permission=true
        createImportedRow({
          name: 'no_app_auth',
          is_public: true,
          allow_apply_permission: true,
          auth_config: {
            auth_verified_required: false,
            app_verified_required: false,
            resource_perm_required: false,
            oauth2_personal_client_enabled: false,
            oauth2_public_client_enabled: false,
          },
        }),
        // 行 2：原行完整开启应用认证、权限校验与公开客户端
        createImportedRow({
          name: 'full_auth',
          is_public: true,
          allow_apply_permission: true,
          auth_config: {
            auth_verified_required: true,
            app_verified_required: true,
            resource_perm_required: true,
            oauth2_personal_client_enabled: false,
            oauth2_public_client_enabled: true,
          },
        }),
        // 行 3：原行缺少 auth_config，应安全回落默认开启应用认证与权限校验
        createImportedRow({
          name: 'missing_auth',
          is_public: true,
          allow_apply_permission: true,
          auth_config: undefined,
        }),
      ],
    });

    // 模拟 V1 批量弹窗提交：锁定字段默认携带 true，但用户实际仅启用了用户认证与个人令牌
    previewVm.triggerUpdateAuthConfig('add', {
      auth_verified_required: true,
      app_verified_required: true,
      resource_perm_required: true,
      oauth2_personal_client_enabled: true,
      oauth2_public_client_enabled: false,
    });
    await nextTick();

    const rows = previewVm.getGroups().add;
    expect(rows[0].auth_config).toEqual({
      auth_verified_required: true,
      app_verified_required: true,
      resource_perm_required: false,
      oauth2_personal_client_enabled: true,
      oauth2_public_client_enabled: false,
    });
    expect(rows[0].allow_apply_permission).toBe(false);

    expect(rows[1].auth_config).toEqual({
      auth_verified_required: true,
      app_verified_required: false,
      resource_perm_required: false,
      oauth2_personal_client_enabled: true,
      oauth2_public_client_enabled: false,
    });
    expect(rows[1].allow_apply_permission).toBe(false);

    expect(rows[2].auth_config).toEqual({
      auth_verified_required: true,
      app_verified_required: true,
      resource_perm_required: true,
      oauth2_personal_client_enabled: true,
      oauth2_public_client_enabled: true,
    });
    expect(rows[2].allow_apply_permission).toBe(true);

    expect(rows[3].auth_config).toEqual({
      auth_verified_required: true,
      app_verified_required: true,
      resource_perm_required: true,
      oauth2_personal_client_enabled: true,
      oauth2_public_client_enabled: false,
    });
    expect(rows[3].allow_apply_permission).toBe(true);

    wrapper.unmount();
  });

  it('V1 且允许修改应用认证时，批量操作覆盖应用认证与权限校验并联动清空允许申请权限与无效公开客户端', async () => {
    const { previewVm, wrapper } = await mountImportPreview({
      oauth2AppEnabled: false,
      allowUpdateGatewayAuth: true,
      resources: [
        createImportedRow({
          name: 'editable_v1',
          is_public: true,
          allow_apply_permission: true,
          auth_config: {
            auth_verified_required: true,
            app_verified_required: true,
            resource_perm_required: true,
            oauth2_personal_client_enabled: true,
            oauth2_public_client_enabled: true,
          },
        }),
      ],
    });

    // 关闭用户认证与权限校验，仅保留应用认证
    previewVm.triggerUpdateAuthConfig('add', {
      auth_verified_required: false,
      app_verified_required: true,
      resource_perm_required: false,
      oauth2_personal_client_enabled: false,
      oauth2_public_client_enabled: false,
    });
    await nextTick();

    const [row] = previewVm.getGroups().add;
    expect(row.auth_config).toEqual({
      auth_verified_required: false,
      app_verified_required: true,
      resource_perm_required: false,
      oauth2_personal_client_enabled: false,
      oauth2_public_client_enabled: false,
    });
    expect(row.allow_apply_permission).toBe(false);

    wrapper.unmount();
  });

  it('V2 模式下，批量操作整体写入包含公开客户端在内的认证配置并联动允许申请权限', async () => {
    const { previewVm, wrapper } = await mountImportPreview({
      oauth2AppEnabled: true,
      allowUpdateGatewayAuth: false,
      resources: [
        createImportedRow({
          name: 'v2_resource',
          is_public: true,
          allow_apply_permission: true,
          auth_config: {
            auth_verified_required: true,
            app_verified_required: true,
            resource_perm_required: true,
            oauth2_personal_client_enabled: false,
            oauth2_public_client_enabled: false,
          },
        }),
      ],
    });

    // V2 切换为仅用户认证（公开客户端，不含 OAuth / 应用认证）
    previewVm.triggerUpdateAuthConfig('add', {
      auth_verified_required: true,
      app_verified_required: false,
      resource_perm_required: false,
      oauth2_personal_client_enabled: false,
      oauth2_public_client_enabled: true,
    });
    await nextTick();

    const [row] = previewVm.getGroups().add;
    expect(row.auth_config).toEqual({
      auth_verified_required: true,
      app_verified_required: false,
      resource_perm_required: false,
      oauth2_personal_client_enabled: false,
      oauth2_public_client_enabled: true,
    });
    expect(row.allow_apply_permission).toBe(false);

    wrapper.unmount();
  });
});
