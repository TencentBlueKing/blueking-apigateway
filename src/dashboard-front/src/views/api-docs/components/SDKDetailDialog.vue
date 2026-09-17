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
  <BkSideslider
    v-model:is-show="isShow"
    :width="720"
    :title="title"
    ext-cls="sdk-detail-sideslider"
    quick-close
  >
    <div class="intro-side-content-wrap">
      <BkCollapse
        v-model="activePanels"
        class="detail-block-collapse"
      >
        <BkCollapsePanel name="sdk">
          <template #header>
            <div class="block-header">
              <div class="block-header-left">
                <AgIcon
                  name="down-shape"
                  class="block-header-icon"
                  :class="{ 'is-fold': !activePanels.includes('sdk') }"
                />
                <span>{{ curTab === 'component' ? t('组件 API SDK') : t('网关 SDK') }}</span>
              </div>
              <div @click.stop>
                <BkSelect
                  v-model="language"
                  class="sdk-lang-select"
                  size="small"
                  filterable
                  :clearable="false"
                  :input-search="false"
                >
                  <BkOption
                    v-for="lang in langList"
                    :key="lang"
                    :value="lang"
                    :label="formatSdkLang(lang)"
                  />
                </BkSelect>
              </div>
            </div>
          </template>
          <template #content>
            <DocSdkSection
              v-if="isShow"
              v-model:language="language"
              :sdks="sdks"
              :board="board"
            />
          </template>
        </BkCollapsePanel>
      </BkCollapse>
    </div>
  </BkSideslider>
</template>

<script setup lang="ts">
import { docTabKey } from '../utils/doc-context';
import DocSdkSection, { type ISdkItem } from './DocSdkSection.vue';
import { useI18n } from 'vue-i18n';
import { useEnv } from '@/stores';

interface IProps {
  sdks?: ISdkItem[]
  targetName?: string
  languages: string[] | undefined
  board?: string
}

const isShow = defineModel<boolean>({
  required: true,
  default: false,
});

const {
  sdks = [],
  targetName = '',
  languages,
  board = 'default',
} = defineProps<IProps>();

const { t } = useI18n();
const envStore = useEnv();
const curTab = inject(docTabKey);

const language = ref('python');
const activePanels = ref(['sdk']);

const formatSdkLang = (lang: string) => {
  if (!lang) {
    return '';
  }
  return lang.charAt(0).toUpperCase() + lang.slice(1);
};

const langList = computed(() => {
  if (languages?.length) {
    return languages;
  }
  const fromEnv = envStore.env.BK_SDK_LANGUAGES || [];
  const fromSdks = sdks.map(item => item.language).filter((item): item is string => !!item);
  return [...new Set([...fromEnv, ...fromSdks])];
});

const title = computed(() => {
  return targetName ? t('{name} SDK', { name: targetName }) : t('查看 SDK');
});

watch(isShow, (visible) => {
  if (visible) {
    activePanels.value = ['sdk'];
    language.value = sdks[0]?.language || langList.value[0] || 'python';
  }
});
</script>

<style scoped lang="scss">
.intro-side-content-wrap {
  min-height: calc(100vh - 52px);
  padding: 16px;
  background: #f5f7fa;
}

.block-header {
  display: flex;
  flex: 1;
  min-width: 0;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  font-weight: 700;
  color: #313238;
}

.block-header-left {
  display: flex;
  min-width: 0;
  align-items: center;

  > span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.block-header-icon {
  flex-shrink: 0;
  margin-right: 8px;
  font-size: 12px;
  color: #63656e;
  transition: transform 0.2s;

  &.is-fold {
    transform: rotate(-90deg);
  }
}

.block-header > div:last-child {
  flex-shrink: 0;
  margin-left: 12px;
  font-weight: 400;
}

.sdk-lang-select {
  width: 140px;
}

.detail-block-collapse {

  :deep(> .bk-collapse-item) {
    margin-bottom: 16px;
    overflow: visible;
    background: #fff;
    border: none;
    border-radius: 2px;
    box-shadow: none;
  }

  :deep(> .bk-collapse-item:last-child) {
    margin-bottom: 0;
  }

  :deep(> .bk-collapse-item > div:first-child:not(.bk-collapse-content)) {
    display: flex;
    min-height: 48px;
    padding: 0 16px;
    cursor: pointer;
    align-items: center;
  }

  :deep(> .bk-collapse-item > .bk-collapse-content) {
    padding: 0 16px 16px;
  }
}
</style>

<style lang="scss">
.sdk-detail-sideslider {

  .bk-sideslider-title {
    display: flex;
    width: 100%;
    padding-right: 0;
  }
}
</style>
