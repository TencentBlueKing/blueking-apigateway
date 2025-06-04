<template>
  <div class="content">
    <guide :markdown-html="markdownHtml" />
  </div>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import guide from '@/components/guide.vue';

const props = defineProps({
  markdownStr: {
    type: String,
    default: '',
  },
});

const md = new MarkdownIt({
  linkify: false,
  html: true,
  breaks: true,
  highlight(str: string, lang: string) {
    try {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(str, { language: lang, ignoreIllegals: true }).value;
      }
    } catch {
      return str;
    }
    return str;
  },
});

const markdownHtml = ref<string>('');

watch(
  () => props.markdownStr,
  (newVal) => {
    markdownHtml.value = md.render(newVal);
  },
);

</script>

<style lang="scss" scoped>
.content {
  padding: 24px 40px 48px;
}
</style>
