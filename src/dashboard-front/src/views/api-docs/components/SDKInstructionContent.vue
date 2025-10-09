/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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
  <!--  SDK使用说明 Slider 的内容  -->
  <div class="sdk-wrapper">
    <LangSelector
      v-if="curTab === 'gateway'"
      v-model="language"
      :margin-bottom="0"
      :sdk-languages="['python', 'java', 'golang']"
      :lang-list="['python', 'java', 'golang']"
      @select="handleLangSelect"
    />
    <div
      v-else
      class="bk-button-group"
    >
      <BkButton
        class="is-selected"
        style="width: 150px"
      >
        Python
      </BkButton>
    </div>
    <div
      v-if="sdkDoc"
      id="sdk-instruction-markdown"
      :key="renderHtmlIndex"
      v-dompurify-html="markdownHtml"
      class="ag-markdown-view"
    />
    <BkException
      v-else
      class="exception-wrap-item exception-part"
      :description="t('没有对应文档')"
      scene="part"
      type="empty"
    />
  </div>
</template>

<script setup lang="ts">
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import { copy } from '@/utils';
import { getESBSDKDoc } from '@/services/source/docs-esb';
import { getGatewaySDKDoc } from '@/services/source/sdks';
import type {
  LanguageType,
  TabType,
} from '../types.d.ts';
import LangSelector from './LangSelector.vue';
import 'highlight.js/styles/github.css';

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

const initMarkdownHtml = (content: string) => {
  markdownHtml.value = md.render(content);
  renderHtmlIndex.value += 1;
  nextTick(() => {
    const markdownDom = document.getElementById('sdk-instruction-markdown');
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
    if (curTab.value === 'gateway') {
      const res = await getGatewaySDKDoc(params);
      sdkDoc.value = res.content;
    }
    else {
      const res = await getESBSDKDoc(board.value, params);
      sdkDoc.value = res.content;
    }
    isLoading.value = false;
    initMarkdownHtml(sdkDoc.value);
  }
  catch (e) {
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
  }
  catch {
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
  {
    immediate: true,
    deep: true,
  },
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
  font-style: normal;
  line-height: 19px;
  color: $code-color;
  text-align: left;

  h1,
  h2,
  h3,
  h4,
  h5,
  h6 {
    padding: 0;
    margin: 25px 0 10px !important;
    font-weight: bold;
    line-height: 21px;
    color: #313238;
    text-align: left;
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
    line-height: 22px;
    color: $code-color;
    word-break: break-all;
    white-space: normal;
  }

  ul {
    padding-left: 17px;
    line-height: 22px;

    li {
      margin-bottom: 8px;
      list-style: disc;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }

  ol {
    padding-left: 15px;
    margin: 14px 0;
    line-height: 22px;

    li {
      margin-bottom: 8px;
      list-style: decimal;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }

  a {
    color: #3a84ff;
  }

  tt {
    padding: 0 5px;
    margin: 0 2px;
    font-size: 75%;
    white-space: nowrap;
    background-color: #f8f8f8;
    border: 1px solid #eaeaea;
    border-radius: 3px;
  }

  table {
    width: 100%;
    margin: 10px 0;
    font-size: 14px;
    font-style: normal;
    color: $code-color;
    text-align: left;
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
      min-width: 70px;
      padding: 10px;
      font-size: 13px;
      font-weight: bold;
      color: $code-color;
      background: #f0f1f5;
      border-bottom: 1px solid #dcdee5;

    }

    th:nth-child(1) {
      width: 20%;
    }

    td {
      max-width: 250px;
      padding: 10px;
      font-size: 13px;
      font-style: normal;
      color: $code-color;
      word-break: break-all;
      border-bottom: 1px solid #dcdee5;
    }
  }

  pre {
    position: relative;
    padding: 10px;
    margin: 14px 0;
    overflow: auto;
    font-size: 14px;
    line-height: 24px;
    text-align: left;
    border-radius: 2px;

    code {
      text-wrap: wrap;
    }

    .hljs {
      margin: -10px;
    }
  }
}
</style>
