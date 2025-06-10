<template>
  <div class="page-content">
    <bk-resize-layout
      :border="false"
      :max="400"
      :min="288"
      initial-divide="288px"
      placement="left"
    >
      <!--  左栏，API 列表  -->
      <template #aside>
        <div class="left-aside-wrap">
          <!--  筛选器  -->
          <header class="left-aside-header">
            <header class="title">{{ t('可用工具') }}</header>
            <main class="nav-filters">
              <bk-input
                v-model="keyword"
                :placeholder="t('请输入工具名称，描述搜索')"
                clearable
                type="search"
              />
            </main>
          </header>
          <!--  API 列表  -->
          <main class="tool-list custom-scroll-bar">
            <template v-if="filteredToolList.length">
              <bk-collapse v-model="activeGroupPanelNames" class="tool-group-collapse">
                <bk-collapse-panel v-for="group of toolGroupList" :key="group.id" :name="group.name">
                  <template #header>
                    <div class="tool-group-collapse-header">
                      <AngleUpFill
                        :class="{ fold: !activeGroupPanelNames.includes(group.name) }"
                        class="menu-header-icon"
                      />
                      <div class="tool-group-collapse-title">{{ group.name }}</div>
                    </div>
                  </template>
                  <template #content>
                    <article
                      v-for="tool in group.toolList"
                      :key="tool.id"
                      :class="{ active: tool.id === selectedTool?.id }"
                      class="tool-item"
                      @click="handleToolClick(tool.id, tool.name)"
                    >
                      <header
                        v-dompurify-html="getHighlightedHtml(tool.name)"
                        class="tool-item-name"
                      ></header>
                      <main v-dompurify-html="getHighlightedHtml(tool.description)" class="tool-item-desc"></main>
                    </article>
                  </template>
                </bk-collapse-panel>
              </bk-collapse>
            </template>
            <template v-else-if="keyword">
              <TableEmpty
                :keyword="keyword"
                @clear-filter="keyword = ''"
              />
            </template>
          </main>
        </div>
      </template>
      <!--  中间栏，当前 API 文档内容  -->
      <template #main>
        <div class="main-content-wrap">
          <header v-if="selectedTool" class="tool-name">
            <span class="name">{{ selectedTool.name }}</span>
            <span class="desc">（{{ selectedTool.description }}）</span>
          </header>
          <article class="tool-basics">
            <section class="basic-cell">
              <span>
                <span class="label">{{ t('更新时间') }}</span>：
                {{ updatedTime || '--' }}
              </span>
            </section>
            <section class="basic-cell">
              <span>
                <span v-bk-tooltips="t('应用访问该网关API时，是否需提供应用认证信息')" class="label">
                  {{ t('应用认证') }}
                </span>：
                {{ selectedTool?.verified_app_required ? t('是') : t('否') }}
              </span>
            </section>
            <section class="basic-cell">
              <span>
                <span
                  v-bk-tooltips="t('应用访问该网关API前，是否需要在开发者中心申请该网关API权限')" class="label"
                >
                  {{ t('权限申请') }}
                </span>：
                {{ selectedTool?.allow_apply_permission ? t('是') : t('否') }}
              </span>
            </section>
            <section class="basic-cell">
              <span>
                <span v-bk-tooltips="t('应用访问该网关API时，是否需要提供用户认证信息')" class="label">
                  {{ t('用户认证') }}
                </span>：
                {{ selectedTool?.verified_user_required ? t('是') : t('否') }}
              </span>
            </section>
          </article>
          <!--  API markdown 文档  -->
          <article v-if="selectedToolMarkdownHtml" class="tool-detail-content">
            <div id="toolDocMarkdown" v-dompurify-html="selectedToolMarkdownHtml" class="ag-markdown-view"></div>
          </article>
        </div>
      </template>
    </bk-resize-layout>
  </div>
</template>
<script lang="ts" setup>
import {
  computed,
  nextTick,
  ref,
  watch,
} from 'vue';
import { useI18n } from 'vue-i18n';
import TableEmpty from '@/components/table-empty.vue';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import { useRoute } from 'vue-router';
import {
  getServer,
  getServerToolDoc,
  getServerTools,
  type IMCPServerTool,
} from '@/http/mcp-server';
import { getMcpServerToolDoc } from '@/http/mcp-market';
import { useCommon } from '@/store';
import { copy } from '@/common/util';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';


type MCPServerType = Awaited<ReturnType<typeof getServer>>;

