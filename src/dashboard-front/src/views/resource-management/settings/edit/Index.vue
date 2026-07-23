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

<template>
  <div class="resource-config-create-wrapper">
    <BkCollapse
      v-model="activeIndex"
      class="page-wrapper-padding collapse-cls"
      use-card-theme
    >
      <Component
        :is="compMap[activeComp]"
        ref="childCompRef"
        v-model:active-index="activeIndex"
        v-model:has-no-request-params="hasNoRequestParams"
        :resource-detail="resourceDetail"
        :front-config="frontConfig"
        :is-clone="isClone"
        @front-config-change="handleFrontConfigChange"
        @service-init="handleSetFormDataBack"
      />
    </BkCollapse>
    <div class="edit-footer">
      <BkButton
        theme="primary"
        class="min-w-88px ml-24px"
        :loading="submitLoading"
        @click="handleSubmit"
      >
        {{ t('提交') }}
      </BkButton>
      <BkButton
        class="min-w-88px ml-8px"
        @click="handleCancel"
      >
        {{ t('取消') }}
      </BkButton>
    </div>
  </div>
</template>

<script setup lang="tsx">
import { Message } from 'bkui-vue';
import { useRouteParams } from '@vueuse/router';
import { useSidebar } from '@/hooks';
import { useGateway } from '@/stores';
import {
  createResources,
  getResourceDetail,
  updateResources,
} from '@/services/source/resource';
import Standard from './Standard.vue';
import ModelProxy from './ModelProxy.vue';

type ChildCompInstance = InstanceType<typeof Standard> | InstanceType<typeof ModelProxy>;

const { initSidebarFormData, isSidebarClosed } = useSidebar();
const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const gatewayStore = useGateway();
const gatewayId = useRouteParams('id', 0, { transform: Number });

const compMap: Record<string, Component> = {
  standard: Standard,
  modelProxy: ModelProxy,
};

const childCompRef = ref<ChildCompInstance | null>(null);
const submitLoading = ref(false);
const hasNoRequestParams = ref(true);
const resourceId = ref(0);
const activeIndex = ref<string[]>(['baseInfo', 'frontConfig', 'backConfig']);
const resourceDetail = ref<Record<string, any>>({});
const formDataBack = ref<Record<string, any>>({});
const frontConfig = ref({
  path: '',
  method: 'GET',
  match_subpath: false,
  enable_websocket: false,
});

const isClone = computed(() => route.name === 'ResourceClone');
const activeComp = computed(() => gatewayStore.isAIGateway && route.query.kind === 'ai' ? 'modelProxy' : 'standard');

const init = async () => {
  const resourceIdParams = route.params.resourceId;
  if (resourceIdParams) {
    resourceId.value = Number(resourceIdParams);
    await getResourceDetails();
  }
};

const getResourceDetails = async () => {
  const res = await getResourceDetail(gatewayId.value, resourceId.value);
  const {
    none_schema = false,
    requestBody = {},
    parameters = [],
  } = ((res?.schema as unknown) as Record<string, any> | null) ?? {};

  // 判断是否无请求参数
  if (none_schema) {
    hasNoRequestParams.value = true;
  }
  else {
    const hasParams = parameters.length > 0 || Object.keys(requestBody).length > 0;
    hasNoRequestParams.value = !hasParams;
  }
  resourceDetail.value = res;
};

const handleSubmit = async () => {
  const {
    baseInfoRef,
    backConfigRef,
    frontConfigRef,
    requestParamsRef,
    responseParamsRef,
  } = (childCompRef.value as any) ?? {};

  try {
    await Promise.all([
      baseInfoRef?.validate(),
      frontConfigRef?.validate(),
      backConfigRef?.validate(),
    ]);
  }
  catch {
    const invalidFormElementIds = [
      ...(baseInfoRef?.invalidFormElementIds ?? []),
      ...(frontConfigRef?.invalidFormElementIds ?? []),
      ...(backConfigRef?.invalidFormElementIds ?? []),
    ];

    if (invalidFormElementIds.length) {
      const el = document.querySelector(`#${invalidFormElementIds[0]}`) as HTMLInputElement;
      if (el) {
        el.scrollIntoView({
          behavior: 'smooth',
          block: 'center',
        });
        el.focus?.();
      }
    }
    return;
  }

  try {
    submitLoading.value = true;

    const baseFormData = baseInfoRef?.formData ?? {};
    const frontFormData = frontConfigRef?.frontConfigData ?? {};
    const backFormData = backConfigRef?.backConfigData ?? {};
    const requestParamsData = !hasNoRequestParams.value
      ? await requestParamsRef?.getValue()
      : {};
    const responseParamsData = await responseParamsRef?.getValue();

    const params = {
      ...baseFormData,
      ...frontFormData,
      backend: backFormData,
      openapi_schema: {},
    };

    if (hasNoRequestParams.value) {
      params.openapi_schema.none_schema = true;
    }
    else {
      if (requestParamsData?.parameters?.length) {
        params.openapi_schema.parameters = requestParamsData.parameters;
      }
      if (requestParamsData?.requestBody) {
        params.openapi_schema.request_body = requestParamsData.requestBody;
      }
    }

    if (Object.keys(responseParamsData || {}).length) {
      params.openapi_schema.responses = responseParamsData;
    }
    // AI网关模型代理不需要这些表单项
    if (activeComp.value === 'modelProxy') {
      delete params.enable_websocket;
      delete params.match_subpath;
      delete params.openapi_schema;
      params.backend.config = {};
    }

    if (!gatewayStore.isAIGateway) {
      delete params.kind;
    }

    if (resourceId.value && !unref(isClone)) {
      if (activeComp.value !== 'modelProxy') {
        Object.assign(params.openapi_schema, { version: resourceDetail.value.schema.version });
      }
      await updateResources(gatewayId.value, resourceId.value, params);
    }
    else {
      await createResources(gatewayId.value, params);
    }

    formDataBack.value = { ...getFormData };

    Message({
      message: t(`${resourceId.value && !unref(isClone) ? '更新' : '新建'}成功`),
      theme: 'success',
    });

    router.push({
      name: 'ResourceSetting',
      query: { ...route.query },
    });
  }
  finally {
    submitLoading.value = false;
  }
};

const handleCancel = async () => {
  const params = { ...getFormData };
  const result = await isSidebarClosed(JSON.stringify(params));
  if (result) {
    router.back();
  }
};

// 缓存初始表单数据
const handleSetFormDataBack = () => {
  formDataBack.value = { ...getFormData };
  nextTick(() => {
    initSidebarFormData(formDataBack.value);
  });
};

// 获取最新的各个表单配置项数据
const getFormData = () => {
  return {
    baseFormData: childCompRef.value?.baseInfoRef?.formData,
    frontFormData: childCompRef.value?.frontConfigRef?.frontConfigData,
    backFormData: childCompRef.value?.backConfigRef?.backConfigData,
  };
};

// 前端配置变更同步
const handleFrontConfigChange = (config: typeof frontConfig.value) => {
  frontConfig.value = config;
};

onMounted(async () => {
  await init();
  handleSetFormDataBack();
});
</script>

<style lang="scss">
@use "./Index.scss" as *;
</style>
