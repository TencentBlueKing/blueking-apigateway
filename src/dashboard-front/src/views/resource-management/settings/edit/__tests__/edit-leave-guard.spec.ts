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

import { defineComponent, h, nextTick, proxyRefs, ref, watch } from 'vue';
import { createPinia, setActivePinia } from 'pinia';
import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useGateway } from '@/stores';
import { DEFAULT_AUTH_CONFIG } from '@/utils/auth-config';

const {
  backMock,
  getResourceDetailMock,
  popInfoBoxMock,
  pushMock,
  routeState,
  triggerAsyncServiceInit,
} = vi.hoisted(() => ({
  backMock: vi.fn(),
  getResourceDetailMock: vi.fn(),
  popInfoBoxMock: vi.fn(),
  pushMock: vi.fn(),
  routeState: {
    name: 'ResourceCreate',
    params: {
      id: '42',
      resourceId: undefined as string | undefined,
    },
    query: {} as Record<string, string>,
  },
  triggerAsyncServiceInit: { current: null as (() => void) | null },
}));

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>();
  return {
    ...actual,
    useRoute: () => routeState,
    useRouter: () => ({
      back: backMock,
      push: pushMock,
    }),
  };
});

vi.mock('@vueuse/router', () => ({
  useRouteParams: () => ref(42),
}));

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>();
  return {
    ...actual,
    useI18n: () => ({ t: (key: string) => key }),
  };
});

vi.mock('@/hooks/use-pop-info-box', () => ({
  usePopInfoBox: popInfoBoxMock,
}));

vi.mock('@/services/source/gateway/resource', () => ({
  createResources: vi.fn(),
  getResourceDetail: getResourceDetailMock,
  updateResources: vi.fn(),
}));

interface IStubResourceDetail {
  name?: string
  description?: string
  path?: string
  method?: string
  match_subpath?: boolean
  enable_websocket?: boolean
  is_public?: boolean
  allow_apply_permission?: boolean
  auth_config?: Partial<typeof DEFAULT_AUTH_CONFIG>
  backend?: {
    id?: number
    config?: {
      path?: string
      method?: string
      timeout?: number
    }
  }
}

// 精简子表单存根，真实保留 AuthConfig 状态与 BackConfig 异步 service-init 时序
vi.mock('../components/Standard.vue', () => ({
  default: defineComponent({
    name: 'StandardStub',

    props: {
      resourceDetail: {
        type: Object,
        default: () => ({}),
      },

      isClone: {
        type: Boolean,
        default: false,
      },
    },

    emits: ['service-init'],

    setup(props, { emit, expose }) {
      const baseFormData = ref({
        name: '',
        description: '',
        label_ids: [] as number[],
      });
      const authFormData = ref({
        auth_config: { ...DEFAULT_AUTH_CONFIG },
        is_public: true,
        allow_apply_permission: true,
      });
      const frontConfigData = ref({
        path: '',
        method: 'GET',
        match_subpath: false,
        enable_websocket: false,
      });
      const backConfigData = ref({
        id: 0,
        name: '',
        config: {
          path: '',
          method: 'GET',
          match_subpath: false,
          timeout: 0,
        },
      });

      watch(
        () => props.resourceDetail,
        (detail: IStubResourceDetail) => {
          if (detail && Object.keys(detail).length) {
            baseFormData.value = {
              name: props.isClone ? `${detail.name}_clone` : (detail.name ?? ''),
              description: detail.description ?? '',
              label_ids: [],
            };
            authFormData.value = {
              auth_config: {
                ...DEFAULT_AUTH_CONFIG,
                ...detail.auth_config,
              },
              is_public: detail.is_public ?? true,
              allow_apply_permission: Boolean(detail.allow_apply_permission),
            };
            frontConfigData.value = {
              path: detail.path ?? '',
              method: detail.method ?? 'GET',
              match_subpath: Boolean(detail.match_subpath),
              enable_websocket: Boolean(detail.enable_websocket),
            };
            backConfigData.value = {
              id: detail.backend?.id ?? 0,
              name: '',
              config: {
                path: detail.backend?.config?.path ?? '',
                method: detail.backend?.config?.method ?? 'GET',
                match_subpath: false,
                timeout: detail.backend?.config?.timeout ?? 0,
              },
            };
            // 模拟 BackConfig.handleServiceChange 异步回填 backend.name 后抛出 service-init
            triggerAsyncServiceInit.current = () => {
              backConfigData.value.name = 'default-backend';
              emit('service-init');
            };
          }
        },
        { immediate: true },
      );

      expose({
        baseInfoRef: proxyRefs({ formData: baseFormData }),
        authConfigRef: proxyRefs({ formData: authFormData }),
        frontConfigRef: proxyRefs({ frontConfigData }),
        backConfigRef: proxyRefs({ backConfigData }),
      });

      return () => h('div', { class: 'standard-stub' });
    },
  }),
}));

vi.mock('../components/ModelProxy.vue', () => ({
  default: {
    name: 'ModelProxyStub',
    template: '<div class="model-proxy-stub" />',
  },
}));

import ResourceEditPage from '../Index.vue';

const MOCK_DETAIL = {
  id: 101,
  name: 'get_orders',
  description: '查询订单',
  method: 'GET',
  path: '/api/v1/orders/',
  match_subpath: false,
  enable_websocket: false,
  is_public: true,
  allow_apply_permission: true,
  auth_config: { ...DEFAULT_AUTH_CONFIG },
  backend: {
    id: 7,
    config: {
      method: 'GET',
      path: '/orders/',
      match_subpath: false,
      timeout: 30,
    },
  },
  schema: { none_schema: false },
};

