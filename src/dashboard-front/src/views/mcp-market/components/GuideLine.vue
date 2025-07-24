<template>
  <div class="content">
    <Guide :markdown-html="markdownHtml" />
  </div>
</template>

<script lang="ts" setup>
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import Guide from '@/components/guide/Index.vue';

interface IProps { markdownStr?: string }

const { markdownStr = '' } = defineProps<IProps>();

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
    return str;
  },
});

const markdownHtml = ref('');

watch(
  () => markdownStr,
  (newVal) => {
    if (newVal) {
      markdownHtml.value = md.render(newVal);
    }
    else {
      markdownHtml.value = '';
    }
  },
  { immediate: true },
);

</script>

<style lang="scss" scoped>
.content {
  padding: 24px 40px 48px;
  background: #fff;
}
</style>
