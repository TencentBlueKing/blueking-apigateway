<template>
  <AgSideSlider
    v-model="isShow"
    v-bind="$attrs"
    :width="960"
    :title="$t('默认使用指引')"
  >
    <template #default>
      <div class="p-l-40px p-r-24px">
        <Guide :markdown-html="markdownHtml" />
      </div>
    </template>
  </AgSideSlider>
</template>

<script setup lang="ts">
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import Guide from '@/components/guide/Index.vue';
import AgSideSlider from '@/components/ag-sideslider/Index.vue';

const isShow = defineModel('isShow', {
  type: Boolean,
  default: false,
});

const { markdownText = '' } = defineProps<IProps>();

interface IProps { markdownText?: string }

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
