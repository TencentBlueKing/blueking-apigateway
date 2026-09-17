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
  <!--  文档详情主内容  -->
  <div class="content-wrap">
    <main
      v-if="api"
      ref="detailWrapRef"
      class="target-detail custom-scroll-bar"
    >
      <header class="detail-header">
        <header class="res-name-row">
          <div class="res-name-main">
            <div class="res-name">
              {{ api.name ?? '--' }}
            </div>
            <BkTag
              v-if="basics?.kind === 2"
              theme="info"
            >
              {{ t('模型代理 API') }}
            </BkTag>
            <BkTag
              v-if="basics?.is_deprecated"
              theme="danger"
              class="font-400"
            >
              deprecated
            </BkTag>
          </div>
          <aside class="res-header-actions">
            <BkButton
              text
              theme="primary"
              class="gateway-detail-btn"
              @click="handleGatewayDetailClick"
            >
              <AgIcon
                name="info"
                class="gateway-detail-icon"
              />
              {{ curTab === 'gateway' ? t('网关详情') : t('组件详情') }}
            </BkButton>
            <BkButton
              v-if="showApplyPermission"
              theme="primary"
              @click="handleApplyClick"
            >
              {{ t('申请权限') }}
            </BkButton>
          </aside>
        </header>
        <p class="res-desc">
          {{ api.description ?? '--' }}
        </p>
        <BkAlert
          v-if="basics?.deprecated_note"
          theme="warning"
          class="mt-16px"
          closable
          :title="basics?.deprecated_note"
        />
      </header>
      <main class="detail-main">
        <article class="res-basics">
          <section class="basic-cell">
            <span>
              <span class="label">{{ t('更新时间') }}</span>：
              {{ updatedTime ?? '--' }}
            </span>
          </section>
          <section class="basic-cell">
            <span>
              <span
                v-bk-tooltips="appVerifiedTooltips"
                class="label"
              >
                {{ t('应用认证') }}
              </span>：
              {{ api.verified_app_required ? t('是') : t('否') }}
            </span>
          </section>
          <section class="basic-cell">
            <span v-if="curTab === 'gateway'">
              <span
                v-bk-tooltips="t('蓝鲸应用需申请资源访问权限')"
                class="label"
              >
                {{ t('校验应用权限') }}
              </span>：
              <span v-if="api.verified_app_required && api.resource_perm_required">
                <span>{{ t('是') }}</span>
                <span
                  v-if="api.allow_apply_permission"
                  v-bk-tooltips="t('可点击右上角「申请权限」提交申请，审批通过后方可调用。')"
                  class="perm-extra is-link"
                  @click="handleApplyClick"
                >{{ t('（允许申请权限）') }}</span>
                <span
                  v-else
                  v-bk-tooltips="t('本资源仅支持由网关管理员授权，不支持在线申请。')"
                  class="perm-extra"
                >{{ t('（只能主动授权）') }}</span>
              </span>
              <span v-else>{{ t('否') }}</span>
            </span>
            <span v-if="curTab === 'component'">
              <span
                v-bk-tooltips="t('应用访问该组件API前，是否需要在开发者中心申请该组件API权限')"
                class="label"
              >
                {{ t('权限申请') }}
              </span>：
              {{ api.verified_app_required
                ? ((api.allow_apply_permission || api.component_permission_required) ? t('是') : t('否'))
                : t('否')
              }}
            </span>
          </section>
          <section class="basic-cell">
            <span>
              <span
                v-bk-tooltips="userVerifiedTooltips"
                class="label"
              >
                {{ t('用户认证') }}
              </span>：
              {{ api.verified_user_required ? t('是') : t('否') }}
            </span>
          </section>
        </article>
        <article
          v-if="curTab === 'gateway' || showStructured || markdownHtml"
          class="res-detail-content"
        >
          <section
            v-if="curTab === 'gateway'"
            class="call-guide"
          >
            <h3 id="doc-heading-调用地址">
              {{ t('调用地址') }}
            </h3>
            <div class="url-hero">
              <span
                class="method-badge"
                :class="api.method"
              >{{ api.method || '--' }}</span>
              <code
                class="url-text"
                :title="resourceUrl || '--'"
              >{{ resourceUrl || '--' }}</code>
              <CopyButton
                v-if="resourceUrl"
                v-bk-tooltips="t('复制')"
                class="url-copy"
                :source="resourceUrl"
              />
            </div>
          </section>
          <DocAuthSection
            v-if="showStructured"
            :plugins="doc?.plugins || []"
            :verified-app-required="api.verified_app_required"
            :verified-user-required="api.verified_user_required"
            :resource-url="resourceUrl"
            :method="api.method"
          />
          <section
            v-if="showRequestParams"
            class="params-section"
          >
            <h3
              id="doc-heading-请求参数"
              class="params-title"
            >
              {{ t('请求参数') }}
            </h3>
            <DocSchemaParams
              :schema="mergedSchema"
              mode="request"
            />
          </section>
          <section
            v-if="showResponseParams"
            class="params-section"
          >
            <h3
              id="doc-heading-响应参数"
              class="params-title"
            >
              {{ t('响应参数') }}
            </h3>
            <DocSchemaParams
              :schema="mergedSchema"
              mode="response"
            />
          </section>
          <section
            v-if="showStructured && extraMarkdownHtml"
            class="extra-markdown"
          >
            <h3
              v-if="!hasExtraHeading"
              id="doc-heading-补充说明"
              class="params-title"
            >
              {{ t('补充说明') }}
            </h3>
            <div
              id="resMarkdownExtra"
              v-bk-xss-html="extraMarkdownHtml"
              class="ag-markdown-view"
            />
          </section>
          <div
            v-if="!showStructured && markdownHtml"
            id="resMarkdown"
            v-bk-xss-html="markdownHtml"
            class="ag-markdown-view"
          />
        </article>
      </main>
    </main>
    <!--  右侧导航栏  -->
    <aside class="detail-nav-box">
      <DocDetailSideNav
        v-model="activeDocHeadingId"
        :list="navList"
      />
    </aside>
  </div>
