<template>
  <div class="code-block">
    <div class="code-block-header">
      <span class="code-lang">{{ language }}</span>
      <span
        class="copy-btn"
        @click="handleCopy"
      >
        <AgIcon
          name="copy-info"
          size="14"
        />
        <span class="copy-text">{{ copied ? t('已复制') : t('复制') }}</span>
      </span>
    </div>
    <div class="code-block-body">
      <pre><code v-bk-xss-html="highlightedCode" /></pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useClipboard } from '@vueuse/core';
import hljs from 'highlight.js';
import 'highlight.js/styles/vs2015.css';

interface IProps {
  /** 代码内容 */
  code?: string
  /** 代码语言，默认 bash */
  language?: string
}

const {
  code = '',
  language = 'bash',
} = defineProps<IProps>();

const { t } = useI18n();

const { copy, copied } = useClipboard({ copiedDuring: 2000 });

// 高亮后的代码 HTML
const highlightedCode = computed(() => {
  if (!code) {
    return '';
  }

  try {
    if (language && hljs.getLanguage(language)) {
      return hljs.highlight(code, {
        language,
        ignoreIllegals: true,
      }).value;
    }
  }
  catch {
    return code;
  }
  return hljs.highlightAuto(code).value;
});

const handleCopy = () => {
  copy(code);
};
</script>

<style scoped lang="scss">
.code-block {
  overflow: hidden;
  background: #2e2e2e;
  border-radius: 4px;

  .code-block-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 16px;
    background: #3a3a3a;
    border-bottom: 1px solid #4a4a4a;

    .code-lang {
      font-size: 12px;
      line-height: 20px;
      color: #979ba5;
    }

    .copy-btn {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      line-height: 20px;
      color: #979ba5;
      cursor: pointer;
      transition: color 0.2s;

      &:hover {
        color: #d4d4d4;
      }

      .copy-text {
        user-select: none;
      }
    }
  }

  .code-block-body {
    padding: 16px;
    overflow-x: auto;

    pre {
      padding: 0;
      margin: 0;
      background: transparent;

      code {
        font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
        font-size: 13px;
        line-height: 22px;
        color: #d4d4d4;
        word-break: normal;
        word-wrap: normal;
        white-space: pre;
        tab-size: 2;
      }
    }
  }
}
</style>
