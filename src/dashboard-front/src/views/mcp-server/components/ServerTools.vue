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
  <div class="page-content">
    <BkResizeLayout
      :border="false"
      :max="400"
      :min="293"
      initial-divide="293px"
      placement="left"
    >
      <!--  左栏，API 列表  -->
      <template #aside>
        <div class="left-aside-wrap">
          <!--  筛选器  -->
          <header class="left-aside-header">
            <header class="title">
              {{ t('可用工具') }}
            </header>
            <main class="nav-filters">
              <BkInput
                v-model="keyword"
                :placeholder="t('请输入工具名称，描述搜索')"
                clearable
                type="search"
              />
            </main>
          </header>
          <!--  API 列表  -->
          <main
            class="tool-list custom-scroll-bar"
            :style="{ height: setSideMaxH }"
          >
            <template v-if="filteredToolList.length">
              <BkCollapse
                v-model="activeGroupPanelNames"
                class="tool-group-collapse"
              >
                <BkCollapsePanel
                  v-for="group of toolGroupList"
                  :key="group.id"
                  :name="group.name"
                >
                  <template #header>
                    <div class="tool-group-collapse-header">
                      <AngleUpFill
                        :class="{ fold: !activeGroupPanelNames.includes(group.name) }"
                        class="menu-header-icon"
                      />
                      <div class="tool-group-collapse-title">
                        {{ group.name }}
                      </div>
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
                        v-bk-xss-html="getHighlightedHtml(tool.tool_name || tool.name)"
                        v-bk-tooltips="{
                          placement:'top',
                          content: `${t('名称')}: ${tool.tool_name || tool.name}
                            ${t('描述')}: ${tool.description}`,
                          disabled: !tool.isOverflow,
                          extCls: 'max-w-480px',
                          delay: 0
                        }"
                        class="truncate color-#4d4f56 tool-item-name"
                        @mouseenter="(e: MouseEvent) => handleToolMouseenter(e, tool)"
                        @mouseleave="() => handleToolMouseleave(tool)"
                      />
                      <main
                        v-bk-xss-html="getHighlightedHtml(tool.description)"
                        v-bk-tooltips="{
                          placement:'top',
                          content: `${t('名称')}: ${tool.tool_name || tool.name}
                          ${t('描述')}: ${tool.description}`,
                          disabled: !tool.isOverflow,
                          extCls: 'max-w-480px',
                          delay: 0
                        }"
                        class="truncate color-#979ba5 tool-item-desc"
                        @mouseenter="(e: MouseEvent) => handleToolMouseenter(e, tool)"
                        @mouseleave="() => handleToolMouseleave(tool)"
                      />
                    </article>
                  </template>
                </BkCollapsePanel>
              </BkCollapse>
            </template>
            <template v-else-if="keyword">
              <TableEmpty
                empty-type="searchEmpty"
                @clear-filter="keyword = ''"
              />
            </template>
            <TableEmpty v-else />
          </main>
        </div>
      </template>
      <!--  中间栏，当前 API 文档内容  -->
      <template #main>
        <div
          class="main-content-wrap"
          :style="{ height: setMainMaxH }"
        >
          <template v-if="selectedTool">
            <header class="tool-name">
              <div
                v-bk-tooltips="{
                  content: selectedTool.tool_name || selectedTool.name,
                  disabled: selectedTool.tool_name
                    ? selectedTool.tool_name.length <= 30
                    : selectedTool.name.length <= 30
                }"
                class="name"
              >
                {{ truncate(selectedTool.tool_name || selectedTool.name) }}
              </div>
              <BkButton
                theme="primary"
                text
                class="ml-16px"
                @click="handleNavDocDetail"
              >
                <AgIcon
                  name="jump"
                  size="16"
                  class="mr-6px"
                />
                {{ t('查看文档详情') }}
              </BkButton>
            </header>
            <div class="pl-40px pr-40px mb-16px">
              <AgDescription class="color-#979ba5 break-all gap-4px">
                <template #description>
                  {{ selectedTool?.description }}
                </template>
              </AgDescription>
            </div>
            <article class="tool-basics">
              <section class="basic-cell">
                <span>
                  <span class="label">{{ t('更新时间') }}</span>：
                  {{ updatedTime || '--' }}
                </span>
              </section>
              <section class="basic-cell">
                <span>
                  <span
                    v-bk-tooltips="t('应用访问该网关API时，是否需提供应用认证信息')"
                    class="label"
                  >
                    {{ t('应用认证') }}
                  </span>：
                  {{ selectedTool?.verified_app_required ? t('是') : t('否') }}
                </span>
              </section>
              <section class="basic-cell">
                <span>
                  <span
                    v-bk-tooltips="t('应用访问该网关API前，是否需要在开发者中心申请该网关API权限')"
                    class="label"
                  >
                    {{ t('权限申请') }}
                  </span>：
                  {{ selectedTool?.allow_apply_permission ? t('是') : t('否') }}
                </span>
              </section>
              <section class="basic-cell">
                <span>
                  <span
                    v-bk-tooltips="t('应用访问该网关API时，是否需要提供用户认证信息')"
                    class="label"
                  >
                    {{ t('用户认证') }}
                  </span>：
                  {{ selectedTool?.verified_user_required ? t('是') : t('否') }}
                </span>
              </section>
            </article>
          </template>
          <!--  API markdown 文档  -->
          <article class="tool-detail-content">
            <div class="schema-wrapper">
              <article class="schema-group">
                <h3 class="title mt-0!">
                  {{ t('请求参数') }}
                </h3>
                <RequestParams
                  v-if="!selectedToolSchema?.none_schema &&
                    (selectedToolSchema?.parameters?.length
                      || Object.keys(selectedToolSchema?.requestBody || {}).length)"
                  :detail="{ schema: selectedToolSchema }"
                  readonly
                />
                <div v-else>
                  {{ t('该资源无请求参数') }}
                </div>
              </article>
              <article class="schema-group">
                <h3 class="title">
                  {{ t('响应参数') }}
                </h3>
                <ResponseParams
                  v-if="Object.keys(selectedToolSchema?.responses || {}).length"
                  :detail="{ schema: selectedToolSchema }"
                  readonly
                />
                <div v-else>
                  {{ t('该资源无响应参数') }}
                </div>
              </article>
            </div>
          </article>
          <!-- <TableEmpty v-else /> -->
        </div>
      </template>
    </BkResizeLayout>
  </div>
