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
  <div class="sdk-section-body">
    <p
      v-if="!curSdk"
      class="sdk-empty-tip"
    >
      {{ t('SDK未生成，可联系负责人生成SDK') }}
    </p>
    <template v-else>
      <DocDetailField :label="t('SDK包名称')">
        {{ curSdk.name || '--' }}
      </DocDetailField>
      <DocDetailField
        v-if="curSdk.sdk_description"
        :label="t('SDK描述')"
      >
        {{ curSdk.sdk_description }}
      </DocDetailField>
      <DocDetailField :label="t('SDK版本')">
        {{ curSdk.version || '--' }}
      </DocDetailField>
      <DocDetailField :label="t('SDK地址')">
        <span>{{ sdkUrl || '--' }}</span>
        <template v-if="sdkUrl">
          <CopyButton :source="sdkUrl" />
          <AgIcon
            v-bk-tooltips="t('下载')"
            name="download"
            class="action-icon"
            @click="handleDownload"
          />
        </template>
      </DocDetailField>
      <DocDetailField :label="t('安装')">
        <span>{{ installCommand || '--' }}</span>
        <CopyButton
          v-if="installCommand"
          :source="installCommand"
        />
      </DocDetailField>
      <template v-if="curTab === 'gateway' && curSdkDoc">
        <DocDetailField :label="t('资源版本')">
          {{ curSdkDoc.resource_version || '--' }}
        </DocDetailField>
        <DocDetailField
          v-if="curSdkDoc.stage?.name"
          :label="t('版本已发环境')"
        >
          {{ curSdkDoc.stage.name }}
        </DocDetailField>
      </template>
      <BkCollapse
        v-model="activeDocPanels"
        class="sdk-doc-collapse"
      >
        <BkCollapsePanel name="sdk-doc">
          <template #header>
            <div class="sdk-doc-header">
              <AgIcon
                name="down-shape"
                class="sdk-doc-icon"
                :class="{ 'is-fold': !activeDocPanels.includes('sdk-doc') }"
              />
              <span class="sdk-doc-title">{{ t('SDK 文档') }}</span>
            </div>
          </template>
          <template #content>
            <div
              v-bkloading="{ loading: isLoading }"
              class="sdk-doc-body"
            >
              <div
                v-if="markdownHtml"
                :id="markdownId"
                :key="renderHtmlIndex"
                v-bk-xss-html="markdownHtml"
                class="ag-markdown-view"
              />
              <BkException
                v-else-if="!isLoading"
                scene="part"
                type="empty"
                :description="t('没有对应文档')"
              />
            </div>
          </template>
        </BkCollapsePanel>
      </BkCollapse>
    </template>
  </div>
</template>

<script setup lang="ts">
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import { getESBSDKDoc } from '@/services/source/docs-esb';
import { getGatewaySDKDoc } from '@/services/source/sdks';
import type { IDocsSdksDocReadQuery } from '@/services/types/query/docs';
import type { ISdk, ISdkDoc } from './SDKDetail.vue';
import { docTabKey } from '../utils/doc-context';
import DocDetailField from './DocDetailField.vue';
import { copy } from '@/utils';
import 'highlight.js/styles/github.css';

// 兼容按环境嵌套的 SDK 数据和历史平铺字段。
export interface ISdkItem extends ISdk, Partial<ISdkDoc> {
  sdk?: ISdk | null
  version_number?: string
  download_url?: string
}

interface IProps {
  sdks?: ISdkItem[]
  board?: string
  defaultExpandDoc?: boolean
}

const language = defineModel<string>('language', { default: 'python' });

const {
  sdks = [],
  board = 'default',
  defaultExpandDoc = false,
} = defineProps<IProps>();

const { t } = useI18n();
const curTab = inject(docTabKey);

const markdownHtml = ref('');
const renderHtmlIndex = ref(0);
const isLoading = ref(false);
const activeDocPanels = ref<string[]>(defaultExpandDoc ? ['sdk-doc'] : []);

const markdownId = 'gateway-sdk-instruction-markdown';
let sdkDocRequestId = 0;

const currentSdkItem = computed(() => sdks.find(item => item.language === language.value) ?? null);

const curSdk = computed<ISdk | null>(() => {
  const item = currentSdkItem.value;
  if (!item) {
    return null;
  }
  const nested = item.sdk || {};
  return {
    language: item.language || nested.language,
    name: nested.name || item.name || item.sdk_name,
    version: nested.version || item.version || item.version_number || item.sdk_version_number,
    url: nested.url || item.url || item.download_url || item.sdk_download_url,
    install_command: nested.install_command || item.install_command || item.sdk_install_command,
    sdk_description: nested.sdk_description || item.sdk_description,
  };
});

const sdkUrl = computed(() => curSdk.value?.url || '');
const installCommand = computed(() => curSdk.value?.install_command || '');