</template>

<script setup lang="ts">
import DocDetailSideNav, { type INavItem } from './DocDetailSideNav.vue';
import DocAuthSection from './DocAuthSection.vue';
import DocSchemaParams from './DocSchemaParams.vue';
import type {
  IDocsEsbBoardsSystemsComponentsListResponse,
  IDocsGatewaysResourcesDocReadResponse,
  IDocsGatewaysResourcesListResponse,
} from '@/services/types/responses/docs';
import type { IDocBasics } from './DocDetailSideContent.vue';
import { docTabKey } from '../utils/doc-context';
import { copy } from '@/utils';
import {
  useElementBounding,
  useScroll,
} from '@vueuse/core';
import { minBy } from 'lodash-es';
import {
  getContentSchema,
  isStructuredDoc,
  mergeGatewayConfigIntoSchema,
  shouldRenderSchemaParams,
} from '../utils/compose-doc';

// 两类 API 的公共字段必填，网关资源或 ESB 组件特有的字段按需提供。
export interface IDocApi extends Pick<IDocsGatewaysResourcesListResponse,
  'id' | 'name' | 'description' | 'verified_app_required' | 'verified_user_required'>,
  Partial<Pick<IDocsGatewaysResourcesListResponse,
    'method' | 'path' | 'resource_perm_required' | 'allow_apply_permission' | 'labels'>>,
  Partial<Pick<IDocsEsbBoardsSystemsComponentsListResponse, 'component_permission_required'>> {}

export type IDocContent = Omit<IDocsGatewaysResourcesDocReadResponse, 'updated_time'> & {
  updated_time: string | null
};

interface IProps {
  api?: IDocApi | null
  basics?: IDocBasics | null
  navList?: INavItem[]
  markdownHtml?: string
  extraMarkdownHtml?: string
  updatedTime?: string | null
  doc?: IDocContent | null
  resourceUrl?: string
}

interface IEmits {
  'show-gateway-detail': []
  'show-apply-permission': []
}

