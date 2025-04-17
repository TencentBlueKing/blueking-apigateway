<template>
  <article v-if="markdownHtml" class="res-detail-content">
    <div class="ag-markdown-view" id="resMarkdown" v-dompurify-html="markdownHtml"></div>
  </article>
</template>

<script lang="ts" setup>
import { ref, toRefs, watch, nextTick } from 'vue';
import { copy } from '@/common/util';

interface IProps {
  markdownHtml: string;
}

const props = withDefaults(defineProps<IProps>(), {
  markdownHtml: () => '',
});

const { markdownHtml } = toRefs(props);
// API 文档大标题元素集合
const docHeadingElements = ref<HTMLElement[]>([]);

const initMarkdownHtml = (box: string) => {
  docHeadingElements.value = [];
  nextTick(() => {
    const markdownDom = document.getElementById(box);
    // 复制代码
    markdownDom?.querySelectorAll('a')?.forEach((item) => {
      item.target = '_blank';
    });
    markdownDom?.querySelectorAll('pre')?.forEach((item) => {
      const parentDiv = document.createElement('div');
      const btn = document.createElement('button');
      const codeBox = document.createElement('div');
      const code = item?.querySelector('code')?.innerText;
      parentDiv.className = 'pre-wrapper';
      btn.className = 'ag-copy-btn';
      codeBox.className = 'code-box';
      btn.innerHTML = '<span title="复制"><i class="apigateway-icon icon-ag-copy-info"></i></span>';
      btn.setAttribute('data-copy', code);
      parentDiv?.appendChild(btn);
      codeBox?.appendChild(item?.querySelector('code'));
      item?.appendChild(codeBox);
      item?.parentNode?.replaceChild(parentDiv, item);
      parentDiv?.appendChild(item);
    });
    // 获取文档中的标题元素，它们的 id 以 doc-heading- 开头
    docHeadingElements.value = Array.from(document.querySelectorAll('.target-detail [id^=doc-heading-]'));

    setTimeout(() => {
      const copyDoms = Array.from(document.getElementsByClassName('ag-copy-btn'));

      const handleCopy = function (this: any) {
        copy(this.dataset?.copy);
      };

      copyDoms.forEach((dom: any) => {
        dom.onclick = handleCopy;
      });
    }, 1000);
  });
};

watch(
  () => markdownHtml,
  () => {
    initMarkdownHtml('resMarkdown');
  },
  { immediate: true },
);

</script>

<style lang="scss" scoped>

</style>
