<template>
  <AgSideslider
    v-model="isShow"
    v-bind="$attrs"
    :width="960"
    :title="t('默认使用指引')"
  >
    <template #default>
      <div class="p-l-40px p-r-24px">
        <AgMarkdownViewer :markdown-html="markdownHtml" />
      </div>
    </template>
  </AgSideslider>
</template>

<script setup lang="ts">
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js/lib/common';
import AgMarkdownViewer from '@/components/base/ag-markdown-viewer/Index.vue';
import AgSideslider from '@/components/base/ag-sideslider/Index.vue';

const isShow = defineModel('isShow', {
  type: Boolean,
  default: false,
});

const { markdownText = '' } = defineProps<IProps>();

interface IProps { markdownText?: string }

const { t } = useI18n();

const md = new MarkdownIt({
  linkify: true,
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
    return hljs.highlightAuto(str)?.value;
  },
});

const markdownHtml = ref('');

watch(
  () => markdownText,
  (newVal: string) => {
    if (newVal) {
      markdownHtml.value = md.render(newVal);
    }
  },
  { immediate: true },
);
</script>
