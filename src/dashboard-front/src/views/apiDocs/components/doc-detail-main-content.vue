<template>
  <!--  文档详情主内容  -->
  <div class="content-wrap">
    <main v-if="api" class="target-detail custom-scroll-bar" ref="detailWrapRef">
      <header class="detail-header">
        <header class="res-name">{{ api.name ?? '--' }}</header>
        <footer class="res-header-footer">
          <main class="res-desc">{{ api.description ?? '--' }}</main>
          <aside class="res-sdk">
            <span class="f12" @click="handleSdkInstructionClick">
              <i class="apigateway-icon icon-ag-document f14"></i>
              {{ t('SDK 使用说明') }}
            </span>
          </aside>
        </footer>
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
              <span class="label" v-bk-tooltips="appVerifiedTooltips">
                {{ t('应用认证') }}
              </span>：
              {{ api.verified_app_required ? t('是') : t('否') }}
            </span>
          </section>
          <section class="basic-cell">
            <span>
              <span
                class="label" v-bk-tooltips="resourcePermTooltips"
              >
                {{ t('权限申请') }}
              </span>：
              {{ (api.allow_apply_permission || api.component_permission_required) ? t('是') : t('否') }}
            </span>
          </section>
          <section class="basic-cell">
            <span>
              <span class="label" v-bk-tooltips="userVerifiedTooltips">
                {{ t('用户认证') }}
              </span>：
              {{ api.verified_user_required ? t('是') : t('否') }}
            </span>
          </section>
        </article>
        <!--  API markdown 文档  -->
        <article v-if="markdownHtml" class="res-detail-content">
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div class="ag-markdown-view" id="resMarkdown" v-dompurify-html="markdownHtml"></div>
        </article>
      </main>
    </main>
    <!--  右侧导航栏  -->
    <aside class="detail-nav-box">
      <DocDetailSideNav :list="navList"></DocDetailSideNav>
    </aside>
  </div>
</template>

<script setup lang="ts">
import DocDetailSideNav from './doc-detail-side-nav.vue';
import {
  IComponent,
  INavItem,
  IResource,
  TabType,
} from '@/views/apiDocs/types';
import {
  computed,
  inject,
  nextTick,
  ref,
  Ref,
  toRefs,
  watch,
} from 'vue';
import { useI18n } from 'vue-i18n';
import { copy } from '@/common/util';
import { useScroll } from '@vueuse/core';

const { t } = useI18n();

interface IProps {
  api: IResource & IComponent | null;
  navList: INavItem[];
  markdownHtml: string;
  updatedTime: string;
}

const props = withDefaults(defineProps<IProps>(), {
  api: () => null,
  navList: () => [],
  markdownHtml: () => '',
  updatedTime: () => null,
});

// 注入当前的总 tab 变量
const curTab = inject<Ref<TabType>>('curTab');

const emit = defineEmits(['show-sdk-instruction']);

const {
  api,
  navList,
  markdownHtml,
  updatedTime,
} = toRefs(props);

const detailWrapRef = ref<HTMLElement | null>(null);
const { y } = useScroll(detailWrapRef);

const appVerifiedTooltips = computed(() => {
  if (curTab.value === 'apigw') return t('应用访问该网关API时，是否需提供应用认证信息');
  if (curTab.value === 'component') return t('应用访问该组件API时，是否需提供应用认证信息');
  return '--';
});

const resourcePermTooltips = computed(() => {
  if (curTab.value === 'apigw') return t('应用访问该网关API前，是否需要在开发者中心申请该网关API权限');
  if (curTab.value === 'component') return t('应用访问该组件API前，是否需要在开发者中心申请该组件API权限');
  return '--';
});

const userVerifiedTooltips = computed(() => {
  if (curTab.value === 'apigw') return t('应用访问该网关API时，是否需要提供用户认证信息');
  if (curTab.value === 'component') return t('应用访问该组件API时，是否需要提供用户认证信息');
  return '--';
});

watch(markdownHtml, () => {
  initMarkdownHtml('resMarkdown');
});

// 切换 api 时滚动到顶部
watch(api, () => {
  if (y.value === 0) return;
  nextTick(() => {
    y.value = 0;
  });
});

const initMarkdownHtml = (box: string) => {
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

const handleSdkInstructionClick = () => {
  emit('show-sdk-instruction');
};

</script>

<style scoped lang="scss">
$primary-color: #3a84ff;
$code-bc: #f5f7fa;
$code-color: #63656e;

.content-wrap {
  display: flex;
  align-items: flex-start;

  .target-detail {
    flex-grow: 1;
    padding-right: 8px;
    padding-left: 8px;
    max-width: 1000px;
    height: calc(100vh - 144px);
    overflow-y: scroll;

    .detail-header {
      margin-bottom: 16px;

      .res-name {
        margin-bottom: 4px;
        font-weight: 700;
        font-size: 20px;
        color: #313238;
        line-height: 28px;
      }

      .res-header-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .res-desc {
          font-size: 14px;
          color: #979ba5;
          letter-spacing: 0;
          line-height: 22px;
        }

        .res-sdk {
          color: #3a84ff;
          cursor: pointer;
        }
      }
    }

    .detail-main {
      .res-basics,
      .res-detail-content {
        padding: 24px;
        background-color: #fff;
        box-shadow: 0 2px 4px 0 #1919290d;
        border-radius: 2px;
      }

      .res-basics {
        margin-bottom: 16px;
        display: grid;
        grid-template-columns: 280px 280px;
        grid-template-rows: 40px 40px;

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
    background-color: lighten(#c4c6cc, 80%);
  }

  &:hover::-webkit-scrollbar-thumb {
    background-color: #c4c6cc;
  }

  &::-webkit-scrollbar-thumb {
    height: 5px;
    border-radius: 2px;
    background-color: #f5f7fb;
  }

  &::-webkit-scrollbar-track {
    background-color: #f5f7fb;
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
      z-index: 1;
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
    line-height: 22px;
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

:deep(.code-box) {
  // 代码块高亮字体颜色
  .hljs-string {
    color: #ff9c01;
  }

  .hljs-keyword {
    color: #ea3636;
  }

  .hljs-comment {
    color: #c4c6cc;
  }
}
</style>