const curSdkDoc = computed<ISdkDoc | null>(() => {
  const item = currentSdkItem.value;
  if (!item) {
    return null;
  }
  const version = typeof item.resource_version === 'string'
    ? item.resource_version
    : item.resource_version?.version;
  if (!version && !item.stage) {
    return null;
  }
  return {
    ...item,
    resource_version: version || '--',
    stage: item.stage,
  };
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

const handleDownload = () => {
  if (sdkUrl.value) {
    window.open(sdkUrl.value);
  }
};

const bindCopyButtons = () => {
  const markdownDom = document.getElementById(markdownId);
  markdownDom?.querySelectorAll('a').forEach((item) => {
    item.target = '_blank';
  });
  markdownDom?.querySelectorAll('pre').forEach((item) => {
    if (item.parentElement?.classList.contains('pre-wrapper')) {
      return;
    }
    const parentDiv = document.createElement('div');
    const btn = document.createElement('button');
    parentDiv.className = 'pre-wrapper';
    btn.className = 'ag-copy-btn';
    btn.title = t('复制');
    btn.innerHTML = '<span><i class="apigateway-icon icon-ag-copy-info"></i></span>';
    btn.setAttribute('data-copy', item.querySelector('code')?.innerText ?? '');
    item.parentNode?.replaceChild(parentDiv, item);
    parentDiv.appendChild(btn);
    parentDiv.appendChild(item);
  });
  markdownDom?.querySelectorAll<HTMLElement>('.ag-copy-btn').forEach((dom) => {
    dom.onclick = () => copy(dom.dataset.copy || '');
  });
};

const fetchSdkDoc = async () => {
  const requestId = ++sdkDocRequestId;
  if (!curSdk.value) {
    markdownHtml.value = '';
    isLoading.value = false;
    return;
  }
  isLoading.value = true;
  try {
    const lang = language.value as IDocsSdksDocReadQuery['language'];
    const res = curTab?.value === 'component'
      ? await getESBSDKDoc(board, { language: lang })
      : await getGatewaySDKDoc({ language: lang });
    if (requestId !== sdkDocRequestId) {
      return;
    }
    markdownHtml.value = md.render(res?.content || '');
    renderHtmlIndex.value += 1;
    await nextTick();
    bindCopyButtons();
  }
  catch {
    if (requestId === sdkDocRequestId) {
      markdownHtml.value = '';
    }
  }
  finally {
    if (requestId === sdkDocRequestId) {
      isLoading.value = false;
    }
  }
};

const isDocExpanded = computed(() => activeDocPanels.value.includes('sdk-doc'));

watch(
  [isDocExpanded, language, () => curTab?.value, currentSdkItem, () => board],
  ([expanded]) => {
    if (expanded) {
      fetchSdkDoc();
    }
  },
  { immediate: true },
);
</script>

<style scoped lang="scss">
.sdk-empty-tip {
  margin: 0;
  font-size: 14px;
  line-height: 22px;
  color: #979ba5;
}

.action-icon {
  font-size: 16px;
  color: #979ba5;
  cursor: pointer;

  &:hover {
    color: #3a84ff;
  }
}

.sdk-doc-header {
  display: flex;
  align-items: center;
}

.sdk-doc-icon {
  margin-right: 8px;
  font-size: 12px;
  color: #979ba5;
  transition: transform 0.2s;

  &.is-fold {
    transform: rotate(-90deg);
  }
}

.sdk-doc-title {
  font-size: 12px;
  font-weight: 700;
  color: #63656e;
}

.sdk-doc-collapse {
  margin-top: 8px;

  :deep(.bk-collapse-item) {
    margin: 0;
    background: transparent;
    border: none;
    box-shadow: none;
  }

  :deep(.bk-collapse-item > div:first-child:not(.bk-collapse-content)) {
    display: flex;
    height: 40px;
    padding: 0 16px;
    cursor: pointer;
    background: #f0f1f5;
    border-radius: 2px;
    align-items: center;
  }

  :deep(.bk-collapse-content) {
    padding: 16px;
    background: #fafbfd;
  }
}

.sdk-doc-body {
  min-height: 48px;
}

:deep(.ag-markdown-view) {
  font-size: 12px;
  line-height: 20px;
  color: #63656e;

  h1,
  h2,
  h3,
  h4,
  h5,
  h6 {
    margin: 16px 0 8px;
    font-weight: 700;
    color: #313238;
  }

  h1,
  h2 {
    font-size: 13px;
  }

  h3,
  h4,
  h5,
  h6 {
    font-size: 12px;
  }

  p {
    margin: 0 0 8px;
    font-size: 12px;
    line-height: 20px;
  }

  ul,
  ol {
    padding-left: 18px;
    margin: 0 0 8px;
  }

  li {
    margin-bottom: 4px;
    font-size: 12px;
    line-height: 20px;
  }

  pre {
    padding: 8px 12px;
    margin: 8px 0;
    overflow: auto;
    font-size: 12px;
    line-height: 20px;
    background: #f5f7fa;
    border-radius: 2px;
  }

  code {
    font-size: 12px;
  }
}
</style>
