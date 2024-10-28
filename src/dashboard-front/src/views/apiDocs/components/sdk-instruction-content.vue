<template>
  <!--  SDK使用说明 Slider 的内容  -->
  <div class="sdk-wrapper">
    <LangSelector
      v-if="curTab === 'apigw'"
      v-model="language"
      :margin-bottom="0"
      :sdk-languages="['python', 'java', 'golang']"
      :lang-list="['python', 'java', 'golang']"
      @select="handleLangSelect"
    />
    <div v-else class="bk-button-group">
      <bk-button class="is-selected" style="width: 150px">Python</bk-button>
    </div>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <div
      v-if="sdkDoc"
      class="ag-markdown-view"
      id="markdown"
      :key="renderHtmlIndex"
      v-dompurify-html="markdownHtml"
    ></div>
    <bk-exception
      v-else
      class="exception-wrap-item exception-part"
      :description="t('没有对应文档')"
      scene="part"
      type="empty"
    />
  </div>
</template>

<script setup lang="ts">
import {
  inject,
  nextTick,
  ref,
  Ref,
  watch,
} from 'vue';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';

import { copy } from '@/common/util';

import {
  getESBSDKDoc,
  getGatewaySDKDoc,
} from '@/http';
import {
  LanguageType,
  TabType,
} from '@/views/apiDocs/types';
import LangSelector from '@/views/apiDocs/components/lang-selector.vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const curTab = inject<Ref<TabType>>('curTab');

const language = ref<LanguageType>('python');
const board = ref('default');
const sdkDoc = ref('');
const markdownHtml = ref('');
const renderKey = ref(0);
const renderHtmlIndex = ref(0);
const isLoading = ref(false);
const pagination = ref({
  offset: 0,
  count: 0,
  limit: 10,
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

const initMarkdownHtml = (content: string) => {
  markdownHtml.value = md.render(content);
  renderHtmlIndex.value += 1;
  nextTick(() => {
    const markdownDom = document.getElementById('markdown');

    // 复制代码
    markdownDom.querySelectorAll('a')
      .forEach((item: any) => {
        item.target = '_blank';
      });
    markdownDom?.querySelectorAll('pre')
      ?.forEach((item) => {
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

// 获取SDK 说明
const getSDKDoc = async () => {
  const params = { language: language.value };
  isLoading.value = true;
  try {
    if (curTab.value === 'apigw') {
      const res = await getGatewaySDKDoc(params);
      sdkDoc.value = res.content;
    } else {
      const res = await getESBSDKDoc(board.value, params);
      sdkDoc.value = res.content;
    }
    isLoading.value = false;
    initMarkdownHtml(sdkDoc.value);
  } catch (e) {
    isLoading.value = false;
    throw e;
  }
};

const handleLangSelect = (lang: LanguageType) => {
  if (lang === language.value) return;
  init();
};

const init = async () => {
  try {
    await getSDKDoc();
  } catch {
    sdkDoc.value = '';
    markdownHtml.value = '';
    pagination.value = {
      offset: 0,
      count: 0,
      limit: 10,
    };
  }
};

// 监听 tab 的变化，改变内容时重新渲染
watch(
  () => curTab.value,
  () => {
    renderKey.value += 1;
    init();
  },
  { immediate: true, deep: true },
);

</script>

<style lang="scss" scoped>
$primary-color: #3a84ff;
$code-bc: #f5f7fa;
$code-color: #63656e;

.sdk-wrapper {
  padding: 24px 40px;
}

:deep(.bk-button-group) {
  .is-selected {
    background-color: #f6f9ff !important;
  }
}

:deep(.ag-markdown-view) {
  font-size: 14px;
  text-align: left;
  color: $code-color;
  line-height: 19px;
  font-style: normal;

  .pre-wrapper {
    .ag-copy-btn {
      right: 12px;
      top: 12px;
      background-color: $code-bc;
      color: $primary-color;
    }
  }

  h1,
  h2,
  h3,
  h4,
  h5,
  h6 {
    padding: 0;
    margin: 25px 0 10px 0 !important;
    font-weight: bold;
    text-align: left;
    color: #313238;
    line-height: 21px;
  }

  h1 {
    font-size: 18px;
  }

  h2 {
    font-size: 17px;
  }

  h3 {
    font-size: 16px;
  }

  h4 {
    font-size: 13px;
  }

  h5 {
    font-size: 12px;
  }

  h6 {
    font-size: 12px;
  }

  p {
    font-size: 14px;
    color: $code-color;
    line-height: 22px;
    white-space: normal;
    word-break: break-all;
  }

  ul {
    padding-left: 17px;
    line-height: 22px;

    li {
      list-style: disc;
      margin-bottom: 8px;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }

  ol {
    padding-left: 15px;
    line-height: 22px;
    margin: 14px 0;

    li {
      list-style: decimal;
      margin-bottom: 8px;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }

  a {
    color: #3a84ff;
  }

  tt {
    margin: 0 2px;
    padding: 0 5px;
    white-space: nowrap;
    border: 1px solid #eaeaea;
    background-color: #f8f8f8;
    border-radius: 3px;
    font-size: 75%;
  }

  table {
    font-size: 14px;
    color: $code-color;
    width: 100%;
    text-align: left;
    margin: 10px 0;
    font-style: normal;
    border: 1px solid #dcdee5;

    &.field-list {
      th {
        width: 12%;
      }
    }

    em {
      font-style: normal;
    }

    th {
      background: #f0f1f5;
      font-size: 13px;
      font-weight: bold;
      color: $code-color;
      border-bottom: 1px solid #dcdee5;
      padding: 10px;
      min-width: 70px;

    }

    th:nth-child(1) {
      width: 20%;
    }

    td {
      padding: 10px;
      font-size: 13px;
      color: $code-color;
      border-bottom: 1px solid #dcdee5;
      max-width: 250px;
      font-style: normal;
      word-break: break-all;
    }
  }

  pre {
    border-radius: 2px;
    background: $code-bc;
    padding: 10px;
    font-size: 14px;
    text-align: left;
    color: $code-color;
    line-height: 24px;
    position: relative;
    overflow: auto;
    margin: 14px 0;

    code {
      font-family: "Lucida Console", "Courier New", "Monaco", monospace;
      color: $code-color;
    }

    .hljs {
      margin: -10px;
    }
  }
}
</style>