interface IProps {
  server: MCPServerType,
  page?: String,
}

const { server, page = 'server' } = defineProps<IProps>();

const emit = defineEmits<{
  'update-count': [count: number],
}>();

const { t } = useI18n();
const route = useRoute();
// const router = useRouter();
const common = useCommon();

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

const toolList = ref<IMCPServerTool[]>([]);
const keyword = ref('');  // 筛选器输入框的搜索关键字
const activeGroupPanelNames = ref<string[]>([]);  // 分类 collapse 展开的 panel
const selectedTool = ref<IMCPServerTool | null>(null); // 当前选中的 tool
const selectedToolName = ref('');
const selectedToolMarkdownHtml = ref('');
const updatedTime = ref<string | null>(null);
const isLoading = ref(false);

const filteredToolList = computed(() => {
  const regex = new RegExp(keyword.value, 'i');
  return toolList.value.filter(tool => regex.test(tool.name) || regex.test(tool.description));
});

// tool 分类列表
const toolGroupList = computed(() => {
  return filteredToolList.value?.reduce((groupList, tool) => {
    if (tool.labels[0]) {
      const { id, name } = tool.labels[0];
      const group = groupList.find(item => item.id === id);

      if (group) {
        group.toolList.push(tool);
      } else {
        groupList.push({
          id,
          name,
          toolList: [tool],
        });
      }
    }

    return groupList;
  }, [] as { id: number, name: string, toolList: typeof toolList.value }[]);
});

// watch(() => route.query, async () => {
//   if (route.query?.tool_name) {
//     selectedToolName.value = route.query.tool_name as string;
//     selectedTool.value = toolList.value.find(tool => tool.name === selectedToolName.value) ?? null;
//
//     if (selectedTool.value) {
//       await getDoc();
//     }
//   }
// }, { deep: true });

watch(() => server, () => {
  if (!server.id) {
    return;
  }
  fetchToolList();
}, { deep: true });

// 分类列表变化时更新 collapse 展开状态
watch(toolGroupList, () => {
  activeGroupPanelNames.value = toolGroupList.value.map(item => item.name);
});

watch(selectedToolMarkdownHtml, () => {
  initMarkdownHtml('toolDocMarkdown');
});

watch(toolList, () => {
  emit('update-count', toolList.value.length);
});

const fetchToolList = async () => {
  try {
    if (page === 'market') {
      toolList.value = server?.tools ?? [];
    } else {
      const res = await getServerTools(common.apigwId, server.id);
      toolList.value = res ?? [];
    }

    if (route.query?.tool_name) {
      selectedToolName.value = route.query.tool_name as string;
    }
    if (selectedToolName.value) {
      selectedTool.value = toolList.value.find(tool => tool.name === selectedToolName.value) ?? null;
    } else {
      selectedTool.value = toolList.value[0] ?? null;
    }
    if (selectedTool.value) {
      await getDoc();
    }
  } catch {
    toolList.value = [];
  }
};

const handleToolClick = async (resId: number, toolName: string) => {
  if (selectedTool.value?.id === resId) {
    return;
  }
  try {
    isLoading.value = true;
    selectedToolName.value = toolName;
    selectedTool.value = toolList.value.find(tool => tool.name === selectedToolName.value) ?? null;
    if (selectedTool.value) {
      await getDoc();
    }
  } finally {
    isLoading.value = false;
  }

  // router.replace({
  //   name: route.name,
  //   params: { ...route.params },
  //   query: {
  //     ...route.query,
  //     tool_name: toolName,
  //   },
  // });
};

const getDoc = async () => {
  try {
    isLoading.value = true;

    let res: any = {};
    if (page === 'market') {
      res = await getMcpServerToolDoc(server.id, selectedTool.value.name);
    } else {
      res = await getServerToolDoc(common.apigwId, server.id, selectedTool.value.name);
    }

    const { content, updated_time } = res;
    selectedToolMarkdownHtml.value = md.render(content);
    updatedTime.value = updated_time;
  } finally {
    isLoading.value = false;
  }
};

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

const getHighlightedHtml = (value: string) => {
  if (keyword.value) {
    return value.replace(new RegExp(`(${keyword.value})`, 'i'), '<em class="ag-keyword">$1</em>');
  }
  return value;
};

</script>

<style lang="scss" scoped>
$primary-color: #3a84ff;
$code-bc: #1e1e1e;
$code-color: #63656e;

