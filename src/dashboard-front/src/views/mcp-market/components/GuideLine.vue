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
    return hljs.highlightAuto(str).value;
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
:deep(.ag-markdown-view) {
  .pre-wrapper {
    .ag-copy-btn {
      background-color: transparent;
    }
  }

  pre {
    background-color: #f6f8fa;
    color: #1f2328;

    code {
      color: #1f2328;
    }
  }
}
</style>
