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
  <!-- 基础信息面板 -->
  <BkCollapsePanel name="baseInfo">
    <template #header>
      <div class="panel-header">
        <AngleUpFill :class="getIconClass('baseInfo')" />
        <div class="title">
          {{ t('基础信息') }}
        </div>
      </div>
    </template>
    <template #content>
      <BaseInfo
        ref="baseInfoRef"
        :detail="resourceDetail"
        :is-clone="isClone"
      />
    </template>
  </BkCollapsePanel>

  <!-- 请求配置面板 -->
  <BkCollapsePanel name="frontConfig">
    <template #header>
      <div class="panel-header">
        <AngleUpFill :class="getIconClass('frontConfig')" />
        <div class="title">
          {{ t('请求配置') }}
        </div>
      </div>
    </template>
    <template #content>
      <FrontConfig
        ref="frontConfigRef"
        :detail="resourceDetail"
        :is-clone="isClone"
        @change="handleFrontConfigChange"
      />
    </template>
  </BkCollapsePanel>

  <!-- 普通API独有：请求参数 -->
  <BkCollapsePanel name="requestParams">
    <template #header>
      <div class="panel-header">
        <AngleUpFill :class="getIconClass('requestParams')" />
        <div class="title">
          {{ t('请求参数') }}
        </div>
        <div class="sub-title">
          {{ t('非必填，可用于生成文档、在线调试、生成 MCP Server 等') }}
        </div>
      </div>
    </template>
    <template #content>
      <RequestParams
        ref="requestParamsRef"
        v-model:is-no-params="hasNoRequestParams"
        :detail="resourceDetail"
      />
    </template>
  </BkCollapsePanel>

  <!-- 后端配置 -->
  <BkCollapsePanel name="backConfig">
    <template #header>
      <div class="panel-header">
        <AngleUpFill :class="getIconClass('backConfig')" />
        <div class="title">
          {{ t('后端配置') }}
        </div>
      </div>
    </template>
    <template #content>
      <BackConfig
        ref="backConfigRef"
        :detail="resourceDetail"
        :front-config="frontConfig"
        @service-init="handleServiceInit"
      />
    </template>
  </BkCollapsePanel>

  <!-- 普通API独有：响应参数 -->
  <BkCollapsePanel name="responseParams">
    <template #header>
      <div class="panel-header">
        <AngleUpFill :class="getIconClass('responseParams')" />
        <div class="title">
          {{ t('响应参数') }}
        </div>
        <div class="sub-title">
          {{ t('非必填，可用于生成文档、在线调试、生成 MCP Server 等') }}
        </div>
      </div>
    </template>
    <template #content>
      <ResponseParams
        ref="responseParamsRef"
        :detail="resourceDetail"
      />
    </template>
  </BkCollapsePanel>
</template>

<script setup lang="ts">
import { AngleUpFill } from 'bkui-vue/lib/icon';
import { t } from '@/locales';
import BaseInfo from '@/views/resource-management/components/BaseInfo.vue';
import FrontConfig from '@/views/resource-management/components/FrontConfig.vue';
import RequestParams from '@/views/resource-management/components/request-params/Index.vue';
import BackConfig from '@/views/resource-management/components/BackConfig.vue';
import ResponseParams from '@/views/resource-management/components/response-params/Index.vue';

interface IProps {
  resourceDetail?: Record<string, any>
  isClone?: boolean
  activeIndex?: string[]
  frontConfig?: {
    path: string
    method: string
    match_subpath: boolean
    enable_websocket: boolean
  }
}

interface IEmits {
  'front-config-change': [config: typeof frontConfig]
  'service-init': [void]
}

const hasNoRequestParams = defineModel('hasNoRequestParams', {
  type: Boolean,
  default: true,
});

const {
  isClone = false,
  resourceDetail = {},
  frontConfig = {
    path: '',
    method: '',
    match_subpath: false,
    enable_websocket: false,
  },
  activeIndex = [],
} = defineProps<IProps>();

const emits = defineEmits<IEmits>();

const baseInfoRef = ref<InstanceType<typeof BaseInfo>>();
const frontConfigRef = ref<InstanceType<typeof FrontConfig>>();
const requestParamsRef = ref<InstanceType<typeof RequestParams>>();
const backConfigRef = ref<InstanceType<typeof BackConfig>>();
const responseParamsRef = ref<InstanceType<typeof ResponseParams>>();

const getIconClass = (activeCollapse: string) => {
  return activeIndex?.includes(activeCollapse) ? 'panel-header-show' : 'panel-header-hide';
};

const handleServiceInit = () => {
  emits('service-init');
};

const handleFrontConfigChange = (config: typeof frontConfig) => {
  emits('front-config-change', config);
};

defineExpose({
  baseInfoRef,
  backConfigRef,
  frontConfigRef,
  requestParamsRef,
  responseParamsRef,
});
</script>