const {
  api = null,
  basics = null,
  navList = [],
  markdownHtml = '',
  extraMarkdownHtml = '',
  updatedTime = null,
  doc = null,
  resourceUrl = '',
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const { t } = useI18n();

// 注入当前的总 tab 变量
const curTab = inject(docTabKey);

const detailWrapRef = ref<HTMLElement | null>(null);
// API 文档大标题元素集合
const docHeadingElements = ref<HTMLElement[]>([]);
// 当前应该高亮右侧导航的文档标题ID
const activeDocHeadingId = ref('');
const { y } = useScroll(detailWrapRef, {
  // 监听 API 文档容器的滚动结束事件，获取距离容器最上方且可见的标题元素
  onStop: () => {
    const topVisibleHeading = minBy(docHeadingElements.value, (el: HTMLElement) => {
      const { top } = useElementBounding(el);
      const offsetTop = top.value - 100;
      return offsetTop > 0 ? offsetTop : Infinity;
    });
    activeDocHeadingId.value = topVisibleHeading?.id || '';
  },
});

const showStructured = computed(() => isStructuredDoc(doc));
const mergedSchema = computed(() => mergeGatewayConfigIntoSchema(doc?.openapi_schema, {
  path: api?.path,
  plugins: doc?.plugins,
}));
const showRequestParams = computed(() => {
  if (!doc || !showStructured.value || !shouldRenderSchemaParams(doc)) {
    return false;
  }
  return Boolean(
    mergedSchema.value.parameters?.length
    || getContentSchema(mergedSchema.value.requestBody?.content),
  );
});
const showResponseParams = computed(() => {
  if (!doc || !showStructured.value || !shouldRenderSchemaParams(doc)) {
    return false;
  }
  return Object.values(mergedSchema.value.responses || {}).some((response) => {
    return Boolean(response.description || getContentSchema(response.content));
  });
});
const showApplyPermission = computed(() => {
  return curTab?.value === 'gateway'
    && Boolean(api?.verified_app_required && api?.resource_perm_required && api?.allow_apply_permission);
});
const hasExtraHeading = computed(() => /<h[1-6][\s>]/i.test(extraMarkdownHtml));

const appVerifiedTooltips = computed(() => {
  if (curTab?.value === 'gateway') return t('应用访问该网关API时，是否需提供应用认证信息');
  if (curTab?.value === 'component') return t('应用访问该组件API时，是否需提供应用认证信息');
  return '--';
});

const userVerifiedTooltips = computed(() => {
  if (curTab?.value === 'gateway') return t('应用访问该网关API时，是否需要提供用户认证信息');
  if (curTab?.value === 'component') return t('应用访问该组件API时，是否需要提供用户认证信息');
  return '--';
});

watch(
  () => [markdownHtml, extraMarkdownHtml, showStructured.value],
  () => {
    initMarkdownHtml(showStructured.value ? 'resMarkdownExtra' : 'resMarkdown');
  },
);

// 切换 api 时滚动到顶部
watch(
  () => api,
  () => {
    if (y.value === 0) return;
    nextTick(() => {
      y.value = 0;
    });
  },
);

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
      btn.title = t('复制');
      btn.innerHTML = '<span><i class="apigateway-icon icon-ag-copy-info"></i></span>';
      btn.setAttribute('data-copy', code ?? '');
      parentDiv?.appendChild(btn);
      const codeEl = item?.querySelector('code');
      if (codeEl) codeBox?.appendChild(codeEl);
      item?.appendChild(codeBox);
      item?.parentNode?.replaceChild(parentDiv, item);
      parentDiv?.appendChild(item);
    });
    // 获取文档中的标题元素，它们的 id 以 doc-heading- 开头
    docHeadingElements.value = Array.from(
      detailWrapRef.value?.querySelectorAll<HTMLElement>('[id^=doc-heading-]') || [],
    );
    markdownDom?.querySelectorAll<HTMLElement>('.ag-copy-btn').forEach((dom) => {
      dom.onclick = () => copy(dom.dataset.copy ?? '');
    });
  });
};

const handleGatewayDetailClick = () => {
  emit('show-gateway-detail');
};

const handleApplyClick = () => {
  emit('show-apply-permission');
};
</script>

<style scoped lang="scss">
@use "sass:color";

$primary-color: #3a84ff;
$code-color: #63656e;