</template>

<script lang="ts" setup>
import TableEmpty from '@/components/table-empty/Index.vue';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import { useRouteParams } from '@vueuse/router';
import { useFeatureFlag, useGateway } from '@/stores';
import {
  type IMCPServerTool,
  getServer,
  getServerToolDoc,
  getServerTools,
} from '@/services/source/mcp-server';
import { getMcpServerToolDoc } from '@/services/source/mcp-market';
import { copy } from '@/utils';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import AgIcon from '@/components/ag-icon/Index.vue';
import ResponseParams from '@/views/resource-management/components/response-params/Index.vue';
import RequestParams from '@/views/resource-management/components/request-params/Index.vue';
import AgDescription from '@/components/ag-description/Index.vue';
import { truncate } from 'lodash-es';

type MCPServerType = Awaited<ReturnType<typeof getServer>>;

interface IProps {
  server: MCPServerType
  page?: string
}

const { server, page = 'server' } = defineProps<IProps>();

const emit = defineEmits<{ 'update-count': [count: number] }>();

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
// 网关id
const gatewayId = useRouteParams('id', 0, { transform: Number });
const gatewayStore = useGateway();
const featureFlagStore = useFeatureFlag();

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

const toolList = ref<IMCPServerTool[]>([]);
const keyword = ref(''); // 筛选器输入框的搜索关键字
const activeGroupPanelNames = ref<string[]>([]); // 分类 collapse 展开的 panel
const selectedTool = ref<IMCPServerTool | null>(null); // 当前选中的 tool
const selectedToolName = ref('');
const selectedToolMarkdownHtml = ref('');
const selectedToolSchema = ref();
const updatedTime = ref<string | null>(null);
const isLoading = ref(false);

const filteredToolList = computed(() => {
  const regex = new RegExp(keyword.value, 'i');
  return toolList.value.filter((tool) => {
    const searchName = tool.tool_name || tool.name;
    return regex.test(searchName) || regex.test(tool.description);
  });
});
// tool 分类列表
const toolGroupList = computed(() => {
  return filteredToolList.value?.reduce((groupList, tool) => {
    if (tool.labels[0]) {
      const { id, name } = tool.labels[0];
      const group = groupList.find(item => item.id === id);
      if (group) {
        group.toolList.push(tool);
      }
      else {
        groupList.push({
          id,
          name,
          toolList: [tool],
        });
      }
    }
    else {
      const group = groupList.find(item => item.id === 0);
      if (group) {
        group.toolList.push(tool);
      }
      else {
        groupList.push({
          id: 0,
          name: t('默认分类'),
          toolList: [tool],
        });
      }
    }

    return groupList;
  }, [] as {
    id: number
    name: string
    toolList: typeof toolList.value
  }[]);
});
const isShowNoticeAlert = computed(() => featureFlagStore.isEnabledNotice);
const setSideMaxH = computed(() => {
  if (page === 'market') {
    return '100%';
  }
  const offsetH = isShowNoticeAlert.value ? 516 : 476;
  return `calc(100vh - ${offsetH}px)`;
});
const setMainMaxH = computed(() => {
  if (page === 'market') {
    return '100%';
  }
  const offsetH = isShowNoticeAlert.value ? 410 : 370;
  return `calc(100vh - ${offsetH}px)`;
});

