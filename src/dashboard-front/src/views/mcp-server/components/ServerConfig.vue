<template>
  <div class="custom-configure-wrapper">
    <div class="color-#313238 text-16px font-700 pl-24px pt-10px configure-title">
      {{ t('配置') }}
    </div>

    <BkTab
      v-model:active="activeTab"
      :type="tabType"
      class="server-config-tab flex-1"
      :border="false"
      @change="handleConfigChange"
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
      class="p-16px bg-white"
    />
  </div>
</template>

<script lang="ts" setup>
import { t } from '@/locales';
import { type IMCPAIConfig } from '@/services/source/mcp-server';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import Guide from '@/components/guide/Index.vue';

interface IProps {
  tabType?: string
  list?: IMCPAIConfig[]
}

const {
  tabType = 'unborder-card',
  list = [],
} = defineProps<IProps>();

const manualActiveTab = ref('');

const activeTab = computed(() => {
  if (list.length > 0 && !manualActiveTab.value) {
    return list[0].name;
  }
  return manualActiveTab.value;
});

// 根据激活的tab自动计算对应的配置内容
const selectedConfigContent = computed(() => {
  if (!activeTab.value) return '';
  const curTab = list.find(item => item.name === activeTab.value);
  if (!curTab || !curTab.content) return '';

  // 初始化markdown解析器
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

  return md.render(curTab.content);
});

const handleConfigChange = (tab: string) => {
  manualActiveTab.value = tab;
};
</script>

<style lang="scss" scoped>
:deep(.server-config-tab) {

  .bk-tab-header {
    padding: 0 24px;

    &-nav {
      display: flex;
      gap: 32px;
    }

    &-item {
      padding: 0 8px;
    }
  }
}
</style>