.content-wrap {
  display: flex;
  height: 100%;
  min-height: 0;
  align-items: flex-start;

  .target-detail {
    height: 100%;
    min-height: 0;
    padding-right: 8px;
    padding-left: 8px;
    overflow-y: scroll;
    box-sizing: border-box;
    flex-grow: 1;

    .detail-header {
      margin-bottom: 16px;

      .res-name-row {
        display: flex;
        gap: 16px;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 4px;
      }

      .res-name-main {
        display: flex;
        flex: 1;
        min-width: 0;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
      }

      .res-name {
        font-size: 20px;
        font-weight: 700;
        line-height: 28px;
        color: #313238;
      }

      .res-desc {
        margin: 0;
        font-size: 14px;
        line-height: 22px;
        color: #979ba5;
      }

      .res-header-actions {
        display: flex;
        flex-shrink: 0;
        gap: 8px;
        align-items: center;
      }

      .gateway-detail-btn {
        padding: 0 8px;
      }

      .gateway-detail-icon {
        margin-right: 4px;
        font-size: 14px;
      }
    }

    .detail-main {
      container-type: inline-size;

      .res-basics,
      .res-detail-content {
        padding: 24px;
        background-color: #fff;
        border-radius: 2px;
        box-shadow: 0 2px 4px 0 #1919290d;
      }

      .res-basics {
        display: grid;
        grid-template-columns: 1fr 1fr;
        grid-template-rows: 40px 40px;
        margin-bottom: 16px;

        .basic-cell {
          display: flex;
          align-items: center;
          line-height: 22px;
          color: #313238;

          .label {
            font-size: 14px;
            color: #63656e;
            border-bottom: 1px dashed #979ba5;
          }

          &:first-of-type .label {
            border: none;
          }
        }

        .perm-extra {
          border-bottom: 1px dashed #979ba5;

          &.is-link {
            cursor: pointer;
          }
        }
      }

      .call-guide {
        margin-bottom: 24px;

        h3 {
          margin: 0 0 12px;
          font-size: 16px;
          font-weight: 700;
          line-height: 22px;
          color: #313238;
        }
      }

      .url-hero {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        min-height: 40px;
        padding: 9px 12px;
        margin-bottom: 0;
        background: #f5f7fa;
        border: 1px solid #dcdee5;
        border-radius: 2px;
      }

      .method-badge {
        flex-shrink: 0;
        min-width: 56px;
        padding: 2px 8px;
        margin-top: 1px;
        font-size: 12px;
        font-weight: 700;
        line-height: 20px;
        color: #3a84ff;
        text-align: center;
        background: #e1ecff;
        border-radius: 2px;

        &.GET {
          color: #14a568;
          background: #e4f5e9;
        }

        &.POST {
          color: #3a84ff;
          background: #e1ecff;
        }

        &.PUT,
        &.PATCH {
          color: #e38b02;
          background: #fff3e0;
        }

        &.DELETE {
          color: #ea3636;
          background: #feebea;
        }
      }

      .url-text {
        flex: 1;
        min-width: 0;
        font-family: "Lucida Console", "Courier New", Monaco, monospace;
        font-size: 13px;
        line-height: 22px;
        color: #313238;
        overflow-wrap: anywhere;
        word-break: break-all;
        white-space: normal;
      }

      .url-copy {
        flex-shrink: 0;
        margin-top: 3px;
      }

      .params-title {
        margin: 0 0 12px;
        font-size: 16px;
        font-weight: bold;
        line-height: 22px;
        color: #313238;
      }

      .params-section {
        margin-top: 24px;
      }

      .extra-markdown {
        margin-top: 24px;
      }
    }

  }

  .detail-nav-box {
    padding-left: 12px;
  }
}

.custom-scroll-bar {

  &::-webkit-scrollbar {
    width: 4px;
    background-color: color.scale(#c4c6cc, $lightness: 80%);
  }

  &:hover::-webkit-scrollbar-thumb {
    background-color: #c4c6cc;
  }

  &::-webkit-scrollbar-thumb {
    height: 5px;
    background-color: #f5f7fb;
    border-radius: 2px;
  }

  &::-webkit-scrollbar-track {
    background-color: #f5f7fb;
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
    line-height: 22px;
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

    &:first-of-type {
      margin-top: 0 !important;
    }
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

    // background: $code-bc;
    border-radius: 2px;

    code {
      font-family: "Lucida Console", "Courier New", Monaco, monospace;

      // color: #dcdcdc;
      // color: #1f2328;
    }

    .hljs {
      margin: -10px;
    }
  }
}
</style>
