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
      width="640"
      :title="t('查看插件')"
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
            <BkCollapsePanel
              v-for="plugin in plugins"
              :key="plugin.type"
              :name="plugin.name || plugin.type"
            >
              <template #header>
                <div class="panel-header">
                  <AngleUpFill
                    :class="[activeIndex?.includes(plugin.type) ? 'panel-header-show' : 'panel-header-hide']"
                  />
                  <div class="title">
                    {{ plugin.name || plugin.type }}
                  </div>
                </div>
              </template>
              <template #content>
                <article class="p24">
                  {{ parseYaml(plugin.yaml) }}
                </article>
              </template>
            </BkCollapsePanel>
          </BkCollapse>
        </div>
      </template>
    </BkSideslider>
  </div>
</template>

<script setup lang="ts">
import { AngleUpFill } from 'bkui-lib/icon';
import yaml from 'js-yaml';

type PluginType = {
  id?: number
  name?: string
  type: string
  yaml: string
};

interface IProps {
  isSliderShow?: boolean
  plugins?: PluginType[]
}

const {
  isSliderShow = false,
  plugins = [],
} = defineProps<IProps>();

const emits = defineEmits<{ 'on-hidden': [] }>();

const { t } = useI18n();

const activeIndex = computed(() => plugins.map(plugin => plugin.type));
const renderShow = ref(isSliderShow);

const handleHidden = () => {
  renderShow.value = false;
  emits('on-hidden');
};

const parseYaml = (yamlStr: string) => {
  try {
    return (yamlStr && typeof yamlStr === 'string') ? JSON.stringify(yaml.load(yamlStr, { json: true })) : '{}';
  }
  catch {
    return yamlStr;
  }
};

watch(() => isSliderShow, (val) => {
  renderShow.value = val;
});

</script>

<style scoped lang="scss">

:deep(.bk-modal-content) {
  background-color: #f5f7fa;
}

.collapse-wrap {
  padding: 24px 24px 0;

  :deep(.collapse-cls) {
    margin-bottom: 52px;

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
