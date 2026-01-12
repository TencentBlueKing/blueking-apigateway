/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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
  <div class="edit-container">
    <BkSideslider
      v-model:is-show="renderShow"
      width="960"
      title="修改配置"
      quick-close
      @hidden="handleHidden"
    >
      <template #default>
        <div class="collapse-wrap">
          <BkCollapse
            v-model="activeIndex"
            class="collapse-cls"
            use-card-theme
          >
            <BkCollapsePanel name="baseInfo">
              <template #header>
                <div class="panel-header">
                  <AngleUpFill
                    :class="[activeIndex?.includes('baseInfo') ? 'panel-header-show' : 'panel-header-hide']"
                  />
                  <div class="title">
                    {{ t('基础信息') }}
                  </div>
                </div>
              </template>
              <template #content>
                <BaseInfo
                  ref="baseInfoRef"
                  :detail="resource"
                  :is-labels-editable="false"
                />
              </template>
            </BkCollapsePanel>

            <BkCollapsePanel name="frontConfig">
              <template #header>
                <div class="panel-header">
                  <AngleUpFill
                    :class="[activeIndex?.includes('frontConfig') ? 'panel-header-show' : 'panel-header-hide']"
                  />
                  <div class="title">
                    {{ t('请求配置') }}
                  </div>
                </div>
              </template>
              <template #content>
                <FrontConfig
                  ref="frontConfigRef"
                  :detail="resource"
                />
              </template>
            </BkCollapsePanel>

            <BkCollapsePanel
              name="backConfig"
              :title="t('后端配置')"
            >
              <template #header>
                <div class="panel-header">
                  <AngleUpFill
                    :class="[activeIndex?.includes('backConfig') ? 'panel-header-show' : 'panel-header-hide']"
                  />
                  <div class="title">
                    {{ t('后端配置') }}
                  </div>
                </div>
              </template>
              <template #content>
                <BackConfig
                  ref="backConfigRef"
                  :detail="resource"
                  :front-config="{
                    path: resource?.path || '',
                    method: resource?.method || 'GET',
                    match_subpath: resource?.match_subpath || false,
                    enable_websocket: resource?.enable_websocket || false,
                  }"
                />
              </template>
            </BkCollapsePanel>
          </BkCollapse>
        </div>
      </template>
      <template #footer>
        <div>
          <BkButton
            theme="primary"
            @click="handleSubmit"
          >
            {{ t('保存') }}
          </BkButton>
          <BkButton
            class="ml-8px"
            @click="handleHidden"
          >
            {{ t('取消') }}
          </BkButton>
        </div>
      </template>
    </BkSideslider>
  </div>
</template>

<script setup lang="ts">
import BaseInfo from '@/views/resource-management/components/BaseInfo.vue';
import FrontConfig from '@/views/resource-management/components/FrontConfig.vue';
import BackConfig from '@/views/resource-management/components/BackConfig.vue';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import { type ILocalImportedResource } from '@/types/resource';

interface IProps {
  isSliderShow?: boolean
  resource?: ILocalImportedResource | null
}

const {
  isSliderShow = false,
  resource = null,
} = defineProps<IProps>();

const emits = defineEmits<{
  'on-hidden': []
  'submit': [resConfig: ILocalImportedResource]
}>();

const { t } = useI18n();

// 默认展开
const activeIndex = ref(['baseInfo', 'frontConfig', 'backConfig']);
const baseInfoRef = ref();
const frontConfigRef = ref();
const backConfigRef = ref();
const renderShow = ref(isSliderShow);

watch(() => isSliderShow, (val) => {
  renderShow.value = val;
});

// 提交
const handleSubmit = async () => {
  await Promise.all([
    baseInfoRef.value?.validate(),
    frontConfigRef.value?.validate(),
    backConfigRef.value?.validate(),
  ]);
  const baseFormData = baseInfoRef.value.formData;
  const frontFormData = frontConfigRef.value.frontConfigData;
  const backFormData = backConfigRef.value.backConfigData;
  const payload = {
    ...baseFormData,
    ...frontFormData,
    backend: { ...backFormData },
    _localId: resource?._localId,
  };
  emits('submit', payload);
  emits('on-hidden');
};

const handleHidden = () => {
  renderShow.value = false;
  emits('on-hidden');
};

</script>

<style scoped lang="scss">

:deep(.bk-modal-content) {
  background-color: #f5f7fa;
}

.collapse-wrap {
  padding: 24px 24px 0;

  :deep(.collapse-cls) {
    margin-bottom: 24px;

    .bk-collapse-item {
      margin-bottom: 16px;
      background: #fff;
      box-shadow: 0 2px 4px 0 #1919290d;
    }
  }

  .panel-header {
    display: flex;
    align-items: center;
    padding: 24px;
    cursor: pointer;

    .title {
      margin-left: 8px;
      font-size: 14px;
      font-weight: 700;
      color: #313238;
    }

    .panel-header-show {
      transform: rotate(0deg);
      transition: .2s;
    }

    .panel-header-hide {
      transform: rotate(-90deg);
      transition: .2s;
    }
  }

  :deep(.bk-collapse-content) {
    padding-top: 0 !important;
    padding-left: 0 !important;
  }
}

:deep(.bk-modal-body),
:deep(.bk-sideslider-footer) {
  background-color: #f5f7fa;
}
</style>
