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
  <div class="model-proxy-wrapper">
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

    <!-- 模型服务配置 -->
    <BkCollapsePanel name="backConfig">
      <template #header>
        <div class="panel-header">
          <AngleUpFill :class="getIconClass('backConfig')" />
          <div class="title">
            {{ t('模型服务配置') }}
          </div>
        </div>
      </template>
      <template #content>
        <BackConfig
          ref="backConfigRef"
          service-label="模型服务"
          is-model-proxy
          :detail="resourceDetail"
          :front-config="frontConfig"
          @service-init="getServiceInit"
        />
      </template>
    </BkCollapsePanel>
  </div>
</template>

<script setup lang="ts">
import { AngleUpFill } from 'bkui-vue/lib/icon';
import { t } from '@/locales';
import BaseInfo from '@/views/resource-management/components/BaseInfo.vue';
import BackConfig from '@/views/resource-management/components/BackConfig.vue';
import FrontConfig from '@/views/resource-management/components/FrontConfig.vue';

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
const backConfigRef = ref<InstanceType<typeof BackConfig>>();
const frontConfigRef = ref<InstanceType<typeof FrontConfig>>();

const getIconClass = (activeCollapse: string) => {
  return activeIndex?.includes(activeCollapse) ? 'panel-header-show' : 'panel-header-hide';
};

const getServiceInit = () => {
  emits('service-init');
};

const handleFrontConfigChange = (config: typeof frontConfig) => {
  emits('front-config-change', config);
};

defineExpose({
  baseInfoRef,
  backConfigRef,
  frontConfigRef,
});
</script>
