/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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
  <div>
    <article
      v-if="markdownHtml"
      class="res-detail-content"
    >
      <div
        id="resMarkdown"
        v-bk-xss-html="markdownHtml"
        class="ag-markdown-view"
      />
    </article>
  </div>
</template>

<script lang="ts" setup>
import { t } from '@/locales';
import { copy } from '@/utils';

interface IProps {
  markdownHtml?: string
  installUrl?: string
}

interface CopyBtnElement extends HTMLElement { dataset: DOMStringMap & { copy?: string } }

const {
  markdownHtml = '',
  installUrl = '',
} = defineProps<IProps>();

// API 文档大标题元素集合
const docHeadingElements = ref<HTMLElement[]>([]);
// 缓存代码内容，避免DOM存储大文本
const codeContentMap = ref(new Map<HTMLElement, string>());

/**
 * 处理安装按钮点击事件
 */
const handleInstall = () => {
  window.open(installUrl, '_blank');
};

/**
 * 复制按钮点击处理函数
 */
function handleCopy(this: CopyBtnElement) {
  const copyBtn = this;
  const copySpan = copyBtn.querySelector('span');
  if (!copySpan) return;

  // 从缓存获取代码内容
  const copyContent = codeContentMap.value.get(copyBtn) || '';
  copy(copyContent);
};

/**
 * 创建复制按钮
 * @param code 代码内容
 * @returns 复制按钮DOM元素
 */
const createCopyBtn = (code: string): CopyBtnElement => {
  const copyBtn = document.createElement('button') as CopyBtnElement;
  const copySpan = document.createElement('span');
  const copyIcon = document.createElement('i');

  copySpan.title = t('复制');
  copyBtn.className = 'ag-markdown-view__copy-btn';
  copyIcon.className = 'apigateway-icon icon-ag-copy-info';
  copySpan.appendChild(copyIcon);
  copyBtn.appendChild(copySpan);

  // 缓存代码内容，无需转义存入DOM
  codeContentMap.value.set(copyBtn, code);

  return copyBtn;
};

/**
 * 创建安装按钮
 * @returns 安装按钮DOM元素
 */
const createInstallBtn = (): HTMLElement => {
  const installBtn = document.createElement('button');
  const installSpan = document.createElement('span');
  const installIcon = document.createElement('i');

  installBtn.className = 'ag-markdown-view__install-btn';
  installSpan.title = t('安装');
  installIcon.className = 'apigateway-icon icon-ag-anzhuang';
  installSpan.appendChild(installIcon);
  installBtn.appendChild(installSpan);
  installBtn.onclick = handleInstall;

  return installBtn;
};

/**
 * 初始化Markdown
 * @param box DOM容器ID
 */
const initMarkdownHtml = (box: string) => {
  docHeadingElements.value = [];
  nextTick(() => {
    const markdownDom = document.getElementById(box);
    if (!markdownDom) return;
    // 清理复制按钮事件
    markdownDom.querySelectorAll('.ag-markdown-view__copy-btn').forEach((btn) => {
      btn.removeEventListener('click', handleCopy);
      // 清理缓存
      codeContentMap.value.delete(btn);
    });
    // 清理安装按钮事件
    markdownDom.querySelectorAll('.ag-markdown-view__install-btn').forEach((btn) => {
      btn.onclick = null;
    });
    markdownDom.querySelectorAll('.pre-wrapper').forEach((wrapper) => {
      const pre = wrapper.querySelector('pre');
      if (pre && wrapper.parentNode) {
        wrapper.parentNode.replaceChild(pre, wrapper);
      }
    });
    markdownDom.querySelectorAll('a').forEach((item) => {
      item.target = '_blank';
    });

    // 添加复制/安装按钮
    markdownDom.querySelectorAll('pre').forEach((item) => {
      // 创建文档片段，批量添加节点（减少重排重绘）
      const fragment = document.createDocumentFragment();

      // 父容器
      const parentDiv = document.createElement('div');
      parentDiv.className = 'pre-wrapper';

      // 按钮容器
      const btnContainer = document.createElement('div');
      btnContainer.className = 'ag-markdown-view__btn-container';

      // code容器
      const codeBox = document.createElement('div');
      codeBox.className = 'code-box';

      // 获取代码内容
      const codeElement = item.querySelector('code');
      const code = codeElement?.innerText || '';

      // 创建复制按钮并添加到容器
      const copyBtn = createCopyBtn(code);
      btnContainer.appendChild(copyBtn);

      // 有安装链接时创建安装按钮
      if (installUrl) {
        const installBtn = createInstallBtn();
        btnContainer.appendChild(installBtn);
      }

      // 批量添加节点到文档片段
      fragment.appendChild(btnContainer);
      parentDiv.appendChild(fragment);

      // 替换原pre元素
      if (item.parentNode) {
        item.parentNode.replaceChild(parentDiv, item);
      }
      // 把pre元素放进父容器
      parentDiv.appendChild(item);
      // 移动code元素到codeBox
      if (codeElement) {
        codeBox.appendChild(codeElement);
        item.appendChild(codeBox);
      }

      // 绑定复制按钮事件（避免匿名函数，支持解绑）
      copyBtn.addEventListener('click', handleCopy);
    });

    // 获取文档标题元素
    docHeadingElements.value = Array.from(
      markdownDom.querySelectorAll('.target-detail [id^=doc-heading-]'),
    );
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
:deep(.res-detail-content) {

  .ag-markdown-view {

    .ag-markdown-view__btn-container {
      display: flex;
      gap: 8px;
      position: absolute;
      top: 0;
      right: 0;
      z-index: 1;

      .ag-markdown-view__copy-btn,
      .ag-markdown-view__install-btn {
        position: absolute;
        top: 12px;
        right: 12px;
        z-index: 10;
        font-size: 0;
        color: #979ba5;
        background-color: transparent;
        border: none;

        .apigateway-icon {
          font-size: 18px;
        }

        &:hover {
          color: #3a84ff;
          cursor: pointer;
        }
      }

      .ag-markdown-view__install-btn {
        right: 46px;
      }
    }
  }
}
</style>
