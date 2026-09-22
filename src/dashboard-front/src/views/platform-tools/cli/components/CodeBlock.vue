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
          size="16"
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
import { useClipboard } from '@vueuse/core';
import hljs from 'highlight.js';
import 'highlight.js/styles/vs2015.css';
import { messageSuccess } from '@/utils/message';

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

const handleCopy = async () => {
  await copy(code);
  messageSuccess(t('复制成功'));
};
</script>

<style scoped lang="scss">
.code-block {
  position: relative;
  overflow: hidden;
  background: #242424;
  border-radius: 2px;

  .code-block-header {
    position: absolute;
    top: 10px;
    right: 12px;
    z-index: 1;
    display: flex;
    align-items: center;
    justify-content: flex-end;

    .code-lang {
      display: none;
    }

    .copy-btn {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      line-height: 20px;
      color: #8c8f99;
      cursor: pointer;
      transition: color 0.2s;

      &:hover {
        color: #c4c6cc;
      }

      .copy-text {
        display: none;
      }
    }
  }

  .code-block-body {
    padding: 12px 48px 12px 16px;
    overflow: auto;
    box-sizing: border-box;

    pre {
      padding: 0;
      margin: 0;
      background: transparent;

      code {
        font-family: Menlo, Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
        font-size: 13px;
        line-height: 20px;
        color: #c4c6cc;
        word-break: normal;
        word-wrap: normal;
        white-space: pre;
        tab-size: 2;
      }
    }
  }
}
</style>
