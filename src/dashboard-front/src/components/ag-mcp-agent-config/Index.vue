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

<template>
  <div class="custom-configure-wrapper">
    <div
      v-if="showTitle"
      class="color-#313238 text-16px font-700 pl-24px pt-10px lh-32px configure-title"
    >
      {{ t('配置') }}
    </div>
    <BkTab
      v-model:active="manualActiveTab"
      class="server-config-tab flex-1"
      :type="tabType"
      :label-height="tabHeight"
      :border="false"
    >
      <BkTabPanel
        v-for="tab of list"
        :key="tab.name"
        :label="tab.display_name"
        :name="tab.name"
      />
    </BkTab>

    <Guide
      :markdown-html="selectedConfigContent"
      :install-url="installUrl"
      class="p-16px bg-white ag-mcp-agent-guide"
    />
  </div>
</template>

<script lang="ts" setup>
import { t } from '@/locales';
import type { IMCPAIConfig } from '@/services/source/mcp-server';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import Guide from '@/components/guide/Index.vue';

interface IProps {
  tabType?: string
  tabHeight?: number
  showTitle?: boolean
  list?: IMCPAIConfig[]
}

const {
  tabType = 'unborder-card',
  tabHeight = 40,
  showTitle = true,
  list = [],
} = defineProps<IProps>();

const manualActiveTab = ref('');
const installUrl = ref('');

const activeTab = computed(() => {
  if (list.length > 0 && !manualActiveTab.value) {
    return list?.[0]?.name;
  }
  return manualActiveTab.value;
});

const currentTab = computed<IMCPAIConfig | null>(() => {
  if (!activeTab.value) return null;
  return list.find((item: IMCPAIConfig) => item.name === activeTab.value) || null;
});

const selectedConfigContent = computed(() => {
  if (!currentTab.value?.content) return '';
  return md.render(currentTab.value.content);
});

const md = new MarkdownIt({
  linkify: false,
  html: true,
  breaks: true,
  highlight(str: string, lang: string) {
    try {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(str, {
          language: lang,
          ignoreIllegals: true,
        }).value;
      }
    }
    catch {
      return str;
    }
    return hljs.highlightAuto(str).value;
  },
});

watch(currentTab, (newTab) => {
  installUrl.value = newTab?.install_url ?? '';
}, { immediate: true });
</script>

<style lang="scss" scoped>
:deep(.server-config-tab) {

  .bk-tab-header {
    padding-right: 24px;
    padding-left: 16px;

    &-nav {
      display: flex;
      gap: 32px;
      scrollbar-width: thin;
      scrollbar-color: #dcdee5 transparent;

      &::-webkit-scrollbar {
        width: 6px;
        height: 6px;
      }

      &::-webkit-scrollbar-thumb {
        background-color: #dcdee5;
        border-radius: 3px;

        &:hover {
          background-color: #b4bccc;
        }
      }

      &::-webkit-scrollbar-track {
        background-color: transparent;
        border-radius: 3px;
      }
    }

    &-item {
      padding: 0 8px;
      flex-shrink: 0;
    }
  }

  .bk-tab-content {
    padding: 0;
  }
}
</style>