const mountEditPage = async () => {
  const pinia = createPinia();
  setActivePinia(pinia);
  useGateway().setCurrentGateway({
    id: 42,
    name: 'demo-gw',
    kind: 0,
    oauth2_app_enabled: true,
  });

  const wrapper = mount(ResourceEditPage, {
    global: {
      plugins: [pinia],
      stubs: {
        BkLoading: { template: '<div><slot /></div>' },
        BkCollapse: { template: '<div><slot /></div>' },
        BkButton: {
          emits: ['click'],
          template: '<button type="button" @click="$emit(\'click\')"><slot /></button>',
        },
      },
    },
  });

  await flushPromises();
  await nextTick();
  return wrapper;
};

const clickCancelButton = async (wrapper: ReturnType<typeof mount>) => {
  const cancelBtn = wrapper.findAll('button').find(btn => btn.text().trim() === '取消')!;
  await cancelBtn.trigger('click');
  await flushPromises();
};

describe('views/resource-management/settings/edit 未保存离开确认', () => {
  beforeEach(() => {
    backMock.mockReset();
    pushMock.mockReset();
    popInfoBoxMock.mockReset();
    getResourceDetailMock.mockReset();
    triggerAsyncServiceInit.current = null;
    routeState.name = 'ResourceCreate';
    routeState.params = {
      id: '42',
      resourceId: undefined,
    };
    routeState.query = {};
  });

  it('新建模式：未修改直接取消不弹窗直接返回；修改认证方式后取消弹出确认框并响应取消/离开', async () => {
    const wrapper = await mountEditPage();

    // 未改动直接取消 → 不弹窗，直接 router.back
    await clickCancelButton(wrapper);
    expect(popInfoBoxMock).not.toHaveBeenCalled();
    expect(backMock).toHaveBeenCalledTimes(1);

    // 修改认证配置后点击取消 → 弹出确认框，点「取消」留在当前页，点「离开」才返回
    backMock.mockClear();
    const stubVm = wrapper.findComponent({ name: 'StandardStub' }).vm as unknown as {
      authConfigRef: { formData: { is_public: boolean } }
    };
    stubVm.authConfigRef.formData.is_public = false;
    await nextTick();

    popInfoBoxMock.mockImplementationOnce((opts: { onCancel?: () => void }) => {
      opts.onCancel?.();
    });
    await clickCancelButton(wrapper);
    expect(popInfoBoxMock).toHaveBeenCalledTimes(1);
    expect(backMock).not.toHaveBeenCalled();

    popInfoBoxMock.mockImplementationOnce((opts: { onConfirm?: () => void }) => {
      opts.onConfirm?.();
    });
    await clickCancelButton(wrapper);
    expect(popInfoBoxMock).toHaveBeenCalledTimes(2);
    expect(backMock).toHaveBeenCalledTimes(1);

    wrapper.unmount();
  });

  it('编辑模式：异步 service-init 回填后端名称后重打快照，未改动直接取消不误弹窗，修改后取消弹出确认框', async () => {
    routeState.name = 'ResourceEdit';
    routeState.params.resourceId = '101';
    getResourceDetailMock.mockResolvedValueOnce(MOCK_DETAIL);

    const wrapper = await mountEditPage();

    // 触发 BackConfig 异步拉取详情并回填 backConfigData.name → emit('service-init')
    expect(triggerAsyncServiceInit.current).not.toBeNull();
    triggerAsyncServiceInit.current!();
    await nextTick();
    await nextTick();

    // 未做用户改动直接点取消 → 不应因异步回填 backend.name 而误报未保存
    await clickCancelButton(wrapper);
    expect(popInfoBoxMock).not.toHaveBeenCalled();
    expect(backMock).toHaveBeenCalledTimes(1);

    // 修改认证开关后再取消 → 正常弹出未保存确认框
    backMock.mockClear();
    const stubVm = wrapper.findComponent({ name: 'StandardStub' }).vm as unknown as {
      authConfigRef: { formData: { auth_config: { resource_perm_required: boolean } } }
    };
    stubVm.authConfigRef.formData.auth_config.resource_perm_required = false;
    await nextTick();

    popInfoBoxMock.mockImplementationOnce((opts: { onConfirm?: () => void }) => {
      opts.onConfirm?.();
    });
    await clickCancelButton(wrapper);
    expect(popInfoBoxMock).toHaveBeenCalledTimes(1);
    expect(backMock).toHaveBeenCalledTimes(1);

    wrapper.unmount();
  });

  it('克隆模式：加载源资源并完成 service-init 后，未改动取消不弹窗，修改认证方式后取消弹出确认框', async () => {
    routeState.name = 'ResourceClone';
    routeState.params.resourceId = '101';
    getResourceDetailMock.mockResolvedValueOnce(MOCK_DETAIL);

    const wrapper = await mountEditPage();
    triggerAsyncServiceInit.current!();
    await nextTick();
    await nextTick();

    await clickCancelButton(wrapper);
    expect(popInfoBoxMock).not.toHaveBeenCalled();
    expect(backMock).toHaveBeenCalledTimes(1);

    backMock.mockClear();
    const stubVm = wrapper.findComponent({ name: 'StandardStub' }).vm as unknown as {
      authConfigRef: { formData: { allow_apply_permission: boolean } }
    };
    stubVm.authConfigRef.formData.allow_apply_permission = false;
    await nextTick();

    popInfoBoxMock.mockImplementationOnce((opts: { onCancel?: () => void }) => {
      opts.onCancel?.();
    });
    await clickCancelButton(wrapper);
    expect(popInfoBoxMock).toHaveBeenCalledTimes(1);
    expect(backMock).not.toHaveBeenCalled();

    wrapper.unmount();
  });
});