watch(() => server, () => {
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
  if (!server?.id) {
    return;
  }
  try {
    if (page === 'market') {
      toolList.value = server?.tools ?? [];
    }
    else {
      const res = await getServerTools(gatewayId.value, server.id);
      toolList.value = res ?? [];
    }

    if (route.query?.tool_name) {
      selectedToolName.value = route.query.tool_name as string;
    }
    if (selectedToolName.value) {
      selectedTool.value = toolList.value.find(tool => tool.name === selectedToolName.value) ?? null;
    }
    else {
      selectedTool.value = toolList.value[0] ?? null;
    }
    if (selectedTool.value) {
      await getDoc();
    }
  }
  catch {
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
  }
  finally {
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
    }
    else {
      res = await getServerToolDoc(gatewayId.value, server.id, selectedTool.value.name);
    }

    const { content, updated_time, schema } = res;
    selectedToolMarkdownHtml.value = md.render(content);
    updatedTime.value = updated_time;
    selectedToolSchema.value = schema || '';
  }
  finally {
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

const handleNavDocDetail = () => {
  const routeData = router.resolve({
    name: 'ApiDocDetail',
    params: {
      curTab: 'gateway',
      targetName: gatewayStore?.currentGateway?.name || server?.gateway?.name || '',
    },
    query: { apiName: selectedTool.value.name },
  });
  window.open(routeData.href, '_blank');
};

const handleToolMouseenter = (e: MouseEvent, row: IMCPServerTool) => {
  const cell = (e.target as HTMLElement).closest('.truncate');
  if (cell) {
    row.isOverflow = cell.scrollWidth > cell.offsetWidth;
  };
};

const handleToolMouseleave = (row: IMCPServerTool) => {
  delete row.isOverflow;
};

onMounted(() => {
  fetchToolList();
});

</script>

<style lang="scss" scoped>
@use "sass:color";

$primary-color: #3a84ff;
$code-bc: #f6f8fa;
$code-color: #63656e;

.page-content {
  display: flex;
  height: 100%;
  box-shadow: 0 2px 4px 0 #1919290d;

  .left-aside-wrap {
    width: auto;
    min-width: 290px;
    height: 100%;
    background-color: #ffffff;
    border-radius: 2px;
    box-shadow: 0 2px 4px 0 #1919290d;

    .left-aside-header {
      padding: 24px 16px;

      .title {
        display: flex;
        margin-bottom: 12px;
        font-size: 14px;
        font-weight: 700;
        line-height: 22px;
        color: #4d4f56;
        align-items: center;
      }
    }

    .tool-list {
      overflow-y: auto;

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
          background-color: color.scale(#c4c6cc, $lightness: 80%);
        }

        &::-webkit-scrollbar-thumb {
          height: 5px;
          background-color: #c4c6cc;
          border-radius: 2px;
        }

        .custom-icon {
          display: inline-block;
          margin: -3px 6px 0 0;
          font-size: 13px;
          vertical-align: middle;
        }

        .tool-group-collapse-header {
          display: flex;
          padding: 4px 16px;
          cursor: pointer;
          align-items: center;

          .tool-group-collapse-title {
            margin-left: 8px;
            font-size: 12px;
            color: #4d4f56;
          }

          .menu-header-icon {
            font-size: 12px;
            color: #979ba5;
            transition: all .2s;

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
        display: flex;
        height: 48px;
        padding-left: 52px;
        cursor: pointer;
        background: #fff;
        flex-direction: column;
        justify-content: center;

        .tool-item-name,
        .tool-item-desc {
          font-size: 12px;
          line-height: 20px;
        }

        &:hover,
        &.active {
          background: #e1ecff;

          .tool-item-name,
          .tool-item-desc {
            color: #3a84ff;
          }
        }

        &.active {

          .tool-item-name {
            font-weight: 700;
          }
        }
      }
    }
  }

  .main-content-wrap {
    overflow-y: auto;
    background-color: #ffffff;

    .tool-name,
    .tool-basics,
    .tool-detail-content {
      padding: 24px 24px 24px 40px;
      background-color: #fff;
      border-radius: 2px;
    }

    .tool-name {
      display: flex;
      align-items: center;
      gap: 6px;

      .name {
        max-width: 660px;
        font-size: 16px;
        font-weight: 700;
        line-height: 22px;
        color: #313238;
      }
    }

    .tool-basics {
      padding-block: 0;
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

  :deep(.bk-resize-layout.bk-resize-layout-left) {
    flex: 1 !important;
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
    background-color: color.scale(#c4c6cc, $lightness: 80%);
  }

  &::-webkit-scrollbar-thumb {
    height: 5px;
    background-color: #c4c6cc;
    border-radius: 2px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
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
    border-radius: 2px;

    code {
      font-family: "Lucida Console", "Courier New", Monaco, monospace;
      text-wrap: wrap;
    }

    .hljs {
      margin: -10px;
    }
  }
}

.schema-wrapper {

  .schema-group {

    .title {
      padding: 0;
      margin: 25px 0 10px;
      font-size: 16px;
      font-weight: bold;
      line-height: 22px;
      color: #313238;
      text-align: left;
    }
  }
}
</style>
