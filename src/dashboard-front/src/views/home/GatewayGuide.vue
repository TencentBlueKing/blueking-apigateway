/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
  <section class="guide-wrapper">
    <section class="main">
      <section class="header">
        <p class="success-icon">
          <AgIcon
            name="check-circle-shape"
            size="42"
          />
        </p>
        <div class="title">
          {{ t('网关（{name}）创建成功', { name: gateway.name }) }}
        </div>
        <div class="tips">
          {{ t('接下来您可以按照开发指引，完成网关的开发，或进入环境概览查看环境信息') }}
        </div>
        <div class="btn-wrapper">
          <BkButton
            theme="primary"
            @click="handleGoToEnvOverview"
          >
            {{ t('环境概览') }}
          </BkButton>
          <BkButton
            class="ml-8px"
            @click="handleClose"
          >
            {{ t('关闭') }}
          </BkButton>
        </div>
      </section>
      <section class="markdown-box" />
    </section>
  </section>
</template>

<script lang="ts" setup>
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import AgIcon from '@/components/ag-icon/Index.vue';
import { getGuideDocs } from '@/services/source/gateway.ts';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();

const gateway = computed(() => ({
  name: route.params.name as string,
  id: Number(route.params.id),
}));

const markdownHtml = ref('');

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

const getGuide = async () => {
  const data = await getGuideDocs(gateway.value.id);
  markdownHtml.value = md.render(data.content);
};

watch(
  () => gateway.value.id,
  () => {
    if (gateway.value.id) {
      getGuide();
    }
  },
);

const handleGoToEnvOverview = () => {
  router.push({
    name: 'StageOverview',
    params: { id: gateway.value.id },
  });
};

const handleClose = () => {
  router.push({
    name: 'Home',
  });
};

</script>

<style lang="scss" scoped>
.guide-wrapper {
  width: 1280px;
  margin: 0 auto;
  padding: 16px 0 24px 0;
  box-sizing: border-box;

  .main {
    padding: 24px;
    background: #FFF;
    border-radius: 2px;
    box-shadow: 0 2px 4px 0 #1919290d;
  }

  .header {
    margin-bottom: 32px;
    text-align: center;

    .success-icon {
      margin-bottom: 18px;

      i {
        color: #65C389;
      }
    }

    .title {
      font-size: 20px;
      color: #313238;
    }

    .tips {
      margin: 12px 0 24px;
      font-size: 14px;
      color: #4D4F56;
    }
  }
}

:deep(.timeline-title-with-tag) {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

:deep(.progress-subtitle) {
  font-size: 12px;
  line-height: 20px;
  color: #979BA5;
}

:deep(.progress-p) {
  margin-bottom: 4px;
}

:deep(.bk-timeline-content) {
  word-break: normal !important;
}

:deep(.ag-markdown-view pre) {
  background: #F5F7FA;
}

:deep(.ag-markdown-view code) {
  color: #4D4F56;
}

:deep(.ag-markdown-view .ag-copy-btn) {
  color: #3A84FF;
  background: #F5F7FA;
}

</style>