.page-content {
  display: flex;
  height: 100%;
  box-shadow: 0 2px 4px 0 #1919290d;

  .left-aside-wrap {
    min-width: 280px;
    width: auto;
    box-shadow: 0 2px 4px 0 #1919290d;
    border-radius: 2px;
    background-color: #fff;

    .left-aside-header {
      padding: 24px 16px;

      .title {
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        line-height: 22px;
        font-weight: 700;
        font-size: 14px;
        color: #4d4f56;
      }
    }

    .tool-list {
      height: calc(100vh - 468px);
      overflow-y: scroll;

      .tool-group-collapse {
        max-height: 100%;
        overflow: auto;

        :deep(.bk-collapse-item) {
          margin-bottom: 12px;
        }

        :deep(.icon-angle-right) {
          display: none;
        }

        &::-webkit-scrollbar {
          width: 4px;
          background-color: lighten(#c4c6cc, 80%);
        }

        &::-webkit-scrollbar-thumb {
          height: 5px;
          border-radius: 2px;
          background-color: #c4c6cc;
        }

        .custom-icon {
          margin: -3px 6px 0 0;
          font-size: 13px;
          vertical-align: middle;
          display: inline-block;
        }

        .tool-group-collapse-header {
          padding: 4px 16px;
          display: flex;
          align-items: center;
          cursor: pointer;

          .tool-group-collapse-title {
            color: #63656e;
            margin-left: 4px;
            font-weight: bold;
          }

          .menu-header-icon {
            transition: all .2s;
            color: #979ba5;
            font-size: 14px;

            &.fold {
              transform: rotate(-90deg);
            }
          }
        }

        :deep(.bk-collapse-content) {
          padding: 2px 0;
        }
      }

      .tool-item {
        padding-left: 24px;
        height: 52px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        background: #fff;
        cursor: pointer;

        .tool-item-name,
        .tool-item-desc {
          display: -webkit-box;
          -webkit-line-clamp: 1;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .tool-item-name {
          font-size: 14px;
          color: #313238;
          line-height: 22px;
        }

        .tool-item-desc {
          font-size: 12px;
          color: #979ba5;
          line-height: 20px;
        }

        &:hover, &.active {
          background: #e1ecff;

          .tool-item-name {
            color: #3a84ff;
          }
        }
      }
    }
  }

  .main-content-wrap {
    height: calc(100vh - 354px);
    overflow-y: scroll;

    .tool-name,
    .tool-basics,
    .tool-detail-content {
      padding: 24px;
      background-color: #fff;
      box-shadow: 0 2px 4px 0 #1919290d;
      border-radius: 2px;
    }

    .tool-name {
      display: flex;
      align-items: center;
      gap: 6px;

      .name {
        font-weight: 700;
        font-size: 16px;
        color: #313238;
        line-height: 22px;
      }

      .desc {
        font-size: 12px;
        color: #979ba5;
        line-height: 20px;
      }
    }

    .tool-basics {
      display: grid;
      grid-template-columns: 280px 280px;
      grid-template-rows: 40px 40px;

      @container (width < 640px) {
        padding-block: 12px;
        grid-template-columns: 1fr;
        grid-template-rows: 40px 40px 40px 40px;
      }

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

  // 去掉右侧伸缩栏的拉伸线
  :deep(.bk-resize-layout-right > .bk-resize-layout-aside) {
    border-left: none;
    transition: none !important;
  }

  // 隐藏的折叠按钮
  :deep(.bk-resize-layout > .bk-resize-layout-aside .bk-resize-collapse) {
    // 避免折叠按钮溢出制造横向滚动条
    svg {
      width: 16px !important;
      height: 16px !important;
    }
  }
}

.custom-scroll-bar {
  &::-webkit-scrollbar {
    width: 4px;
    background-color: lighten(#c4c6cc, 80%);
  }

  &::-webkit-scrollbar-thumb {
    height: 5px;
    border-radius: 2px;
    background-color: #c4c6cc;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }
}

:deep(.ag-markdown-view) {
  font-size: 14px;
  text-align: left;
  color: $code-color;
  line-height: 19px;
  font-style: normal;

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
    line-height: 24px;
    position: relative;
    overflow: auto;
    margin: 14px 0;

    code {
      font-family: "Lucida Console", "Courier New", "Monaco", monospace;
      color: #dcdcdc;
    }

    .hljs {
      margin: -10px;
    }
  }
}
</style>
